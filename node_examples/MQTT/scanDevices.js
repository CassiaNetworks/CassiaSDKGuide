/**
 * Handling gateway BLE scan data via MQTT
 * - Requires an MQTT Broker
 * - Requires logging into the gateway Web configuration Service
 *  - Configure MQTT Broker
 *  - Configure scan to be enabled
 */

/**
 * The mqtt library being used, can be installed via npm/yarn
 */
const mqtt = require("mqtt");

/**
 * MQTT Broker's address
 */
const MQTT_BROKER = "mqtt://192.168.3.112:9883";

const client = mqtt.connect(MQTT_BROKER);

client.on("connect", () => {
    /**
     * Subscribe to all gateway uplink data using a wildcard
     */
    client.subscribe("up/#", (err) => {
        console.log("subscribe done:", err);
    });
});

/**
 * Gateway uplink data processing
 */
client.on("message", (topic, message) => {

    /**
     * All messages are in JSON format
     */
    let payload = JSON.parse(message.toString());

    let data = payload.data;

    /**
     * Message type is distinguished by the action field
     */
    if (payload.action === 'data.scan') {
        data.forEach(item => {
            let deviceMac = item.bdaddrs[0].bdaddr;
            let addrType = item.bdaddrs[0].bdaddrType;
            let name = item.name;
            let rssi = item.rssi;
            console.log('scanned device:', deviceMac, addrType, rssi, name);
        });
    }
});