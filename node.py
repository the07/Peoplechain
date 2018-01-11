import json
import socket
import requests
import random

from klein import Klein

from user import User
from endorsement import EndorsementRequest, Endorsement
from peoplechain import Peoplechain

FULL_NODE_PORT = "30609"
NODES_URL = "http://{}:{}/nodes"
CHAIN_URL = "http://{}:{}/chain"

class Node:

    full_nodes = set()
    app = Klein()

    def __init__(self, host='34.216.166.186'):
        #TODO: if a config file exists, load from config file else start a new chain
        if host is None:
            self.peoplechain = Peoplechain()
            self.node = self.get_my_node()
            self.full_nodes.add(self.node)
        else:
            self.node = self.get_my_node()
            self.add_node(host)
            self.request_nodes_from_all()
            self.broadcast_node()
            self.full_nodes.add(self.node)
            remote_chain_data = self.download()
            self.peoplechain = Peoplechain(remote_chain_data)


        print ("\n Full Node Server Started... \n\n")
        self.app.run('0.0.0.0', FULL_NODE_PORT)

    def request_nodes_from_all(self):
        full_nodes = self.full_nodes.copy()
        bad_nodes = set()

        for node in full_nodes:
            all_nodes = self.request_nodes(node)
            if all_nodes is not None:
                full_nodes = full_nodes.union(all_nodes['full_nodes'])
            else:
                bad_nodes.add(node)

        self.full_nodes = full_nodes

        for node in bad_nodes:
            self.remove_node(node)

        bad_nodes.clear()
        return

    def request_nodes(self, host):
        url = NODES_URL.format(host, FULL_NODE_PORT)
        try:
            response = requests.get(url)
            if response.status_code == 200:
                all_nodes = response.json()
                return all_nodes
        except requests.exceptions.RequestException as re:
            pass
        return None

    def broadcast_node(self):

        bad_nodes = set()
        data = {
            "host": self.node
        }

        for node in self.full_nodes:
            if node == self.node:
                continue
            url = NODES_URL.format(node, FULL_NODE_PORT)
            try:
                requests.post(url, json=data)
            except requests.exceptions.RequestException as re:
                bad_nodes.add(node)

        for node in bad_nodes:
            self.remove_node(node)
        bad_nodes.clear()
        return

    def random_node(self):
        all_nodes = self.full_nodes.copy()
        all_nodes.remove(self.node)
        node = random.sample(all_nodes, 1)[0]
        return node


    def download(self):
        print ("Randomly select a node from full nodes")
        node = self.random_node()
        print("Downloading chain from: {}".format(node))
        url = CHAIN_URL.format(node, FULL_NODE_PORT)
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()

    def shout(self, broadcast_object):
        full_nodes = self.full_nodes.copy()
        bad_nodes = set()
        for node in full_nodes:
            if node == self.node:
                continue
            url = CHAIN_URL.format(node, FULL_NODE_PORT)
            if type(broadcast_object) == User:
                data = {
                    "user": broadcast_object.to_json()
                }
            elif type(broadcast_object) == EndorsementRequest:
                data = {
                    "endorsement_request": broadcast_object.to_json()
                }
            elif type(broadcast_object) == Endorsement:
                data = {
                    "endorsement": broadcast_object.to_json()
                }

            try:
                requests.post(url, json=data)
            except requests.exceptions.RequestException as re:
                bad_nodes.add(node)



    def get_my_node(self):
        my_node = requests.get('https://api.ipify.org').text
        return my_node

    def add_node(self, node):
        if node == self.node:
            return
        if node not in self.full_nodes:
            self.full_nodes.add(node)

    def approve_endorsements(self, endorser, endorsee_list):
        for each_endorsee in endorsee_list:
            self.peoplechain.remove_endorsement_request(endorser, each_endorsee)
            endorsement = Endorsement(each_endorsee, endorser, 5, 'SIGNED')
            self.peoplechain.add_endorsement(endorsement)
            self.shout(endorsement)
            return

    @app.route('/', methods=['GET'])
    def get_root(self, request):
        return "This is a Peoplechain Node, not much you can do here."

    @app.route('/user/<address>', methods=['GET'])
    def get_user_data(self, request, address):
        user = self.peoplechain.get_user_by_address(address)
        if user is None:
            response = "User not found!"
            return json.dumps(response).encode('utf-8')
        else:
            user_data = user.to_json()
            return json.dumps(user_data).encode('utf-8')


    @app.route('/user', methods=['POST'])
    def create_user(self, request):
        user_json = json.loads(request.content.read().decode('utf-8'))
        user = User(user_json['name'], user_json['signature'], user_json['user_type'])
        self.peoplechain.add_user(user)
        self.shout(user)
        response = {
            "message": "Profile created",
            "address": user.address
        }
        return json.dumps(response).encode('utf-8')

    @app.route('/users', methods=['GET'])
    def get_all_users(self, request):
        print (self.peoplechain.users)

    @app.route('/endorsements/request/<address>', methods=['GET'])
    def get_endorsment_requests_by_address(self, request, address):
        er_by_address = []
        for er in self.peoplechain.endorsement_requests:
            if er.endorser == address:
                er_by_address.append(er)
        if len(er_by_address) > 0:
            return json.dumps([ers.to_json() for ers in er_by_address]).encode('utf-8')
        return

    @app.route('/endorsements/request/', methods=['POST'])
    def add_endorsement_request(self, request):
        endorsement_request_json = json.loads(request.content.read().decode('utf-8'))
        endorsement_request = EndorsementRequest(endorsement_request_json['endorsee'], endorsement_request_json['endorser'])
        self.peoplechain.add_endorsement_request(endorsement_request)
        self.shout(endorsement_request)
        response = {
            "message": "Endorsement Request added"
        }
        return json.dumps(response).encode('utf-8')

    @app.route('/endorsements/<address>', methods=['GET'])
    def get_endorsements_by_address(self, request, address):
        e_by_address = []
        for e in self.peoplechain.endorsements:
            if e.endorsee == address:
                e_by_address.append(e)
        if len(e_by_address) > 0:
            return json.dumps([es.to_json() for es in e_by_address]).encode('utf-8')
        return

    @app.route('/endorsements', methods=['POST'])
    def add_endorsement(self, request):
        data = request.content.read().decode('utf-8')
        data_json = json.loads(data)
        endorser = data_json['endorser']
        endorsee_list = data_json['endorsees']
        self.approve_endorsements(endorser, endorsee_list)
        return

    @app.route('/nodes', methods=['GET'])
    def get_nodes(self, request):
        response = {
            "full_nodes": list(self.full_nodes)
        }
        return json.dumps(response).encode('utf-8')

    @app.route('/nodes', methods=['POST'])
    def post_node(self, request):
        request = json.loads(request.content.read().decode('utf-8'))
        host = request['host']
        self.add_node(host) #TODO: create a add_node function
        response = {
            "message": "Node Register"
        }
        return json.dumps(response).encode('utf-8')

    @app.route('/chain', methods=['GET'])
    def get_chain(self, request):
        data = {
            "users": [user.to_json() for user in self.peoplechain.users],
            "endorsements": [endorsement.to_json() for endorsement in self.peoplechain.endorsements],
            "endorsement_requests": [endorsement_request.to_json() for endorsement_request in self.peoplechain.endorsement_requests]
        }
        return json.dumps(data).encode('utf-8')

    @app.route('/chain', methods=['POST'])
    def update_chain(self, request):
        data_json = json.loads(request.content.read().decode('utf-8'))
        if 'user' in data_json:
            user_json = json.loads(data_json['user'])
            user = User.from_json(user_json)
            self.peoplechain.add_user(user)
            return
        if 'endorsement' in data_json:
            endorsement_json = json.loads(data_json['endorsement'])
            endorsement = Endorsement.from_json(endorsement_json)
            self.peoplechain.approve_endorsements(endorsement)
            return
        if 'endorsement_request' in data_json:
            endorsement_request_json = json.loads(data_json['endorsement_request'])
            endorsement_request = EndorsementRequest.from_json(endorsement_request_json)
            self.peoplechain.add_endorsement_request(endorsement_request)
            return
        return


if __name__ == '__main__':
    full_node = Node()
