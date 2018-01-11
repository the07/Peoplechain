import json
import hashlib
from klein import Klein
import requests
from twisted.web.static import File
from bs4 import BeautifulSoup

CLIENT_PORT = '30906'
FULL_NODE_PORT = '30609'

class Client:

    app = Klein()
    session = set()

    def __init__(self, host='34.216.166.186'):

        self.host = host
        self.app.run('0.0.0.0', CLIENT_PORT)

    def get_endorsement_requests(self, address):
        url = 'http://{}:{}/endorsements/request/{}'.format(self.host, FULL_NODE_PORT, address)
        response = requests.get(url)
        response_content = response.content.decode('utf-8')
        if response_content is not '':
            response_list = json.loads(response.content.decode('utf-8'))
            endorsement_requests = []
            for item in response_list:
                endorsement_requests.append(json.loads(item))
            return endorsement_requests
        else:
            return []

    def get_endorsements(self, address):
        url = 'http://{}:{}/endorsements/{}'.format(self.host, FULL_NODE_PORT, address)
        response = requests.get(url)
        response_content = response.content.decode('utf-8')
        if response_content is not '':
            response_list = json.loads(response.content.decode('utf-8'))
            endorsement_list = []
            for item in response_list:
                endorsement_list.append(json.loads(item))
            return endorsement_list
        else:
            return []


    @app.route('/', methods=['GET'], branch=True)
    def get_root(self, request):
        return File('./web/')

    @app.route('/signup', methods=['POST'])
    def signup(self, request):
        content = request.content.read().decode('utf-8')
        user_data = content.split('&')
        name = user_data[0].split('=')[1]
        password = user_data[1].split('=')[1]
        signature = hashlib.sha256(password.encode()).hexdigest()
        user_type = user_data[2].split('=')[1]
        data = {
            "name": name,
            "signature": signature,
            "user_type": user_type
        }
        url = "http://{}:{}/user".format(self.host, FULL_NODE_PORT)
        response = requests.post(url, json=data)
        if response.status_code == 200:
            message = "Your account has been created, please note your address: {}. <a href='index.html'>Login</a>".format(response.json()['address'])
            return message

    @app.route('/login', methods=['POST'])
    def login(self, request):
        content = request.content.read().decode('utf-8')
        login_data = content.split('&')
        address = login_data[0].split('=')[1]
        password = login_data[1].split('=')[1]
        #TODO: verify password
        self.session.add(address)
        request.redirect('/user')
        return

    @app.route('/logout', methods=['GET'])
    def logout(self, request):
        self.session.clear()
        request.redirect('/')
        return

    @app.route('/user', methods=['GET'])
    def user_profile(self, request):
        if len(self.session) == 0:
            message = "Please login. <a href='index.html'>Login</a>"
            return message
        else:
            for data in self.session:
                user_address = data
            endorsement_requests = self.get_endorsement_requests(user_address)
            endorsements = self.get_endorsements(user_address)
            url = "http://{}:{}/user/{}".format(self.host, FULL_NODE_PORT, user_address) #TODO: send address and signature as authorization headers
            response = requests.get(url)
            user_data = json.loads(response.json())

            html_file = open('web/user.html').read()
            soup = BeautifulSoup(html_file, 'html.parser')

            original_tag = soup.b
            new_tag = soup.new_tag('a', href='/logout')
            new_tag.string = "Logout"
            original_tag.append(new_tag)

            if len(endorsements) > 0:
                endorsements_div = soup.find(id="endorsements")
                for each in endorsements:
                    new_p_tag = soup.new_tag('p')
                    new_p_tag.string = "Endorsed by: " + each['endorser']
                    endorsements_div.append(new_p_tag)

            if len(endorsement_requests) > 0:
                endorsement_requests_form = soup.find(id="endorsement_requests_form")
                for each_item in endorsement_requests:
                    new_input_tag = soup.new_tag("input", type="checkbox", checked="checked", value=each_item['endorsee'])
                    new_input_tag["name"] = each_item['endorsee']
                    new_input_tag.string = each_item['endorsee']
                    endorsement_requests_form.append(new_input_tag)
                submit_tag = soup.new_tag("input", type="submit", value="Accept")
                endorsement_requests_form.append(submit_tag)

            soup.find(id="name").string = user_data['name']
            soup.find(id="address").string = user_data['address']
            soup.find(id="balance").string = str(user_data['balance'])
            soup.find(id="user_type").string = str(user_data['user_type'])

            return str(soup)

    @app.route('/endorsement/request', methods=['POST'])
    def request_endorsement(self, request):
        content = request.content.read().decode('utf-8')
        endorser = content.split('=')[1]
        for address in self.session:
            endorsee = address
        data = {
            "endorser": endorser,
            "endorsee": endorsee
        }
        url = "http://{}:{}/endorsements/request/".format(self.host, FULL_NODE_PORT)
        response = requests.post(url, json=data)
        print (response)
        if response.status_code == 200:
            message = "Endorsement request sent, <a href='/user'>Go back</a>"
            return message

    @app.route('/endorsement', methods=['POST'])
    def approve_endorsement(self, request):
        content = request.args.keys()
        endorsee_approved = []
        for each_endorsee in content:
            endorsee_approved.append(each_endorsee.decode('utf-8'))
        for address in self.session:
            endorser = address
        data = {
            "endorsees": endorsee_approved,
            "endorser": endorser
        }
        url = "http://{}:{}/endorsements".format(self.host, FULL_NODE_PORT)
        response = requests.post(url, json=data)
        if response.status_code == 200:
            message = "Endorsement approval sent, <a href='/user'>Go back</a>"
            return message


if __name__ == '__main__':
    client = Client(host)
