import { render, Fragment } from "preact";
import { useEffect, useRef, useState } from "preact/hooks";

import { CassiaNotifyContainer, CassiaNotifyContainerRef } from "./components/CassiaNotifyContainer";
import { CassiaNotifyTypes } from "./components/CassiaNotify";
import { CassiaTooltip } from "./components/CassiaTooltip";
import { T, t, LANG } from "./i18n";
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
    const [lang, setLang] = useState(navigator.language.startsWith('zh-') ? "cn" : "en");

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
        ['#app-data-forward', t(lang, T.APP_DATA_FORWARD)],
        ['#mqtt-broker', t(lang, T.MQTT_BROKER)],
        ['#gateway-scan-config', t(lang, T.GATEWAY_SCAN_CONFIG)],
        ['#gateway-connect-config', t(lang, T.GATEWAY_CONN_CONFIG)],
        ['#gateway-more-config', t(lang, T.GATEWAY_MORE_CONFIG)],
        ['#more-operations', t(lang, T.MORE_OPERATIONS)],
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

            const text = await res.text();
            if (!res.ok) {
                throw new Error(`HTTP ${res.status}: ${text}`);
            }

            console.log('save done:', text);
            setSavingStatus('ok');

            notifyContainerRef.current?.addNotify({
                title: t(lang, T.OPERATION_OK),
                message: t(lang, T.SAVE_OK_NOTIFY),
                type: CassiaNotifyTypes.SUCCESS,
            });
        } catch (err) {
            console.log('save failed:', err);
            setSavingStatus('fail');

            notifyContainerRef.current?.addNotify({
                title: t(lang, T.OPERATION_FAIL),
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
                <div class="cassia-header-left">
                    <img class="cassia-header-logo" src={logoUrl}></img>
                    <div class="cassia-header-title">Cassia Device Integration</div>
                </div>

                <div class="cassia-header-right">
                    <select class="cassia-select cassia-select-mini" value={lang} onChange={
                        e => setLang(e.currentTarget.value)
                    }>
                        <option value={LANG.CN}>中文</option>
                        <option value={LANG.EN}>English</option>
                    </select>
                </div>
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
                                {t(lang, T.APP_DATA_FORWARD)}
                            </div>
                            <div class="cassia-nav-block-content">
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        {t(lang, T.DATA_FORWARD_PROTOCOL)}
                                    </div>
                                    <div class="cassia-form-value">
                                        <select class="cassia-select" value={meta.forward_protocol} onChange={
                                            e => handleChange('forward_protocol', e.currentTarget.value)
                                        }>
                                            <option value={FORWORD_PROTOCOL.OFF}>{t(lang, T.OFF)}</option>
                                            <option value={FORWORD_PROTOCOL.MQTT}>MQTT</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        {t(lang, T.RAW_SCAN_DATA)}
                                    </div>
                                    <div class="cassia-form-value">
                                        <select disabled class="cassia-select" value={meta.forward_raw_scan} onChange={
                                            e => handleChange('forward_raw_scan', e.currentTarget.value)
                                        }>
                                            <option value={FORWORD_RAW_SCAN.OFF}>{t(lang, T.OFF)}</option>
                                            <option value={FORWORD_RAW_SCAN.ON}>{t(lang, T.ON)}</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        {t(lang, T.RAW_NOTIFY_DATA)}
                                    </div>
                                    <div class="cassia-form-value">
                                        <select disabled class="cassia-select" value={meta.forward_raw_notify} onChange={
                                            e => handleChange('forward_raw_notify', e.currentTarget.value)
                                        }>
                                            <option value={FORWORD_RAW_NOTIFY.OFF}>{t(lang, T.OFF)}</option>
                                            <option value={FORWORD_RAW_NOTIFY.ON}>{t(lang, T.ON)}</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="mqtt-broker" class="cassia-nav-block">
                            <div class="cassia-nav-block-title">
                                {t(lang, T.APP_DATA_FORWARD)}
                            </div>
                            <div class="cassia-nav-block-content">
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        {t(lang, T.HOST)}
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.mqtt_host} onInput={
                                            e => handleChange('mqtt_host', e.currentTarget.value)
                                        } />
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        {t(lang, T.PORT)}
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.mqtt_port} onInput={
                                            e => handleChange('mqtt_port', e.currentTarget.value)
                                        } />
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        {t(lang, T.USERNAME)}
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.mqtt_username} onInput={
                                            e => handleChange('mqtt_username', e.currentTarget.value)
                                        } />
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        {t(lang, T.PASSWORD)}
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.mqtt_password} onInput={
                                            e => handleChange('mqtt_password', e.currentTarget.value)
                                        } />
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        {t(lang, T.TOPIC_PREFIX)}
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
                                {t(lang, T.GATEWAY_SCAN_CONFIG)}
                                <CassiaTooltip>
                                    <a href="https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#scan-bluetooth-devices" target="_blank">Scan Bluetooth Devices API</a>
                                </CassiaTooltip>
                            </div>
                            <div class="cassia-nav-block-content">
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        {t(lang, T.SCAN_MODE)}
                                    </div>
                                    <div class="cassia-form-value">
                                        <select class="cassia-select" value={meta.scan_mode} onChange={
                                            e => handleChange('scan_mode', e.currentTarget.value)
                                        }>
                                            <option value={SCAN_MODE.OFF}>{t(lang, T.OFF)}</option>
                                            <option value={SCAN_MODE.PASSIVE}>{t(lang, T.SCAN_MODE_PASSIVE)}</option>
                                            <option value={SCAN_MODE.ACTIVE}>{t(lang, T.SCAN_MODE_ACTIVE)}</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        {t(lang, T.SCAN_CHIP)}
                                    </div>
                                    <div class="cassia-form-value">
                                        <select class="cassia-select" value={meta.scan_chip} onChange={
                                            e => handleChange('scan_chip', e.currentTarget.value)
                                        }>
                                            <option value={SCAN_CHIP.DEFAULT}>{t(lang, T.DEFAULT)}</option>
                                            <option value={SCAN_CHIP.CHIP0}>0</option>
                                            <option value={SCAN_CHIP.CHIP1}>1</option>
                                            <option value={SCAN_CHIP.ALL}>{t(lang, T.ALL)}</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        {t(lang, T.FILTER_MAC)}
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.scan_filter_mac} onInput={
                                            e => handleChange('scan_filter_mac', e.currentTarget.value)
                                        } />
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        {t(lang, T.FILTER_NAME)}
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.scan_filter_name} onInput={
                                            e => handleChange('scan_filter_name', e.currentTarget.value)
                                        } />
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        {t(lang, T.FILTER_RSSI)}
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.scan_filter_rssi} onInput={
                                            e => handleChange('scan_filter_rssi', e.currentTarget.value)
                                        } />
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        {t(lang, T.FILTER_DUP)}
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.scan_filter_duplicates} onInput={
                                            e => handleChange('scan_filter_duplicates', e.currentTarget.value)
                                        } /> {t(lang, T.MILLISECOND)}
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        {t(lang, T.REPORT_INTERVAL)}
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.scan_report_interval} onInput={
                                            e => handleChange('scan_report_interval', e.currentTarget.value)
                                        } /> {t(lang, T.MILLISECOND)}
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="gateway-connect-config" class="cassia-nav-block">
                            <div class="cassia-nav-block-title">
                                {t(lang, T.GATEWAY_CONN_CONFIG)}
                                <CassiaTooltip>
                                    <a href="https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#connectdisconnect-to-a-target-device" target="_blank">Connect to a Target Device API</a>
                                </CassiaTooltip>
                            </div>
                            <div class="cassia-nav-block-content">
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        {t(lang, T.CONN_CHIP)}
                                    </div>
                                    <div class="cassia-form-value">
                                        <select class="cassia-select" value={meta.conn_chip} onChange={
                                            e => handleChange('conn_chip', e.currentTarget.value)
                                        }>
                                            <option value={CONN_CHIP.DEFAULT}>{t(lang, T.AUTO)}</option>
                                            <option value={CONN_CHIP.CHIP0}>0</option>
                                            <option value={CONN_CHIP.CHIP1}>1</option>
                                        </select>
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        {t(lang, T.TIMEOUT)}
                                    </div>
                                    <div class="cassia-form-value">
                                        <input class="cassia-input" value={meta.conn_timeout} onInput={
                                            e => handleChange('conn_timeout', e.currentTarget.value)
                                        } /> {t(lang, T.MILLISECOND)}
                                    </div>
                                </div>
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        {t(lang, T.FAIL_RETRY)}
                                    </div>
                                    <div class="cassia-form-value">
                                        <select class="cassia-select" value={meta.conn_fail_retry_times} onChange={
                                            e => handleChange('conn_fail_retry_times', e.currentTarget.value)
                                        }>
                                            <option value={CONN_FAILS_RETRY.OFF}>{t(lang, T.NO_RETRY)}</option>
                                            <option value={CONN_FAILS_RETRY.TIMES1}>1</option>
                                            <option value={CONN_FAILS_RETRY.TIMES2}>2</option>
                                            <option value={CONN_FAILS_RETRY.TIMES3}>3</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="gateway-more-config" class="cassia-nav-block">
                            <div class="cassia-nav-block-title">
                                {t(lang, T.GATEWAY_MORE_CONFIG)}
                                <CassiaTooltip>
                                    <a href="https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/BLE-5-Interface-Specification-For-X2000" target="_blank">BLE 5 Interface Specification For X2000</a>
                                </CassiaTooltip>
                            </div>
                            <div class="cassia-nav-block-content">
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">
                                        {t(lang, T.BLE5_PROTOCOL)}
                                    </div>
                                    <div class="cassia-form-value">
                                        <select disabled class="cassia-select" value={meta.ble5_protocol} onChange={
                                            e => handleChange('ble5_protocol', e.currentTarget.value)
                                        }>
                                            <option value={BLE_PROTOCOL.OFF}>{t(lang, T.OFF)}</option>
                                            <option value={BLE_PROTOCOL.ON}>{t(lang, T.ON)}</option>
                                        </select>
                                    </div>
                                </div>
                            </div>
                        </div>
                        <div id="more-operations" class="cassia-nav-block">
                            <div class="cassia-nav-block-title">
                                {t(lang, T.MORE_OPERATIONS)}
                            </div>
                            <div class="cassia-nav-block-content">
                                <div class="cassia-form-row">
                                    <div class="cassia-form-label">

                                    </div>
                                    <div class="cassia-form-value">
                                        <button disabled={saving} class={`cassia-button ${saving ? "cassia-button-loading" : ""}`} onClick={saveMetaClickHandle}>
                                            {t(lang, T.SAVE)}
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