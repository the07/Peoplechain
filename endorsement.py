import json
import hashlib

class EndorsementRequest:

    def __init__(self, endorsee, endorser):

        self._endorsee = endorsee
        self._endorser = endorser

    @property
    def endorsee(self):
        return self._endorsee

    @property
    def endorser(self):
        return self._endorser

    @classmethod
    def from_json(cls, endorsement_request_json):
        endorsement_request = cls(endorsement_request_json['endorsee'], endorsement_request_json['endorser'])
        return endorsement_request

    def to_json(self):
        return json.dumps(self, default=lambda o: {key.lstrip('_'): value for key, value in o.__dict__.items()}, sort_keys=True)

    def __repr__(self):
        return "<Endorsement Request from {}>".format(self._endorsee)

    def __str__(self):
        return str(self.__dict__)

class Endorsement(EndorsementRequest):

    def __init__(self, endorsee, endorser, score, signature):
        super().__init__(endorsee, endorser)
        self._score = score
        self._signature = signature

    @property
    def score(self):
        return self._score

    @property
    def signature(self):
        return self._signature

    @classmethod
    def from_json(cls, endorsement_json):
        endorsement = cls(endorsement_json['endorsee'], endorsement_json['endorser'], endorsement_json['score'], endorsement_json['signature'])
        return endorsement

    def __repr__(self):
        return "<Endorsement for {}>".format(self._endorsee)

if __name__ == '__main__':
    pass
