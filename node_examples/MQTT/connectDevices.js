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
 * Generate unique request ID
 */
function genUniqueId() {
  return Math.random().toString(16).substr(2, 8);
}

/**
 * Send request to connect to device
 */
function reqConnectDevice(gatewayMac, deviceMac, addrType) {
  console.log('connecting device:', deviceMac, addrType);

  /**
   * Topic used for calling the API
   */
  let topic = `down/${gatewayMac}/api`;

  /**
   * action field is 'api', indicating calling the HTTP API
   */
  let payload = {
    id: genUniqueId(),
    action: 'api',
    timestamp: Date.now(),
    gateway: gatewayMac,
    data: {
      method: 'POST',
      url: `/gap/nodes/${deviceMac}/connection`,
      body: {
        type: addrType,
      }
    }
  };

  /**
   * Message is in JSON format
   */
  let jsonStr = JSON.stringify(payload);

  /**
   * Publish message
   */
  client.publish(topic, jsonStr);
}

/**
 * Send request to disconnect device
 */
function reqDisconnectDevice(gatewayMac, deviceMac) {
  console.log('disconnecting device:', deviceMac);

  let topic = `down/${gatewayMac}/api`;
  let payload = {
    id: genUniqueId(),
    action: 'api',
    timestamp: Date.now(),
    gateway: gatewayMac,
    data: {
      method: 'DELETE',
      url: `/gap/nodes/${deviceMac}/connection`,
      body: null,
    }
  };
  let jsonStr = JSON.stringify(payload);
  client.publish(topic, jsonStr);
}

/**
 * Devices to be connected
 */
const DEVICES = ['AA:AA:AA:00:01:05'];

/**
 * Gateway uplink data processing
 */
client.on("message", (topic, message) => {

  /**
   * All messages are in JSON format
   */
  let payload = JSON.parse(message.toString());
  let gatewayMac = payload.gateway;
  let data = payload.data;

  /**
   * Message type is distinguished by the action field
   */
  if (payload.action === 'data.scan') {
    data.forEach(item => {
      let deviceMac = item.bdaddrs[0].bdaddr;
      let addrType = item.bdaddrs[0].bdaddrType;
      console.log('scanned device:', deviceMac, addrType);

      if (DEVICES.includes(deviceMac)) {
        reqConnectDevice(gatewayMac, deviceMac, addrType);
      }
    });
  } else if (payload.action === 'data.connection_state') {
    data.forEach(item => {
      let deviceMac = item.handle;
      let state = item.connectionState;
      console.log('connection state:', deviceMac, state);

      /**
       * If connected successfully, disconnect after 15 seconds (for demonstration purposes only, not needed in actual applications)
       */
      if (state === 'connected') {
        setTimeout(() => {
          reqDisconnectDevice(payload.gateway, deviceMac);
        }, 15000);
      }
    });
  }
});