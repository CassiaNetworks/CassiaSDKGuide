import os
import asyncio
import json

import aiofiles

from logger import logger
from gateway import CassiaGatewayAsync

BASE_URL = os.getenv("BASE_URL") or "http://10.10.10.254"
PRIORITY = int(os.getenv("PRIORITY") or 3)
DEV_TYPE = int(os.getenv("DEV_TYPE") or 50)
TEST_FILE = os.getenv("TEST_FILE") or "./test_devices.json"

devices = {}


def scanner(event):
    logger.info(f"scan sse event: {event}")
    scan_data = json.loads(event.data)
    mac = scan_data["bdaddrs"][0]["bdaddr"]

    if mac not in devices:
        devices[mac] = {
            "priority": PRIORITY,
            "devicetype": DEV_TYPE,
        }


async def scan_test_devices():
    scan_filter = {
        "filter_name": "BLE_Sample_Dev",
        "filter_rssi": -90,
    }

    async with CassiaGatewayAsync(BASE_URL, scan_filter) as gateway:
        gateway.reg_scan_handler(scanner)
        asyncio.create_task(gateway.open_scan())
        await asyncio.sleep(5)

    async with aiofiles.open(TEST_FILE, "w") as f:
        json_str = json.dumps(devices, indent=4)
        await f.write(json_str)
        logger.info(f"save test json file ok: {len(devices)} {TEST_FILE}")

    exit()


if __name__ == "__main__":
    """Scan BLE_Sample_Dev test devices

    TEST_FILE=test_devices.json BASE_URL=http://GatewayIp python3 scan_test_devices.py
    """
    asyncio.run(scan_test_devices())
