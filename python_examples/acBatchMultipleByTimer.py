import asyncio
import aiohttp
from aiohttp_sse_client import client as sse_client
import json
import urllib.parse

"""
sample for connect multiple BLE devices(use batch-connect), and write data to all device
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

# batch connection period, please determine according to the specific broadcast period of the device,
# try to ensure that as many devices as possible can be scanned in the minimum time
BATCH_CONN_INTERVAL = 2000

is_written = {}
scan_devices = {}

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
async def auth(session, key, secret):
    url = f"{AC_HOST}/oauth2/token"
    auth = aiohttp.BasicAuth(key, secret)
    data = {"grant_type": "client_credentials"}
    return await req(session, 'POST', url, auth=auth, json_data=data)

"""
scan and connect devices
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#scan-bluetooth-devices
Sever-Sent Event(SSE) is used in scan, connection-state and notify of Cassia RESTful API,
SSE spec: https://html.spec.whatwg.org/multipage/server-sent-events.html#the-eventsource-interface
API will send ':keep-alive' every 30 seconds in SSE connection for user to check if the connection is active or not.
User need to call Cassia RESTful API to reconnect SSE in case that the connection is termincated abnormally, such as keep-alive lost, socket error, network problem, etc.
"""
async def open_scan_sse(session, token):
    query = {
        # filter devices whose rssi is below -75, and name begins with 'Cassia',
        # there are many other filters, you can find them in document
        # use proper filters can significantly reduce traffic between Router and AC
        'filter_rssi': -75,
        'filter_name': 'Cassia*',
        'filter_mac': 'CC:0A:19:32:6A:0A',
        # use active scan, default is passive scan
        # active scan makes devices response with data packet which usually contains device's name
        'active': 1,
        'mac': ROUTER_MAC,  # which router you want to start scan
        'access_token': token  # you can put token in query 'access_token=<token>' or in header 'Bearer <token>'
    }
    url = f"{AC_HOST}/gap/nodes?event=1&{urllib.parse.urlencode(query)}"
    
    async def handle_event(event):
        if event.data:
            try:
                data = json.loads(event.data)
                device_addr = data['bdaddrs'][0]
                device_mac = device_addr['bdaddr']
                device_addr_type = device_addr['bdaddrType']
                if device_mac not in is_written:
                    scan_devices[device_mac] = {'deviceMac': device_mac, 'deviceAddrType': device_addr_type}
            except Exception as ex:
                print(f'Error processing scan event: {ex}')

    try:
        async with sse_client.EventSource(url, session=session) as event_source:
            async for event in event_source:
                await handle_event(event)
    except Exception as ex:
        print(f'Scan SSE error: {ex}')

"""
Batch Connect/Disconnect to a Target Device (v2.0 and above)
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#batch-connectdisconnect-to-a-target-device-v20-and-above
"""
async def batch_connect(session, token):
    if not token or not scan_devices:
        return
    
    # you can put multiple devices in list parameter, all the devices will enter a connecting queue
    # when device is connected, it will report connected event in connection-state SSE
    body = {
        'list': [],
        'timeout': 5000,
        'per_dev_timeout': 10000,
    }

    # add devices scanned within timer
    for device_mac, device_info in scan_devices.items():
        body['list'].append({
            'type': device_info['deviceAddrType'],
            'addr': device_mac
        })

    # you can use the batch connection API, set per_dev_timeout for a long time, measure the overall time consumption several times,
    # calculate the average time consumption, set per_dev_timeout = average_time * number_of_devices
    body['per_dev_timeout'] = len(body['list']) * body['timeout']

    url = f"{AC_HOST}/gap/batch-connect?mac={ROUTER_MAC}&access_token={token}"
    return await req(session, 'POST', url, json_data=body)

"""
Read/Write the Value of a Specific Characteristic
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#readwrite-the-value-of-a-specific-characteristic
"""
async def write(session, token, device_mac, handle, value):
    url = f"{AC_HOST}/gatt/nodes/{device_mac}/handle/{handle}/value/{value}?mac={ROUTER_MAC}&access_token={token}"
    return await req(session, 'GET', url)

"""
disconnect device
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#connectdisconnect-to-a-target-device
"""
async def disconnect(session, token, device_mac):
    url = f"{AC_HOST}/gap/nodes/{device_mac}/connection?mac={ROUTER_MAC}&access_token={token}"
    return await req(session, 'DELETE', url)

"""
Get Device Connection Status
you will get notify when device connected or disconnected to a Router
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#get-device-connection-status
Sever-Sent Event(SSE) is used in scan, connection-state and notify of Cassia RESTful API,
SSE spec: https://html.spec.whatwg.org/multipage/server-sent-events.html#the-eventsource-interface
API will send ':keep-alive' every 30 seconds in SSE connection for user to check if the connection is active or not.
User need to call Cassia RESTful API to reconnect SSE in case that the connection is termincated abnormally, such as keep-alive lost, socket error, network problem, etc.
"""
async def open_connect_state_sse(session, token):
    url = f"{AC_HOST}/management/nodes/connection-state?mac={ROUTER_MAC}&access_token={token}"
    
    async def handle_event(event):
        if event.data:
            try:
                data = json.loads(event.data)
                device_mac = data['handle']
                print('connect state message:', data)
                # skip device which have already written data
                if device_mac in is_written:
                    return
                if data['connectionState'] == 'connected':
                    await write(session, token, device_mac, 39, '21ff310302ff31')
                    is_written[device_mac] = True
                    # TODO: clear batch connect cache
                    await disconnect(session, token, device_mac)
                else:
                    # if device is disconnected, it can be scanned again
                    pass
            except Exception as ex:
                print(f'Error processing connection state event: {ex}')

    try:
        async with sse_client.EventSource(url, session=session) as event_source:
            async for event in event_source:
                await handle_event(event)
    except Exception as ex:
        print(f'Connection state SSE error: {ex}')

async def batch_connect_timer(session, token):
    while True:
        await batch_connect(session, token)
        scan_devices.clear()
        await asyncio.sleep(BATCH_CONN_INTERVAL / 1000)

async def main():
    timeout = aiohttp.ClientTimeout(total=None)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        token_data = await auth(session, DEVELOPER_KEY, DEVELOPER_SECRET)
        print('token:', token_data)
        token = token_data['access_token']
        
        # Run SSE listeners and timer in parallel
        await asyncio.gather(
            open_scan_sse(session, token),
            open_connect_state_sse(session, token),
            batch_connect_timer(session, token)
        )

if __name__ == '__main__':
    asyncio.run(main())