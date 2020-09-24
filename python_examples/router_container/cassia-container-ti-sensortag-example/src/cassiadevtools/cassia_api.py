"""This module contains a class that interfaces with the Cassia RESTful API.

The CassiaApi class contains methods that interface with the
Cassia RESTful API for the container, router, and AC.

  The api_type parameter

  Typical usage example:

  cassia_api = CassiaApi('router', '10.10.10.254')

TODO: Add more Cassia RESTful API methods.
"""

from enum import Enum
from aiohttp_sse_client import client as sse_client

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
        self.__is_sse_scan = False
        self.__is_sse_notify = False
        self.__ac_access_token = ''

    def scan(self):
        async with sse_client.EventSource(self.api_domain) as event_source:
            try:
                async for event in event_source:
                    print(event)
            except ConnectionError as e:
                print(e)

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
