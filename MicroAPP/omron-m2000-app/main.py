import asyncio
import json
import math
import time

import cassiablue
import cassiasys

try:
    from cassiacommon import DataCache
except ImportError:
    class DataCache:
        def __init__(self):
            self._items = {}

        async def put(self, key, value):
            self._items[key] = value

        async def get_next(self, flag=True):
            values = list(self._items.values())
            self._items = {}
            return values

try:
    from cassiamqtt import CassiaMQTTClient
except ImportError:
    CassiaMQTTClient = None


# Runtime configuration.
BP_SERVICE_AD_DATA = "1018"
BP_MEASUREMENT_HANDLE = 2065
CCCD_HANDLE = 2066
CCCD_VALUE = "0200"
CURRENT_TIME_HANDLE = 1297
CURRENT_TIME_DAY_OF_WEEK = 0x00
CURRENT_TIME_ADJUST_REASON = 0x01
CURRENT_TIME_MIN_YEAR = 2020
CURRENT_TIME_MAX_YEAR = 2035
CURRENT_TIME_TIMEZONE_OFFSET_MIN = None
SERVER_HOST = "http://127.0.0.1:8000"
UPLOAD_CHANNEL = "http"  # http, mqtt, both, none

CONNECT_TIMEOUT_MS = 5000
OP_TIMEOUT = 10
DATA_IDLE_TIMEOUT_SEC = 3
CONNECT_RETRY_COUNT = 3
CONNECT_RETRY_DELAY_SEC = 2
DEVICE_COOLDOWN_SEC = 15
SCAN_FILTER = '&active=1&filter_duplicates=1000&filter_value=[{"offset":"1","data":"020106020A0003021018"}]'

MQTT_URL = None
MQTT_CA = None
MQTT_CERT = None
MQTT_KEY = None
MQTT_KEY_PASS = None
MQTT_TOPIC = "omron/blood_pressure"
MQTT_QOS = 1
MQTT_PUBLISH_RETRY_COUNT = 3
MQTT_PUBLISH_RETRY_DELAY_SEC = 5


# Runtime state.
processed_cache = {}
device_events = {}
ble_session_lock = asyncio.Lock()
mqtt_connected = False
mqtt_client = None
mqtt_cache = DataCache()
mqtt_publish_count = 0
mqtt_retry_counts = {}


def get_str(conf, key, default=None):
    value = conf.get(key, default)
    if value is None:
        return default
    return str(value).strip()


def get_int(conf, key, default):
    try:
        value = conf.get(key, default)
        if value is None or value == "":
            return default
        return int(value)
    except Exception:
        print("Invalid integer config {}, using {}".format(key, default))
        return default


def get_float(conf, key, default):
    try:
        value = conf.get(key, default)
        if value is None or value == "":
            return default
        return float(value)
    except Exception:
        print("Invalid numeric config {}, using {}".format(key, default))
        return default


def get_optional_int(conf, key, default=None):
    value = get_str(conf, key, None)
    if value is None or value == "":
        return default

    try:
        return int(value)
    except Exception:
        print("Invalid integer config {}, using {}".format(key, default))
        return default


def should_upload_http():
    channel = (UPLOAD_CHANNEL or "none").lower()
    return channel == "http" or channel == "both"


def should_upload_mqtt():
    channel = (UPLOAD_CHANNEL or "none").lower()
    return channel == "mqtt" or channel == "both"


def normalize_upload_channel(channel):
    channel = (channel or "http").strip().lower()
    aliases = {
        "http(s)": "http",
        "http(s) and mqtt(s)": "both",
        "mqtt(s)": "mqtt",
    }
    return aliases.get(channel, channel)


