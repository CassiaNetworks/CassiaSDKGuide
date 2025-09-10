import asyncio
import time

from cassia_log import get_logger
from error import Error


class Future:
    def __init__(self, id: str = ""):
        self.log = get_logger(self.__class__.__name__)
        self._id = id
        self._flag: asyncio.Event = asyncio.Event()
        self._done: bool = False
        self._result: any = None
        self._exception: Exception = None

    def set_result(self, result):
        self.log.info(f"[{self._id}] set result")

        if self._done:
            raise RuntimeError("Future already done")

        self._result = result
        self._flag.set()
        self._done = True

    def set_exception(self, exc):
        self.log.info(f"[{self._id}] set exception")

        if self._done:
            raise RuntimeError("Future already done")

        self._exception = exc
        self._flag.set()
        self._done = True

    def done(self):
        return self._done

    async def wait(self):
        await self._flag.wait()
        if self._exception is not None:
            raise self._exception
        return self._result


class LastActive:
    def __init__(
        self,
        last_time: any,
        timeout: int,
    ):
        self.last_time = last_time
        self.timeout = timeout


class Waiter:
    def __init__(
        self,
        id: str,
        timeout: int,
        future: Future,
        args: dict[str, any],
    ):
        self.id = id
        self.timeout = timeout
        self.future = future
        self.args = args


# TODO: lock
class WaiterManager:
    CHECK_INTERVAL = 1

    @staticmethod
    def gen_task_id(prefix: str, device_mac: str, action: str):
        return f"{prefix}_{device_mac}_{action}"

    def __init__(self):
        self.log = get_logger(self.__class__.__name__)
        self.waits: dict[str, Waiter] = {}
        self.last_active: dict[str, LastActive] = {}
        self.loop = asyncio.get_event_loop()
        self._timer = self.loop.create_task(self._timer_checker())

    async def _timer_checker(self):
        while True:
            now = time.ticks_ms()
            expired_ids = []

            for id, (last_time, timeout) in self.last_active.items():
                if time.ticks_diff(now, last_time) >= timeout * 1000:
                    expired_ids.append(id)

            for id in expired_ids:
                self._handle_timeout(id)

            self.log.info(f"wait timer checker")
            await asyncio.sleep(self.CHECK_INTERVAL)

    def _handle_timeout(self, id):
        self.log.info(f"[{id}] wait handle timeout")

        wait = self.waits.pop(id, None)
        if wait and not wait.future.done():
            wait.future.set_exception(asyncio.TimeoutError("wait timeout"))

        if id in self.last_active:
            del self.last_active[id]

    def add(self, id, args=None, timeout=5) -> Future:
        self.log.info(f"[{id}] wait add {args} {timeout}")

        future = Future(id)
        self.last_active[id] = (time.ticks_ms(), timeout)

        self.waits[id] = Waiter(
            id=id,
            timeout=timeout,
            future=future,
            args=args,
        )

        return future

    def get(self, id, refresh=True) -> Waiter:
        self.log.info(f"[{id}] wait get")
        if refresh:
            self.refresh(id)
        return self.waits.get(id)

    def refresh(self, id):
        if id not in self.waits:
            self.log.warn(f"[{id}] refresh no id")
            return

        timeout = self.waits[id].timeout
        self.last_active[id] = (time.ticks_ms(), timeout)
        self.log.info(f"[{id}] refresh timeouter ok")

    def end(self, id, data=None, error=None):
        if isinstance(data, bytearray) or isinstance(data, str):
            self.log.info(f"[{id}] wait end {id} {error} {len(data)} {data[:8]}...")
        else:
            self.log.info(f"[{id}] wait end {id} {error} {data}")

        if id in self.last_active:
            del self.last_active[id]

        wait = self.waits.pop(id, None)
        if wait and not wait.future.done():
            if error is not None:
                if isinstance(error, Exception):
                    wait.future.set_exception(error)
                else:
                    wait.future.set_exception(Exception(error))
            else:
                wait.future.set_result(data)
        else:
            self.log.warn(f"[{id}] wait end no id or done")

    def end_by_id_prefix(self, prefix, error: Error):
        self.log.info("end by id prefix start:", prefix, error)

        matched_ids = [id for id in self.waits.keys() if id.startswith(prefix)]

        for id in matched_ids:
            self.end(id=id, error=error)
            self.log.info("end by id prefix one ok:", id)
