import asyncio
import aiohttp
import base64
import json
from aiohttp_sse_client import client as sse_client_async
from urllib.parse import urlencode

"""
sample for connect multiple BLE devices
use Cassia AC APIs, refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki
to run the code, you should have a Cassia Router connected to a Cassia AC
"""

"""
replace it with your AC address
"""
AC_HOST = 'http://10.100.144.168:8882/api'

"""
you can set your developer key and secret under AC -> Settings -> Developer account for RESTful APIs
"""
DEVELOPER_KEY = 'admin1'
DEVELOPER_SECRET = '1q2w#E$R'

"""
this is your router's MAC, you should add the router to AC's online list first
"""
ROUTER_MAC = 'CC:1B:E0:E2:E9:B8'

async def req(session, method, url, headers=None, json_data=None):
    async with session.request(method, url, headers=headers, json=json_data) as resp:
        try:
            if resp.content_type == 'application/json':
                return await resp.json()
            else:
                return await resp.text()
        except Exception as e:
            raise Exception(f"Failed to parse response: {e}")

"""
since Router can only connect one device at one time, or it will return "chip busy" error
so we need a queue to connect devices sequentially
and prevent same device to enter queue
"""
class Queue:
    def __init__(self):
        self.q = []
        self.uniq_check = {}

    def enq(self, item):
        """
        we filter same device
        """
        if item['mac'] in self.uniq_check:
            return
        self.q.append(item)
        self.uniq_check[item['mac']] = True

    def deq(self):
        if not self.q:
            return None
        item = self.q.pop(0)
        del self.uniq_check[item['mac']]
        return item

connect_q = Queue()

"""
auth with your AC, the token will expired after ONE hour,
if you run a long term task, you should refresh the token every hour
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/Getting-Started#access-cassia-router-through-the-cassia-ac
"""
async def auth(session, key, secret):
    auth_str = base64.b64encode(f"{key}:{secret}".encode()).decode()
    headers = {
        'Authorization': f'Basic {auth_str}',
        'Content-Type': 'application/json'
    }
    data = {'grant_type': 'client_credentials'}
    return await req(session, 'POST', f"{AC_HOST}/oauth2/token", headers=headers, json_data=data)

"""
scan devices
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#scan-bluetooth-devices
Sever-Sent Event(SSE) is used in scan, connection-state and notify of Cassia RESTful API,
SSE spec: https://html.spec.whatwg.org/multipage/server-sent-events.html#the-eventsource-interface
API will send ':keep-alive' every 30 seconds in SSE connection for user to check if the connection is active or not.
User need to call Cassia RESTful API to reconnect SSE in case that the connection is termincated abnormally, such as keep-alive lost, socket error, network problem, etc.
"""
async def open_scan_sse(session, router_mac, token):
    query = {
        """
        filter devices whose rssi is below -75, and name begins with 'Cassia',
        there are many other filters, you can find them in document
        use proper filters can significantly reduce traffic between Router and AC
        """
        'filter_rssi': -75,
        'filter_name': 'Cassia*',
        'filter_mac': 'CC:0A:19:32:6A:0A',
        """
        use active scan, default is passive scan
        active scan makes devices response with data packet which usually contains device's name
        """
        'active': 1,
        'mac': router_mac,  # which router you want to start scan
        'access_token': token  # you can put token in query 'access_token=<token>' or in header 'Bearer <token>'
    }
    url = f"{AC_HOST}/gap/nodes?event=1&{urlencode(query)}"

    async def sse_handler():
        try:
            async with sse_client_async.EventSource(url, session=session) as event_source:
                async for event in event_source:
                    if event.data:
                        """
                        if scan open successful, it will return like follow:
                        data: {"bdaddrs":[{"bdaddr":"ED:47:B0:D3:A9:C8","bdaddrType":"public"}],"scanData":"0C09536C656570616365205A32","name":"Sleepace Z2","rssi":-37,"evt_type":4}
                        """
                        data = json.loads(event.data)
                        device_mac = data['bdaddrs'][0]['bdaddr']
                        addr_type = data['bdaddrs'][0]['bdaddrType']
                        """
                        enqueue device data to connect it lately
                        the scanning will get multiple scan data of same device in short time,
                        so we need filter same device
                        """
                        connect_q.enq({'mac': device_mac, 'addrType': addr_type})
        except Exception as e:
            print(f'open scan sse failed: {e}')

    asyncio.create_task(sse_handler())

"""
connect one device
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#connectdisconnect-to-a-target-device
"""
async def connect(session, token, device_mac, addr_type):
    print(f'connect device {device_mac}')
    url = f"{AC_HOST}/gap/nodes/{device_mac}/connection?mac={ROUTER_MAC}&access_token={token}"
    data = {'timeout': 5000, 'type': addr_type}
    headers = {'Content-Type': 'application/json'}
    return await req(session, 'POST', url, headers=headers, json_data=data)

async def process_queue(session, token):
    device = connect_q.deq()
    while device:
        try:
            result = await connect(session, token, device['mac'], device['addrType'])
            print(f'connect {device["mac"]} {result}')
        except Exception as e:
            print(f'connect {device["mac"]} failed: {e}')
        device = connect_q.deq()

    """
    check queue again in 5 seconds
    """
    await asyncio.sleep(5)
    await process_queue(session, token)

async def main():
    try:
        timeout = aiohttp.ClientTimeout(total=None)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            auth_info = await auth(session, DEVELOPER_KEY, DEVELOPER_SECRET)
            token = auth_info['access_token']
            await open_scan_sse(session, ROUTER_MAC, token)
            await process_queue(session, token)
    except Exception as ex:
        print(f'fail: {ex}')

if __name__ == "__main__":
    asyncio.run(main())