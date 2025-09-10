from cassiablue_manager import CassiaBlueManager
from waiter_manager import WaiterManager
from error import Error

try:
    from typing import Dict, Deque, Any
except ImportError:
    pass


class TaskMeta:
    def __init__(
        self,
        id: str,
        device_mac: str,
        model: str,
        action: str,
        timeout: int,
        payload: Any = None,
    ):
        self.id = id
        self.device_mac = device_mac
        self.model = model
        self.action = action
        self.timeout = timeout
        self.payload = payload


class State:
    CREATED = "Created"
    WAITING = "Waiting"
    RUNNING = "Running"
    KILLED = "Killed"
    DONE = "Done"


class TaskResult:
    SUCCESS = "Success"
    FAILED = "Failed"
    EMPTY = "Empty"


class TaskResultRecord:
    def __init__(
        self,
        start_ts: int,
        end_ts: int,
        duration: int,
        reason: Error,
    ):
        self.start_ts = start_ts
        self.end_ts = end_ts
        self.duration = duration
        self.reason = reason


class DeviceTaskEntry:
    def __init__(
        self,
        cassiablue_mgr: CassiaBlueManager,
        meta: TaskMeta,
        state: State,
        result: TaskResult,
        create_ts: int,
        results: Deque[TaskResultRecord],
        fails: Dict[Error, int],
    ):
        self.cassiablue_mgr = cassiablue_mgr
        self.meta = meta
        self.state = state
        self.result = result
        self.create_ts = create_ts
        self.results = results
        self.fails = fails