def load_config():
    global SERVER_HOST, UPLOAD_CHANNEL, CURRENT_TIME_TIMEZONE_OFFSET_MIN
    global CONNECT_TIMEOUT_MS, OP_TIMEOUT, DATA_IDLE_TIMEOUT_SEC, CONNECT_RETRY_COUNT
    global CONNECT_RETRY_DELAY_SEC, DEVICE_COOLDOWN_SEC
    global MQTT_URL, MQTT_CA, MQTT_CERT, MQTT_KEY, MQTT_KEY_PASS, MQTT_TOPIC, MQTT_QOS
    global MQTT_PUBLISH_RETRY_COUNT, MQTT_PUBLISH_RETRY_DELAY_SEC

    ret = cassiasys.read_user_config()
    print("read user conf {}".format(ret))
    conf = json.loads(ret) if ret else {}

    SERVER_HOST = get_str(conf, "server_host", SERVER_HOST)
    UPLOAD_CHANNEL = normalize_upload_channel(get_str(conf, "upload_channel", UPLOAD_CHANNEL))
    CONNECT_TIMEOUT_MS = get_int(conf, "connect_timeout_ms", CONNECT_TIMEOUT_MS)
    OP_TIMEOUT = get_int(conf, "op_timeout_sec", OP_TIMEOUT)
    DATA_IDLE_TIMEOUT_SEC = get_float(conf, "data_idle_timeout_sec", DATA_IDLE_TIMEOUT_SEC)
    CONNECT_RETRY_COUNT = get_int(conf, "connect_retry_count", CONNECT_RETRY_COUNT)
    if CONNECT_RETRY_COUNT < 1:
        CONNECT_RETRY_COUNT = 1
    CONNECT_RETRY_DELAY_SEC = get_float(conf, "connect_retry_delay_sec", CONNECT_RETRY_DELAY_SEC)
    DEVICE_COOLDOWN_SEC = get_float(conf, "device_cooldown_sec", DEVICE_COOLDOWN_SEC)

    MQTT_URL = get_str(conf, "mqtt_url", None)
    MQTT_CA = get_str(conf, "mqtt_ca", None)
    MQTT_CERT = get_str(conf, "mqtt_cert", None)
    MQTT_KEY = get_str(conf, "mqtt_key", None)
    MQTT_KEY_PASS = get_str(conf, "mqtt_key_pass", None)
    MQTT_TOPIC = get_str(conf, "mqtt_topic", MQTT_TOPIC)
    MQTT_QOS = get_int(conf, "mqtt_qos", MQTT_QOS)
    MQTT_PUBLISH_RETRY_COUNT = get_int(
        conf,
        "mqtt_publish_retry_count",
        MQTT_PUBLISH_RETRY_COUNT,
    )
    if MQTT_PUBLISH_RETRY_COUNT < 1:
        MQTT_PUBLISH_RETRY_COUNT = 1
    MQTT_PUBLISH_RETRY_DELAY_SEC = get_float(
        conf,
        "mqtt_publish_retry_delay_sec",
        MQTT_PUBLISH_RETRY_DELAY_SEC,
    )

    if UPLOAD_CHANNEL not in ("http", "mqtt", "both", "none"):
        print("Invalid upload_channel {}, using http".format(UPLOAD_CHANNEL))
        UPLOAD_CHANNEL = "http"

    CURRENT_TIME_TIMEZONE_OFFSET_MIN = get_optional_int(
        conf,
        "current_time_timezone_offset_min",
        CURRENT_TIME_TIMEZONE_OFFSET_MIN,
    )


def sfloat_to_float(byte1, byte2):
    raw = (byte2 << 8) | byte1
    if raw == 0x07FF:
        return float("nan")
    if raw == 0x07FE:
        return float("inf")
    if raw == 0x0802:
        return float("-inf")
    mantissa = raw & 0x0FFF
    if mantissa >= 0x0800:
        mantissa = -((0x1000) - mantissa)
    exponent = raw >> 12
    if exponent >= 0x0008:
        exponent = -((0x0010) - exponent)
    return mantissa * (10 ** exponent)


def safe_int(value):
    try:
        return 0 if math.isnan(value) or math.isinf(value) else int(value)
    except Exception:
        return 0


def read_u16_le(data, offset):
    return data[offset] | (data[offset + 1] << 8)


def normalize_handle(handle):
    if handle is None:
        return None

    if isinstance(handle, int):
        return handle

    text = str(handle).strip().lower()
    if not text:
        return None

    try:
        if text.startswith("0x"):
            return int(text, 16)
        return int(text)
    except Exception:
        try:
            return int(text, 16)
        except Exception:
            return None


def get_event_handle(evt):
    for key in ("handle", "att_handle", "valueHandle", "value_handle", "hnd", "hdl"):
        handle = normalize_handle(evt.get(key))
        if handle is not None:
            return handle
    return None


