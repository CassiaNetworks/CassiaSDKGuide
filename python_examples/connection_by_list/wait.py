import asyncio
import time

from logger import logger


class WaitFuture:
    def __init__(self):
        self.CHECK_INTERVAL = 1

        self.waits = {}
        self.last_active = {}  # {id: (last_time, timeout)}
        self.loop = asyncio.get_event_loop()
        self._timer = self.loop.create_task(self._timer_checker())

    async def _timer_checker(self):
        """Check the cycle and adjust based on the actual situation"""
        while True:
            now = time.monotonic()
            expired_ids = []

            for id, (last_time, timeout) in self.last_active.items():
                if now - last_time >= timeout:
                    expired_ids.append(id)

            for id in expired_ids:
                self._handle_timeout(id)

            logger.info("wait timer checker")
            await asyncio.sleep(self.CHECK_INTERVAL)

    def _handle_timeout(self, id):
        logger.warning(f"[{id}] wait handle timeout")

        wait = self.waits.pop(id, None)
        if wait and not wait["future"].done():
            wait["future"].set_exception(asyncio.TimeoutError("wait timeout"))

        if id in self.last_active:
            del self.last_active[id]

    def add(self, id, args=None, timeout=5):
        logger.info(f"[{id}] wait add {args} {timeout}")

        future = asyncio.Future()
        self.last_active[id] = (time.monotonic(), timeout)

        self.waits[id] = {
            "id": id,
            "timeout": timeout,
            "future": future,
            "args": args,
        }

        return future

    def get(self, id, refresh=True):
        logger.debug(f"[{id}] wait get")
        if refresh:
            self.refresh(id)
        return self.waits.get(id)

    def refresh(self, id):
        """Reset the timer for the specified ID"""
        if id not in self.waits:
            logger.debug(f"[{id}] refresh failed, no id")
            return

        timeout = self.waits[id]["timeout"]
        self.last_active[id] = (time.monotonic(), timeout)
        logger.debug(f"[{id}] refresh timeouter ok")

    def end(self, id, data=None, error=None):
        if isinstance(data, bytearray) or isinstance(data, str):
            logger.info(f"[{id}] wait end {id} {error} {len(data)} {data[:32]}...")
        else:
            logger.info(f"[{id}] wait end {id} {error} data)")

        if id in self.last_active:
            del self.last_active[id]

        wait = self.waits.pop(id, None)
        if wait and not wait["future"].done():
            if error is not None:
                if isinstance(error, Exception):
                    wait["future"].set_exception(error)
                else:
                    wait["future"].set_exception(Exception(error))
            else:
                wait["future"].set_result(data)
