import asyncio
import json
import gc
import sys

from cassia_log import get_logger
from meta import MetaConfigManager
from action_model import MqttData
from cassiamqtt import CassiaMQTTClient

try:
    from typing import Dict
except ImportError:
    pass


class MqttModule:
    def __init__(
        self,
        meta_mgr: MetaConfigManager,
    ):
        self.log = get_logger(self.__class__.__name__)

        self.client: CassiaMQTTClient = None
        self.meta_mgr = meta_mgr
        self.dispatcher = None

    async def _sub_topics(self) -> bool:
        topics = [
            self.meta_mgr.topics.unicast,
            self.meta_mgr.topics.broadcast,
        ]

        for topic in topics:
            ok, ret = await self.client.subscribe(topic, qos=1)
            if not ok:
                self.log.error("sub topic failed:", ret, topic)
                return False
            self.log.info(f"sub topic ok: {topic}")

        return True

    async def _run(self):
        host = self.meta_mgr.config.mqtt_host
        port = self.meta_mgr.config.mqtt_port
        uri = f"mqtt://{host}:{port}"
        client_id = self.meta_mgr.config.gateway_mac

        while True:
            try:
                self.log.info("connect start...", uri)
                async with CassiaMQTTClient(uri, client_id=client_id) as client:
                    self.log.info("connect ok")
                    self.client = client

                    ok = await self._sub_topics()
                    if not ok:
                        self.client = None
                        self.log.error("sub topics failed, waiting retry...")
                        await asyncio.sleep(5)
                        continue

                    async for msg in self.client:
                        self.log.info("recv:", msg)
                        if self.dispatcher is not None:
                            try:
                                await self.dispatcher(
                                    msg.get("topic"), msg.get("payload"), False
                                )
                            except Exception as e:
                                self.log.error(f"!!!msg exception!!!")
                                sys.print_exception(e)

                    self.log.warn(f"!!!for msg exit!!!")

            except Exception as e:
                self.client = None
                self.log.error("connection exception, waiting retry...", e)
            finally:
                await asyncio.sleep(5)

    async def _print_mem(self):
        while True:
            await asyncio.sleep(1)
            gc.collect()
            free = gc.mem_free()
            alloc = gc.mem_alloc()
            self.log.info(f"RAM free {free} alloc {alloc}")

    async def pub(self, topic: str, data: MqttData, qos: int = 1):
        # cache or stats, and do not log
        if not self.client:
            self.log.info("pub no client:", topic, data)
            return

        try:
            msg = json.dumps(data.to_dict())
            self.log.info("pub start:", topic, msg, qos)
            ok, ret = await self.client.publish(topic, msg, qos)
            self.log.info("pub done:", ok, ret)
        except Exception as e:
            self.log.warn("!!!!!!!!!!!!", e)

    def set_dispatcher(self, dispatcher):
        self.dispatcher = dispatcher

    def co_tasks(self) -> list[asyncio.Task]:
        return [
            asyncio.create_task(self._run()),
            asyncio.create_task(self._print_mem()),
        ]
