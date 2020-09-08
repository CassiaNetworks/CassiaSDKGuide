/**
 * connect BLE device, open notification, receive notification data
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
const ROUTER_MAC = 'CC:1B:E0:E0:28:EC';
const DEVICE_MAC = 'C0:00:5B:D1:AA:BC';

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
  const auth = Buffer.from(key + ':' + secret).toString('base64');
  let options = {
    method: 'POST',
    url: `${AC_HOST}/oauth2/token`,
    json: true,
    headers: {
      'Authorization': 'Basic ' + auth,
      'Content-Type': 'application/json'
    },
    body: {'grant_type': 'client_credentials'}
  };
  return req(options);
}

/*
 * connect one device
 * refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#connectdisconnect-to-a-target-device
 */
function connect(token, deviceMac, addrType) {
  let options = {
    method: 'POST',
    url: `${AC_HOST}/gap/nodes/${deviceMac}/connection?mac=${ROUTER_MAC}&access_token=${token}`,
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({timeout: 5000, type: addrType})
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
 * Receive Notification and Indication
 * refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#receive-notification-and-indication
 */
function openNotifySse(token) {
  const url = `${AC_HOST}/gatt/nodes?mac=${ROUTER_MAC}&access_token=${token}`;
  const sse = new EventSource(url);

  sse.on('error', error => {
    console.error('open notify sse failed:', error);
  });
  
  sse.on('message', message => {
    console.log('recevied notify sse message:', message);
  });
  
  return Promise.resolve(sse);
}

(async () => {
  try {
    let authInfo = await auth(DEVELOPER_KEY, DEVELOPER_SECRET);
    let token = authInfo['access_token'];
    await openNotifySse(token);
    await connect(token, DEVICE_MAC, 'public');
    await write(token, DEVICE_MAC, '39', '21ff310302ff31');
  } catch(ex) {
    console.error('fail:', ex);
  }
})();