import asyncio
import time

import cassiasys

from cassia_log import get_logger
from meta import MetaConfigManager
from cassia_mqtt import MqttModule
from action_model import ActionData, HeartbeatData


class Heartbeat:
    def __init__(
        self,
        meta_mgr: MetaConfigManager,
        mqtt: MqttModule,
    ):
        self.log = get_logger(self.__class__.__name__)
        self.meta_mgr = meta_mgr
        self.mqtt = mqtt

    async def timer(self):
        id = 0

        data = HeartbeatData()

        message = ActionData(
            id=str(id),
            action="heartbeat",
            timestamp=int(time.time() * 1000),
            gateway=cassiasys.gateway_mac(),
            data=data,
        )

        # TODO: 严格5分钟周期，避免间隙
        while True:
            self.log.info("timer start")

            id += 1
            message.id = str(id)
            message.timestamp = int(time.time() * 1000)

            await self.mqtt.pub(self.meta_mgr.topics.heartbeat, message, qos=1)
            self.log.info("timer ok, wait next...")

            await asyncio.sleep(60)

    def co_tasks(self):
        return [
            asyncio.create_task(self.timer()),
        ]
