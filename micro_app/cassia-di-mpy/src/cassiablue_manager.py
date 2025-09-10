import asyncio
import json
import cassiablue

from cassia_log import get_logger
from error import Error
from meta import MetaConfigManager
from mqtt import MqttData

try:
    from typing import Optional, List, Dict, Any
except ImportError:
    pass


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


class GatewayError(Exception):
    pass


class DeviceInfo:
    def __init__(
        self,
        name: str,
        addr_type: str,
    ):
        self.name = name
        self.addr_type = addr_type


class CassiaBlueManager:

    def __init__(
        self,
        meta_mgr: MetaConfigManager,
    ):
        self.log = get_logger(self.__class__.__name__)

        self.scanner = None
        self.notifier = None
        self.stater = None

        self.device_info: Dict[str, DeviceInfo] = {}
        self.meta_mgr = meta_mgr

    async def _print_ret_raw(
        self, ok, prefix=None, mac=None, ret=None, ignore_ex=False
    ):
        self.log.info(f"[{mac}] {prefix} status: {ok}, resp: {ret}")
        if not ignore_ex and not ok:
            error = Error.from_cassiablue_ret(ret)
            raise GatewayError(error)
        return ret

    async def _print_ret_json(self, ok, ret, prefix=None, mac=None, ignore_ex=False):
        self.log.info(f"[{mac}] {prefix} status: {ok}, resp: {ret}")
        if not ignore_ex and not ok:
            error = Error.from_cassiablue_ret(ret)
            raise GatewayError(error)
        return json.loads(ret)

    async def connect(self, mac: str, params: Dict = None):
        if params is None:
            info = self.device_info.get(mac)
            if info is not None:
                params = {"type": info.addr_type}
            else:
                params = {}

        params["timeout"] = self.meta_mgr.config.conn_timeout
        params["fail_retry_times"] = self.meta_mgr.config.conn_fail_retry_times

        params = json.dumps(params)
        self.log.info(f"[{mac}] connect start: {params}")

        ok, ret = await cassiablue.connect(mac, params)
        await self._print_ret_raw(ok=ok, prefix="connect done", mac=mac, ret=ret)

    async def write_handle(self, mac, handle, value):
        self.log.info(f"[{mac}] write handle start: {handle} {value}")
        ok, ret = await cassiablue.gatt_write(mac, handle, value)
        await self._print_ret_raw(ok=ok, prefix="write handle done", mac=mac, ret=ret)

    async def read_handle(self, mac, handle):
        self.log.info(f"[{mac}] read handle start: {handle}")
        ok, ret = await cassiablue.gatt_read(mac, handle)
        return await self._print_ret_json(
            ok=ok, ret=ret, prefix="read handle done", mac=mac
        )

    async def discover_gatt_all(self, mac):
        self.log.info(f"[{mac}] discover gatt all start")
        ok, ret = await cassiablue.gatt_read(mac)
        return await self._print_ret_json(
            ok=ok, ret=ret, prefix="discover gatt all done", mac=mac
        )

    async def get_connected(self):
        self.log.info(f"get connected start")
        ok, ret = await cassiablue.get_connected_devices()
        return await self._print_ret_json(ok=ok, prefix="get connected done", ret=ret)

    async def disconnect(self, mac: str):
        self.log.info(f"[{mac}] disconnect start")
        ok, ret = await cassiablue.disconnect(mac)
        self._print_ret_raw(ok=ok, mac=mac, prefix="disconnect done", ret=ret)

    def _update_device_info(self, adv):
        mac = adv.get("bdaddr")

        info = self.device_info.get(mac)
        if info is None:
            self.device_info[mac] = DeviceInfo(
                name=adv["name"],
                addr_type=adv["bdaddrType"],
            )
            self.log.info(f"add device info: {mac} {adv["name"]}")
            return

        if info.name != "(unknown)":
            adv["name"] = info.name
        elif adv.get("name") != "(unknown)":
            self.log.info(f"update device name: {mac} {adv.get("name")}")
            info.name = adv.get("name")

    async def co_scanner(self) -> None:
        self.log.info(f"co scanner start")
        filter = self.meta_mgr.get_scan_filter()
        ok, _ = await cassiablue.start_scan(filter)
        self._print_ret_raw(ok=ok, prefix="co scanner done")
        async for adv in cassiablue.scan_result():
            self._update_device_info(adv)
            await self.scanner(adv)

    async def co_notifier(self) -> None:
        self.log.info(f"co notifier start")
        ok, _ = await cassiablue.start_recv_notify()
        self._print_ret_raw(ok=ok, prefix="co noitifier done")
        async for notication in cassiablue.notify_result():
            await self.notifier(notication)

    async def co_stater(self) -> None:
        self.log.info(f"co stater start")
        ok, _ = await cassiablue.start_recv_connection_state()
        self._print_ret_raw(ok=ok, prefix="co stater done")
        async for state in cassiablue.connection_result():
            await self.stater(state)

    def set_handler(self, scanner, notifier, stater):
        self.scanner = scanner
        self.notifier = notifier
        self.stater = stater

    def co_tasks(self) -> List[asyncio.Task]:
        return [
            asyncio.create_task(self.co_scanner()),
            asyncio.create_task(self.co_notifier()),
            asyncio.create_task(self.co_stater()),
        ]
