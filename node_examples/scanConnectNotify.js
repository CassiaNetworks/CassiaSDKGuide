/**
 * sample for connect multiple BLE devices and open notification
 * first open listen to scan events and connect specific devices one by one,
 * open device's notification and receive notification of all devices
 * use Cassia AC APIs, refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki
 * to run the code, you should have a Cassia Router connected to a Cassia AC
 */
const request = require('request');
const EventSource = require('eventsource');
const qs = require('querystring');

/*
 * replace it with your AC address
 */
const AC_HOST = 'http://192.168.0.226/api';

/*
 * you can set your developer key and secret under AC -> Settings -> Developer account for RESTful APIs
 */
const DEVELOPER_KEY = 'cassia';
const DEVELOPER_SECRET = 'cassia';

/*
 * this is your router's MAC, you should add the router to AC's online list first
 */
const ROUTER_MAC = 'CC:1B:E0:E0:05:B8';

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
 * since Router can only connect one device at one time, or it will return "chip busy" error
 * so we need a queue to connect devices sequentially
 * and prevent same device to enter queue
 */
function queue() {
  let q = [];
  let uniqCheck = {};
  function enq(item) {
    /*
     * we filter same device
     */
    if (uniqCheck[item.mac]) return;
    q.push(item);
    uniqCheck[item.mac] = true;
  }

  function deq() {
    let item = q.pop();
    if (!item) return null;
    delete uniqCheck[item.mac];
    return item;
  }
  return {
    enq, deq
  }
}

let connectQ = new queue();
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
 */
function openScanSse(token, routerMac) {
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
    console.error('open scan sse failed:', error);
  });
  
  /*
   * if scan open successful, it will return like follow:
   * data: {"bdaddrs":[{"bdaddr":"ED:47:B0:D3:A9:C8","bdaddrType":"public"}],"scanData":"0C09536C656570616365205A32","name":"Sleepace Z2","rssi":-37,"evt_type":4}
   */
   sse.on('message', function(message) {
    let data = JSON.parse(message.data);
    let deviceMac = data.bdaddrs[0].bdaddr;
    let addrType = data.bdaddrs[0].bdaddrType;
    /*
     * enqueue device data to connect it lately
     * the scanning will get multiple scan data of same device in short time,
     * so we need filter same device
     */
    connectQ.enq({mac: deviceMac, addrType});
  });
}

/*
 * connect one device
 * refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#connectdisconnect-to-a-target-device
 */
function connect(token, deviceMac, addrType) {
  console.log('connect device', deviceMac);
  let options = {
    method: 'POST',
    url: `${AC_HOST}/gap/nodes/${deviceMac}/connection?access_token=${token}`,
    qs: {mac: ROUTER_MAC},
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({timeout: 5000, type: addrType})
  };
  return req(options);
}

async function processQueue(token) {
  let device = connectQ.deq()
  while (device) {
    let result;
    try {
      result = await connect(token, device.mac, device.addrType);
      /*
      * write 0200 to notification handle to open notification
      */
      await write(token, device.mac, 17, '0200');
    } catch (e) {
      result = e;
    }
    console.log('connect', device.mac, result);
    device = connectQ.deq();
  }

  /*
   * check queue again in 5 seconds
   */
  setTimeout(() => {
    processQueue(token);
  }, 5000);
}

/*
 * Receive Notification and Indication
 * refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#receive-notification-and-indication
 */
function openNotifySse(token, routerMac) {
  const url = `${AC_HOST}/gatt/nodes?mac=${routerMac}&access_token=${token}`;
  const sse = new EventSource(url);

  sse.on('error', error => {
    console.error('open notify sse failed:', error);
  });
  
  sse.on('message', message => {
    console.log('recevied notify sse message:', message);
  });
  
  return Promise.resolve(sse);
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

(async () => {
  try {
    let authInfo = await auth(DEVELOPER_KEY, DEVELOPER_SECRET);
    let token = authInfo = authInfo.access_token;
    openScanSse(token, ROUTER_MAC);
    openNotifySse(token, ROUTER_MAC);
    processQueue(token, ROUTER_MAC);
  } catch(ex) {
    console.error('fail:', ex);
  }
})();