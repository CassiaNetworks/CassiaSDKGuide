import os
import json
import asyncio

import aiofiles

from logger import logger
from const import DeviceType, TaskPriority, TaskState
from util import get_timestamp
from util import get_timestamp_str

# Execution rounds: 0 - repeat execution, others - specific rounds
TEST_ROUND = int(os.getenv("TEST_ROUND") or "1")


class TestDevices:
    def __init__(self, json_file):
        self.json_raw = ""
        self.devices = None

        self.start_ts = 0
        self.end_ts = 0
        self.used_sec = 0
        self.history = []

        self._run_counter = 0

        with open(json_file, "r") as file:
            self.json_raw = file.read()
            self.devices = json.loads(self.json_raw)

        logger.info(f"[TEST] load devices ok: {self.json_raw}")

    def _history_append(self):
        """Record all results for display"""
        self.end_ts = get_timestamp()
        self.used_sec = self.end_ts - self.start_ts
        self.history.append(
            {
                "start_ts": self.start_ts,
                "end_ts": self.end_ts,
                "used_sec": self.used_sec,
                "devices": self.devices,
            }
        )
        if len(self.history) > 10:
            self.history.pop(0)

    async def _history_save(self):
        """Save historical results to a file"""
        ts_str = get_timestamp_str()
        file_name = f"../result/test_devices_history_{ts_str}.json"
        json_str = json.dumps(self.history_get(), indent=4)

        async with aiofiles.open(file_name, "w") as f:
            await f.write(json_str)
        logger.info(f"[TEST] save history file ok: {file_name}")
        return file_name

    def _is_all_priority_low(self):
        """Check if all tasks have been changed to low priority"""
        for k, v in self.devices.items():
            if v["priority"] > TaskPriority.LOW:
                return False
        return True

    def _reset_all(self):
        """Reset the status of all test devices"""
        self.devices = json.loads(self.json_raw)
        ts = get_timestamp()
        self.start_ts = ts
        self.end_ts = ts
        self.used_sec = 0
        logger.info(f"[TEST] reset all priority ok")

    def _update_scan_devices(self, scanned_devices):
        """Mock scan data based on the test status"""
        no_permit_list = []

        for mac, val in scanned_devices.items():
            mock_device = self.devices.get(mac)
            logger.info(f"[TEST] [{mac}] update device info by mock: {mock_device}")
            if mock_device is not None:
                val["priority"] = mock_device["priority"] or TaskPriority.HIGH
                val["devicetype"] = mock_device["devicetype"] or DeviceType.SENSOR
            else:
                logger.warning(f"[TEST] [{mac}] no mock device")
                no_permit_list.append(mac)

        for mac in no_permit_list:
            scanned_devices.pop(mac, None)
            logger.warning(f"[TEST] [{mac}] no permit device")

    def history_get(self):
        return {
            "worker_num": int(os.getenv("WORKER_NUM") or "2"),
            "test_round": TEST_ROUND,
            "history": self.history,
        }

    def update_by_done_task(self, task):
        mac = task["mac"]
        device = self.devices.get(mac)
        if not device:
            logger.warning(f"[TEST] [{mac}] not device")
            return

        stat_key = f"{device['priority']} -> {device['priority'] - 1}"
        if task["state"] == TaskState.SUCCESS:
            device["priority"] = device["priority"] - 1

        self.devices[mac].setdefault(stat_key, []).append(task)

    async def check_reset_or_mock_scanned_devices(self, scanned_devices):
        logger.info(f"[TEST] all mocked state")
        logger.info(f"{json.dumps(self.devices)}")

        if self._is_all_priority_low():
            self._history_append()
            file_path = await self._history_save()
            self._run_counter += 1

            if TEST_ROUND > 0 and self._run_counter >= TEST_ROUND:
                logger.info(f"[TEST] has all reset, exceed test round, exit")

                try:
                    from render_history_json import render
                    logger.info("=============================================")
                    render(file_path)
                except Exception as ex:
                    logger.warning(f"render history json failed: {ex}")
                os._exit(0)
            else:
                logger.info(
                    f"[TEST] has all reset, sleep await next round...{self._run_counter} {TEST_ROUND}"
                )

            self._reset_all()
            await asyncio.sleep(300)
        else:
            self._update_scan_devices(scanned_devices)
            if self.start_ts == 0:
                self.start_ts = get_timestamp()