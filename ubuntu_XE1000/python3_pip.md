# BLE + Python3 + ubuntu_XE1000.2.x.x  
### check pip3  
```
# pip3 list
Package                Version
---------------------- -------
build                  1.1.1  
wheel                  0.34.2 
```
### install pip3  
```
# sudo apt-get update
# sudo apt-get install -y python3-pip
```
## bleak
### install bleak by pip3  
[dbus_fast-2.21.1-cp38-cp38-linux_armv7l.whl](https://raw.githubusercontent.com/CassiaNetworks/CassiaSDKGuide/master/ubuntu_XE1000/pip3_whl/dbus_fast-2.21.1-cp38-cp38-linux_armv7l.whl) should be used , not the offical one. Please download by click [here](https://raw.githubusercontent.com/CassiaNetworks/CassiaSDKGuide/master/ubuntu_XE1000/pip3_whl/dbus_fast-2.21.1-cp38-cp38-linux_armv7l.whl) or by wget
```
# wget https://raw.githubusercontent.com/CassiaNetworks/CassiaSDKGuide/master/ubuntu_XE1000/pip3_whl/dbus_fast-2.21.1-cp38-cp38-linux_armv7l.whl
```
[bleak-0.21.1-py3-none-any.whl](https://raw.githubusercontent.com/CassiaNetworks/CassiaSDKGuide/master/ubuntu_XE1000/pip3_whl/bleak-0.21.1-py3-none-any.whl) should be used , not the offical one. Please download by click [here](https://raw.githubusercontent.com/CassiaNetworks/CassiaSDKGuide/master/ubuntu_XE1000/pip3_whl/bleak-0.21.1-py3-none-any.whl) or by wget
```
# wget https://raw.githubusercontent.com/CassiaNetworks/CassiaSDKGuide/master/ubuntu_XE1000/pip3_whl/bleak-0.21.1-py3-none-any.whl
```
check the file format and size , then install in container
```
# pip3 install dbus_fast-2.21.1-cp38-cp38-linux_armv7l.whl  
# pip3 show dbus_fast
# pip3 install bleak-0.21.1-py3-none-any.whl
# pip3 show bleak
```
### export dbus_fast as whl
there is no dbus_fast-xxx-linux_armv7l.whl , so pip3 install dbus_fast means to compile dbus_fast from source . and E1000 don't have enough memory for compile dbus_fast.  
X2000 has that memory and both E1000 and X2000 be the same arch of armv7l. so we could do pip3 install dbus_fast in X2000 and then export it as whl.  
in X2000 Ubuntu Container, execute command as follow:  
```
# pip3 install dbus_fast
# pip3 show
# pip wheel dbus_fast -w ./
```
### build bleak  from source
the bleak is an open source on github : https://github.com/hbldh/bleak  
edit the source code as you need  
```
# git clone git@github.com:hbldh/bleak.git
# git checkout master
```
preparation for build wheel  
```
# apt-get install -y zip unzip tree git python3-venv
# pip3 install --upgrade build
```
build wheel of bleak
```
# cd bleak
# python3 -m build
# tree dist/
dist/
|-- bleak-0.21.1-py3-none-any.whl
`-- bleak-0.21.1.tar.gz
```
to apply the newer whl you build , please remove the older bleak in the system  
```
# pip3 uninstall bleak
# pip3 install bleak-0.21.1-py3-none-any.whl
# pip3 list
```
## TI-SensorTag-CC2650
### install aiohttp-sse-client by pip3
[aiohttp-3.9.3-cp38-cp38-linux_armv7l.whl](https://raw.githubusercontent.com/CassiaNetworks/CassiaSDKGuide/master/ubuntu_XE1000/pip3_whl/aiohttp-3.9.3-cp38-cp38-linux_armv7l.whl) should be used , not the offical one. Please download by click [here](https://raw.githubusercontent.com/CassiaNetworks/CassiaSDKGuide/master/ubuntu_XE1000/pip3_whl/aiohttp-3.9.3-cp38-cp38-linux_armv7l.whl) or by wget
```
# wget https://raw.githubusercontent.com/CassiaNetworks/CassiaSDKGuide/master/ubuntu_XE1000/pip3_whl/aiohttp-3.9.3-cp38-cp38-linux_armv7l.whl
```
check the file format and size , then install in container
```
# pip3 install aiohttp-3.9.3-cp38-cp38-linux_armv7l.whl
# pip3 show aiohttp
# pip3 install aiohttp-sse-client
```
### export aiohttp as whl
please refer to the section [dbus_fast](python3_pip.md#export-dbus_fast-as-whl)  
