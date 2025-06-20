/**
 * sample for scan BLE devices
 * use Cassia AC APIs, refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki
 * to run the code, you should have a Cassia Router connected to a Cassia AC
 */
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

const AC_HOST = `${AC_BASE_URL}/api`;

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

/*
 * open combined sse connection
 * refer: https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#sse-combination-api
 */
function openCombinedSse(token) {
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
                console.log('scan data', data);
                break;
            default:
                console.log('unknown type', data);
                break;
        }
  });
}

function openScan(aps, token) {
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

(async () => {
  try {
    let token = await auth(DEVELOPER_KEY, DEVELOPER_SECRET);
    console.log(`get token: ${token}`);
    // open combine sse and wait for message
    openCombinedSse(token);
    await openScan(['CC:1B:E0:E0:05:B8'], token);
  } catch(ex) {
    console.error('fail:', ex);
  }
})();