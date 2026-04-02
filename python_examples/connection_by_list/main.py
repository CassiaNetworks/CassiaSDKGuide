"""Use BLE_Sample_Dev to simulate dongle, test log retrieval. The specific BLE_Sample_Dev device protocol can be found in the relevant documentation."""

import os
import asyncio

from logger import logger
from gateway import CassiaGatewayAsync
from device_profile import DeviceProfile
from task import TaskScheduler
from http_server import HttpServer

WORKER_NUM = int(os.getenv("WORKER_NUM") or "2")
BASE_URL = os.getenv("BASE_URL") or "http://10.10.10.254"
TEST_FILE = os.getenv("TEST_FILE")


async def main():
    logger.info("app start")

    scan_filter = {"filter_name": "BLE_Sample_Dev"}
    async with CassiaGatewayAsync(BASE_URL, scan_filter) as gateway:
        # await gateway.init()

        device_profile = DeviceProfile(gateway)
        gateway.reg_notification_handler(device_profile.notifier)
        gateway.reg_scan_handler(device_profile.scanner)

        task_scheduler = TaskScheduler(gateway, device_profile, WORKER_NUM, TEST_FILE)
        gateway.reg_state_handler(task_scheduler.stater)

        gateway_tasks = gateway.run_tasks()
        scheduler_tasks = task_scheduler.run_tasks()

        http_server = HttpServer(task_scheduler)
        http_tasks = http_server.run_tasks()

        task_list = gateway_tasks + scheduler_tasks + http_tasks

        try:
            await asyncio.gather(*task_list)
        except asyncio.CancelledError:
            logger.warning("task list was cancelled.")
        finally:
            for task in task_list:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    logger.warning("app exit")


if __name__ == "__main__":
    asyncio.run(main())
