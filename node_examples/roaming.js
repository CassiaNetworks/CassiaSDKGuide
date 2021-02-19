/**
 * sample for roaming
 * use Cassia AC APIs, refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki
 * to run the code, you should have a Cassia Router connected to a Cassia AC
 */
const request = require('request');
const EventSource = require('eventsource');

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
const DEVICE_MAC = '**:**:**:**:**:**';

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
 * This API will create one combined SSE connection with AC. This SSE connection can receive scan data, notification/indication data, and connected device status for all the routers controlled by this AC.
 * refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#sse-combination-api
 * Sever-Sent Event(SSE) is used in scan, connection-state and notify of Cassia RESTful API,
 * SSE spec: https://html.spec.whatwg.org/multipage/server-sent-events.html#the-eventsource-interface
 * API will send ':keep-alive' every 30 seconds in SSE connection for user to check if the connection is active or not.
 * User need to call Cassia RESTful API to reconnect SSE in case that the connection is termincated abnormally, such as keep-alive lost, socket error, network problem, etc.
 * Nodejs library 'eventsource' handle the SSE reconnection automatically. For other lanuages, the reconnection may needs to be handled by users application.
 */
function openCombinationSse(token) {
  const url = `${AC_HOST}/aps/events?access_token=${token}`;
  const sse = new EventSource(url);

  sse.on('error', function(error) {
    console.error('open combination sse failed:', error);
  });
  
  sse.on('message', function(message) {
    let data = JSON.parse(message.data);
    switch(data.dataType) {
      case 'state': // include all Router’s information
        break;
      case 'scan': // scan data
        break;
      case 'notification': // notification data
        break;
      case 'connection_state': // connection state change events
        /*
        * if device is connected, you can write handle or do other operation here
        */
        pair(token, data.ap, data.handle);
        break;
      case 'ap_state': // Router online/offline events
        break;
    }
    console.log('receive combination sse events', data);
  });
}

/*
 * turn on Router Auto-Selection feature
 * AC will begin to collect scan data to determine which Router is best for connecting specify device
 * refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#router-auto-selection
 */
function autoSelectOn(token) {
  let options = {
    method: 'POST',
    url: `${AC_HOST}/aps/ap-select-switch?access_token=${token}`,
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
        flag: 1, // enable auto-selection feature
        /*
        * since auto-selection feature will collect all Router's scan data,
        * use proper scan filter will significantly reduce AC's CPU and memory usage
        * this parameter is available in AC v2.0.3, same as scan filters in scan SSE
        */
       scan_params: {
         filter_rssi: -75,
         filter_name: 'Cassia*'
       }
    })
  };
  return req(options);
}

function connectWithAutoSelection(token, devices) {
  return req({
    url: `${AC_HOST}/aps/connections/connect?access_token=${token}`,
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({
      /*
      * you can define a Router range to connect to devices, or '*' means all online Routers
      */
      aps: '*',
      devices: devices,
      /*
      * (Mandatory) use the roaming feature, Router use random address to connect devices,
        AC will reconnect devices among Routers,
      * you can listen to connection-state changes in combination SSE
      */
      random: 1,
      /*
      * (Optional): in ms, the connection request will timeout if it can’t be finished within this time. 
      * The default timeout is 10,000ms. The range of value is 1000ms – 20000ms.
      */
      timeout: 20000
    })
  });
}

function pair(token, routerMAC, deviceMAC) {
  return req({
    url: `${AC_HOST}/management/nodes/${deviceMAC}/pair?access_token=${token}&mac=${routerMAC}`,
    method: 'POST',
    body: JSON.stringify({ "bond": 1})
  });
}

(async () => {
  try {
    let authInfo = await auth(DEVELOPER_KEY, DEVELOPER_SECRET);
    let token = authInfo.access_token;
    await autoSelectOn(token);
    await openCombinationSse(token);
    await connectWithAutoSelection(token, [DEVICE_MAC]);
  } catch(ex) {
    console.error('fail:', ex);
  }
})();