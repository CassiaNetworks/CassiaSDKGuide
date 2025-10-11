import { render, Fragment } from "preact";
import { useEffect, useRef, useState } from "preact/hooks";

import { CassiaNotifyContainer, CassiaNotifyContainerRef } from "./components/CassiaNotifyContainer";
import { CassiaNotifyTypes } from "./components/CassiaNotify";
import { CassiaTooltip } from "./components/CassiaTooltip";
import { SettingIcon } from "./icon";

import logoUrl from "./assets/logo.png";

import "./style.css";

const VITE_API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '';
const META_API = `${VITE_API_BASE_URL}/api/app/config/meta`;

interface Meta {
    ble5_protocol: string;
    conn_chip: string;
    conn_fail_retry_times: string;
    conn_timeout: string;
    forward_protocol: string;
    forward_raw_notify: string;
    forward_raw_scan: string;
    gateway_mac: string;
    http_port: string;
    mqtt_host: string;
    mqtt_password: string;
    mqtt_port: string;
    mqtt_qos: string;
    mqtt_topic_prefix: string;
    mqtt_username: string;
    scan_chip: string;
    scan_filter_duplicates: string;
    scan_filter_mac: string;
    scan_filter_name: string;
    scan_filter_rssi: string;
    scan_mode: string;
    scan_report_interval: string;
}

const FORWORD_PROTOCOL = {
    OFF: "",
    MQTT: "mqtt",
};

const FORWORD_RAW_SCAN = {
    OFF: "",
    ON: "on",
};

const FORWORD_RAW_NOTIFY = {
    OFF: "",
    ON: "on",
};

const MQTT_QOS = {
    QOS0: "0",
    QOS1: "1",
};

const SCAN_MODE = {
    OFF: "",
    ACTIVE: "active",
    PASSIVE: "passive",
};

const SCAN_CHIP = {
    DEFAULT: "",
    CHIP0: "0",
    CHIP1: "1",
    ALL: "all",
};

const CONN_CHIP = {
    DEFAULT: "",
    CHIP0: "0",
    CHIP1: "1",
};

const CONN_FAILS_RETRY = {
    OFF: "",
    TIMES1: "1",
    TIMES2: "2",
    TIMES3: "3",
};

const BLE_PROTOCOL = {
    OFF: "",
    ON: "on",
};


