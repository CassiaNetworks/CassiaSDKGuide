import asyncio
import aiohttp
from aiohttp_sse_client import client as sse_client_async
import json

# replace it with your AC address base URL
AC_BASE_URL = 'http://10.100.144.168'

# you can set your developer key and secret under AC -> Settings -> Developer account for RESTful APIs
DEVELOPER_KEY = 'admin1'
DEVELOPER_SECRET = '1q2w#E$R'

# this is your router's MAC, you should add the router to AC's online list first
ROUTER_MAC = 'CC:1B:E0:E2:E9:B8'

# this is your device scan filter
FILTER_MAC = 'CC:0A:19:32:6A:0A'

AC_HOST = f'{AC_BASE_URL}/api'

is_written = {}

async def req(session, method, url, headers=None, json_data=None, auth=None):
    async with session.request(method, url, headers=headers, json=json_data, auth=auth) as resp:
        try:
            if resp.content_type == 'application/json':
                return await resp.json()
            else:
                return await resp.text()
        except Exception as e:
            raise Exception(f"Failed to parse response: {e}")

# auth with your AC, the token will expired after ONE hour,
# if you run a long term task, you should refresh the token every hour
# refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/Getting-Started#access-cassia-router-through-the-cassia-ac
async def auth(session, key, secret):
    url = f"{AC_HOST}/oauth2/token"
    headers = {'Content-Type': 'application/json'}
    auth = aiohttp.BasicAuth(key, secret)
    data = {"grant_type": "client_credentials"}
    return await req(session, 'POST', url, headers=headers, json_data=data, auth=auth)

# scan and connect devices
# refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#scan-bluetooth-devices
async def open_scan_sse_and_connect(session, token):
    params = {
        'filter_rssi': -75,
        'filter_mac': FILTER_MAC,
        'active': 1,
        'mac': ROUTER_MAC,
        'access_token': token,
        'event': 1
    }
    url = f"{AC_HOST}/gap/nodes"
    
    async with sse_client_async.EventSource(url, session=session, params=params) as evts:
        async for event in evts:
            if event.data:
                data = json.loads(event.data)
                device_addr = data['bdaddrs'][0]
                device_mac = device_addr['bdaddr']
                device_addr_type = device_addr['bdaddrType']
                if device_mac not in is_written:
                    await batch_connect(session, token, device_mac, device_addr_type)

# Batch Connect/Disconnect to a Target Device (v2.0 and above)
# refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#batch-connectdisconnect-to-a-target-device-v20-and-above
async def batch_connect(session, token, device_mac, addr_type):
    url = f"{AC_HOST}/gap/batch-connect?mac={ROUTER_MAC}&access_token={token}"
    headers = {'Content-Type': 'application/json'}
    data = {
        "list": [{"type": addr_type, "addr": device_mac}],
        "timeout": 5000,
        "per_dev_timeout": 10000
    }
    await req(session, 'POST', url, headers=headers, json_data=data)

# Read/Write the Value of a Specific Characteristic
# refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#readwrite-the-value-of-a-specific-characteristic
async def write(session, token, device_mac, handle, value):
    url = f"{AC_HOST}/gatt/nodes/{device_mac}/handle/{handle}/value/{value}?mac={ROUTER_MAC}&access_token={token}"
    await req(session, 'GET', url)
    print('write ok:', device_mac)

# disconnect device
# refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#connectdisconnect-to-a-target-device
async def disconnect(session, token, device_mac):
    url = f"{AC_HOST}/gap/nodes/{device_mac}/connection?mac={ROUTER_MAC}&access_token={token}"
    await req(session, 'DELETE', url)
    print('disconnect ok:', device_mac)

# Get Device Connection Status
async def open_connect_state_sse(session, token):
    url = f"{AC_HOST}/management/nodes/connection-state?mac={ROUTER_MAC}&access_token={token}"
    
    async with sse_client_async.EventSource(url, session=session) as evts:
        async for event in evts:
            if event.data:
                print(event.data)
                data = json.loads(event.data)
                device_mac = data['handle']
                if device_mac not in is_written:
                    if data['connectionState'] == 'connected':
                        await write(session, token, device_mac, 24, '0100')
                        is_written[device_mac] = True
                        # TODO: remove batch connect
                        await disconnect(session, token, device_mac)

async def main():
    timeout = aiohttp.ClientTimeout(total=None)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            token_data = await auth(session, DEVELOPER_KEY, DEVELOPER_SECRET)
            print('token:', token_data)
            token = token_data['access_token']
            
            # Run both SSE connections concurrently
            await asyncio.gather(
                open_scan_sse_and_connect(session, token),
                open_connect_state_sse(session, token)
            )
            print('success')
        except Exception as ex:
            print('fail:', ex)

if __name__ == "__main__":
    asyncio.run(main())