import asyncio
import aiohttp
from aiohttp_sse_client import client as sse_client_async
import json
from urllib.parse import urlencode

# Configuration
AC_HOST = 'http://10.100.144.168:8882/api'
DEVELOPER_KEY = 'admin1'
DEVELOPER_SECRET = '1q2w#E$R'
ROUTER_MAC = 'CC:1B:E0:E2:E9:B8'

class DeviceQueue:
    def __init__(self):
        self._queue = []
        self._unique_check = set()

    def enqueue(self, device):
        if device['mac'] not in self._unique_check:
            self._queue.append(device)
            self._unique_check.add(device['mac'])

    def dequeue(self):
        if not self._queue:
            return None
        device = self._queue.pop(0)
        self._unique_check.remove(device['mac'])
        return device

async def req(session, method, url, headers=None, json_data=None, auth=None):
    async with session.request(method, url, headers=headers, json=json_data, auth=auth) as resp:
        try:
            if resp.content_type == 'application/json':
                return await resp.json()
            else:
                return await resp.text()
        except Exception as e:
            raise Exception(f"Failed to parse response: {e}")

async def authenticate(session, key, secret):
    auth_url = f"{AC_HOST}/oauth2/token"
    auth = aiohttp.BasicAuth(key, secret)
    data = {"grant_type": "client_credentials"}
    return await req(session, 'POST', auth_url, json_data=data, auth=auth)

async def open_scan_sse(session, token, router_mac):
    params = {
        'filter_rssi': -75,
        'filter_name': 'Cassia*',
        'filter_mac': 'CC:0A:19:32:6A:0A',
        'active': 1,
        'mac': router_mac,
        'access_token': token,
        'event': 1
    }
    url = f"{AC_HOST}/gap/nodes?{urlencode(params)}"
    
    async def handle_scan_event(event):
        try:
            data = json.loads(event.data)
            device_mac = data['bdaddrs'][0]['bdaddr']
            addr_type = data['bdaddrs'][0]['bdaddrType']
            device_queue.enqueue({'mac': device_mac, 'addrType': addr_type})
        except Exception as e:
            print(f"Error processing scan event: {e}")

    try:
        async with sse_client_async.EventSource(url, session=session) as events:
            async for event in events:
                  await handle_scan_event(event)
    except Exception as e:
        print(f"Scan SSE error: {e}")

async def open_notify_sse(session, token, router_mac):
    params = {
        'mac': router_mac,
        'access_token': token
    }
    url = f"{AC_HOST}/gatt/nodes?{urlencode(params)}"
    
    try:
        async with sse_client_async.EventSource(url, session=session) as events:
            async for event in events:
                print(f"Received notification: {event.data}")
    except Exception as e:
        print(f"Notify SSE error: {e}")

async def connect_device(session, token, device_mac, addr_type):
    params = {
        'mac': ROUTER_MAC,
        'access_token': token
    }
    url = f"{AC_HOST}/gap/nodes/{device_mac}/connection?{urlencode(params)}"
    data = {
        'timeout': 5000,
        'type': addr_type
    }
    return await req(session, 'POST', url, json_data=data)

async def write_characteristic(session, token, device_mac, handle, value):
    url = f"{AC_HOST}/gatt/nodes/{device_mac}/handle/{handle}/value/{value}?mac={ROUTER_MAC}&access_token={token}"
    return await req(session, 'GET', url)

async def process_queue(session, token):
    while True:
        # TODO: using state check
        device = device_queue.dequeue()
        if not device:
            await asyncio.sleep(5)
            continue
        
        try:
            print(f"Connecting device {device['mac']}")
            await connect_device(session, token, device['mac'], device['addrType'])
            print(f"Enabling notifications for {device['mac']}")
            await write_characteristic(session, token, device['mac'], 24, '0100')
            await write_characteristic(session, token, device['mac'], 23, 'b56206')
            print(f"Successfully processed {device['mac']}")
        except Exception as e:
            print(f"Error processing device {device['mac']}: {e}")

async def main():
    timeout = aiohttp.ClientTimeout(total=None)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            # Authenticate and get token
            auth_info = await authenticate(session, DEVELOPER_KEY, DEVELOPER_SECRET)
            token = auth_info['access_token']
            
            # Start SSE connections and queue processing
            scan_task = asyncio.create_task(open_scan_sse(session, token, ROUTER_MAC))
            notify_task = asyncio.create_task(open_notify_sse(session, token, ROUTER_MAC))
            queue_task = asyncio.create_task(process_queue(session, token))
            
            await asyncio.gather(scan_task, notify_task, queue_task)
        except Exception as e:
            print(f"Main error: {e}")

# Global queue instance
device_queue = DeviceQueue()

if __name__ == "__main__":
    asyncio.run(main())