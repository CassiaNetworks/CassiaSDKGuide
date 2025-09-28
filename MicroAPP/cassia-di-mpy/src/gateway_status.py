import asyncio
import json
import time
import gc

import cassiablue

from cassia_log import get_logger
from meta import MetaConfigManager
from cassia_mqtt import MqttModule
from action_model import GatewayStatusData, ActionData


class GatewayStatus:
    def __init__(
        self,
        meta_mgr: MetaConfigManager,
        mqtt: MqttModule,
    ):
        self.log = get_logger(self.__class__.__name__)
        self.meta_mgr = meta_mgr
        self.mqtt = mqtt

    async def get_cassia_info(self):
        path = "/cassia/info"
        self.log.info(f"get cassia info start")
        ok, ret = await cassiablue.send_cmd(url=path)
        self.log.info(f"get cassia info status: {ok}, resp: {ret}")
        if not ok:
            return False, {}
        return True, json.loads(ret)

    async def get_cassia_memory(self):
        path = "/cassia/memory"
        self.log.info(f"get cassia memory start")
        ok, ret = await cassiablue.send_cmd(url=path)
        self.log.info(f"get cassia memory status: {ok}, resp: {ret}")
        if not ok:
            return False, {}
        return True, json.loads(ret)

    async def timer(self):
        id = 0

        data = GatewayStatusData(
            model=cassiablue._gateway_type,
            version="",
            uptime=0,
            free_memory=0,
            free_internel=0,
            free_spiram=0,
            gc_mem_free=0,
            gc_mem_alloc=0,
        )

        message = ActionData(
            id=str(id),
            action="gateway_status",
            timestamp=int(time.time() * 1000),
            gateway=cassiablue._gateway_mac,
            data=data,
        )

        # TODO: 严格5分钟周期，避免间隙
        while True:
            self.log.info("timer start")

            id += 1
            message.id = str(id)

            message.data.version = cassiablue._gateway_ver
            _ok, info = await self.get_cassia_info()
            message.data.uptime = info.get("uptime", 0)

            _ok, memory = await self.get_cassia_memory()
            message.data.free_memory = memory.get("free-memory", 0)
            message.data.free_internel = memory.get("free-internel", 0)
            message.data.free_spiram = memory.get("free-spiram", 0)

            message.data.gc_mem_alloc = gc.mem_alloc()
            message.data.gc_mem_free = gc.mem_free()

            message.timestamp = int(time.time() * 1000)
            await self.mqtt.pub(self.meta_mgr.topics.gateway_status, message, qos=1)
            self.log.info("timer ok, wait next...")

            await asyncio.sleep(300)

    def co_tasks(self):
        return [
            asyncio.create_task(self.timer()),
        ]
