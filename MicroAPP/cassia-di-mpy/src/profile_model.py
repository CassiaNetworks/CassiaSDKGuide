try:
    from typing import Optional, Dict, Any
except ImportError:
    pass

from cassiablue_manager import ScanData, NotifyData
from task_entry import DeviceTaskEntry


class DeviceActionRequestData:
    def __init__(
        self,
        device_mac: str,
        model: str,
        timeout: int,
        extra_fields: Optional[Dict[str, Any]] = None,
    ):
        self.device_mac = device_mac
        self.model = model
        self.timeout = timeout
        self.extra_fields = extra_fields or {}

    def to_dict(self):
        result = {
            "device_mac": self.device_mac,
            "model": self.model,
            "timeout": self.timeout,
        }
        result.update(self.extra_fields)
        return result


class DeviceActionResDataBody:
    def __init__(self, device_mac: str, data: Any):
        self.device_mac = device_mac
        self.data = data

    def to_dict(self):
        return {"device_mac": self.device_mac, "data": self.data}


class DeviceActionResData:
    def __init__(
        self, code: int, msg: str, body: Optional[DeviceActionResDataBody] = None
    ):
        self.code = code
        self.msg = msg
        self.body = body

    def to_dict(self):
        result = {"code": self.code, "msg": str(self.msg)}
        if self.body:
            result["body"] = self.body.to_dict()
        return result


class DeviceActionResponse:
    def __init__(
        self,
        id: str,
        action: str,
        timestamp: int,
        gateway: str,
        data: DeviceActionResData,
    ):
        self.id = id
        self.action = action
        self.timestamp = timestamp
        self.gateway = gateway
        self.data = data

    def to_dict(self):
        return {
            "id": self.id,
            "action": self.action,
            "timestamp": self.timestamp,
            "gateway": self.gateway,
            "data": self.data.to_dict(),
        }


class Model:

    def get_name(self) -> str:
        raise NotImplementedError

    def is_model(self, scan_data: ScanData) -> bool:
        raise NotImplementedError

    async def scan_handler(self, scan_data: ScanData) -> Optional[any]:
        raise NotImplementedError

    async def notify_handler(self, task_entry, notify_data: NotifyData):
        raise NotImplementedError

    async def execute(self, task: DeviceTaskEntry):
        raise NotImplementedError
