import hashlib
from uuid import uuid4
import json

class User:

    def __init__(self, name, signature, user_type, address=None, balance=None):
        self._name = name
        self._signature = signature
        self._user_type = user_type
        if address is None:
            self._address = uuid4().hex
        else:
            self._address = address
        if balance is None:
            self._balance = 100
        else:
            self._balance = balance

    @property
    def signature(self):
        return self._signature

    @property
    def name(self):
        return self._name

    @property
    def address(self):
        return self._address

    @property
    def balance(self):
        return self._balance

    @property
    def user_type(self):
        return self._user_type

    @balance.setter
    def balance(self, value):
        self._balance = value

    @classmethod
    def from_json(cls, user_json):
        user = cls(user_json['name'], user_json['signature'], user_json['user_type'], user_json['address'], user_json['balance'])
        return user

    def to_json(self):
        return json.dumps(self, default=lambda o: {key.lstrip('_'): value for key, value in o.__dict__.items()}, sort_keys=True)

    def __repr__(self):
        return "<User {}>".format(self._address)

    def __str__(self):
        return str(self.__dict__)

if __name__ == '__main__':
    pass
