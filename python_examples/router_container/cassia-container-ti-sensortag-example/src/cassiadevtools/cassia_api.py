"""This module contains a class that interfaces with the Cassia RESTful API.

The CassiaApi class contains methods that interface with the
Cassia RESTful API for the container, rouer, and AC.

  The api_type parameter

  Typical usage example:

  cassia_api = CassiaApi('router', '10.10.10.254')

TODO: Add more Cassia RESTful API methods.
"""

from enum import Enum

class CassiaApi:
    CONTAINER_ADDRESS = "10.10.10.254";
    class ApiType(Enum):
        CONTAINER = 'container'
        ROUTER = 'router'
        AC = 'ac'

    def __init__(self, api_type, api_domain=CONTAINER_ADDRESS):
        try:
            ApiType(api_type)
        except ValueError as ve:
            print(ve)
            print("Please provide a valid api_type value:"
                  "'container', 'router', 'ac'")
        else:
            self.api_type = api_type

        self.api_domain = api_domain
        #  TODO: make local variables using __
        #self.

    def scan(self):
        print('scan')
        pass

    def connect(self):
        print('connect')
        pass

    def disconnect(self):
        print('disconnect')
        pass

    def open_notify(self):
        print('open_notify')
        pass

    def close_notify(self):
        pass