def normalize_current_time_year(year):
    if CURRENT_TIME_MIN_YEAR <= year <= CURRENT_TIME_MAX_YEAR:
        return year

    if 0 <= year < 100:
        return 2000 + year

    if 100 <= year < 200:
        return 1900 + year

    shifted_year = year - 30
    if CURRENT_TIME_MIN_YEAR <= shifted_year <= CURRENT_TIME_MAX_YEAR:
        print("Current time year {} adjusted to {}".format(year, shifted_year))
        return shifted_year

    print("Current time year {} is outside expected range".format(year))
    return year


def current_time_tuple():
    if CURRENT_TIME_TIMEZONE_OFFSET_MIN is None:
        return time.localtime()

    adjusted_epoch = int(time.time() + CURRENT_TIME_TIMEZONE_OFFSET_MIN * 60)
    try:
        return time.localtime(adjusted_epoch)
    except TypeError:
        return time.gmtime(adjusted_epoch)


def build_current_time_value(now=None):
    now = now or current_time_tuple()
    raw_year = now.tm_year if hasattr(now, "tm_year") else now[0]
    year = normalize_current_time_year(raw_year)
    month = now.tm_mon if hasattr(now, "tm_mon") else now[1]
    day = now.tm_mday if hasattr(now, "tm_mday") else now[2]
    hour = now.tm_hour if hasattr(now, "tm_hour") else now[3]
    minute = now.tm_min if hasattr(now, "tm_min") else now[4]
    second = now.tm_sec if hasattr(now, "tm_sec") else now[5]
    payload = [
        year & 0xFF,
        (year >> 8) & 0xFF,
        month,
        day,
        hour,
        minute,
        second,
        CURRENT_TIME_DAY_OF_WEEK,
        0x00,
        CURRENT_TIME_ADJUST_REASON,
    ]
    value = "".join("{:02X}".format(byte) for byte in payload)
    print(
        "Current time payload {} from {:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            value, year, month, day, hour, minute, second
        )
    )
    return value


def parse_gateway_now(now_text):
    date_text, time_text = str(now_text).strip().split(" ")
    year, month, day = [int(part) for part in date_text.split("-")]
    hour, minute, second = [int(part) for part in time_text.split(":")]
    return (year, month, day, hour, minute, second, 0, 0)


async def build_current_time_value_from_gateway():
    ok, ret = await cassiablue.send_cmd("/cassia/info")
    if not ok:
        raise ValueError("cassia info request failed: {}".format(ret))

    info = json.loads(ret) if isinstance(ret, str) else ret
    timeconf = info.get("timeconf", {}) if isinstance(info, dict) else {}
    now_text = timeconf.get("now")
    if not now_text:
        raise ValueError("cassia info timeconf.now is empty")

    timezone = info.get("timezone", "") if isinstance(info, dict) else ""
    print("Gateway time {} timezone {}".format(now_text, timezone))
    return build_current_time_value(parse_gateway_now(now_text))


def parse_current_time_value(hex_str):
    data = bytes.fromhex(hex_str)
    if len(data) < 10:
        raise ValueError("current time payload is too short")

    year = read_u16_le(data, 0)
    return {
        "year": year,
        "month": data[2],
        "day": data[3],
        "hour": data[4],
        "minute": data[5],
        "second": data[6],
        "day_of_week": data[7],
        "fractions256": data[8],
        "adjust_reason": data[9],
    }


