/**
 * sample for connect multiple BLE devices(use batch-connect), and write data to all device
 * use Cassia AC APIs, refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki
 * to run the code, you should have a Cassia Router connected to a Cassia AC
 */
const request = require('request');
const EventSource = require('eventsource');
const qs = require('querystring');

/*
 * replace it with your AC address
 */
const AC_HOST = 'http://q1.lunxue.cc/api';

/*
 * you can set your developer key and secret under AC -> Settings -> Developer account for RESTful APIs
 */
const DEVELOPER_KEY = 'cassia';
const DEVELOPER_SECRET = 'cassia';

/*
 * this is your router's MAC, you should add the router to AC's online list first
 */
const ROUTER_MAC = 'CC:1B:E0:E0:28:EC';

const isWritten = {};

// convert http request to promise
function req(options) {
  return new Promise((resolve, reject) => {
    request(options, function (error, response) {
      if (error) reject(error);
      else if (response.statusCode !== 200) reject(response.body);
      else resolve(response.body);
    });
  });
}
/*
 * auth with your AC, the token will expired after ONE hour,
 * if you run a long term task, you should refresh the token every hour
 * refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/Getting-Started#access-cassia-router-through-the-cassia-ac
 */ 
function auth(key, secret) {
  let options = {
    method: 'POST',
    url: `${AC_HOST}/oauth2/token`,
    headers: {
      'Content-Type': 'application/json'
    },
    json: true,
    /*
     * auth options will encode Authorization header for you,
     * you can also add header "Authorization: Basic <Base64_encode(key + ':' + secret)>" manually
     */
    auth: {
      user: key,
      pass: secret,
    },
    body: {grant_type: 'client_credentials'}
  };
  return req(options);
}

/*
 * scan and connect devices
 * refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#scan-bluetooth-devices
 * Sever-Sent Event(SSE) is used in scan, connection-state and notify of Cassia RESTful API,
 * SSE spec: https://html.spec.whatwg.org/multipage/server-sent-events.html#the-eventsource-interface
 * API will send ':keep-alive' every 30 seconds in SSE connection for user to check if the connection is active or not.
 * User need to call Cassia RESTful API to reconnect SSE in case that the connection is termincated abnormally, such as keep-alive lost, socket error, network problem, etc.
 * Nodejs library 'eventsource' handle the SSE reconnection automatically. For other lanuages, the reconnection may needs to be handled by users application.
 */
function openScanSseAndConnect(routerMac, token) {
  const query = {
    /*
     * filter devices whose rssi is below -75, and name begins with 'Cassia',
     * there are many other filters, you can find them in document
     * use proper filters can significantly reduce traffic between Router and AC
     */
    filter_rssi: -75,
    filter_name: 'Cassia*',
    /*
     * use active scan, default is passive scan
     * active scan makes devices response with data packet which usually contains device's name
     */
    active: 1,
    mac: routerMac, // which router you want to start scan
    access_token: token // you can put token in query 'access_token=<token>' or in header 'Bearer <token>' 
  };
  const url = `${AC_HOST}/gap/nodes?event=1&${qs.encode(query)}`;
  const sse = new EventSource(url);

  sse.on('error', function(error) {
    console.log('open notify sse failed:', error);
  });
  
  sse.on('message', function(message) {
    const data = JSON.parse(message.data);
    const deviceAddr = data.bdaddrs[0];
    const deviceMac = deviceAddr.bdaddr;
    const deviceAddrType = deviceAddr.bdaddrType;
    if (isWritten[deviceMac]) return;
    batchConnect(token, deviceMac, deviceAddrType);
  });
  
  return Promise.resolve(sse);
}

/*
 * Batch Connect/Disconnect to a Target Device (v2.0 and above)
 * refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#batch-connectdisconnect-to-a-target-device-v20-and-above
 */
function batchConnect(token, deviceMac, addrType) {
  let options = {
    'method': 'POST',
    'url': `${AC_HOST}/api/gap/batch-connect?mac=${routerMac}&access_token=${token}`,
    'headers': {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      /*
      * you can put multiple devices in list parameter, all the devices will enter a connecting queue
      * when device is connected, it will report connected event in connection-state SSE
      */
      list: [{"type": addrType,"addr": deviceMac}],
      timeout: 5000,
      per_dev_timeout: 10000
    })
  };

  return req(options);
}

/*
 * Read/Write the Value of a Specific Characteristic
 * refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#readwrite-the-value-of-a-specific-characteristic
 */
function write(token, deviceMac, handle, value) {
  let options = {
    method: 'GET',
    url: `${AC_HOST}/gatt/nodes/${deviceMac}/handle/${handle}/value/${value}?mac=${ROUTER_MAC}&access_token=${token}`,
  };
  return req(options);
}

/*
 * disconnect device
 * refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#connectdisconnect-to-a-target-device
 */
function disconnect(token, deviceMac) {
  let options = {
    'method': 'DELETE',
    'url': `${AC_HOST}/api/gap/nodes/${deviceMac}/connection?mac=${ROUTER_MAC}&access_token=${token}`,
  };
  return req(options);
}

/*
 * Get Device Connection Status
 * you will get notify when device connected or disconnected to a Router
 * refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#get-device-connection-status
 * Sever-Sent Event(SSE) is used in scan, connection-state and notify of Cassia RESTful API,
 * SSE spec: https://html.spec.whatwg.org/multipage/server-sent-events.html#the-eventsource-interface
 * API will send ':keep-alive' every 30 seconds in SSE connection for user to check if the connection is active or not.
 * User need to call Cassia RESTful API to reconnect SSE in case that the connection is termincated abnormally, such as keep-alive lost, socket error, network problem, etc.
 * Nodejs library 'eventsource' handle the SSE reconnection automatically. For other lanuages, the reconnection may needs to be handled by users application.
 */
function openConnectStateSse(token) {
  const url = `${AC_HOST}/management/nodes/connection-state?mac=${routerMac}&access_token=${token}`;
  const sse = new EventSource(url);

  sse.on('error',function(error) {
    console.log('open connect status sse failed:', error);
  });
  
  sse.on('message', async function(message) {
    const data = JSON.parse(message.data);
    const deviceMac = data.handle;
    // skip device which have already written data
    if (isWritten[deviceMac]) return;
    if (data.connectionState === 'connected') {
      await write(token, deviceMac, 39, '21ff310302ff31');
      isWritten[deviceMac] = true;
      await disconnect(token, deviceMac);
    } else {
      // if device is disconnected, it can be scanned again
    }
  });
  
  return Promise.resolve(sse);
}

(async () => {
  try {
    let token = await auth(DEVELOPER_KEY, DEVELOPER_SECRET);
    console.log('token:', token);
    await openScanSseAndConnect(token);
    await openConnectStateSse(token);
    console.log('success');
  } catch(ex) {
    console.error('fail:', ex);
  }
})();