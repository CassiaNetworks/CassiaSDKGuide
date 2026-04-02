import asyncio

from aiohttp import web

from logger import logger
from task import TaskScheduler

HTTP_HOST = "0.0.0.0"
HTTP_PORT = 3000


class HttpServer:
    def __init__(self, task_scheduler: TaskScheduler):
        self._task_scheduler = task_scheduler

    async def _health_check(self, _req):
        text = "OK"
        return web.Response(text=text)

    async def _get_tasks_state(self, _req):
        return web.json_response(self._task_scheduler.devices_task)

    async def _get_tests_devices_state(self, _req):
        return web.json_response(self._task_scheduler.test_devices.devices)

    async def _get_tests_devices_raw(self, _req):
        text = self._task_scheduler.test_devices.json_raw
        return web.Response(text=text, content_type="application/json")

    async def _get_tests_history(self, _req):
        return web.json_response(self._task_scheduler.test_devices.history)

    async def _server(self):
        app = web.Application()

        app.router.add_get("/api/health", self._health_check)
        app.router.add_get("/api/tasks/state", self._get_tasks_state)
        app.router.add_get("/api/tests/devices/state", self._get_tests_devices_state)
        app.router.add_get("/api/tests/devices/raw", self._get_tests_devices_raw)
        app.router.add_get("/api/tests/history", self._get_tests_history)

        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, HTTP_HOST, HTTP_PORT)

        logger.info(f"web server start ok: {HTTP_HOST} {HTTP_PORT}")
        await site.start()

        try:
            while True:
                await asyncio.sleep(3600)
        except asyncio.CancelledError:
            logger.warning("web server shutdown...")
        finally:
            await runner.cleanup()
            logger.info("web server stopped")

    def run_tasks(self):
        return [
            asyncio.create_task(self._server(), name="server"),
        ]
