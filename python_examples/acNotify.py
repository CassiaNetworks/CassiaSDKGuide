import asyncio
import aiohttp
import base64
import json
from aiohttp_sse_client import client as sse_client_async

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
DEVICE_MAC = 'CC:0A:19:32:6A:0A'

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
connect one device
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#connectdisconnect-to-a-target-device
"""
async def connect(session, token, deviceMac, addrType):
    url = f"{AC_HOST}/gap/nodes/{deviceMac}/connection?mac={ROUTER_MAC}&access_token={token}"
    data = {'timeout': 5000, 'type': addrType}
    headers = {'Content-Type': 'application/json'}
    return await req(session, 'POST', url, headers=headers, json_data=data)

"""
Read/Write the Value of a Specific Characteristic
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#readwrite-the-value-of-a-specific-characteristic
"""
async def write(session, token, deviceMac, handle, value):
    url = f"{AC_HOST}/gatt/nodes/{deviceMac}/handle/{handle}/value/{value}?mac={ROUTER_MAC}&access_token={token}"
    return await req(session, 'GET', url)

"""
Receive Notification and Indication
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#receive-notification-and-indication
Sever-Sent Event(SSE) is used in scan, connection-state and notify of Cassia RESTful API,
SSE spec: https://html.spec.whatwg.org/multipage/server-sent-events.html#the-eventsource-interface
API will send ':keep-alive' every 30 seconds in SSE connection for user to check if the connection is active or not.
User need to call Cassia RESTful API to reconnect SSE in case that the connection is termincated abnormally, such as keep-alive lost, socket error, network problem, etc.
"""
async def open_notify_sse(session, token):
    url = f"{AC_HOST}/gatt/nodes?mac={ROUTER_MAC}&access_token={token}"
    
    async def sse_handler():
        try:
            async with sse_client_async.EventSource(url, session=session) as event_source:
                async for event in event_source:
                    if event.data:
                        print(f"received notify sse message: {event.data}")
        except Exception as e:
            print(f"open notify sse failed: {e}")
    
    # Run SSE handler in background
    asyncio.create_task(sse_handler())
    return True

async def main():
    try:
        timeout = aiohttp.ClientTimeout(total=None)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            auth_info = await auth(session, DEVELOPER_KEY, DEVELOPER_SECRET)
            token = auth_info['access_token']
            await open_notify_sse(session, token)
            await connect(session, token, DEVICE_MAC, 'random')
            await write(session, token, DEVICE_MAC, '24', '0100')
            await write(session, token, DEVICE_MAC, '23', 'b56206')
    except Exception as ex:
        print(f"fail: {ex}")

if __name__ == "__main__":
    asyncio.run(main())