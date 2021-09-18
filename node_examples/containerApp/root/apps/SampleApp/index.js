/**
 * container embeded nodejs v6.11.5 already
 */
const co = require('co');
const { Router } = require('node-cassia-sdk');
const fs = require('fs');
const cp = require('child_process');
/*
* API will serve at 10.10.10.254 in container
*/
const IP = '10.10.10.254';
/*
* custom config will write to location /root/config/${AppName}/config.json in JSON format
*/
const APP_NAME = 'SampleApp';
const CONFIG_FILE = `/root/config/${APP_NAME}/config.json`;

function readConfig() {
    let config = JSON.parse(fs.readFileSync(CONFIG_FILE));
    console.log('get config file', config);
    return config;
}

co(function *() {
    let config = readConfig();
    // update config every 30 minutes
    setInterval(() => {
        config = readConfig();
    }, 30 * 60 * 1000);
    var router = new Router(IP);
    yield router.scan({active:1, filter_rssi: -50});
    router.on('scan', (d) => {
        console.log(d);
        let deviceMac = d.bdaddrs[0].bdaddr;
        let deviceType = d.bdaddrs[0].bdaddrType;
        co(function*() {
            yield router.connect(deviceMac, deviceType);
            yield router.writeByHandle(deviceMac, 17, '0200');
        }).catch((err) => {
            console.error('connect device error', err);
        });
    });
    yield router.listenNotify();
    router.on('notify', (d) => {
        console.log(d);
        // send data to endpoint
        cp.exec(`curl -XPOST ${config.endpoint} -H 'Content-Type: application/json' -d '${JSON.encode(d)}'`);
    });
    router.on('error', (e) => {
        console.error('router error', e);
    });
}).catch((e) => {
    console.error(e);
});