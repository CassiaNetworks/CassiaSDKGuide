# Examples for Cassia RESTful APIs
This folder contains a number of ready-to-run examples demonstrating various use cases of Cassia RESTful APIs

## Prerequisites

- Install dependencies
    ```bash
    pip3 install aiohttp
    pip3 install aiohttp_sse_client
    ```
- Configure scan filter
    - The example uses the `filter_mac` parameter to precisely match the device MAC address. 
    - Please adjust according to your actual device.
- Read/Write Device Operations
    - You need to modify the handle value according to the actual GATT service list of the device.
    - Discover device GATT Services API
        - https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#discover-gatt-services-and-characteristics
- AC mode
    - Configure the correct developer account and password.
    - Log in to the AC Web -> go to the Settings page -> Developer Account for RESTful APIs.
- Gateway mode
    - You need to enable the local API or set standalone mode.
    - Enable local API:
        - Log in to the AC Web -> go to the Gateways page -> click the corresponding gateway -> Config -> General -> Local RESTful API.
    - Set standalone mode:
        - Log in to the gateway Web -> Basic -> Gateway Mode.

## Examples

### acScan.py
this example show you how to auth with your AC,
and use a router under the AC to scan devices

### acNotify.py
example for scan, connect and get notification for one device

### connectDevices.py
example for scan, connect from one router for multiple devices

### scanConnectNotify.py
example for scan, connect and get notification for multiple devices

### connectDevicesWithMultipleRouters.py
example for connect multiple devices with multiple routers

### acBatch.py
example for connect multiple devices in batch-connect mode

### scanConnectNotify(SingleRouter).py
example for scan, connect and get notification with single router(use router local API)