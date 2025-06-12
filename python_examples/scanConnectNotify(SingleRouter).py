import asyncio
import aiohttp
from aiohttp_sse_client import client as sse_client_async
import json

"""
sample for connect multiple BLE devices and open notification
use router local API in this example
first open listen to scan events and connect specific devices one by one,
open device's notification and receive notification of all devices
use Cassia AC APIs, refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki
to run the code, you should have a Cassia Router
"""

# replace it with your router ip adderss
# remember switching on local API in setting page
HOST = 'http://10.100.176.164'

# convert http request to promise
async def req(options):
    async with aiohttp.ClientSession() as session:
        method = options.get('method', 'GET')
        url = options['url']
        headers = options.get('headers', {})
        data = options.get('body')
        
        async with session.request(method, url, headers=headers, data=data) as resp:
            if resp.status != 200:
                raise Exception(await resp.text())
            return await resp.text()

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
        if self.uniq_check.get(item['mac']):
            return
        self.q.append(item)
        self.uniq_check[item['mac']] = True
    
    def deq(self):
        if not self.q:
            return None
        item = self.q.pop()
        del self.uniq_check[item['mac']]
        return item

connect_q = Queue()

"""
scan devices
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#scan-bluetooth-devices
Sever-Sent Event(SSE) is used in scan, connection-state and notify of Cassia RESTful API,
SSE spec: https://html.spec.whatwg.org/multipage/server-sent-events.html#the-eventsource-interface
API will send ':keep-alive' every 30 seconds in SSE connection for user to check if the connection is active or not.
User need to call Cassia RESTful API to reconnect SSE in case that the connection is termincated abnormally, such as keep-alive lost, socket error, network problem, etc.
Nodejs library 'eventsource' handle the SSE reconnection automatically. For other lanuages, the reconnection may needs to be handled by users application.
"""
async def open_scan_sse():
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
        'active': 1
    }
    url = f"{HOST}/gap/nodes?event=1&{'&'.join(f'{k}={v}' for k,v in query.items())}"
    
    try:
        async with aiohttp.ClientSession() as session:
            async with sse_client_async.EventSource(url, session=session) as event_source:
                async for event in event_source:
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
    except Exception as error:
        print('open scan sse failed:', error)

"""
connect one device
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#connectdisconnect-to-a-target-device
"""
async def connect(device_mac, addr_type):
    print('connect device', device_mac)
    options = {
        'method': 'POST',
        'url': f"{HOST}/gap/nodes/{device_mac}/connection",
        'headers': {'Content-Type': 'application/json'},
        'body': json.dumps({'timeout': 5000, 'type': addr_type})
    }
    return await req(options)

async def process_queue(token=None):
    device = connect_q.deq()
    while device:
        result = None
        try:
            result = await connect(device['mac'], device['addrType'])
            print('connect', device['mac'], result)
            """
            write 0200 to notification handle to open notification
            """
            result = await write(device['mac'], 17, '0200')
            print('write', device['mac'], result)
        except Exception as e:
            result = str(e)
        device = connect_q.deq()
    
    """
    check queue again in 5 seconds
    """
    await asyncio.sleep(5)
    await process_queue(token)

"""
Receive Notification and Indication
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#receive-notification-and-indication
Sever-Sent Event(SSE) is used in scan, connection-state and notify of Cassia RESTful API,
SSE spec: https://html.spec.whatwg.org/multipage/server-sent-events.html#the-eventsource-interface
API will send ':keep-alive' every 30 seconds in SSE connection for user to check if the connection is active or not.
User need to call Cassia RESTful API to reconnect SSE in case that the connection is termincated abnormally, such as keep-alive lost, socket error, network problem, etc.
Nodejs library 'eventsource' handle the SSE reconnection automatically. For other lanuages, the reconnection may needs to be handled by users application.
"""
async def open_notify_sse():
    url = f"{HOST}/gatt/nodes"
    try:
        async with aiohttp.ClientSession() as session:
            async with sse_client_async.EventSource(url, session=session) as event_source:
                async for event in event_source:
                    print('received notify sse message:', event.data)
    except Exception as error:
        print('open notify sse failed:', error)

"""
Read/Write the Value of a Specific Characteristic
refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#readwrite-the-value-of-a-specific-characteristic
"""
async def write(device_mac, handle, value):
    options = {
        'method': 'GET',
        'url': f"{HOST}/gatt/nodes/{device_mac}/handle/{handle}/value/{value}",
    }
    return await req(options)

async def main():
    try:
        # Run SSE listeners in background
        asyncio.create_task(open_scan_sse())
        asyncio.create_task(open_notify_sse())
        await process_queue()
    except Exception as ex:
        print('fail:', ex)

if __name__ == '__main__':
    asyncio.run(main())