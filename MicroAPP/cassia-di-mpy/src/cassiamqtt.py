"""
Module name: cassiamqtt.py
Purpose: Local MicroPython debugging mock. Exposes the same high-level API as the real gateway by forwarding calls to mqtt_as interface, so you can develop and test your MicroPython logic on a PC without flashing firmware.
MicroPython compatibility: v1.24.1
Important: Do **not** copy this file into the gateway itself—the gateway already contains a native C implementation. This module is **only** for convenient desktop debugging and has no performance guarantees.
"""

import asyncio

from mqtt_as import MQTTClient
from cassia_log import get_logger


def _parse_uri(uri):
    try:
        host_port = uri.split("://", 1)[1]
        host, port = host_port.rsplit(":", 1)
        return {
            "host": host,
            "port": port,
        }
    except (IndexError, ValueError):
        return None


class CassiaMQTTClient:
    def __init__(self, uri, username=None, password=None, client_id=None):
        self.log = get_logger("__mock_cassiamqtt__")

        addr = _parse_uri(uri)
        if addr is None:
            self.log.warn(f"parse uri failed: {uri}")
            return

        config = {
            "client_id": client_id,
            "server": addr.get("host", None),
            "port": addr.get("port", None),
            "user": username,
            "password": password,
            "keepalive": 60,
            "ping_interval": 0,
            "ssl": False,
            "ssl_params": {},
            "response_time": 10,
            "clean_init": True,
            "clean": True,
            "max_repubs": 4,
            "will": None,
            "subs_cb": lambda *_: None,
            "ssid": None,
            "wifi_pw": None,
            "queue_len": 64,
            "gateway": False,
            "mqttv5": False,
            "mqttv5_con_props": None,
        }

        MQTTClient.DEBUG = True
        self.client = MQTTClient(config=config)

    async def __aenter__(self):
        while True:
            try:
                self.log.info("connect start...")
                await self.client.connect()
                self.log.info("connect ok")
                break
            except Exception as e:
                self.log.error(f"connect failed: {e}, wait next retry...")
                await asyncio.sleep(3)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        self.log.info("disconnect start")
        await self.client.disconnect()
        self.client = None
        self.log.info("disconnect ok")

    def __aiter__(self):
        return self

    async def __anext__(self):
        if self.client is None:
            raise StopAsyncIteration

        (topic, msg, retained) = await self.client.queue.__anext__()

        return {
            "topic": topic.decode(),
            "payload": msg.decode(),
            "qos": 0,
        }

    async def publish(self, topic, payload: str, qos=0, retain=False):
        try:
            self.log.info(f"pub start: {topic} {qos} {retain} {payload[:32]}...")
            await self.client.publish(topic, payload, qos=qos, retain=retain)
            self.log.info(f"pub ok")
            return True, ""
        except Exception as e:
            self.log.warn(f"pub failed: {e}")
            return False, e

    async def subscribe(self, topic, qos=0):
        try:
            self.log.info(f"sub start: {topic} {qos}")
            await self.client.subscribe(topic, qos=qos)
            self.log.info(f"sub ok")
            return True, ""
        except Exception as e:
            self.log.warn(f"sub failed: {e}")
            return False, e

    async def unsubscribe(self, topic):
        try:
            self.log.info(f"unsub start: {topic}")
            await self.client.unsubscribe(topic)
            self.log.info(f"unsub ok")
            return True, ""
        except Exception as e:
            self.log.warn(f"unsub failed: {e}")
            return False, e
