import json
import time
import asyncio

from cassia_log import get_logger
from error import Error
from meta import MetaConfigManager
from meta import FORWORD_RAW_SCAN_ON
from meta import FORWORD_RAW_NOTIFY_ON
from waiter_manager import WaiterManager
from cassiablue_manager import ScanData
from cassiablue_manager import ScanDataParsed
from cassiablue_manager import NotifyData
from cassiablue_manager import ConnectionStateData

from task_entry import TaskMeta, State
from task_manager import DeviceTaskQueueManager

from profile_model import DeviceActionRequestData
from profile_model import DeviceActionResponse
from profile_model import DeviceActionResData

from profile_manager import ProfileManager
from mqtt import MqttModule
from mqtt import MqttData

try:
    from typing import List, Union, Dict, Any, Optional
except ImportError:
    pass


class ActionData(MqttData):
    def __init__(
        self,
        id: str,
        action: str,
        timestamp: int,
        gateway: str,
        data: Union[
            List[ScanData],
            List[ScanDataParsed],
            List[NotifyData],
            List[ConnectionStateData],
            # "Heartbeat",
            # "GatewayStatus",
            None,
        ] = None,
    ):
        self.id = id
        self.action = action
        self.timestamp = timestamp
        self.gateway = gateway
        self.data = data

    def to_dict(self) -> dict:
        data_dict = None
        if self.data is not None:
            data_dict = [x.to_dict() for x in self.data]

        return {
            "id": self.id,
            "action": self.action,
            "timestamp": self.timestamp,
            "gateway": self.gateway,
            "data": data_dict,
        }


