import sys
import asyncio
import time
import collections

from cassia_uuid import uuid4
from cassia_log import get_logger
from cassiablue_manager import CassiaBlueManager
from profile_model import DeviceActionResponse
from profile_model import DeviceActionResData
from profile_model import DeviceActionResDataBody
from profile_manager import ProfileManager

from task_entry import Error
from task_entry import State
from task_entry import TaskMeta
from task_entry import TaskResult
from task_entry import TaskResultRecord
from task_entry import DeviceTaskEntry

from mqtt import MqttModule, MqttData

try:
    from typing import Dict, Optional, Any, Deque, List
except ImportError:
    pass


NEED_RETRY_ERRORS = [
    Error.GATEWAY_CHIP_IS_NOT_READY,
    Error.GATEWAY_INCORRECT_MODE,
    Error.GATEWAY_CHIP_IS_BUSY,
    
    Error.GATEWAY_DEVICE_NOT_FOUND,
    Error.GATEWAY_DEVICE_NOT_SCAN,
    Error.GATEWAY_DEVICE_DISCONNECTING,
    Error.GATEWAY_DEVICE_CAN_NOT_SCAN,
    
    # 设备主动断连，不做重试
    # Error.GATEWAY_DEVICE_DISCONNECT,
    
    Error.GATEWAY_HOST_DISCONNECT,
    Error.GATEWAY_CONNECT_FAILED,
    Error.GATEWAY_FAILURE,
    Error.GATEWAY_OPERATION_TIMEOUT,
]


class DeviceTaskQueue:
    def __init__(self, device_mac: str):
        self.device_mac = device_mac
        self.queue: Deque[DeviceTaskEntry] = collections.deque((), 64)
        self.current: Optional[DeviceTaskEntry] = None
        self._lock = asyncio.Lock()


