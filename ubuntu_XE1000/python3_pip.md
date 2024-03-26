


## BLE + Python3 + ubuntu_XE1000.2.x.x  
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
### install bleak by pip3  
[dbus_fast-2.21.1-cp38-cp38-linux_armv7l.whl](pip3_whl/dbus_fast-2.21.1-cp38-cp38-linux_armv7l.whl) should be used , not the offical one  
[bleak-0.21.1-py3-none-any.whl](pip3_whl/bleak-0.21.1-py3-none-any.whl) should be used , not the offical one
```
# pip3 install dbus_fast-2.21.1-cp38-cp38-linux_armv7l.whl  
# show dbus_fast
# pip3 install bleak-0.21.1-py3-none-any.whl
```
### export dbus_fast wheel pack  
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
