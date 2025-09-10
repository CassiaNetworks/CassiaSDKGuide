import cassiablue

from cassia_log import get_logger

"""数据透传通道"""
FORWORD_PROTOCOL_OFF = ""
FORWORD_PROTOCOL_MQTT = "mqtt"

"""原始广播数据"""
FORWORD_RAW_SCAN_OFF = ""
FORWORD_RAW_SCAN_ON = "on"

"""原始通知数据"""
FORWORD_RAW_NOTIFY_OFF = ""
FORWORD_RAW_NOTIFY_ON = "on"

"""MQTT QOS"""
MQTT_QOS_0 = "0"
MQTT_QOS_1 = "1"

"""扫描模式"""
SCAN_MODE_OFF = ""
SCAN_MODE_ACTIVE = "active"
SCAN_MODE_PASSIVE = "passive"

"""扫描芯片"""
SCAN_CHIP_DEFAULT = ""
SCAN_CHIP_0 = "0"
SCAN_CHIP_1 = "1"
SCAN_CHIP_ALL = "all"

"""连接芯片"""
CONN_CHIP_DEFAULT = ""
CONN_CHIP_0 = "0"
CONN_CHIP_1 = "1"

"""BLE5开关"""
BLE5_PROTOCOL_OFF = ""
BLE5_PROTOCOL_ON = "on"


class Config:
    def __init__(
        self,
        http_port: str = "60000",
        gateway_mac: str = cassiablue._gateway_mac,
        mqtt_topic_prefix: str = "/dev",
        scan_filter_name: str = "cassia-device*",
        scan_filter_mac: str = "",
        scan_filter_duplicates: str = "1000",
        forward_protocol: str = FORWORD_PROTOCOL_MQTT,
        forward_raw_scan: str = FORWORD_RAW_SCAN_OFF,
        forward_raw_notify: str = FORWORD_RAW_NOTIFY_OFF,
        mqtt_host: str = "115.190.27.121",
        mqtt_port: str = "61883",
        mqtt_username: str = "",
        mqtt_password: str = "",
        mqtt_qos: str = MQTT_QOS_1,
        ble5_protocol: str = BLE5_PROTOCOL_OFF,
        scan_mode: str = SCAN_MODE_ACTIVE,
        scan_chip: str = SCAN_CHIP_DEFAULT,
        scan_filter_rssi: str = "",
        scan_report_interval: str = "",
        conn_chip: str = CONN_CHIP_DEFAULT,
        conn_timeout: str = "15000",
        conn_fail_retry_times: str = "3",
    ):
        self.log = get_logger(self.__class__.__name__)

        self.http_port = http_port
        self.gateway_mac = gateway_mac

        self.forward_protocol = forward_protocol
        self.forward_raw_scan = forward_raw_scan
        self.forward_raw_notify = forward_raw_notify

        self.mqtt_host = mqtt_host
        self.mqtt_port = mqtt_port
        self.mqtt_username = mqtt_username
        self.mqtt_password = mqtt_password
        self.mqtt_topic_prefix = mqtt_topic_prefix
        self.mqtt_qos = mqtt_qos

        self.ble5_protocol = ble5_protocol
        self.scan_mode = scan_mode
        self.scan_chip = scan_chip
        self.scan_filter_name = scan_filter_name
        self.scan_filter_mac = scan_filter_mac
        self.scan_filter_rssi = scan_filter_rssi
        self.scan_filter_duplicates = scan_filter_duplicates
        self.scan_report_interval = scan_report_interval

        self.conn_chip = conn_chip
        self.conn_timeout = conn_timeout
        self.conn_fail_retry_times = conn_fail_retry_times

    def to_dict(self):
        return {k: v for k, v in self.__dict__.items() if k != "log"}


class MqttTopics:
    def __init__(
        self,
        scan: str,
        notify: str,
        state: str,
        api: str,
        api_reply: str,
        unicast: str,
        broadcast: str,
    ):
        self.scan = scan
        self.notify = notify
        self.state = state
        self.api = api
        self.api_reply = api_reply
        self.unicast = unicast
        self.broadcast = broadcast


class MetaConfigManager:

    def __init__(self):
        self.log = get_logger(self.__class__.__name__)
        self.config = Config()

        prefix = self.config.mqtt_topic_prefix
        gateway = self.config.gateway_mac

        self.topics = MqttTopics(
            scan=f"{prefix}/up/{gateway}/scan",
            notify=f"{prefix}/up/{gateway}/notification",
            state=f"{prefix}/up/{gateway}/connection_state",
            api=f"{prefix}/down/{gateway}/api",
            api_reply=f"{prefix}/up/{gateway}/api_reply",
            unicast=f"{prefix}/down/{gateway}/#",
            broadcast=f"{prefix}/down/FF:FF:FF:FF:FF:FF/#",
        )

    def get(self) -> Config:
        return self.config

    def get_scan_filter(self) -> str:
        parts = []

        if self.config.scan_mode == SCAN_MODE_ACTIVE:
            parts.append("active=1")

        parts.extend(
            (
                f"chip={self.config.scan_chip}",
                f"filter_name={self.config.scan_filter_name}",
                f"filter_mac={self.config.scan_filter_mac}",
                f"filter_rssi={self.config.scan_filter_rssi}",
                f"filter_duplicates={self.config.scan_filter_duplicates}",
                f"report_interval={self.config.scan_report_interval}",
            )
        )

        if self.config.ble5_protocol == BLE5_PROTOCOL_ON:
            parts.append("phy=1M,2M,CODED")

        filter = "&".join(parts) + "&"
        self.log.info(f"get scan filter ok: {filter}")

        return filter