class MessageDispatcher:
    def __init__(
        self,
        meta_mgr: MetaConfigManager,
        mqtt: MqttModule,
        waiter_mgr: WaiterManager,
        profile_mgr: ProfileManager,
        task_mgr: DeviceTaskQueueManager,
    ):
        self.log = get_logger(self.__class__.__name__)

        self.mqtt = mqtt
        self.waiter_mgr = waiter_mgr
        self.task_mgr = task_mgr
        self.profile_mgr = profile_mgr
        self.meta_mgr = meta_mgr

    async def scan_data_handler(self, scan_data: Dict[str, Any]) -> None:
        self.log.debug("scan data handler", json.dumps(scan_data))

        message = ActionData(
            id="",
            action="",
            timestamp=int(time.time() * 1000),
            gateway=self.meta_mgr.config.gateway_mac,
            data=None,
        )

        scan_data_obj = ScanData(
            device_mac=scan_data["bdaddr"],
            addr_type=scan_data["bdaddrType"],
            event_type=scan_data["evtType"],
            rssi=scan_data["rssi"],
            name=scan_data["name"],
            ad_data=scan_data.get("adData"),
            scan_data=scan_data.get("scanData"),
            chip_id=scan_data.get("chipId"),
            primary_phy=scan_data.get("primaryPhy"),
            prop=scan_data.get("prop"),
            data_status=scan_data.get("dataStatus"),
            interval=scan_data.get("interval"),
            secondary_phy=scan_data.get("secondaryPhy"),
            tx_power=scan_data.get("txPower"),
            sid=scan_data.get("sid"),
        )

        if self.meta_mgr.config.forward_raw_scan == FORWORD_RAW_SCAN_ON:
            message.action = "scan_data"
            message.data = [scan_data_obj]
            await self.mqtt.pub(self.meta_mgr.topics.scan, message, qos=0)

        matched_model = None

        for _, v in self.profile_mgr.get_models().items():
            if v.is_model(scan_data_obj):
                matched_model = v

        if matched_model is None or matched_model.scan_handler is None:
            return

        payload = await matched_model.scan_handler(scan_data_obj)
        if payload is None:
            return

        message.action = "scan_data_decoded"
        scan_data_decoded = ScanDataParsed(
            device_mac=scan_data["bdaddr"],
            model=matched_model.get_name(),
            name=scan_data["name"],
            ad_data=scan_data.get("adData"),
            rssi=scan_data["rssi"],
            payload=payload,
        )
        message.data = [scan_data_decoded]

        await self.mqtt.pub(self.meta_mgr.topics.scan, message, qos=0)

    async def notify_data_handler(self, notify: Dict[str, Any]) -> None:
        self.log.debug("notify data:", notify)

        notify_data = NotifyData(
            device_mac=notify["id"],
            handle=notify["handle"],
            value=notify["value"],
        )

        if self.meta_mgr.config.forward_raw_notify == FORWORD_RAW_NOTIFY_ON:
            message = ActionData(
                id="",
                action="notification",
                timestamp=int(time.time() * 1000),
                gateway=self.meta_mgr.config.gateway_mac,
                data=[notify_data],
            )

            await self.mqtt.pub(self.meta_mgr.topics.notify, message, qos=1)

        device_mac = notify["id"]
        current_task = await self.task_mgr.get_current_task(device_mac)
        if current_task is None:
            self.log.warn(f"notify device no task {device_mac}")
            await asyncio.sleep_ms(0)
            return

        model = self.profile_mgr.get_model(current_task.meta.model)
        if model is None:
            self.log.warn(f"task no profile: {device_mac} {current_task.meta.model}")
            await asyncio.sleep_ms(0)
            return

        await model.notify_handler(current_task, notify_data)

    async def connection_state_data_handler(self, data: Dict[str, Any]) -> None:
        state_data = ConnectionStateData(
            device_mac=data["handle"],
            connection_state=data["connectionState"],
            chip_id=data.get("chip_id"),
            reason=data.get("reason"),
        )

        message = ActionData(
            id="",
            action="connection_state",
            timestamp=int(time.time() * 1000),
            gateway=self.meta_mgr.config.gateway_mac,
            data=[state_data],
        )

        await self.mqtt.pub(self.meta_mgr.topics.state, message, qos=1)

        if state_data.connection_state != "disconnected":
            return

        # 设备断链事件，获取设备任务，设置任务状态
        # 这里是为了优化下面的场景
        # - 下行的操作都成功了，但是设备上行传输数据过程中断链了
        # - 没有下面的逻辑的话，设备任务会等到超时时间到了才能触发，导致后续的任务也无法正常执行
        device_mac = data["handle"]
        current_task = await self.task_mgr.get_current_task(device_mac)
        if current_task is None:
            self.log.warn(f"state device no task {device_mac}")
            return

        if current_task.state != State.RUNNING:
            self.log.info(f"device current task no running {device_mac}")
            return

        error = Error.from_cassiablue_ret(data.get("reason"))
        self.waiter_mgr.end_by_id_prefix(current_task.meta.id, error)

    async def dispatcher(self, topic: str, msg: str, retained: bool):

        try:
            parsed_msg = json.loads(msg)

            id = parsed_msg.get("id")
            action = parsed_msg.get("action")

            if id is None or action is None:
                return

            data = parsed_msg.get("data")

            device_req: List[DeviceActionRequestData] = []
            if isinstance(data, list):
                device_req = data
            elif isinstance(data, dict):
                device_req = [data]

            if not device_req:
                self.log.info(f"device req empty: {data}")

                action_reply = DeviceActionResponse(
                    id=id,
                    action=f"{action}_reply",
                    timestamp=int(time.time() * 1000),
                    gateway="",
                    data=DeviceActionResData(
                        code=400,
                        msg="empty device data or invalid req data format",
                        body=None,
                    ),
                )

                return json.dumps(action_reply.to_dict())

            for req_data in device_req:
                task_meta = TaskMeta(
                    id=str(id),
                    model=req_data.get("model"),
                    device_mac=req_data.get("device_mac"),
                    action=action,
                    timeout=req_data.get("timeout"),
                    payload=req_data.get("extra_fields"),
                )
                await self.task_mgr.create_task(task_meta)

            return None

        except Exception as e:
            self.log.info(f"execute error: {e}")
            # todo返回响应
