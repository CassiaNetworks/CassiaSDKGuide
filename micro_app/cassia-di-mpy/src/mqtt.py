import asyncio
import json

from cassia_log import get_logger
from meta import MetaConfigManager
from mqtt_as import MQTTClient

try:
    from typing import Dict
except ImportError:
    pass


class MqttData:
    def to_dict(self) -> Dict:
        raise NotImplementedError


class MqttModule:
    def __init__(
        self,
        meta_mgr: MetaConfigManager,
    ):
        self.log = get_logger(self.__class__.__name__)

        self.client: MQTTClient = None
        self.meta_mgr = meta_mgr
        self.dispatcher = None

    async def _net_down_watcher(self):
        while True:
            await self.client.down.wait()
            self.client.down.clear()
            self.log.warn("!!!disconnected")

    async def _subscriber(self):
        while True:
            await self.client.up.wait()
            self.client.up.clear()
            self.log.info("connected to broker")

            await self.client.subscribe(self.meta_mgr.topics.unicast)
            self.log.info(f"sub topic ok: {self.meta_mgr.topics.unicast}")

            await self.client.subscribe(self.meta_mgr.topics.broadcast)
            self.log.info(f"sub topic ok: {self.meta_mgr.topics.broadcast}")

    async def _messager(self):
        async for topic, msg, retained in self.client.queue:
            self.log.info("recv:", topic, msg, retained)
            if self.dispatcher is not None:
                await self.dispatcher(topic.decode(), msg.decode(), retained)

    async def _start(self):
        config = {
            "client_id": self.meta_mgr.config.gateway_mac,
            "server": self.meta_mgr.config.mqtt_host,
            "port": self.meta_mgr.config.mqtt_port,
            "user": "",
            "password": "",
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

        while True:
            try:
                self.log.info("connect start...")
                await self.client.connect()
                self.log.info("connect ok")
                break
            except Exception as e:
                self.log.error("connect failed, waiting retry...")
                await asyncio.sleep(3)

    async def pub(self, topic: str, data: MqttData, qos: int = 0):
        msg = json.dumps(data.to_dict())
        self.log.info("pub:", topic, msg)
        await self.client.publish(topic, msg, qos=qos)

    def set_dispatcher(self, dispatcher):
        self.dispatcher = dispatcher

    def co_tasks(self) -> list[asyncio.Task]:
        return [
            asyncio.create_task(self._net_down_watcher()),
            asyncio.create_task(self._subscriber()),
            asyncio.create_task(self._messager()),
        ]

    async def start(self):
        await self._start()
