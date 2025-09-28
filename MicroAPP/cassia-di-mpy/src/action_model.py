try:
    from typing import List, Union, Optional, Dict
except ImportError:
    pass


class MqttData:
    def to_dict(self) -> Dict:
        raise NotImplementedError


class HeartbeatData(MqttData):
    def __init__(self):
        pass

    def to_dict(self) -> dict:
        data = {}
        return data


class GatewayStatusData(MqttData):
    def __init__(
        self,
        model: str,
        version: str,
        uptime: int,
        free_memory: int,
        free_internel: int,
        free_spiram: int,
        gc_mem_free: int,
        gc_mem_alloc: int,
    ):
        self.model = model
        self.version = version
        self.uptime = uptime
        self.free_memory = free_memory
        self.free_internel = free_internel
        self.free_spiram = free_spiram
        self.gc_mem_free = gc_mem_free
        self.gc_mem_alloc = gc_mem_alloc

    def to_dict(self) -> dict:
        data = {
            "model": self.model,
            "version": self.version,
            "uptime": self.uptime,
            "free_memory": self.free_memory,
            "free_internel": self.free_internel,
            "free_spiram": self.free_spiram,
            "gc_mem_free": self.gc_mem_free,
            "gc_mem_alloc": self.gc_mem_alloc,
        }
        return data


class ScanDataParsed(MqttData):

    def __init__(
        self,
        device_mac: str,
        model: str,
        name: str,
        ad_data: str,
        rssi: int,
        payload: MqttData,
    ):
        self.device_mac = device_mac
        self.model = model
        self.name = name
        self.ad_data = ad_data
        self.rssi = rssi
        self.payload = payload

    def to_dict(self):
        return {
            "device_mac": self.device_mac,
            "model": self.model,
            "name": self.name,
            "ad_data": self.ad_data,
            "rssi": self.rssi,
            "payload": self.payload.to_dict(),
        }


class ScanData(MqttData):
    def __init__(
        self,
        device_mac: str,
        addr_type: str,
        chip_id: int,
        event_type: int,
        rssi: int,
        name: str,
        ad_data: str,
        scan_data: str,
        primary_phy: Optional[str] = None,
        prop: Optional[str] = None,
        data_status: Optional[str] = None,
        interval: Optional[int] = None,
        secondary_phy: Optional[str] = None,
        tx_power: Optional[int] = None,
        sid: Optional[int] = None,
    ):
        self.device_mac = device_mac
        self.addr_type = addr_type
        self.chip_id = chip_id
        self.event_type = event_type
        self.rssi = rssi
        self.name = name
        self.ad_data = ad_data
        self.scan_data = scan_data

        self.primary_phy = primary_phy
        self.prop = prop
        self.data_status = data_status
        self.interval = interval
        self.secondary_phy = secondary_phy
        self.tx_power = tx_power
        self.sid = sid

    def to_dict(self) -> dict:
        data = {
            "device_mac": self.device_mac,
            "addr_type": self.addr_type,
            "event_type": self.event_type,
            "rssi": self.rssi,
            "name": self.name,
            "ad_data": self.ad_data,
            "scan_data": self.scan_data,
        }

        if self.chip_id is not None:
            data["chip_id"] = self.chip_id

        if self.primary_phy is not None:
            data["primary_phy"] = self.primary_phy

        if self.prop is not None:
            data["prop"] = self.prop

        if self.data_status is not None:
            data["data_status"] = self.data_status

        if self.interval is not None:
            data["interval"] = self.interval

        if self.secondary_phy is not None:
            data["secondary_phy"] = self.secondary_phy

        if self.tx_power is not None:
            data["tx_power"] = self.tx_power

        if self.sid is not None:
            data["sid"] = self.sid

        return data


class NotifyData(MqttData):
    def __init__(
        self,
        device_mac: str,
        handle: int,
        value: str,
    ):
        self.device_mac = device_mac
        self.handle = handle
        self.value = value

    def to_dict(self):
        return {
            "device_mac": self.device_mac,
            "handle": self.handle,
            "value": self.value,
        }


class ConnectionStateData(MqttData):
    def __init__(
        self,
        device_mac: str,
        connection_state: str,
        chip_id: Optional[int] = None,
        reason: Optional[str] = None,
    ):
        self.device_mac = device_mac
        self.connection_state = connection_state
        self.chip_id = chip_id
        self.reason = reason

    def to_dict(self):
        data = {
            "device_mac": self.device_mac,
            "connection_state": self.connection_state,
        }

        if self.chip_id is not None:
            data["chip_id"] = self.chip_id

        if self.reason is not None:
            data["reason"] = self.reason

        return data


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
            GatewayStatusData,
            HeartbeatData,
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
            if isinstance(self.data, list):
                data_dict = [x.to_dict() for x in self.data]
            elif isinstance(self.data, MqttData):
                data_dict = self.data.to_dict()

        return {
            "id": self.id,
            "action": self.action,
            "timestamp": self.timestamp,
            "gateway": self.gateway,
            "data": data_dict,
        }
