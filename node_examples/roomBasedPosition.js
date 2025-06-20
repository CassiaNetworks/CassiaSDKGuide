/**
 * sample for Positioning(Room Based)
 * use Cassia AC APIs, refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki
 * to run the code, you should have a Cassia Router connected to a Cassia AC
 */
const request = require('request');
const EventSource = require('eventsource');
const qs = require('querystring');

/*
 * replace it with your AC address base URL
 */
const AC_BASE_URL = 'https://192.168.0.226';

/*
 * you can set your developer key and secret under AC -> Settings -> Developer account for RESTful APIs
 */
const DEVELOPER_KEY = 'cassia';
const DEVELOPER_SECRET = 'cassia';

/*
 * this is your router's MAC, you should add the router to AC's online list first
 */
const ROUTER_MAC = 'CC:1B:E0:E0:05:B8';

const AC_HOST = `${AC_BASE_URL}/api`;

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
 * scan devices
 * refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#scan-bluetooth-devices
 * Sever-Sent Event(SSE) is used in scan, connection-state and notify of Cassia RESTful API,
 * SSE spec: https://html.spec.whatwg.org/multipage/server-sent-events.html#the-eventsource-interface
 * API will send ':keep-alive' every 30 seconds in SSE connection for user to check if the connection is active or not.
 * User need to call Cassia RESTful API to reconnect SSE in case that the connection is termincated abnormally, such as keep-alive lost, socket error, network problem, etc.
 * Nodejs library 'eventsource' handle the SSE reconnection automatically. For other lanuages, the reconnection may needs to be handled by users application.
 */
function openScanSse(routerMac, token) {
  const query = {
    filter_rssi: -75, // filter devices whose rssi is below -75, there are many other filters you can find them in document
    active: 1, // use active scan node
    mac: routerMac, // which router you want to start scan
    access_token: token // you can put token in query 'access_token=<token>' or in header 'Bearer <token>' 
  };
  const url = `${AC_HOST}/gap/nodes?event=1&${qs.encode(query)}`;
  console.log(url);
  const sse = new EventSource(url);

  sse.on('error', function(error) {
    console.error('open scan sse failed:', error);
  });
  
  /*
   * if scan open successful, it will return
   * data: {"bdaddrs":[{"bdaddr":"ED:47:B0:D3:A9:C8","bdaddrType":"public"}],"scanData":"0C09536C656570616365205A32","name":"Sleepace Z2","rssi":-37,"evt_type":4}
   */
   sse.on('message', function(message) {
  });
}

/*
 * room-based Bluetooth location tracking
 * enable this feature at Settings -> BT Positioning -> Room-based
 * the result is based on scan data, so we need open scan first
 * refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#positioning-api
 */
function getPosition(deviceMac) {
  return req({
    method: 'GET',
    url: `${AC_HOST}/middleware/position/by-device/${deviceMac}`
  });
}

(async () => {
  try {
    let authInfo = await auth(DEVELOPER_KEY, DEVELOPER_SECRET);
    let token = authInfo.access_token;
    openScanSse(ROUTER_MAC, token);

    // wait AC for collect some scan data
    setTimeout(async () => {
      let position = await getPosition('*'); // pass '*' means get all devices
      console.log('get position', position);
    }, 10000);
  } catch(ex) {
    console.error('fail:', ex);
  }
})();