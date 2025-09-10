import sys
import json
import asyncio

from cassia_log import get_logger
from cassia_device import CassiaDevice
from waiter_manager import WaiterManager
from profile_manager import ProfileManager
from meta import MetaConfigManager
from cassiablue_manager import CassiaBlueManager
from task_manager import DeviceTaskQueueManager
from bypass import MessageDispatcher
from mqtt import MqttModule
from http_server import HttpServer


async def main():
    log = get_logger("App")
    log.info("==========================")
    log.info("        App start         ")
    log.info("==========================")

    co_tasks = []

    """
    本地运行时，使用本地网关RESTful API Mock
    """
    if sys.platform != "esp32":
        from cassiablue import set_gateway

        set_gateway("172.16.66.107")
        log.info("set mock gateway ok")

    meta_mgr = MetaConfigManager()
    meta_json = json.dumps(meta_mgr.config.to_dict())
    log.info(f"meta:", meta_json)

    waiter_mgr = WaiterManager()
    cassia_device = CassiaDevice(waiter_mgr)

    profile_mgr = ProfileManager()
    profile_mgr.add_model(cassia_device)

    mqtt = MqttModule(meta_mgr=meta_mgr)
    await mqtt.start()

    cassiablue_mgr = CassiaBlueManager(
        meta_mgr=meta_mgr,
    )

    task_mgr = DeviceTaskQueueManager(
        mqtt=mqtt,
        cassiablue_mgr=cassiablue_mgr,
        profile_mgr=profile_mgr,
    )

    msg_dsp = MessageDispatcher(
        meta_mgr=meta_mgr,
        mqtt=mqtt,
        waiter_mgr=waiter_mgr,
        profile_mgr=profile_mgr,
        task_mgr=task_mgr,
    )

    cassiablue_mgr.set_handler(
        scanner=msg_dsp.scan_data_handler,
        notifier=msg_dsp.notify_data_handler,
        stater=msg_dsp.connection_state_data_handler,
    )

    mqtt.set_dispatcher(msg_dsp.dispatcher)

    http_srv = HttpServer(
        meta_mgr=meta_mgr,
    )

    co_tasks.extend(cassiablue_mgr.co_tasks())
    co_tasks.extend(task_mgr.co_tasks())
    co_tasks.extend(mqtt.co_tasks())

    """
    Linux/MacOS不支持，否则发送HTTP请求时会导致segment fault
    目前已知的情况是asyncio.start_server和asyncio.open_connection冲突
    """
    if sys.platform == "esp32":
        co_tasks.extend(http_srv.co_tasks())

    await asyncio.gather(*co_tasks)


if __name__ == "__main__":
    asyncio.run(main())
