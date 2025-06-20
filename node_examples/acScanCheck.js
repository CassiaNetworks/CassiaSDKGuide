const request = require('request');
const EventSource = require('eventsource');
const qs = require('querystring');

/*
 * replace it with your AC address base URL
 */
const AC_BASE_URL = 'http://192.168.0.226';

/*
 * you can set your developer key and secret under AC -> Settings -> Developer account for RESTful APIs
 */
const DEVELOPER_KEY = 'cassia';
const DEVELOPER_SECRET = 'cassia';

let GATEWAYS = [
  // 'CC:1B:E0:E0:05:B8',
];

const TEST_INTERVAL = 5000;

const AC_HOST = `${AC_BASE_URL}/api`;

function auth(key, secret) {
  let options = {
    method: 'POST',
    url: `${AC_HOST}/oauth2/token`,
    headers: {
      'Content-Type': 'application/json'
    },
    json: true,
    auth: {
      user: key,
      pass: secret,
    },
    body: {grant_type: 'client_credentials'}
  };
  return new Promise((resolve, reject) => {
    request(options, function (error, response) {
      if (error) reject(error);
      else if (response.statusCode !== 200) reject(response.body);
      else resolve(response.body.access_token);
    });
  });
}

function getAllHubs() {
  let options = {
    method: 'POST',
    url: `${AC_HOST}/cassia/hubs?access_token=${token}`,
    headers: {
      'Content-Type': 'application/json'
    },
    json: true,
  };
  return new Promise((resolve, reject) => {
    request(options, function (error, response) {
      if (error) reject(error);
      else if (response.statusCode !== 200) reject(response.body);
      else resolve(response.body);
    });
  });
}


function checkScan(routerMac) {
  return new Promise((resolve, reject) => {
    const query = {
      // filter_rssi: -75, // filter devices whose rssi is below -75, there are many other filters you can find them in document
      active: 1, // use active scan node
      mac: routerMac, // which router you want to start scan
      access_token: token // you can put token in query 'access_token=<token>' or in header 'Bearer <token>' 
    };
    const url = `${AC_HOST}/gap/nodes?event=1&${qs.encode(query)}`;
    const sse = new EventSource(url);
    
    let deviceCount = {};
    let scanCount = 0;
    let hasKeepAlive = false;

    let reportTime = setTimeout(() => {
      sse.close();
      if (scanCount > 0) {
        resolve({state: 'ok', detail: {sc: scanCount, dc: Object.keys(deviceCount).length}});
      } else if (hasKeepAlive) {
        resolve({state:'keepalive'});
      } else {
        resolve({state:'timeout'});
      }
    },TEST_INTERVAL);
    sse.on('error', function(error) {
      // console.error('open scan sse failed:', error);
      // reject(error);
      clearTimeout(reportTime);
      resolve({state:'err', detail: error.toString()});
    });
    sse.on('message', function(message) {
      let data = JSON.parse(message.data);
      let deviceMac = data.bdaddrs[0].bdaddr;
      let addrType = data.bdaddrs[0].bdaddrType;
      let name = data.name;
      let rssi = data.rssi;
      deviceCount[deviceMac] = 1;
      scanCount ++;
      // console.log(`scanned device: ${deviceMac}, ${addrType}, ${rssi}, ${name}`);
    });
    
    sse.on('keep-alive', () => {
      // console.log('receive event keep-alive');
      hasKeepAlive = true;
    });
  });
}

function renderResult(mac, info) {
  switch(info.state) {
    case 'ok':
      return `CHECK ${mac}, RESULT: ${info.state}, scan count: ${info.detail.sc}, scan device: ${info.detail.dc}`;
    case 'err':
      return `CHECK ${mac}, RESULT: ${info.state}, err message: ${info.detail}`;
    case 'keepalive':
      return `CHECK ${mac}, RESULT: ${info.state}, ONLY KeepAlive`;
    case 'timeout':
      return `CHECK ${mac}, RESULT: ${info.state}, NO Response`;
  }
}
let token;

(async () => {
  try {
    token = await auth(DEVELOPER_KEY, DEVELOPER_SECRET);
    setInterval(async function() {
      token = await auth(DEVELOPER_KEY, DEVELOPER_SECRET);
    }, 59 * 60 * 1000);
    // console.log(`get token: ${token}`);
    if (GATEWAYS.length <= 0) {
      let result = await getAllHubs();
      GATEWAYS = result.map((h) => h.mac);
    }
    console.log(`begin check ${GATEWAYS.length} gateways ...`);
    for(let i=0; i < GATEWAYS.length; i++) {
      let gateway = GATEWAYS[i];
      let info = await checkScan(gateway);
      console.log(renderResult(gateway, info));
    }

    process.exit(0);
  } catch(ex) {
    console.error('fail:', ex);
  }
})();

