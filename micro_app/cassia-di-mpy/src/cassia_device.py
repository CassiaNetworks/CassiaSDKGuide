import asyncio
import struct

from cassia_log import get_logger
from waiter_manager import WaiterManager
from profile_model import Model
from task_entry import DeviceTaskEntry
from cassiablue_manager import NotifyData, ScanData
from mqtt import MqttData


class CassiaDeviceParsedScanData(MqttData):
    def __init__(self, buffer):
        self.app_id = 1
        self.build_no = 99

    def to_dict(self):
        return {
            "app_id": self.app_id,
            "build_no": self.build_no,
        }


class CassiaDeviceGetLogsResponseData:
    def __init__(self, count: int, logs: str):
        self.count = count
        self.logs = logs

    def to_dict(self):
        return {
            "count": self.count,
            "logs": self.logs,
        }


class CassiaDeviceAction:
    GET_LOGS = "get_logs"


class CassiaDevice(Model):
    NAME = "CassiaDevice"
    ADV_FLAG = "cassia-device"

    LOG_COUNT = 10
    DATA_NOTIFY_HANDLE = 44
    CMD_NOTIFY_HANDLE = 45
    CMD_WRITE_HANDLE = 42

    GATT_REQ_OPEN_NOTIFY = "0100"
    GATT_REQ_GET_LOGS = "GATT_REQ_GET_LOGS"

    def __init__(
        self,
        waiter_mgr: WaiterManager,
    ):
        self.log = get_logger(self.__class__.__name__)

        self.model = CassiaDevice.NAME
        self.name = CassiaDevice.NAME
        self.waiter_mgr = waiter_mgr
        self.devices_logs_buf: dict[str, any] = {}

    def get_name(self):
        return self.name

    def is_model(self, scan_data: ScanData):
        return scan_data.name.startswith(CassiaDevice.ADV_FLAG)

    async def sleep_more(self):
        """这里需要根据一次处理notification耗时情况，主动让出，方便其他命令响应处理，否则可能响应时间会较长"""
        await asyncio.sleep_ms(1000)

    async def notify_handler(
        self, task_entry: DeviceTaskEntry, notify_data: NotifyData
    ):
        self.log.info("profile notify data:", notify_data)

        notify_handle = notify_data.handle
        if notify_handle != CassiaDevice.DATA_NOTIFY_HANDLE:
            await self.sleep_more()
            return

        task = task_entry
        if task.meta.action != CassiaDeviceAction.GET_LOGS:
            await self.sleep_more()
            return

        device_mac = notify_data.device_mac
        notify_value = notify_data.value

        value_buf = bytes.fromhex(notify_value)
        if value_buf[0] == 0xA0:
            await self._get_logs_res(task_entry, device_mac, value_buf)

    async def _get_logs_res(self, task_entry: DeviceTaskEntry, mac, value_buf):
        id = WaiterManager.gen_task_id(
            task_entry.meta.id, mac, CassiaDevice.GATT_REQ_GET_LOGS
        )
        waiter = self.waiter_mgr.get(id)

        if waiter is None:
            self.log.info(f"get logs res no waiter by id: {id}")
            return False

        if waiter.args is None:
            self.log.info(f"no args by id: {id}")
            return False

        pkt_seq = (value_buf[2] << 0x08) | value_buf[3]
        self.log.debug(f"[{mac}] [{CassiaDevice.LOG_COUNT}] [{pkt_seq}] add logs...")

        self.devices_logs_buf.setdefault(mac, bytearray()).extend(value_buf)

        if pkt_seq >= CassiaDevice.LOG_COUNT - 1:
            self.log.debug(
                f"[{mac}] [{CassiaDevice.LOG_COUNT}] [{pkt_seq}] get logs ok"
            )
            self.waiter_mgr.end(id, data=self.devices_logs_buf[mac])
            self.devices_logs_buf.pop(mac, None)
        else:
            self.log.info(f"[{mac}] logs pkt ...")

    async def scan_handler(self, scan_data: ScanData):
        self.log.debug(f"profile scan data: {scan_data.to_dict()}")

        if not scan_data.ad_data:
            return None

        try:
            buffer = bytes.fromhex(scan_data.ad_data)
            data = CassiaDeviceParsedScanData(buffer)
            return data

        except Exception as e:
            self.log.error(f"scan handler error: {e}")
            return None

    async def get_logs(self, task: DeviceTaskEntry, log_count: int):
        mac = task.meta.device_mac
        id = WaiterManager.gen_task_id(
            task.meta.id, mac, CassiaDevice.GATT_REQ_GET_LOGS
        )

        self.log.info(f"[{mac}] get logs start")
        future = self.waiter_mgr.add(id, {"log_count": log_count})

        buf = struct.pack(">H", self.LOG_COUNT)
        REQ_LOG_HEX = f"2002{buf.hex()}"
        await task.cassiablue_mgr.write_handle(
            mac, CassiaDevice.CMD_WRITE_HANDLE, REQ_LOG_HEX
        )
        ret = await future.wait()
        self.log.info(f"[{mac}] get logs ok: {len(ret)} {ret[:32]}...")
        return ret

    async def get_logs_handler(self, task: DeviceTaskEntry):
        id = task.meta.id
        mac = task.meta.device_mac
        self.log.info(f"get logs handler start: {id} {mac}")

        if mac in self.devices_logs_buf:
            del self.devices_logs_buf[mac]

        await task.cassiablue_mgr.connect(mac)
        await task.cassiablue_mgr.write_handle(
            mac,
            CassiaDevice.CMD_NOTIFY_HANDLE,
            CassiaDevice.GATT_REQ_OPEN_NOTIFY,
        )

        logs = await self.get_logs(task, CassiaDevice.LOG_COUNT)
        self.log.info(f"[{mac}] get logs handler data ok: {len(logs)}")

        return CassiaDeviceGetLogsResponseData(
            count=len(logs),
            logs=bytes(logs).hex(),
        )

    async def execute(self, task: DeviceTaskEntry) -> MqttData:
        ret = None

        if task.meta.action == CassiaDeviceAction.GET_LOGS:
            ret = await self.get_logs_handler(task)

        if ret is not None:
            await asyncio.sleep(0.5)
            await task.cassiablue_mgr.disconnect(task.meta.device_mac)
            self.log.info(f"disconnect device ok: {task.meta.device_mac}")

        return ret
