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

/**
 * Definitions of some message types
 */
const ACTION_TYPE = {
  API: 'api',
  SCAN: 'data.scan',
  CONNECTION_STATE: 'data.connection_state',
  NOTIFICATION: 'data.notification',
};

/**
 * HTTP API request methods
 */
const HTTP_METHOD = {
  GET: 'GET',
  POST: 'POST',
  DELETE: 'DELETE',
};

/**
 * Generate unique request ID
 */
function genUniqueId() {
  return Math.random().toString(16).substr(2, 8);
}

/**
 * Send HTTP API request via MQTT
 */
function apiReqAsync(gatewayMac, method, url, body) {
  console.log('api request async:', method, url, body);

  /**
   * Topic used for calling the API
   */
  let topic = `down/${gatewayMac}/api`;

  let payload = {
    id: genUniqueId(),
    action: ACTION_TYPE.API,
    timestamp: Date.now(),
    gateway: gatewayMac,
    data: {
      method,
      url,
      body,
    }
  };

  /**
   * Message body is in JSON format
   */
  let jsonStr = JSON.stringify(payload);

  /**
   * Publish message
   */
  client.publish(topic, jsonStr);
}

/**
 * Send request to connect to device
 */
function reqConnectDevice(gatewayMac, deviceMac, addrType) {
  console.log(`connecting device: ${deviceMac}, ${addrType}`);
  let url = `/gap/nodes/${deviceMac}/connection`;
  apiReqAsync(gatewayMac, HTTP_METHOD.POST, url, { type: addrType });
}

/**
 * Send request to write to device
 */
function reqwriteValue(gatewayMac, deviceMac, serviceUuid, charUuid, value) {
  console.log(`writing value: ${deviceMac}, ${serviceUuid}, ${charUuid}, ${value}`);
  let url = `/gatt/nodes/${deviceMac}/services/${serviceUuid}/characteristics/${charUuid}/value/${value}`;
  apiReqAsync(gatewayMac, HTTP_METHOD.GET, url, null);
}

/**
 * Define GATT service and characteristic UUIDs to be written
 * Replace with actual device UUIDs
 * https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#discover-all-services-characteristics-and-descriptors-all-at-once
 */
const GATT_UUID = {
  SERVICE: '0000ff00-0f0e-0d0c-0b0a-050403020100',
  CHAR: '0000ff01-0f0e-0d0c-0b0a-050403020100',
};

/**
 * Send request to enable notifications
 */
function openNotifyAsync(gatewayMac, deviceMac, serviceUuid, charUuid) {
  console.log(`opening notify: ${deviceMac}, ${serviceUuid}, ${charUuid}`);
  reqwriteValue(gatewayMac, deviceMac, serviceUuid, charUuid, '0100');
}

/**
 * Gateway uplink BLE scan data handler
 */
function scanHandler(payload) {
  payload.data.forEach(item => {
    let deviceMac = item.bdaddrs[0].bdaddr;
    let addrType = item.bdaddrs[0].bdaddrType;
    let name = item.name;
    let rssi = item.rssi;
    console.log('scanned device:', deviceMac, addrType, rssi, name);
    reqConnectDevice(payload.gateway, deviceMac, addrType);
  });
}

/**
 * Gateway uplink connection state data handler
 */
function connectionStateHandler(payload) {
  payload.data.forEach(item => {
    let deviceMac = item.handle;
    let state = item.connectionState;
    console.log('connection state:', deviceMac, state);

    if (state === 'connected') {
      openNotifyAsync(payload.gateway, deviceMac, GATT_UUID.SERVICE, GATT_UUID.CHAR);
    }
  });
}

/**
 * Gateway uplink notification data handler
 */
function notificationHandler(payload) {
  payload.data.forEach(item => {
    let deviceMac = item.id;
    let handle = item.handle;
    let value = item.value;
    console.log('notification data:', deviceMac, handle, value);
  });
}

/**
 * Default handler function
 */
function defaultHandler(payload) {
  console.log('other message:', payload);
}

/**
 * Message handler functions
 */
const actionHandler = {
  [ACTION_TYPE.SCAN]: scanHandler,
  [ACTION_TYPE.CONNECTION_STATE]: connectionStateHandler,
  [ACTION_TYPE.NOTIFICATION]: notificationHandler,
};

/**
 * Message dispatch function
 */
function messageDispatcher(topic, message) {
  let payload = JSON.parse(message.toString());
  let handler = actionHandler[payload.action] || defaultHandler;
  handler(payload);
}

/**
 * MQTT connect event handler
 */
function connectHandler() {
  client.subscribe("up/#", (err) => {
    console.log("subscribe done:", err);
  });
}


let client = null;

/**
 * Main function
 */
function main() {
  client = mqtt.connect(MQTT_BROKER);
  client.on("connect", connectHandler);
  client.on("message", messageDispatcher);
}

main();