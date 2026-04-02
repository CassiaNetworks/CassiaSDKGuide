"""Simulated log protocol implementation using an nRF52840 Dongle. Please modify it according to your specific device."""

import struct
import json
import asyncio

from logger import logger
from wait import WaitFuture
from const import TaskPriority
from const import DeviceType
from gateway import CassiaGatewayAsync


class DeviceProfile:
    def __init__(self, gateway: CassiaGatewayAsync):
        # Sample GATT handles and commands below; replace with your actual device values
        self.NOTIFY_DATA_HANDLE = 0x17
        self.NOTIFY_HANDLE = 0x18
        self.WRITE_HANDLE = 0x17

        self.GATT_REQ_GET_LOGS_SIZE = "b56201"
        self.GATT_REQ_GET_LOGS = "b56206"

        self.gateway = gateway

        # Scan data cache
        self.scanned_devices = {}

        # Device task data cache
        self.devices_logs_buf = {}

        self.devices_waiter = WaitFuture()

        # Gateway packet continuity check
        self.devices_last_seq_gw = {}  # Gateway packet sequence number
        self.devices_seq_stats_gw = {}

    def _parse_addata(self, scan_data):
        if scan_data.get("adData") is None:
            return

        mac = scan_data["bdaddrs"][0]["bdaddr"]
        type = scan_data["bdaddrs"][0]["bdaddrType"]
        rssi = scan_data["rssi"]

        try:
            # TODO: Parser
            buf = bytes.fromhex(scan_data["adData"])
            self.scanned_devices[mac] = {
                "mac": mac,
                "type": type,
                "priority": TaskPriority.HIGH,
                "devicetype": DeviceType.SENSOR,
                "rssi": rssi,
            }
        except Exception as e:
            logger.debug(f"parse addata failed: {e} {scan_data}")

    def _pkt_seq_stat_gateway(self, mac, seq_num):
        """[Gateway Packet] Packet Loss Detection"""
        self.devices_last_seq_gw[mac] = self.devices_last_seq_gw.setdefault(mac, -1)
        last_seq_num = self.devices_last_seq_gw[mac]
        # logger.debug(f"[{mac}] pkt seq checker gateway: {seq_num} {last_seq_num}")

        if last_seq_num != -1 and seq_num - last_seq_num > 1:
            logger.error(f"[{mac}] pkt seq error gateway: {seq_num} {last_seq_num}")
            self.devices_seq_stats_gw[mac] = self.devices_seq_stats_gw.setdefault(
                mac, 0
            )
            self.devices_seq_stats_gw[mac] += 1
        self.devices_last_seq_gw[mac] = seq_num

    def _pkt_seq_stat_print(self, mac):
        logger.info("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
        logger.info(f"[{mac}] seq stat gw: {self.devices_seq_stats_gw.get(mac)}")
        logger.info("xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")

    def _pkt_seq_stat_clear(self, mac):
        self.devices_last_seq_gw.pop(mac, None)
        self.devices_seq_stats_gw.pop(mac, None)

    def _get_logs_size_res(self, mac, value_buf):
        id = self.gatt_gen_id(mac, "gatt_get_logs_size")
        logger.info(f"[{mac}] get logs size res: {value_buf.hex()}")
        packs = struct.unpack("<I", value_buf[:4])
        self.devices_waiter.end(id, data=packs[0])

    def _get_logs_res(self, mac, value_buf):
        # logger.debug(f"[{mac}] get logs res: {value_buf.hex()}")

        # Refresh timeout timer
        id = self.gatt_gen_id(mac, "gatt_get_logs")
        waiter = self.devices_waiter.get(id)
        if not waiter:
            return

        expect_logs_size = waiter["args"]["logs_size"]
        packs = struct.unpack("<I", value_buf[3 : 3 + 4])
        pkt_offset = packs[0]
        pkt_size = len(value_buf)
        logger.debug(
            f"[{mac}] [{expect_logs_size}] [{pkt_offset}] [{pkt_size}] add logs: {value_buf.hex()}"
        )

        self.devices_logs_buf.setdefault(mac, bytearray()).extend(value_buf)
        expect_offset = len(self.devices_logs_buf[mac]) - pkt_size

        if pkt_offset != expect_offset:
            error = (
                f"[{mac}] logs pkt offset check failed: {pkt_offset} {expect_offset}"
            )
            logger.error(error)
            self.devices_waiter.end(id, error=error)
            self.devices_logs_buf.pop(mac, None)

        if pkt_offset + pkt_size >= expect_logs_size:
            logger.info(f"[{mac}] [{expect_logs_size}] [{pkt_offset}] get logs ok:")
            self.devices_waiter.end(id, data=self.devices_logs_buf[mac])
            self.devices_logs_buf.pop(mac, None)
        else:
            logger.debug(f"[{mac}] logs pkt ...")
            pass

    def gatt_gen_id(self, mac, ops):
        """Generate a unique operation ID for waiting"""
        return f"{mac}_{ops}"

    async def gatt_get_logs(self, mac, logs_size):
        """Read internal device logs"""
        id = self.gatt_gen_id(mac, "gatt_get_logs")
        logger.info(f"[{mac}] get logs start: {logs_size}")

        await self.gateway.write_handle(mac, self.WRITE_HANDLE, self.GATT_REQ_GET_LOGS)

        ret = await self.devices_waiter.add(id, {"logs_size": logs_size})

        logger.info(f"[{mac}] get logs ok: {len(ret)} {ret[:32]}...")

    async def gatt_open_notify(self, mac):
        logger.info(f"[{mac}] open gatt notify start")
        await self.gateway.write_handle(mac, self.NOTIFY_HANDLE, "0100")
        logger.info(f"[{mac}] open gatt notify ok")

    async def gatt_get_logs_size(self, mac):
        id = self.gatt_gen_id(mac, "gatt_get_logs_size")
        logger.info(f"[{mac}] get logs size start")

        waiter = self.devices_waiter.add(id)
        await self.gateway.write_handle(
            mac, self.WRITE_HANDLE, self.GATT_REQ_GET_LOGS_SIZE
        )

        ret = await waiter
        logger.info(f"[{mac}] get logs size ok: {ret}")

        return ret

    def scanner(self, event):
        """Gateway Scan SSE Data Processing"""
        logger.debug(f"scan sse event: {event}")
        scan_data = json.loads(event.data)
        self._parse_addata(scan_data)

    def notifier(self, event):
        """Gateway Notification SSE Data Processing"""
        # logger.info(f"notify sse event: {event}")
        data = json.loads(event.data)

        # [Gateway] <--> [APP]: Transmission Packet Loss Detection
        self._pkt_seq_stat_gateway(data["id"], data["seqNum"])

        if data["handle"] != self.NOTIFY_DATA_HANDLE:
            return

        value_buf = bytes.fromhex(data["value"])
        if value_buf[0] == 0xB5 and value_buf[1] == 0x62 and value_buf[2] == 0x06:
            self._get_logs_res(data["id"], value_buf)
        else:
            self._get_logs_size_res(data["id"], value_buf)

    async def task_get_logs(self, mac):
        """Device Task: Retrieve Logs"""
        try:
            logger.info(f"[{mac}] task get logs start")
            await self.gatt_open_notify(mac)
            logs_size = await self.gatt_get_logs_size(mac)
            logger.info(f"[{mac}] task logs size: {logs_size}")
            logs = await self.gatt_get_logs(mac, logs_size)
            logger.info(f"[{mac}] task logs: {logs}")
            self._pkt_seq_stat_print(mac)
        except Exception as ex:
            logger.error(f"[{mac}] task get logs failed: {ex}")
            raise ex
        finally:
            self.devices_logs_buf.pop(mac, None)
            self._pkt_seq_stat_clear(mac)

    def get_scanned_devices(self):
        return self.scanned_devices

    def remove_scanned_device(self, mac):
        self.scanned_devices.pop(mac, None)
        logger.info(f"[{mac}] removed in scanned data")

    def clear_scanned_devices(self):
        self.scanned_devices.clear()
