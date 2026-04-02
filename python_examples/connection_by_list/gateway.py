import asyncio
import json
from urllib.parse import urlencode

import aiohttp
from aiohttp_sse_client import client as sse_client_async

from logger import logger


class CassiaGatewayAsync:
    def __init__(self, base_url, scan_filter):
        self.base_url = base_url
        self.session = aiohttp.ClientSession()
        self.sse_sess = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=None))
        self.scan_filter = scan_filter
        self.scan_handler = None
        self.state_handler = None
        self.notification_handler = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        await self.session.close()
        await self.sse_sess.close()

    async def _open_sse(self, url, handler, session, wait=False):
        try:
            logger.info(f"open sse start: {url}")
            async with sse_client_async.EventSource(url, session=session) as evts:
                async for event in evts:
                    if wait:
                        await handler(event)
                    else:
                        handler(event)
        except Exception as e:
            logger.info(f"sse error: {url} {e}")

    async def _print_text_and_raise(self, resp, mac=None):
        text = await resp.text()
        logger.info(f"[{mac}] resp: {text}")
        resp.raise_for_status()
        return text

    async def _print_status_text(self, mac, resp):
        text = await resp.text()
        logger.info(f"[{mac}] status: {resp.status}, resp: {text}")
        return text

    async def _print_json_and_raise(self, resp, mac=None):
        text = await resp.text()
        logger.info(f"[{mac}] resp: {text}")
        resp.raise_for_status()
        return json.loads(text)

    async def disconnect(self, mac):
        logger.info(f"[{mac}] disconnect start")
        url = f"{self.base_url}/gap/nodes/{mac}/connection"
        async with self.session.delete(url) as resp:
            await self._print_status_text(mac, resp)

    async def disconnect_ignore_ex(self, mac):
        try:
            logger.info(f"[{mac}] disconnect start")
            url = f"{self.base_url}/gap/nodes/{mac}/connection"
            async with self.session.delete(url) as resp:
                await self._print_status_text(mac, resp)
        except Exception as ex:
            logger.warning(ex)

    async def connect_by_list(self, nodes, chip=0, timeout=10000):
        """Connect by List(Sync)"""
        logger.info(f"connect by list start: {chip} {nodes}")
        url = f"{self.base_url}/gap/connection?chip={chip}"

        # TODO: Connection parameters, adjust as needed
        list = [{"type": "random", "addr": mac} for mac in nodes]
        payload = {
            "timeout": timeout,
            "list": list,
            "dle": 251,
            "phy": "2M",
        }
        async with self.session.post(url, json=payload) as resp:
            return await self._print_json_and_raise(resp, nodes)

    async def write_handle(self, mac, handle, value, noresponse=False):
        url = f"{self.base_url}/gatt/nodes/{mac}/handle/{handle}/value/{value}?"

        if noresponse:
            url += "noresponse=1"
        logger.info(f"[{mac}] write handle start: {url}")

        async with self.session.get(url) as resp:
            await self._print_text_and_raise(resp, mac)

    def reg_scan_handler(self, handler):
        self.scan_handler = handler

    def reg_state_handler(self, handler):
        self.state_handler = handler

    def reg_notification_handler(self, handler):
        self.notification_handler = handler

    async def open_state(self):
        url = f"{self.base_url}/management/nodes/connection-state"
        await self._open_sse(
            url, handler=self.state_handler, session=self.sse_sess, wait=True
        )

    async def open_scan(self, chip=0):
        """Keep scan SSE always on, auto-reconnect on disconnect"""
        url = f"{self.base_url}/gap/nodes?event=1&active=1&chip={chip}&"
        if self.scan_filter is not None:
            query = urlencode(self.scan_filter)
            url = f"{url}{query}"

        while True:
            try:
                logger.info(f"open scan sse start")
                timeout = aiohttp.ClientTimeout(total=None)
                async with aiohttp.ClientSession(timeout=timeout) as session:
                    await self._open_sse(url, handler=self.scan_handler, session=session)
                logger.warning("scan sse disconnected, reconnecting...")
            except asyncio.CancelledError:
                raise
            except Exception as e:
                logger.error(f"scan sse error: {e}")
            await asyncio.sleep(3)

    async def open_notify(self):
        """Enable Notification SSE, each device has a separate seqNum"""
        url = f"{self.base_url}/gatt/nodes?event=1&sequence=2&timestamp=1"
        await self._open_sse(
            url, handler=self.notification_handler, session=self.sse_sess
        )

    def run_tasks(self):
        return [
            asyncio.create_task(self.open_scan(), name="scanner"),
            asyncio.create_task(self.open_state(), name="stater"),
            asyncio.create_task(self.open_notify(), name="notifier"),
        ]

    # --- Additional API examples (not used in the main flow) ---

    async def connect_batch(self, nodes, timeout=10000):
        """Connect Batch(Async)"""
        logger.info(f"connect batch start: {nodes}")
        url = f"{self.base_url}/gap/batch-connect"
        list = [{"type": "random", "addr": mac} for mac in nodes]
        payload = {
            "timeout": timeout,
            "per_dev_timeout": timeout,
            "list": list,
        }
        async with self.session.post(url, json=payload) as resp:
            await self._print_text_and_raise(resp, mac=nodes)

    async def update_phy(self, mac):
        logger.info(f"update phy start: {mac}")
        url = f"{self.base_url}/gap/nodes/{mac}/phy"
        payload = {
            "tx": "2M",
            "rx": "2M",
        }
        async with self.session.post(url, json=payload) as resp:
            await self._print_text_and_raise(resp, mac)

    async def connect(self, mac):
        """Connect Device(Sync)"""
        logger.info(f"[{mac}] connect start")
        url = f"{self.base_url}/gap/nodes/{mac}/connection"
        payload = {
            "type": "random",
        }
        async with self.session.post(url, json=payload) as resp:
            await self._print_text_and_raise(resp, mac)

    async def read_handle(self, mac, handle):
        url = f"{self.base_url}/gatt/nodes/{mac}/handle/{handle}/value"
        logger.info(f"[{mac}] read handle start: {url}")

        async with self.session.get(url) as resp:
            return await self._print_json_and_raise(resp, mac)

    async def get_interference(self):
        url = f"{self.base_url}/gap/connection/interference"
        logger.info(f"get interference start: {url}")

        async with self.session.get(url) as resp:
            return await self._print_json_and_raise(resp)

    async def get_rate(self):
        url = f"{self.base_url}/gatt/nodes/rate"
        logger.info(f"get rate start: {url}")

        async with self.session.get(url) as resp:
            return await self._print_json_and_raise(resp)

    async def set_link_track(self, enable=True):
        url = f"{self.base_url}/gap/link-track"
        logger.info(f"set link track start: {url}")
        payload = {"enable": "1" if enable else "0"}
        async with self.session.post(url, json=payload) as resp:
            await self._print_text_and_raise(resp)

    async def get_conns(self):
        url = f"{self.base_url}/conns"
        logger.info(f"get conns start: {url}")

        async with self.session.get(url) as resp:
            return await self._print_json_and_raise(resp)

    async def discover_gatt_all(self, mac):
        logger.info(f"[{mac}] discover gatt start")
        url = f"{self.base_url}/gatt/nodes/{mac}/services/characteristics/descriptors"
        async with self.session.get(url) as resp:
            return await self._print_json_and_raise(resp, mac)

    async def get_connected(self):
        logger.info(f"get connected start")
        url = f"{self.base_url}/gap/nodes"
        async with self.session.get(url) as resp:
            return await self._print_json_and_raise(resp)

    async def init(self):
        await self.set_link_track(True)
        logger.info("gateway init ok")