class DeviceTaskQueueManager:
    def __init__(
        self,
        mqtt: MqttModule,
        cassiablue_mgr: CassiaBlueManager,
        profile_mgr: ProfileManager,
    ):
        self.log = get_logger(self.__class__.__name__)

        self.mqtt = mqtt

        self.cassiablue_mgr = cassiablue_mgr
        self.profile_mgr = profile_mgr
        self._devices_tasks_queue: Dict[str, DeviceTaskQueue] = {}
        self._lock = asyncio.Lock()
        self._scheduler_check_interval = 1000

    async def create_task(self, meta: TaskMeta) -> str:
        self.log.info(f"create task start: {meta}")

        task = DeviceTaskEntry(
            cassiablue_mgr=self.cassiablue_mgr,
            meta=meta,
            state=State.CREATED,
            result=TaskResult.EMPTY,
            create_ts=int(time.time() * 1000),
            results=collections.deque((), 4),
            fails={},
        )

        if not task.meta.id:
            task.meta.id = str(uuid4())
            self.log.info(f"use new id: {task.meta.id}")

        self.log.info(f"create task ok: {task}")
        await self._add_task_to_queue(task, False)
        return task.meta.id

    async def _add_task_to_queue(self, task: DeviceTaskEntry, header: bool):
        task_id = task.meta.id
        device_mac = task.meta.device_mac

        self.log.info(f"add task to queue start: {task_id} {device_mac}")

        async with self._lock:
            if device_mac not in self._devices_tasks_queue:
                self._devices_tasks_queue[device_mac] = DeviceTaskQueue(device_mac)

            device_queue = self._devices_tasks_queue[device_mac]
            async with device_queue._lock:
                if header:
                    device_queue.queue.appendleft(task)
                else:
                    device_queue.queue.append(task)

        self.log.info(f"add task to queue ok: {task_id} {device_mac}")

    async def set_task_fail_with_reason(self, task: DeviceTaskEntry, reason: Error):
        self.log.warn(
            f"set task fail start: {task.meta.id} {task.meta.device_mac} {reason}"
        )

        if task.state == State.DONE:
            self.log.info(
                f"set task fail ok, already state done: {task.meta.id} {task.meta.device_mac}"
            )
            return

        task.state = State.DONE
        task.result = TaskResult.FAILED

        if task.results:
            last_result = task.results[-1]
            last_result.end_ts = int(time.time() * 1000)
            last_result.duration = last_result.end_ts - last_result.start_ts

            if reason == Error.TASK_TIMEOUT_BY_SCHEDULER:
                if last_result.reason == Error.EMPTY:
                    last_result.reason = reason
            else:
                last_result.reason = reason

        await self.send_res_fail(task, reason)

        self.log.info(f"set task fail ok: {task}")

    async def send_res_fail(self, task: DeviceTaskEntry, reason: Error):
        body = DeviceActionResDataBody(
            device_mac=task.meta.device_mac,
            data=None,
        )

        res = DeviceActionResponse(
            id=task.meta.id,
            action=f"{task.meta.action}_reply",
            timestamp=int(time.time() * 1000),
            gateway=self.mqtt.meta_mgr.config.gateway_mac,
            data=DeviceActionResData(
                code=500,
                msg=reason,
                body=body,
            ),
        )

        await self.mqtt.pub(self.mqtt.meta_mgr.topics.api_reply, res, qos=1)

    async def send_res_ok(self, task: DeviceTaskEntry, res_body: MqttData):
        body = DeviceActionResDataBody(
            device_mac=task.meta.device_mac,
            data=res_body.to_dict(),
        )

        res = DeviceActionResponse(
            id=task.meta.id,
            action=f"{task.meta.action}_reply",
            timestamp=int(time.time() * 1000),
            gateway=self.mqtt.meta_mgr.config.gateway_mac,
            data=DeviceActionResData(
                code=200,
                msg=Error.OK,
                body=body,
            ),
        )

        await self.mqtt.pub(self.mqtt.meta_mgr.topics.api_reply, res, qos=1)

    async def set_task_success(self, task: DeviceTaskEntry, res_body: MqttData):
        self.log.info(f"set task success start: {task}")
        task.state = State.DONE
        task.result = TaskResult.SUCCESS

        if task.results:
            task.results[-1].end_ts = int(time.time() * 1000)

        self.log.info(f"set task success ok: {task}")
        await self.send_res_ok(task, res_body)

    def _set_task_running(self, task: DeviceTaskEntry):
        task.state = State.RUNNING
        task.results.append(
            TaskResultRecord(
                start_ts=int(time.time() * 1000),
                end_ts=0,
                duration=0,
                reason=Error.EMPTY,
            )
        )
        self.log.info(f"set task running: {task.meta.id} {task.meta.device_mac}")

    def _is_task_timeout(self, task: DeviceTaskEntry) -> bool:
        if task is None or task.meta is None:
            self.log.warn("task or meta is none")
            return

        if task.meta.timeout == 0:
            return False

        is_timeout = task.create_ts != 0 and (
            task.create_ts + task.meta.timeout * 1000
        ) < int(time.time() * 1000)

        if is_timeout:
            self.log.warn(f"task timeout: {task.meta.id} {task.meta.device_mac}")

        return is_timeout

    def _need_retry_error(self, reason: Error) -> bool:
        return reason in NEED_RETRY_ERRORS

    async def _select_task_and_execute(self, device_queue: DeviceTaskQueue):
        async with device_queue._lock:
            if not device_queue.queue:
                self.log.warn(f"select device task, no task: {device_queue.device_mac}")
                return

            task = device_queue.queue.popleft()
            device_mac = device_queue.device_mac

        task_id = task.meta.id
        self.log.info(f"select task one: {task_id} {device_mac}")

        if task.state == State.DONE:
            self.log.info(f"select task fail, task has done: {task.meta.device_mac}")
            return

        self.log.info(f"select task ok: {task_id} {device_mac}")

        self._set_task_running(task)

        async with device_queue._lock:
            device_queue.current = task

        if self._is_task_timeout(task):
            async with device_queue._lock:
                await self.set_task_fail_with_reason(
                    task, Error.TASK_TIMEOUT_BY_SCHEDULER
                )
                device_queue.current = None
            return

        self.log.info(
            f"task do profile execute start: {task.meta.id} {task.meta.device_mac}"
        )

        result: Any = None
        try:
            profile = self.profile_mgr.get_model(task.meta.model)
            self.log.info(
                "get model done:",
                task.meta.model,
                profile,
                self.profile_mgr.models,
            )
            if profile is None:
                raise Exception("model not supported")

            result = await profile.execute(task)

        except Exception as e:
            self.log.warn("!!!sys print exception!!!")
            sys.print_exception(e)
            result = e

        if isinstance(result, Exception):
            reason = str(result) if result.args else str(result)

            if reason in task.fails:
                task.fails[reason] += 1
            else:
                task.fails[reason] = 1

            if self._need_retry_error(reason):
                task.state = State.WAITING
                self.log.info(f"is task need retry error: {task.meta.id} {reason}")
                await self._add_task_to_queue(task, True)
            else:
                await self.set_task_fail_with_reason(task, reason)

            async with device_queue._lock:
                device_queue.current = None
        else:
            await self.set_task_success(task, result)
            async with device_queue._lock:
                device_queue.current = None

    async def _scheduler(self):
        self.log.info("scheduler handler start")

        async with self._lock:
            device_queues = list(self._devices_tasks_queue.values())

        for device_queue in device_queues:
            async with device_queue._lock:
                if device_queue.current is None:
                    asyncio.create_task(self._select_task_and_execute(device_queue))
                else:
                    self.log.info(
                        f"scheduler task is running: {device_queue.device_mac} {device_queue.current.meta.id}"
                    )

        self.log.info("scheduler handler done")

    async def _device_has_task(self, device_mac: str) -> bool:
        async with self._lock:
            if device_mac not in self._devices_tasks_queue:
                return False

            device_queue = self._devices_tasks_queue[device_mac]
            async with device_queue._lock:
                return len(device_queue.queue) > 0 or device_queue.current is not None

    async def get_current_task(self, device_mac: str) -> Optional[DeviceTaskEntry]:
        async with self._lock:
            if device_mac not in self._devices_tasks_queue:
                return None

            device_queue = self._devices_tasks_queue[device_mac]
            async with device_queue._lock:
                return device_queue.current

    async def _create_scheduler_timer(self):
        self.log.info("create scheduler timer start")

        while True:
            await asyncio.sleep(self._scheduler_check_interval / 1000)
            await self._scheduler()

    def co_tasks(self) -> list[asyncio.Task]:
        return [
            asyncio.create_task(self._create_scheduler_timer()),
        ]