def parse_bp_data(mac, hex_str):
    try:
        data = bytes.fromhex(hex_str)
        if len(data) < 7:
            raise ValueError("blood pressure payload is too short")

        flags = data[0]
        sys_val = sfloat_to_float(data[1], data[2])
        dia_val = sfloat_to_float(data[3], data[4])
        map_val = sfloat_to_float(data[5], data[6])

        unit = "mmHg"
        if flags & 0x01:
            sys_val *= 7.50062
            dia_val *= 7.50062
            map_val *= 7.50062
            unit = "mmHg (Converted)"

        pulse = 0.0
        user_id = None
        measurement_status = None
        timestamp = int(time.time())
        current_offset = 7

        if flags & 0x02:
            if len(data) < current_offset + 7:
                raise ValueError("timestamp flag is set but payload is too short")

            year = read_u16_le(data, current_offset)
            month = data[current_offset + 2]
            day = data[current_offset + 3]
            hour = data[current_offset + 4]
            minute = data[current_offset + 5]
            second = data[current_offset + 6]
            if year or month or day or hour or minute or second:
                print(
                    "Device time: {}-{}-{} {}:{}:{} ignored, using system timestamp {}".format(
                        year, month, day, hour, minute, second, timestamp
                    )
                )
            else:
                print("Device time is empty, using system timestamp {}".format(timestamp))
            current_offset += 7

        if flags & 0x04:
            if len(data) < current_offset + 2:
                raise ValueError("pulse flag is set but payload is too short")

            pulse = sfloat_to_float(data[current_offset], data[current_offset + 1])
            current_offset += 2

        if flags & 0x08:
            if len(data) < current_offset + 1:
                raise ValueError("user id flag is set but payload is too short")

            user_id = data[current_offset]
            current_offset += 1

        if flags & 0x10:
            if len(data) < current_offset + 2:
                raise ValueError("measurement status flag is set but payload is too short")

            measurement_status = read_u16_le(data, current_offset)
            current_offset += 2

        print(
            "[RESULT] Device {}: Sys {:.0f}, Dia {:.0f}, MAP {:.0f}, Pulse {:.0f}, User {}, Status {}".format(
                mac, sys_val, dia_val, map_val, pulse, user_id, measurement_status
            )
        )

        return {
            "mac": mac,
            "flags": flags,
            "systolic": safe_int(sys_val),
            "diastolic": safe_int(dia_val),
            "map": safe_int(map_val),
            "pulse": safe_int(pulse),
            "unit": unit,
            "ts": timestamp,
            "user_id": user_id,
            "measurement_status": measurement_status,
        }
    except Exception as error:
        print("Parse error for {}: {}".format(mac, error))
        return None


async def push_http(data):
    try:
        import aiohttp

        async with aiohttp.ClientSession() as session:
            async with session.post(SERVER_HOST, json=data) as resp:
                print("HTTP push status: {}".format(resp.status))
    except ImportError:
        print("aiohttp not found, skipping HTTP push")
    except Exception as error:
        print("HTTP push failed: {}".format(error))


def mqtt_cache_key(data):
    return "{}-{}".format(data.get("mac"), data.get("ts"))


async def push_mqtt(data):
    await mqtt_cache.put(mqtt_cache_key(data), data)


async def push_data(data):
    if should_upload_http():
        asyncio.create_task(push_http(data))
    if should_upload_mqtt():
        await push_mqtt(data)


def is_mqtt_publish_ok(ret):
    if ret is True:
        return True

    if ret is False or ret is None:
        return False

    if isinstance(ret, int):
        return ret == 0

    text = str(ret).strip().lower()
    return text in ("0", "ok", "success", "true")


def mask_secret_text(value):
    if not value:
        return value

    text = str(value)
    if "://" in text and "@" in text:
        prefix, rest = text.split("://", 1)
        _, host = rest.rsplit("@", 1)
        return "{}://***@{}".format(prefix, host)

    return text


async def handle_mqtt_publish_failure(payload_items, reason):
    retry_items = []
    dropped_count = 0

    for item in payload_items:
        cache_key = mqtt_cache_key(item)
        retry_count = mqtt_retry_counts.get(cache_key, 0) + 1
        mqtt_retry_counts[cache_key] = retry_count

        if retry_count >= MQTT_PUBLISH_RETRY_COUNT:
            dropped_count += 1
            del mqtt_retry_counts[cache_key]
            print(
                "Dropping MQTT payload {} after {} failed publish attempt(s): {}".format(
                    cache_key, retry_count, reason
                )
            )
        else:
            retry_items.append(item)
            await mqtt_cache.put(cache_key, item)

    if retry_items:
        print(
            "MQTT publish failed, retrying {} payload(s) after {} seconds".format(
                len(retry_items), MQTT_PUBLISH_RETRY_DELAY_SEC
            )
        )
        await asyncio.sleep(MQTT_PUBLISH_RETRY_DELAY_SEC)

    if dropped_count:
        print("Dropped {} MQTT payload(s) after publish retry limit".format(dropped_count))


