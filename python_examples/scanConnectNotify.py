"""
sample for connect multiple BLE devices and open notification
first open listen to scan events and connect specific devices one by one,
open device's notification and receive notification of all devices
use Cassia AC APIs, refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki
to run the code, you should have a Cassia Router connected to a Cassia AC
"""
import asyncio
import aiohttp
from aiohttp_sse_client import client as sse_client_async
import json
from urllib.parse import urlencode

"""
replace it with your AC address base URL
"""
AC_BASE_URL = 'http://10.100.144.168'

"""
you can set your developer key and secret under AC -> Settings -> Developer account for RESTful APIs
"""
DEVELOPER_KEY = 'admin1'
DEVELOPER_SECRET = '1q2w#E$R'

"""
this is your router's MAC, you should add the router to AC's online list first
"""
ROUTER_MAC = 'CC:1B:E0:E2:E9:B8'

"""
this is your device scan filter
"""
FILTER_MAC = 'CC:0A:19:32:6A:0A'

AC_HOST = f'{AC_BASE_URL}/api'

"""
since Router can only connect one device at one time, or it will return "chip busy" error
so we need a queue to connect devices sequentially
and prevent same device to enter queue
"""
class DeviceQueue:
    def __init__(self):
        self._queue = []
        self._unique_check = set()

    def enqueue(self, device):
        if device['mac'] not in self._unique_check:
            self._unique_check.add(device['mac'])
            self._queue.append(device)

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

"""
auth with your AC, the token will expired after ONE hour,
if you run a long term task, you should refresh the token every hour
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/Getting-Started#access-cassia-router-through-the-cassia-ac
"""
async def authenticate(session, key, secret):
    auth_url = f"{AC_HOST}/oauth2/token"
    auth = aiohttp.BasicAuth(key, secret)
    data = {"grant_type": "client_credentials"}
    return await req(session, 'POST', auth_url, json_data=data, auth=auth)

"""
scan devices
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#scan-bluetooth-devices
Sever-Sent Event(SSE) is used in scan, connection-state and notify of Cassia RESTful API,
SSE spec: https://html.spec.whatwg.org/multipage/server-sent-events.html#the-eventsource-interface
API will send ':keep-alive' every 30 seconds in SSE connection for user to check if the connection is active or not.
User need to call Cassia RESTful API to reconnect SSE in case that the connection is termincated abnormally, such as keep-alive lost, socket error, network problem, etc.
"""
async def open_scan_sse(session, token, router_mac):
    params = {
        # filter devices whose rssi is below -75, and name begins with 'Cassia',
        # there are many other filters, you can find them in document
        # use proper filters can significantly reduce traffic between Router and AC
        'filter_rssi': -75,
        'filter_mac': FILTER_MAC,
        
        # use active scan, default is passive scan
        # active scan makes devices response with data packet which usually contains device's name
        'active': 1,
        
        # which router you want to start scan
        'mac': router_mac,
        
        # you can put token in query 'access_token=<token>' or in header 'Bearer <token>' 
        'access_token': token,
        'event': 1
    }
    url = f"{AC_HOST}/gap/nodes?{urlencode(params)}"
    
    """
    * if scan open successful, it will return like follow:
    * data: {"bdaddrs":[{"bdaddr":"ED:47:B0:D3:A9:C8","bdaddrType":"public"}],"scanData":"0C09536C656570616365205A32","name":"Sleepace Z2","rssi":-37,"evt_type":4}
    """
    async def handle_scan_event(event):
        try:
            data = json.loads(event.data)
            device_mac = data['bdaddrs'][0]['bdaddr']
            addr_type = data['bdaddrs'][0]['bdaddrType']
            
            """
            * enqueue device data to connect it lately
            * the scanning will get multiple scan data of same device in short time,
            * so we need filter same device
            """
            device_queue.enqueue({'mac': device_mac, 'addrType': addr_type})
        except Exception as e:
            print(f"Error processing scan event: {e}")

    try:
        async with sse_client_async.EventSource(url, session=session) as events:
            async for event in events:
                  await handle_scan_event(event)
    except Exception as e:
        print(f"Scan SSE error: {e}")

"""
Receive Notification and Indication
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#receive-notification-and-indication
Sever-Sent Event(SSE) is used in scan, connection-state and notify of Cassia RESTful API,
SSE spec: https://html.spec.whatwg.org/multipage/server-sent-events.html#the-eventsource-interface
API will send ':keep-alive' every 30 seconds in SSE connection for user to check if the connection is active or not.
User need to call Cassia RESTful API to reconnect SSE in case that the connection is termincated abnormally, such as keep-alive lost, socket error, network problem, etc.
"""
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

"""
connect one device
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#connectdisconnect-to-a-target-device
"""
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

"""
Read/Write the Value of a Specific Characteristic
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#readwrite-the-value-of-a-specific-characteristic
"""
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