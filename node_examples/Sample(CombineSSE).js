/**
 * sample for scan BLE devices
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

function req(options) {
  if (typeof options == 'string') options = {url: options};
  // options.headers = Object.assign({}, this.headers, options.headers);
  // options.qs = Object.assign({}, this.qs, options.qs);
  let opts = Object.assign({}, {method: 'GET', baseUrl: AC_HOST, json: true}, options);
  return new Promise((resolve, reject) => {
    // console.log(JSON.stringify(opts));
    request(opts, function(err, response, body) {
      if (err) return reject(err);
      if (response && response.statusCode === 200) {
        return resolve(body);
      } else {
        if (typeof body == 'object') body = JSON.stringify(body);
        return reject(`${response.statusCode} ${body}`);
      }
    })
  })
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
  return new Promise((resolve, reject) => {
    request(options, function (error, response) {
      if (error) reject(error);
      else if (response.statusCode !== 200) reject(response.body);
      else resolve(response.body.access_token);
    });
  });
}

async function refreshToken() {
  token = await auth(DEVELOPER_KEY, DEVELOPER_SECRET);
}

function getRouterList() {
  return req({url: "cassia/hubs", qs: {access_token: token}});
}

/*
 * open combined sse connection
 * refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#sse-combination-api
 */
function openCombinedSse() {
  const url = `${AC_HOST}/aps/events?access_token=${token}`;
  const sse = new EventSource(url);

  sse.on('error', function(error) {
    console.error('open scan sse failed:', error);
  });

   sse.on('message', function(message) {
        let data = JSON.parse(message.data);
        switch(data.dataType) {
            case 'state':
                console.log('get gateway state', data);
                break;
            case 'scan':
                // console.log('scan data', data);
                connect(data['ap'], data["bdaddrs"][0]["bdaddr"], data["bdaddrs"][0]["bdaddrType"]);
                // or you can use router auto selection
                //connectWithRouterAutoSelection(routers.map(r => r.mac), data["bdaddrs"][0]["bdaddr"]);
                break;
            case 'connection_state':
                console.log('connection result');
                if (data["connectionState"] == "connected") {
                  writeData(data['ap'], data['handle']);
                }
                break;
            default:
                console.log('unknown type', data);
                break;
        }
  });
}

// enable gateway auto-selection function
// refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#router-auto-selection
function enableRouterAutoSelection() {
  return req({url: "aps/ap-select-switch", qs: {access_token: token},
    body: {
      "flag":1,
      // more scan filter parameters refers: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#scan-bluetooth-devices
      "scan_params":{
         "filter_mac":[
            "C7:ED:44:24:3E:55",
            "C7:ED:44:24:3E:56",
            "C7:ED:44:24:3E:57"
         ],
         "filter_rssi":"-70"
      }
   }});
}

function openScan(aps) {
    let options = {
        method: 'POST',
        url: `${AC_HOST}/aps/scan/open?access_token=${token}`,
        headers: {
          'Content-Type': 'application/json'
        },
        json: true,
        // more scan filter parameters refers: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#scan-bluetooth-devices
        body: {
            aps: aps,
            filter_mac: '36:A0:63:73:D6:79', //filter for device MAC
            filter_rssi: -80,
            filter_duplicates: '1',
            filter_name: 'HW' //filter for device name
        }
      };
      return new Promise((resolve, reject) => {
        request(options, function (error, response) {
          if (error) reject(error);
          else if (response.statusCode < 200 || response.statusCode > 202) reject(response.body);
          else resolve(response.body.access_token);
        });
      });
}

/*
 * connect one device
 * refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#connectdisconnect-to-a-target-device
 */
function connect(router, deviceMac, addrType) {
  let options = {
    method: 'POST',
    url: `/gap/nodes/${deviceMac}/connection?mac=${router}&access_token=${token}`,
    body: {timeout: 5000, type: addrType}
  };
  return req(options).catch((e) => console.error("connect device error", e));
}

// connect device use router auto selection
// refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#connect-a-device
function connectWithRouterAutoSelection(routers, deviceMac) {
  return req({
    url: "aps/connections/connect",
    method: "POST",
    body: {
      aps:routers,
      devices: [deviceMac]
    }
  }).catch((e) => console.error("connect device error", e));
}

// write device handle 
// refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#readwrite-the-value-of-a-specific-characteristic
function writeData(router, deviceMac) {
  let handle = 21;
  let data = "0100";
  return req({
    method: 'GET', 
    url: `/gatt/nodes/${deviceMac}/handle/${handle}/value/${data}?mac=${router}&access_token=${token}`,
  });
}

let token;
let routers;

(async () => {
  try {
    await refreshToken();
    setInterval(refreshToken, 60 * 60 * 1000);// refresh token every 1 hour

    // open combine sse and wait for message
    openCombinedSse();

    // if you want use ap auto selection feature
    await enableRouterAutoSelection();

    routers = await getRouterList();
    await openScan(routers.map(r => r.mac));
  } catch(ex) {
    console.error('fail:', ex);
  }
})();