async def mqtt_publish_loop():
    global mqtt_publish_count

    while mqtt_client:
        payload_items = await mqtt_cache.get_next(flag=True)
        if not payload_items or payload_items == []:
            await asyncio.sleep(1)
            continue

        try:
            payload = json.dumps(payload_items)
            print(
                "MQTT publishing topic {} qos {} bytes {}".format(
                    MQTT_TOPIC, MQTT_QOS, len(payload)
                )
            )
            ret, info = await mqtt_client.publish(MQTT_TOPIC, payload, MQTT_QOS)
            print("MQTT publish result: {} {}".format(ret, info))
            if is_mqtt_publish_ok(ret):
                mqtt_publish_count += len(payload_items)
                for item in payload_items:
                    mqtt_retry_counts.pop(mqtt_cache_key(item), None)
                print("MQTT publish successful {}".format(mqtt_publish_count))
            else:
                await handle_mqtt_publish_failure(
                    payload_items,
                    "{} {}".format(ret, info),
                )
        except Exception as error:
            print("Error occurred while publishing MQTT data: {}".format(error))
            await handle_mqtt_publish_failure(payload_items, error)


async def mqtt_main():
    global mqtt_connected, mqtt_client

    if not MQTT_URL:
        print("MQTT URL is not configured, MQTT upload disabled")
        return
    if CassiaMQTTClient is None:
        print("cassiamqtt is not available, MQTT upload disabled")
        return

    while True:
        try:
            async with CassiaMQTTClient(
                uri=MQTT_URL,
                ca=MQTT_CA,
                cert=MQTT_CERT,
                key=MQTT_KEY,
                key_pass=MQTT_KEY_PASS,
            ) as client:
                mqtt_connected = True
                mqtt_client = client
                print(
                    "MQTT connected uri {} topic {} qos {}".format(
                        mask_secret_text(MQTT_URL), MQTT_TOPIC, MQTT_QOS
                    )
                )
                await mqtt_publish_loop()
        except Exception as error:
            print("Failed to connect to MQTT broker: {}".format(error))
        finally:
            mqtt_connected = False
            mqtt_client = None
            await asyncio.sleep(2)


def is_busy_response(ret):
    text = str(ret).lower()
    return "busy" in text or "in progress" in text or "already" in text


async def connect_with_retry(mac):
    params = json.dumps({"type": "public", "timeout": CONNECT_TIMEOUT_MS})

    for attempt in range(1, CONNECT_RETRY_COUNT + 1):
        print("Connecting {} attempt {}/{}...".format(mac, attempt, CONNECT_RETRY_COUNT))
        ok, ret = await cassiablue.connect(mac, params)
        print("connect done: {} {}, {} {}".format(type(ok), ok, type(ret), ret))

        if ok:
            return True, ret

        if is_busy_response(ret) and attempt < CONNECT_RETRY_COUNT:
            print("Connect busy for {}, retrying in {} seconds".format(mac, CONNECT_RETRY_DELAY_SEC))
            await asyncio.sleep(CONNECT_RETRY_DELAY_SEC)
            continue

        return False, ret

    return False, "connect retry exhausted"


def is_handle_type_error(ret):
    text = str(ret).lower()
    return "handle" in text and ("type" in text or "str" in text or "string" in text)


async def write_gatt_hex(mac, handle, value, label):
    print("Writing {} to {} handle {} value {}...".format(label, mac, handle, value))
    handle_type_error = False
    try:
        ok, ret = await cassiablue.gatt_write(mac, handle, value)
    except TypeError as error:
        ok = False
        ret = error
        handle_type_error = True
    print("gatt write done: {} {}, {} {}".format(type(ok), ok, type(ret), ret))

    if ok:
        return True, ret

    if handle_type_error or is_handle_type_error(ret):
        print("Retrying gatt_write with string handle for SDK compatibility")
        try:
            ok, ret = await cassiablue.gatt_write(mac, str(handle), value)
            print("gatt write retry done: {} {}, {} {}".format(type(ok), ok, type(ret), ret))
        except Exception as error:
            ok = False
            ret = error

    return ok, ret


async def write_indication_cccd(mac):
    return await write_gatt_hex(mac, CCCD_HANDLE, CCCD_VALUE, "Indicate")


async def write_current_time(mac, value=None):
    if value is None:
        try:
            value = await build_current_time_value_from_gateway()
        except Exception as error:
            print("Gateway time unavailable, using local current time: {}".format(error))
            value = build_current_time_value()

    ok, ret = await write_gatt_hex(
        mac,
        CURRENT_TIME_HANDLE,
        value,
        "Current Time",
    )
    return ok, ret, value


