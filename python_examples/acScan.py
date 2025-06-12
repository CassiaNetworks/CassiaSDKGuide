import asyncio
import aiohttp
from aiohttp_sse_client import client as sse_client_async
import json

"""
sample for scan BLE devices
use Cassia AC APIs, refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki
to run the code, you should have a Cassia Router connected to a Cassia AC
"""

# replace it with your AC address
AC_HOST = 'http://10.100.144.168:8882/api'

# you can set your developer key and secret under AC -> Settings -> Developer account for RESTful APIs
DEVELOPER_KEY = 'admin1'
DEVELOPER_SECRET = '1q2w#E$R'

# this is your router's MAC, you should add the router to AC's online list first
ROUTER_MAC = 'CC:1B:E0:E2:E9:B8'

"""
auth with your AC, the token will expired after ONE hour,
if you run a long term task, you should refresh the token every hour
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/Getting-Started#access-cassia-router-through-the-cassia-ac
"""
async def auth(key, secret):
    url = f"{AC_HOST}/oauth2/token"
    auth = aiohttp.BasicAuth(key, secret)
    data = {"grant_type": "client_credentials"}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, auth=auth, json=data) as resp:
            if resp.status != 200:
                error = await resp.text()
                raise Exception(f"Auth failed: {error}")
            result = await resp.json()
            return result.get('access_token')

"""
scan devices
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#scan-bluetooth-devices
Sever-Sent Event(SSE) is used in scan, connection-state and notify of Cassia RESTful API,
SSE spec: https://html.spec.whatwg.org/multipage/server-sent-events.html#the-eventsource-interface
API will send ':keep-alive' every 30 seconds in SSE connection for user to check if the connection is active or not.
User need to call Cassia RESTful API to reconnect SSE in case that the connection is termincated abnormally, such as keep-alive lost, socket error, network problem, etc.
"""
async def open_scan_sse(router_mac, token):
    params = {
        'filter_rssi': -75,  # filter devices whose rssi is below -75
        'active': 1,         # use active scan node
        'mac': router_mac,   # which router you want to start scan
        'access_token': token, # you can put token in query 'access_token=<token>' or in header 'Bearer <token>'
        'event': 1
    }
    
    url = f"{AC_HOST}/gap/nodes"
    timeout = aiohttp.ClientTimeout(total=None)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with sse_client_async.EventSource(url, params=params, session=session) as evts:
                async for event in evts:
                    """
                    if scan open successful, it will return
                    data: {"bdaddrs":[{"bdaddr":"ED:47:B0:D3:A9:C8","bdaddrType":"public"}],"scanData":"0C09536C656570616365205A32","name":"Sleepace Z2","rssi":-37,"evt_type":4}
                    """
                    data = json.loads(event.data)
                    device_mac = data['bdaddrs'][0]['bdaddr']
                    addr_type = data['bdaddrs'][0]['bdaddrType']
                    name = data['name']
                    rssi = data['rssi']
                    print(f"scanned device: {device_mac}, {addr_type}, {rssi}, {name}")
        except Exception as e:
            print(f"open scan sse failed: {e}")

async def main():
    try:
        token = await auth(DEVELOPER_KEY, DEVELOPER_SECRET)
        print(f"get token: {token}")
        await open_scan_sse(ROUTER_MAC, token)
    except Exception as ex:
        print(f"fail: {ex}")

if __name__ == "__main__":
    asyncio.run(main())