import hashlib
import json
import threading

from user import User
from endorsement import EndorsementRequest, Endorsement

class Peoplechain:

    users = []
    endorsements = []
    endorsement_requests = []

    def __init__(self, remote_chain_data=None):

        self.users_lock = threading.Lock()
        self.endorsements_lock = threading.Lock()
        self.endorsement_requests_lock = threading.Lock()
        if remote_chain_data is None:
            self.users = []
            self.endorsements = []
            self.endorsement_requests = []
        else:
            for user in remote_chain_data['users']:
                new_user = User.from_json(json.loads(user))
                self.add_user(new_user)
            for endorsement in remote_chain_data['endorsements']:
                new_endorsement = Endorsement.from_json(json.loads(endorsement))
                self.add_endorsement(new_endorsement)
            for endorsement_request in remote_chain_data['endorsement_requests']:
                new_endorsement_request = EndorsementRequest.from_json(json.loads(endorsement_request))
                self.add_endorsement_request(new_endorsement_request)

    def add_user(self, user):
        with self.users_lock:
            self.users.append(user)
            return True
        return False

    def add_endorsement(self, endorsement):
        with self.endorsements_lock:
            self.endorsements.append(endorsement)
            return True
        return False

    def add_endorsement_request(self, endorsement_request):
        with self.endorsement_requests_lock:
            self.endorsement_requests.append(endorsement_request)
            return True
        return False

    def get_user_by_address(self, address):
        for user in self.users:
            if address == user.address:
                return user
        return None

    def remove_endorsement_request(self, endorser, endorsee):
        with self.endorsement_requests_lock:
            for each in self.endorsement_requests:
                if each.endorser == endorser and each.endorsee == endorsee:
                    self.endorsement_requests.remove(each)
                    return