async def notification_loop():
    print("Starting notification loop...")
    ok, err = await cassiablue.start_recv_notify()
    if not ok:
        print("Failed to start recv notify: {}".format(err))
        return

    async for evt in cassiablue.notify_result():
        print("Raw event: {}".format(evt))
        mac = evt.get("id")
        value = evt.get("value")
        handle = get_event_handle(evt)

        if mac and value:
            state = device_events.get(mac)
            value = value.upper()
            if handle == CURRENT_TIME_HANDLE:
                try:
                    current_time = parse_current_time_value(value)
                    print("Current time event from {}: {}".format(mac, current_time))
                except Exception as error:
                    print("Ignoring current time event from {}: {}".format(mac, error))
                continue

            if handle is not None and handle != BP_MEASUREMENT_HANDLE:
                print("Ignoring event from {} handle {} value {}".format(mac, handle, value))
                continue

            if handle is None and state and value == state.get("current_time_value"):
                print("Ignoring echoed current time write from {}".format(mac))
                continue

            if state and not state.get("current_time_written"):
                state["current_time_written"] = True
                ok, ret, current_time_value = await write_current_time(mac)
                state["current_time_value"] = current_time_value
                if not ok:
                    print("Write current time failed for {}: {}".format(mac, ret))

            data = parse_bp_data(mac, value)
            if data:
                print("parsed data: {}".format(data))
                if state:
                    state["records"].append(data)
                    state["event"].set()
                asyncio.create_task(push_data(data))


async def process_device_task(mac):
    print("Start processing {}...".format(mac))

    async with ble_session_lock:
        try:
            ok, ret = await connect_with_retry(mac)
            if not ok:
                print("Connect failed for {}: {}".format(mac, ret))
                return

            state = {
                "event": asyncio.Event(),
                "records": [],
                "current_time_written": False,
                "current_time_value": None,
            }
            device_events[mac] = state

            ok, ret = await write_indication_cccd(mac)
            if not ok:
                print("Write failed for {}: {}".format(mac, ret))

            print("Waiting for data from {}...".format(mac))
            try:
                await asyncio.wait_for(state["event"].wait(), timeout=OP_TIMEOUT)
                print("First data received for {}".format(mac))
                while True:
                    state["event"].clear()
                    try:
                        await asyncio.wait_for(state["event"].wait(), timeout=DATA_IDLE_TIMEOUT_SEC)
                    except asyncio.TimeoutError:
                        break

                print(
                    "Data idle for {} seconds, received {} record(s) from {}".format(
                        DATA_IDLE_TIMEOUT_SEC, len(state["records"]), mac
                    )
                )
                if state["records"]:
                    print("Last record for {}: {}".format(mac, state["records"][-1]))
            except asyncio.TimeoutError:
                print("Timeout waiting for data from {}".format(mac))

        except Exception as error:
            print("Error processing {}: {}".format(mac, error))

        finally:
            print("Disconnecting {}...".format(mac))
            try:
                await cassiablue.disconnect(mac)
            except Exception:
                pass

            if mac in device_events:
                del device_events[mac]

            print("--- Finished {} ---\n".format(mac))


async def main():
    print("Scanner started")
    load_config()
    print(
        "Upload channel {}, connect timeout {} ms, operation timeout {} sec".format(
            UPLOAD_CHANNEL, CONNECT_TIMEOUT_MS, OP_TIMEOUT
        )
    )

    if should_upload_mqtt():
        asyncio.create_task(mqtt_main())

    ok, err = await cassiablue.start_scan(SCAN_FILTER)
    print("Scan start status: {}, {}".format(ok, err))
    if not ok:
        return

    asyncio.create_task(notification_loop())

    async for dev in cassiablue.scan_result():
        mac = dev.get("bdaddr")
        ad_data = dev.get("adData", "")
        print("Found device: {}, {}".format(mac, ad_data))

        if mac and BP_SERVICE_AD_DATA in ad_data:
            last_time = processed_cache.get(mac, 0)
            if time.time() - last_time > DEVICE_COOLDOWN_SEC:
                print("Found target BP monitor: {}".format(mac))
                processed_cache[mac] = time.time()
                asyncio.create_task(process_device_task(mac))

        try:
            await asyncio.sleep(0.01)
        except AttributeError:
            await asyncio.sleep_ms(10)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Stopped by user")
