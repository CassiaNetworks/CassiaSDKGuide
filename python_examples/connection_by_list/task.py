import json
import asyncio

from logger import logger
from const import DeviceType, ChipId, TaskPriority, TaskState
from util import get_timestamp
from gateway import CassiaGatewayAsync
from device_profile import DeviceProfile
from test_devices import TestDevices


class TaskScheduler:
    def __init__(
        self,
        gateway: CassiaGatewayAsync,
        device_profile: DeviceProfile,
        worker_cnt,
        test_file,
    ):
        self._gateway = gateway
        self._device_profile = device_profile

        self._worker_cnt = worker_cnt
        self._worker_queue = asyncio.Queue(maxsize=worker_cnt)

        self._tasks_lock = asyncio.Lock()
        self.devices_task = {}

        # [TEST] Test Devices
        self.test_devices: TestDevices = None

        if test_file:
            self.test_devices = TestDevices(test_file)

    def _tasks_add(self, mac, priority):
        self.devices_task[mac] = {
            "mac": mac,
            "priority": priority,
            "chip": ChipId.NOP,
            "state": TaskState.INIT,
            "type": "get_logs",
            "scan_ts": get_timestamp(),
            "create_ts": get_timestamp(),
            "exec_start_ts": 0,
            "exec_connect_start_ts": 0,
            "exec_connect_end_ts": 0,
            "exec_data_start_ts": 0,
            "exec_data_end_ts": 0,
            "exec_done_ts": 0,
        }
        logger.debug(f"[{mac}] task add: {priority}")

    def _tasks_get(self, mac):
        return self.devices_task.get(mac)

    def _tasks_has(self, mac):
        return mac in self.devices_task

    def _tasks_update(
        self,
        mac,
        state=None,
        chip=None,
    ):
        logger.info(f"[{mac}] task update: state={state}, chip={chip}")

        if state is not None:
            pre_state = self.devices_task[mac]["state"]

            if pre_state > state and state > TaskState.CONNECT_START:
                logger.warning(
                    f"[{mac}] task state update ignore: {pre_state} -> {state}?"
                )
                return

            self.devices_task[mac]["state"] = state
            logger.info(f"[{mac}] task state update ok: {pre_state} -> {state}")

            ts = get_timestamp()
            if state == TaskState.CONNECT_START:
                self.devices_task[mac]["exec_start_ts"] = ts
                self.devices_task[mac]["exec_connect_start_ts"] = ts
            elif state == TaskState.CONNECTED:
                self.devices_task[mac]["exec_connect_end_ts"] = ts
            elif state == TaskState.EXECUTING:
                self.devices_task[mac]["exec_data_start_ts"] = ts
            elif state == TaskState.SUCCESS:
                self.devices_task[mac]["exec_data_end_ts"] = ts
                self.devices_task[mac]["exec_done_ts"] = ts
            elif state == TaskState.FAILED:
                self.devices_task[mac]["exec_data_end_ts"] = ts
                self.devices_task[mac]["exec_done_ts"] = ts
                pass

        if chip is not None:
            self.devices_task[mac]["chip"] = chip

    async def _tasks_update_with_lock(self, mac, state=None, chip=None):
        async with self._tasks_lock:
            return self._tasks_update(mac, state=state, chip=chip)

    def _tasks_remove(self, mac):
        self.devices_task.pop(mac, None)
        logger.debug(f"[{mac}] task remove")

    async def _tasks_remove_with_lock(self, mac):
        async with self._tasks_lock:
            logger.info(f"[{mac}] task remove with lock")
            return self.devices_task.pop(mac, None)

    async def _tasks_stat_with_lock(self):
        tasks_stat = {
            ChipId.H0: {
                TaskPriority.HIGH: 0,
                TaskPriority.MEDIUM: 0,
                TaskPriority.LOW: 0,
                "total": 0,
            },
            ChipId.H1: {
                TaskPriority.HIGH: 0,
                TaskPriority.MEDIUM: 0,
                TaskPriority.LOW: 0,
                "total": 0,
            },
        }
        async with self._tasks_lock:
            json_str = json.dumps(self.devices_task)
            logger.info(f"devices task: {len(self.devices_task)} {json_str}")

            for _, task in self.devices_task.items():
                if task["state"] >= TaskState.CONNECTED:
                    chip = ChipId(task["chip"])
                    priority = TaskPriority(task["priority"])
                    tasks_stat[chip][priority] += 1
                    tasks_stat[chip]["total"] += 1

        return tasks_stat

    async def _worker(self):
        """Worker coroutine
        - Actively fetch tasks -> Check status -> Execute pipeline
        - The execution process does not support being forcefully terminated
        """
        while True:
            mac = await self._worker_queue.get()

            logger.info(f"[{mac}] do device task start")
            await self._tasks_update_with_lock(mac=mac, state=TaskState.EXECUTING)

            # Execute the work task. Regardless of success or failure, immediately release the task and wait for the broadcast trigger
            try:
                await self._device_profile.task_get_logs(mac)
                await self._tasks_update_with_lock(mac=mac, state=TaskState.SUCCESS)
            except Exception as ex:
                logger.info(f"task failed: {mac} {ex}")
                await self._tasks_update_with_lock(mac=mac, state=TaskState.FAILED)
            finally:
                await self._gateway.disconnect_ignore_ex(mac)
                task = await self._tasks_remove_with_lock(mac)
                if self.test_devices is not None:
                    self.test_devices.update_by_done_task(task)

    def _sort_devices(self, scanned_devices):
        """Devices scanned in this cycle, prioritize sorting"""
        sorted_devices = sorted(
            scanned_devices.values(),
            key=lambda x: (
                x["priority"] != TaskPriority.HIGH,
                x["devicetype"] != DeviceType.SENSOR,
                x["priority"] != TaskPriority.MEDIUM,
                (-x["rssi"] if x["devicetype"] == DeviceType.SENSOR else 0),
            ),
        )
        return sorted_devices

    async def _select_connect_chip_and_devices(self, scanned_devices):
        """Select devices and allocate chip for connection.

        This implementation targets dual-chip gateways (e.g. E1000) with priority-based scheduling.
        For single-chip gateways, you can simplify this to always return (ChipId.H0, sorted_devices).
        """
        tasks_stat = await self._tasks_stat_with_lock()

        json_str = json.dumps(tasks_stat)
        logger.info(f"task stat: {json_str}")

        sorted_devices = self._sort_devices(scanned_devices)
        json_str = json.dumps(sorted_devices)
        logger.info(f"scanned devices sorted: {json_str}")

        # The number of work tasks exceeds the number of workers
        total = tasks_stat[ChipId.H0]["total"] + tasks_stat[ChipId.H1]["total"]
        if total >= self._worker_cnt:
            logger.warning(f"exceed max worker, wait...: {total} {self._worker_cnt}")
            return (ChipId.NOP, [])

        # Both chips are busy with high-priority tasks, no allocation processing will be done
        if (
            tasks_stat[ChipId.H1][TaskPriority.HIGH] > 0
            and tasks_stat[ChipId.H0][TaskPriority.HIGH] > 0
        ):
            logger.warning(f"exceed high priority max count, wait...")
            return (ChipId.NOP, [])

        # If there are high-priority tasks, process the high-priority tasks first
        highs = []
        mediums = []
        for device_info in sorted_devices:
            if device_info["priority"] == TaskPriority.HIGH:
                highs.append(device_info)
            elif device_info["priority"] == TaskPriority.MEDIUM:
                mediums.append(device_info)

        alloc_chip = ChipId.NOP
        devices = []

        if len(highs) > 0:
            # High-priority chip allocation: each chip can handle a maximum of 1 task, with chip1 having a higher priority than chip0
            devices = highs
            if tasks_stat[ChipId.H1][TaskPriority.HIGH] <= 0:
                alloc_chip = ChipId.H1
            elif tasks_stat[ChipId.H0][TaskPriority.HIGH] <= 0:
                alloc_chip = ChipId.H0
            else:
                logger.warning(f"all chip has high task")
        elif len(mediums) > 0:
            devices = mediums

            if (
                tasks_stat[ChipId.H0][TaskPriority.HIGH] > 0
                and tasks_stat[ChipId.H1][TaskPriority.HIGH] <= 0
            ):
                # Chip0 is busy with high-priority tasks, so temporarily choose chip1 to process low-priority tasks
                alloc_chip = ChipId.H1
            elif (
                tasks_stat[ChipId.H1][TaskPriority.HIGH] > 0
                and tasks_stat[ChipId.H0][TaskPriority.HIGH] <= 0
            ):
                # Chip1 is busy with high-priority tasks, so temporarily choose chip0 to process low-priority tasks
                alloc_chip = ChipId.H0
            else:
                # There are no high-priority tasks being processed currently. Choose the chip with fewer connections, prioritizing chip1
                if tasks_stat[ChipId.H0]["total"] >= tasks_stat[ChipId.H1]["total"]:
                    alloc_chip = ChipId.H1
                else:
                    alloc_chip = ChipId.H0
        else:
            logger.warning(f"no devices task")

        return (alloc_chip, devices[:8])

    async def _connect_by_list(self, chip, devices):
        """Connect using the batch list API (gateway.connect_by_list).

        If your gateway does not support connect_by_list, replace
        gateway.connect_by_list() with gateway.connect(mac) to connect
        devices one at a time.
        """
        connect_list = []

        async with self._tasks_lock:
            for device_info in devices:
                mac = device_info["mac"]
                task = self._tasks_get(mac)
                if task is None:
                    self._tasks_add(mac, device_info["priority"])
                    self._tasks_update(mac, state=TaskState.CONNECT_START, chip=chip)
                    connect_list.append(mac)
                elif task["state"] < TaskState.CONNECTED:
                    self._tasks_update(mac, state=TaskState.CONNECT_START, chip=chip)
                    connect_list.append(mac)
                else:
                    # Already busy with tasks, temporarily ignore it and wait for it to finish on its own
                    continue

        if not connect_list:
            logger.info(f"connect list empty")
            return None

        """Connect by List(Sync)"""
        connected_mac = ""
        try:
            ret = await self._gateway.connect_by_list(connect_list, int(chip))
            connected_mac = ret["addr"]
        except Exception as ex:
            logger.info(f"connect by list failed: {ex}")

        await self._tasks_lock.acquire()
        for mac in connect_list:
            if mac == connected_mac:
                self._tasks_update(mac=mac, state=TaskState.CONNECTED, chip=chip)
            else:
                self._tasks_update(mac, state=TaskState.INIT)
        self._tasks_lock.release()

        return connected_mac

    async def _scheduler(self):
        """Connection scheduling"""
        while True:
            try:
                logger.info("=============================================")

                scanned_devices = self._device_profile.get_scanned_devices()

                if self.test_devices is not None:
                    await self.test_devices.check_reset_or_mock_scanned_devices(
                        scanned_devices
                    )

                json_str = json.dumps(scanned_devices)
                logger.info(f"scanned devices: {len(scanned_devices)} {json_str}")

                if not scanned_devices:
                    await asyncio.sleep(0.5)
                    continue

                (chip, devices) = await self._select_connect_chip_and_devices(
                    scanned_devices
                )
                json_str = json.dumps(devices)
                logger.info(f"scanned devices selected: {chip} {json_str}")

                if not devices or chip == ChipId.NOP:
                    await asyncio.sleep(0.5)
                    continue

                connected_mac = await self._connect_by_list(chip, devices)
                if connected_mac is None:
                    await asyncio.sleep(1)
                elif connected_mac:
                    self._device_profile.remove_scanned_device(connected_mac)
                    await self._worker_queue.put(connected_mac)
                    await asyncio.sleep(1)
            except Exception as ex:
                logger.error(f"schedule task failed:", ex)
                self._device_profile.clear_scanned_devices()

    async def stater(self, event):
        logger.info(f"state sse event: {event.data}")

    def run_tasks(self):
        task_list = [
            asyncio.create_task(self._worker_queue.join(), name=f"queue"),
            asyncio.create_task(self._scheduler(), name=f"scheduler"),
        ]

        for i in range(self._worker_cnt):
            task_list.append(asyncio.create_task(self._worker(), name=f"worker{i}"))

        return task_list
