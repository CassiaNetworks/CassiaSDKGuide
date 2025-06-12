import asyncio
import aiohttp
from aiohttp_sse_client import client as sse_client_async
import json
from urllib.parse import urlencode

"""
sample for connect multiple BLE devices
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
get all routers connected to AC
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#obtain-cassia-routers-status-through-ac
"""
async def getAllRouters(session, token):
    url = f"{AC_HOST}/cassia/hubs?access_token={token}"
    return await req(session, 'GET', url)

"""
since Router can only connect one device at one time, or it will return "chip busy" error
so we need a queue to connect devices sequentially, and prevent same device to enter queue
To improve efficiency, it is recommended to have one queue for each router when you have more than 10 routers. 
"""
class Queue:
    def __init__(self):
        self.q = []
        self.uniqCheck = {}
    
    def enq(self, item):
        # we filter same device
        if item['mac'] in self.uniqCheck:
            return
        self.q.append(item)
        self.uniqCheck[item['mac']] = True
    
    def deq(self):
        if not self.q:
            return None
        item = self.q.pop()
        del self.uniqCheck[item['mac']]
        return item

connectQ = Queue()

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
scan devices
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#scan-bluetooth-devices
"""
async def openScanSse(session, token, routerMac):
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
        'mac': routerMac,  # which router you want to start scan
        'access_token': token  # you can put token in query 'access_token=<token>' or in header 'Bearer <token>'
    }
    url = f"{AC_HOST}/gap/nodes?event=1&{urlencode(query)}"
    
    async def handle_event(event):
        try:
            data = json.loads(event.data)
            deviceMac = data['bdaddrs'][0]['bdaddr']
            addrType = data['bdaddrs'][0]['bdaddrType']
            # enqueue device data to connect it lately
            # the scanning will get multiple scan data of same device in short time,
            # so we need filter same device
            connectQ.enq({'mac': deviceMac, 'addrType': addrType})
        except Exception as e:
            print('parse scan data error:', e)
    
    try:
        async with sse_client_async.EventSource(url, session=session) as evts:
            async for event in evts:
                await handle_event(event)
    except Exception as e:
        print('open scan sse failed:', e)

"""
connect one device
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#connectdisconnect-to-a-target-device
"""
async def connect(session, token, deviceMac, addrType):
    print('connect device', deviceMac)
    url = f"{AC_HOST}/gap/nodes/{deviceMac}/connection?mac={ROUTER_MAC}&access_token={token}"
    data = {'timeout': 5000, 'type': addrType}
    return await req(session, 'POST', url, json_data=data)

async def processQueue(session, token):
    # TODO: using state check
    device = connectQ.deq()
    while device:
        try:
            result = await connect(session, token, device['mac'], device['addrType'])
            print('connect', device['mac'], result)
        except Exception as e:
            print('connect', device['mac'], str(e))
        device = connectQ.deq()
    
    # check queue again in 5 seconds
    await asyncio.sleep(5)
    await processQueue(session, token)

async def main():
    try:
        timeout = aiohttp.ClientTimeout(total=None)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            authInfo = await auth(session, DEVELOPER_KEY, DEVELOPER_SECRET)
            token = authInfo['access_token']
            allRouters = await getAllRouters(session, token)
            onlineRouters = [r for r in allRouters if r['status'] == 'online']
            
            # Start scan SSE for each online router
            scan_tasks = [openScanSse(session, token, router['mac']) for router in onlineRouters]
            asyncio.gather(*scan_tasks)
            
            # Start processing queue
            await processQueue(session, token)
    except Exception as ex:
        print('fail:', ex)

if __name__ == '__main__':
    asyncio.run(main())