"""
Module name: cassiablue.py  
Purpose: Local MicroPython debugging mock. Exposes the same high-level API as the real gateway by forwarding calls to its REST + Server-Sent-Events interface, so you can develop and test your MicroPython logic on a PC without flashing firmware.  
MicroPython compatibility: v1.24.1  
Important: Do **not** copy this file into the gateway itself—the gateway already contains a native C implementation. This module is **only** for convenient desktop debugging and has no performance guarantees.  
Usage: Change the variable `GATEWAY` to the actual IP address of your gateway.
"""

GATEWAY = ""

import json
import asyncio

from cassia_log import get_logger
import aiohttp

try:
    from typing import Optional
except ImportError:
    pass


log = get_logger("__mock_cassiablue__")

_gateway_type = "M2000"
_gateway_mac = "00:00:00:00:00:00"
_gateway_ver = ""


class AsyncQueue:
    def __init__(self):
        self._buffer = []
        self._flag = asyncio.ThreadSafeFlag()

    def put_nowait(self, item):
        self._buffer.append(item)
        self._flag.set()

    async def get(self):
        while not self._buffer:
            await self._flag.wait()
        return self._buffer.pop(0)


async def send_cmd(url, method="GET", query=None, body=None):
    global GATEWAY
    url = f"http://{GATEWAY}{url}"

    print("send cmd start:", method, url, query, body)

    async with aiohttp.ClientSession() as session:
        if body is not None:
            async with session.request(
                method=method, url=url, json=json.loads(body)
            ) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return True, text
                else:
                    text = await resp.text()
                    return False, text
        else:
            async with session.request(method=method, url=url) as resp:
                if resp.status == 200:
                    text = await resp.text()
                    return True, text
                else:
                    text = await resp.text()
                    return False, text


# address is a string like "00:11:22:33:44:55"
# params is a json string like '{"param1": "value1", "param2": "value2"}'
async def connect(addr, params=None):
    if not addr:
        raise ValueError("Address cannot be empty")
    url = "/gap/nodes/{}/connection".format(addr)
    return await send_cmd(url, "POST", None, body=params)


# address is a string like "00:11:22:33:44:55"
async def disconnect(addr):
    if not addr:
        raise ValueError("Address cannot be empty")
    url = "/gap/nodes/{}/connection".format(addr)
    return await send_cmd(url, "DELETE")


async def get_connected_devices():
    return await send_cmd("/gap/nodes", "GET")


async def gatt_discover(addr):
    if not addr:
        raise ValueError("Address cannot be empty")
    url = "/gatt/nodes/{}/services/characteristics/descriptors".format(addr)
    return await send_cmd(url, "GET")


async def gatt_read(addr, handle):
    if not addr or not handle:
        raise ValueError("Address and handle cannot be empty")
    url = "/gatt/nodes/{}/handle/{}/value".format(addr, handle)
    return await send_cmd(url, "GET")


async def gatt_write(addr, handle, value):
    if not addr or not handle or value is None:
        raise ValueError("Address, handle, and value cannot be empty")
    url = "/gatt/nodes/{}/handle/{}/value/{}".format(addr, handle, value)
    return await send_cmd(url, "GET")


class SSEClient:
    def __init__(
        self,
        host: str,
        path: str,
        reconnect_delay: int = 3,
    ):
        self.log = get_logger(self.__class__.__name__)
        self.host = host
        self.path = path
        self.reconnect_delay = reconnect_delay
        self.running = True
        self.queue = AsyncQueue()
        self.reader = None
        self.writer = None

    async def connect(self):
        self.log.info(f"connect to sse start: {self.host}{self.path}")
        self.reader, self.writer = await asyncio.open_connection(self.host, 80)
        req = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Accept: text/event-stream\r\n"
            f"Host: {self.host}\r\n"
            f"Connection: keep-alive\r\n"
            "\r\n"
        )
        self.writer.write(req.encode())
        await self.writer.drain()
        self.log.info(f"connect to sse ok")

    async def co_read(self):
        while self.running:
            try:
                line = await self.reader.readline()

                if not line:
                    raise OSError("connection closed")

                line = line.decode().strip()

                if not line:
                    continue

                log.debug("raw line:", line)
                if not (line[0] in ("{", "[") or line.startswith("data: {")):
                    continue

                log.debug("raw line:", line)
                line = line.replace("data: ", "")
                line = line.replace("\n", "")
                line = line.replace("\r", "")
                line = line.replace("\r\n", "")

                try:
                    data = json.loads(line)

                    if "bdaddrs" in data:
                        data["bdaddr"] = data["bdaddrs"][0]["bdaddr"]
                        data["bdaddrType"] = data["bdaddrs"][0]["bdaddrType"]
                        del data["bdaddrs"]

                    self.queue.put_nowait(data)
                except Exception as e:
                    self.log.info("parse data error:", e, line)

            except Exception as e:
                self.log.error("sse disconnected:", e)
                await asyncio.sleep(self.reconnect_delay)
                self.log.info("reconnecting...")

    async def stop(self):
        self.running = False


#######################
# scan sse
#######################

scan_sse_client: Optional[SSEClient] = None


class BLEScanResult:
    def __aiter__(self):
        return self

    async def __anext__(self):
        global scan_sse_client
        item = await scan_sse_client.queue.get()
        return item


def scan_result():
    return BLEScanResult()


async def start_scan(query: str = None):
    global scan_sse_client

    qs = ""
    if query is None:
        qs = "event=1"
    else:
        if "event=1" not in query:
            qs = qs + "event=1&"
        qs = qs + query

    log.info("start scan:", qs)

    scan_sse_client = SSEClient(
        host=GATEWAY,
        path=f"/gap/nodes?{qs}",
    )

    await scan_sse_client.connect()

    asyncio.create_task(scan_sse_client.co_read())

    return True, "OK"


#######################
# notify sse
#######################

notify_sse_client: Optional[SSEClient] = None


class BLENotifyResult:
    def __aiter__(self):
        return self

    async def __anext__(self):
        global notify_sse_client
        item = await notify_sse_client.queue.get()
        return item


def notify_result():
    return BLENotifyResult()


async def start_recv_notify(query: str = None):
    global notify_sse_client

    qs = ""
    if query is None:
        qs = "event=1"
    else:
        if "event=1" not in query:
            qs = qs + "event=1&"
        qs = qs + query

    log.info("start notify:", qs)

    notify_sse_client = SSEClient(
        host=GATEWAY,
        path=f"/gatt/nodes?{qs}",
    )

    await notify_sse_client.connect()

    asyncio.create_task(notify_sse_client.co_read())

    return True, "OK"


#######################
# state sse
#######################

state_sse_client: Optional[SSEClient] = None


class BLEConnectionResult:
    def __aiter__(self):
        return self

    async def __anext__(self):
        global state_sse_client
        item = await state_sse_client.queue.get()
        return item


def connection_result():
    return BLEConnectionResult()


async def start_recv_connection_state():
    global state_sse_client

    log.info("start state")

    state_sse_client = SSEClient(
        host=GATEWAY,
        path=f"/management/nodes/connection-state",
    )

    await state_sse_client.connect()
    asyncio.create_task(state_sse_client.co_read())

    return True, "OK"


def set_gateway(ip: str):
    global GATEWAY
    GATEWAY = ip