function App() {
    const notifyContainerRef = useRef<CassiaNotifyContainerRef>(null);

    const [meta, setMeta] = useState<Meta>({
        ble5_protocol: BLE_PROTOCOL.OFF,
        conn_chip: CONN_CHIP.DEFAULT,
        conn_fail_retry_times: "3",
        conn_timeout: "15000",
        forward_protocol: FORWORD_PROTOCOL.MQTT,
        forward_raw_notify: FORWORD_RAW_NOTIFY.OFF,
        forward_raw_scan: FORWORD_RAW_SCAN.OFF,
        gateway_mac: "",
        http_port: "60000",
        mqtt_host: "",
        mqtt_password: "",
        mqtt_port: "",
        mqtt_qos: MQTT_QOS.QOS0,
        mqtt_topic_prefix: "",
        mqtt_username: "",
        scan_chip: SCAN_CHIP.DEFAULT,
        scan_filter_duplicates: "",
        scan_filter_mac: "",
        scan_filter_name: "",
        scan_filter_rssi: "",
        scan_mode: SCAN_MODE.ACTIVE,
        scan_report_interval: "",
    });

    const [activeNav, setActiveNav] = useState('#app-data-forward');
    const [saving, setSaving] = useState(false);
    const [savingStatus, setSavingStatus] = useState("");

    const NAV_LIST = [
        ['#app-data-forward', 'APP数据转发'],
        ['#mqtt-broker', 'MQTT中继'],
        ['#gateway-scan-config', '网关扫描配置'],
        ['#gateway-connect-config', '网关连接配置'],
        ['#gateway-more-config', '网关更多配置'],
        ['#more-operations', '更多操作'],
    ];

    useEffect(() => {
        fetch(META_API)
            .then(r => r.json())
            .then(setMeta)
            .catch(e => console.error(e));
    }, []);

    const handleChange = (key: keyof Meta, value: string) => {
        setMeta(prev => ({ ...prev, [key]: value }));
    };

    const saveMetaClickHandle = async () => {
        try {
            setSaving(true);
            setSavingStatus("");

            const body = JSON.stringify(meta);
            console.log('save config start:', body);

            const res = await fetch(META_API, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(meta),
            });

            if (!res.ok) {
                const text = await res.text();
                throw new Error(`HTTP ${res.status}: ${text}`);
            }

            const result = await res.json();
            console.log('save ok:', result);
            setSavingStatus('ok');

            notifyContainerRef.current?.addNotify({
                message: "操作成功！",
                type: CassiaNotifyTypes.SUCCESS,
            });
        } catch (err) {
            console.log('save failed:', err);
            setSavingStatus('fail');

            notifyContainerRef.current?.addNotify({
                title: "操作失败！",
                message: err instanceof Error ? err.message : String(err),
                type: CassiaNotifyTypes.ERROR,
            });
        } finally {
            setSaving(false);
        }
    };

    return (
        <Fragment>
            <div class="cassia-header">
                <img class="cassia-header-logo" src={logoUrl}></img>
                <div class="cassia-header-title">Cassia Device Integration</div>
            </div>

            <div class="cassia-main">
                <div class="cassia-sidebar">
                    <li class="cassia-sidebar-item">
                        <SettingIcon />
                    </li>
                </div>

                <div class="cassia-content">
                    <div class="cassia-nav">
                        {
                            NAV_LIST.map(nav => (
                                <a
                                    key={nav[0]}
                                    href={nav[0]}
                                    onClick={() => setActiveNav(nav[0])}
                                    class={activeNav === nav[0] ? "cassia-nav-active" : ""}
                                >
                                    {nav[1]}
                                </a>
                            ))
                        }
                    </div>

                    <div class="cassia-nav-content">
                        <div id="app-data-forward" class="cassia-nav-block">
                            <div class="cassia-nav-block-title">
                                APP数据转发
                            </div>
                            <div class="cassia-nav-block-content">
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        数据转发协议
                                    </div>
                                    <div class="cassia-form-value">
                                        <select class="cassia-select" value={meta.forward_protocol} onChange={
                                            e => handleChange('forward_protocol', e.currentTarget.value)
                                        }>
                                            <option value={FORWORD_PROTOCOL.OFF}>关闭</option>
                                            <option value={FORWORD_PROTOCOL.MQTT}>MQTT</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        原始广播数据
                                    </div>
                                    <div class="cassia-form-value">
                                        <select disabled class="cassia-select" value={meta.forward_raw_scan} onChange={
                                            e => handleChange('forward_raw_scan', e.currentTarget.value)
                                        }>
                                            <option value={FORWORD_RAW_SCAN.OFF}>关闭</option>
                                            <option value={FORWORD_RAW_SCAN.ON}>开启</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        原始通知数据
                                    </div>
                                    <div class="cassia-form-value">
                                        <select disabled class="cassia-select" value={meta.forward_raw_notify} onChange={
                                            e => handleChange('forward_raw_notify', e.currentTarget.value)
                                        }>
                                            <option value={FORWORD_RAW_NOTIFY.OFF}>关闭</option>
                                            <option value={FORWORD_RAW_NOTIFY.ON}>开启</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="mqtt-broker" class="cassia-nav-block">
                            <div class="cassia-nav-block-title">
                                MQTT中继
                            </div>
                            <div class="cassia-nav-block-content">
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        主机
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.mqtt_host} onInput={
                                            e => handleChange('mqtt_host', e.currentTarget.value)
                                        } />
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        端口
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.mqtt_port} onInput={
                                            e => handleChange('mqtt_port', e.currentTarget.value)
                                        } />
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        用户名
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.mqtt_username} onInput={
                                            e => handleChange('mqtt_username', e.currentTarget.value)
                                        } />
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        密码
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.mqtt_password} onInput={
                                            e => handleChange('mqtt_password', e.currentTarget.value)
                                        } />
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        主题前缀
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.mqtt_topic_prefix} onInput={
                                            e => handleChange('mqtt_topic_prefix', e.currentTarget.value)
                                        } />
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        QoS
                                    </div>
                                    <div class="cassia-form-value">
                                        <select class="cassia-select" value={meta.mqtt_qos} onChange={
                                            e => handleChange('mqtt_qos', e.currentTarget.value)
                                        }>
                                            <option value={MQTT_QOS.QOS0}>0</option>
                                            <option value={MQTT_QOS.QOS1}>1</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="gateway-scan-config" class="cassia-nav-block">
                            <div class="cassia-nav-block-title">
                                网关扫描配置
                                <CassiaTooltip>
                                    <a href="https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#scan-bluetooth-devices" target="_blank">Scan Bluetooth Devices API</a>
                                </CassiaTooltip>
                            </div>
                            <div class="cassia-nav-block-content">
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        扫描模式
                                    </div>
                                    <div class="cassia-form-value">
                                        <select class="cassia-select" value={meta.scan_mode} onChange={
                                            e => handleChange('scan_mode', e.currentTarget.value)
                                        }>
                                            <option value={SCAN_MODE.OFF}>关闭</option>
                                            <option value={SCAN_MODE.PASSIVE}>被动</option>
                                            <option value={SCAN_MODE.ACTIVE}>主动</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        扫描芯片
                                    </div>
                                    <div class="cassia-form-value">
                                        <select class="cassia-select" value={meta.scan_chip} onChange={
                                            e => handleChange('scan_chip', e.currentTarget.value)
                                        }>
                                            <option value={SCAN_CHIP.DEFAULT}>缺省</option>
                                            <option value={SCAN_CHIP.CHIP0}>0</option>
                                            <option value={SCAN_CHIP.CHIP1}>1</option>
                                            <option value={SCAN_CHIP.ALL}>全部</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        MAC过滤
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.scan_filter_mac} onInput={
                                            e => handleChange('scan_filter_mac', e.currentTarget.value)
                                        } />
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        Name过滤
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.scan_filter_name} onInput={
                                            e => handleChange('scan_filter_name', e.currentTarget.value)
                                        } />
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        RSSI过滤
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.scan_filter_rssi} onInput={
                                            e => handleChange('scan_filter_rssi', e.currentTarget.value)
                                        } />
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        重复过滤
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.scan_filter_duplicates} onInput={
                                            e => handleChange('scan_filter_duplicates', e.currentTarget.value)
                                        } /> 毫秒
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        周期过滤
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.scan_report_interval} onInput={
                                            e => handleChange('scan_report_interval', e.currentTarget.value)
                                        } /> 毫秒
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="gateway-connect-config" class="cassia-nav-block">
                            <div class="cassia-nav-block-title">
                                网关连接配置
                                <CassiaTooltip>
                                    <a href="https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#connectdisconnect-to-a-target-device" target="_blank">Connect to a Target Device API</a>
                                </CassiaTooltip>
                            </div>
                            <div class="cassia-nav-block-content">
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        连接芯片
                                    </div>
                                    <div class="cassia-form-value">
                                        <select class="cassia-select" value={meta.conn_chip} onChange={
                                            e => handleChange('conn_chip', e.currentTarget.value)
                                        }>
                                            <option value={CONN_CHIP.DEFAULT}>自动分配</option>
                                            <option value={CONN_CHIP.CHIP0}>0</option>
                                            <option value={CONN_CHIP.CHIP1}>1</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        超时时间
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.conn_timeout} onInput={
                                            e => handleChange('conn_timeout', e.currentTarget.value)
                                        } /> 毫秒
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        失败重试
                                    </div>
                                    <div class="cassia-form-value">
                                        <select class="cassia-select" value={meta.conn_fail_retry_times} onChange={
                                            e => handleChange('conn_fail_retry_times', e.currentTarget.value)
                                        }>
                                            <option value={CONN_FAILS_RETRY.OFF}>不重试</option>
                                            <option value={CONN_FAILS_RETRY.TIMES1}>1次</option>
                                            <option value={CONN_FAILS_RETRY.TIMES2}>2次</option>
                                            <option value={CONN_FAILS_RETRY.TIMES3}>3次</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="gateway-more-config" class="cassia-nav-block">
                            <div class="cassia-nav-block-title">
                                网关BLE5配置
                                <CassiaTooltip>
                                    <a href="https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/BLE-5-Interface-Specification-For-X2000" target="_blank">BLE 5 Interface Specification For X2000</a>
                                </CassiaTooltip>
                            </div>
                            <div class="cassia-nav-block-content">
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        BLE5协议
                                    </div>
                                    <div class="cassia-form-value">
                                        <select disabled class="cassia-select" value={meta.ble5_protocol} onChange={
                                            e => handleChange('ble5_protocol', e.currentTarget.value)
                                        }>
                                            <option value={BLE_PROTOCOL.OFF}>关闭</option>
                                            <option value={BLE_PROTOCOL.ON}>开启</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="more-operations" class="cassia-nav-block">
                            <div class="cassia-nav-block-title">
                                更多操作
                            </div>
                            <div class="cassia-nav-block-content">
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">

                                    </div>
                                    <div class="cassia-form-value">
                                        <button disabled={saving} class={`cassia-button ${saving ? "cassia-button-loading" : ""}`} onClick={saveMetaClickHandle}>
                                            保存配置
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            <CassiaNotifyContainer ref={notifyContainerRef} />
        </Fragment>
    );
}

render(<App />, document.getElementById("app"));