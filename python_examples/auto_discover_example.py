import requests
from requests.adapters import HTTPAdapter
import base64
import json
import os
import time
import datetime
import logging

# Example code to auto-discover devices on a LAN.

request = requests.session()
request.mount("http://", HTTPAdapter(max_retries=3))
request.mount("https://", HTTPAdapter(max_retries=3))

# Configuration
protocl = "http://"
ac_ip = "172.16.60.200"
ac_dev_id = "tester"
ac_dev_pwd = "10b83f9a2e823c47"
device_mac = "00:00:00:00:00:01"
intaval_time = 10
##########

scan_data_count = 0
counts = 0
summary = {}
summary_file = ''
summary_count = 1


def log():
    logger = logging.getLogger("test")
    logger.setLevel(logging.INFO)

    ch_handle = logging.StreamHandler()
    format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    ch_handle.setFormatter(format)

    logger.addHandler(ch_handle)

    return logger


log = log()


def get_token():
    url = protocl + ac_ip + '/api/oauth2/token'
    data = {'grant_type': 'client_credentials'}

    # Encode dev_id and dev_pwd by base64
    IDSEC = ac_dev_id + ':' + ac_dev_pwd
    author = base64.b64encode((IDSEC).encode('utf-8'))
    authorize = author.decode('utf-8')

    headers = {'Authorization': 'Basic ' + authorize}

    try:
        r = requests.post(url, headers=headers, data=data)
        access_token = json.loads(r.content.decode('utf-8'))['access_token']
        return access_token
    except:
        log.error("Get access_token failed: ")
        sys.exit(1)


access_token = get_token()


def get_online_hubs():
    url = protocl + ac_ip + '/api/cassia/hubs'
    print(url)
    headers = {'Content-Type': 'application/json',
               'version': '1', 'Authorization': 'Bearer ' + access_token}
    res = request.get(url, headers=headers)
    res_hub_info = json.loads(res.text)
    hubs = []
    if len(res_hub_info) > 0:
        for i in res_hub_info:
            if isinstance(i, dict):
                hubs.append(i['mac'])
        return hubs
    else:
        log.error('No routers online!')


def get_hub_model(hub_mac):
    url = protocl+ac_ip + '/api/cassia/info?mac='+hub_mac
    headers = {'Content-Type': 'application/json',
               'version': '1', 'Authorization': 'Bearer ' + access_token}
    with request.get(url, headers=headers) as r:
        if r.status_code == 200:
            hub_detail = r.json()
            hub_wireless_ip = hub_detail["wireless"]["iface"].get("ip")
            hub_wired_ip = hub_detail["wired"]["iface"].get("ip")
            if hub_wired_ip:
                hub_ip = hub_wired_ip
            else:
                hub_ip = hub_wireless_ip
            hub_model = hub_detail["model"]
            return hub_ip, hub_model
        else:
            log.error(r.text)


if __name__ == '__main__':
    hubs = get_online_hubs()
    for i in hubs:
        hub_ip, hub_model = get_hub_model("CC:1B:E0:E0:94:24")
        log.info(hub_ip, hub_model)
