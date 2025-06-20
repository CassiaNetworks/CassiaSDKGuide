import asyncio
import aiohttp
from aiohttp_sse_client import client as sse_client
import json

# replace it with your AC address base URL
AC_BASE_URL = 'http://10.100.144.168'

# Set your developer key and secret under AC -> Settings -> Developer account
DEVELOPER_KEY = 'admin1'
DEVELOPER_SECRET = '1q2w#E$R'

# this is your router's MAC, you should add the router to AC's online list first
ROUTER_MAC = 'CC:1B:E0:E2:E9:B8'

# this is your device scan filter
FILTER_MAC = 'CC:0A:19:32:6A:0A'

AC_HOST = f'{AC_BASE_URL}/api'

async def auth(key, secret):
    url = f"{AC_HOST}/oauth2/token"
    auth = aiohttp.BasicAuth(key, secret)
    data = {'grant_type': 'client_credentials'}
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, auth=auth, json=data) as resp:
            if resp.status != 200:
                error = await resp.text()
                raise Exception(f"Auth failed: {error}")
            result = await resp.json()
            return result['access_token']

async def open_combined_sse(token):
    url = f"{AC_HOST}/aps/events?access_token={token}"
    timeout = aiohttp.ClientTimeout(total=None)
    
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with sse_client.EventSource(url, session=session) as event_source:
                async for event in event_source:
                    try:
                        data = json.loads(event.data)
                        if data.get('dataType') == 'state':
                            print('get gateway state', data)
                        elif data.get('dataType') == 'scan':
                            print('scan data', data)
                        else:
                            print('unknown type', data)
                    except json.JSONDecodeError:
                        print('invalid json data:', event.data)
        except Exception as e:
            print('SSE error:', e)

async def open_scan(aps, token):
    url = f"{AC_HOST}/aps/scan/open?access_token={token}"
    payload = {
        'aps': aps,
        'filter_mac': FILTER_MAC,
        'filter_rssi': -80,
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, json=payload) as resp:
            if resp.status < 200 or resp.status > 202:
                error = await resp.text()
                raise Exception(f"Open scan failed: {error}")
            try:
              if resp.content_type == 'application/json':
                  return await resp.json()
              else:
                  return await resp.text()
            except Exception as e:
                raise Exception(f"Failed to parse response: {e}")

async def main():
    try:
        token = await auth(DEVELOPER_KEY, DEVELOPER_SECRET)
        print(f"get token: {token}")
        
        # Start SSE in background
        asyncio.create_task(open_combined_sse(token))
        
        # Open scan
        await open_scan([ROUTER_MAC], token)
        
        # Keep running to receive SSE events
        while True:
            await asyncio.sleep(1)
            
    except Exception as ex:
        print('fail:', ex)

if __name__ == '__main__':
    asyncio.run(main())