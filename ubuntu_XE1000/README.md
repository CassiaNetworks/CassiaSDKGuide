## SSH Remote Login Container
[Click Here](remote_login.md)
## Port Forwarding
Some ports will, by default, forward traffic to the interior of the container. Refer to the following table for details. Container APP can directly use these ports as service ports and listening ports.
| Protocol | Port |
|--|--|
| TCP | 502 |
| TCP | 655 |
| UDP | 655 |
| TCP | 1337 |
| TCP | 3000 |
| UDP | 20203 |
| TCP | 44818 |
| UDP | 44818 |
## ubuntu_XE1000.2.0.1.tar.gz
#### Disk/Storage usage in Gateway
| space stat. | size (MB) |
|--|--|
| tarball size | 272MB |
| total file size | 938MB |
| used space | 1213MB |
| free space | 986MB |
#### OS and Tools
| soft info | version |
|--|--|
| Ubuntu| 20.04.2 LTS |
| dotnet | 3.1.16 |
| gcc | 9.3.0-17ubuntu1~20.04 |
| g++ | 9.3.0-17ubuntu1~20.04 |
| nodejs | 10.19.0~dfsg-3ubuntu1 |
| python2 | 2.7.18 |
| python3 | 3.8.5 |
#### Python3 libs
| pip3 | version |
|--|--|
| dbus-python | 1.2.16 |
| netifaces | 0.10.4 |
| pip | 20.0.2 |
| PyGObject | 3.36.0 |
| 0.13.0 | pymacaroons |
| PyNaCl | 1.3.0 |
| PyYAML | 5.3.1 |
| setuptools | 45.2.0 |
| six | 1.14.0 |
| ubuntu-advantage-tools | 20.3 |
| wheel | 0.34.2 |
## ubuntu_XE1000.2.0.7.tar.gz
From [ubuntu_XE1000.2.0.1](README.md#ubuntu_xe1000201targz)
#### Disk/Storage usage in Gateway
| space stat. | size (MB) |
|--|--|
| tarball size | 229MB |
| total file size | 739MB |
| used space | 971MB |
| free space | 1272MB |
#### OS and Tools
| soft info | version |
|--|--|
| Ubuntu| 20.04.6 LTS |
| bluez | 5.53-0ubuntu3.6 |
| aspnetcore-runtime | 6.0.21 |

## ubuntu_XE1000.2.0.8.tar.gz
#### Disk/Storage usage in Gateway
| space stat. | size (MB) |
|--|--|
| tarball size | 159MB |
| total file size | 551MB |
| used space | 712MB |
| free space | 1486MB |
#### OS and Tools
| soft info | version |
|--|--|
| Ubuntu| 20.04.6 LTS |
| dotnet | N/A |
| nodejs | N/A |
| python2 | 2.7.18 |
| python3 | 3.8.10 |
## ubuntu_XE1000.2.0.10.tar.gz
#### Disk/Storage usage in Gateway
| space stat. | size (MB) |
|--|--|
| tarball size | 191MB |
| total file size | 640MB |
| used space | 833MB |
| free space | 1365MB |
#### OS and Tools
| soft info | version |
|--|--|
| Ubuntu| 20.04.6 LTS |
| bluetooth | 5.53-0ubuntu3.8 |
| bluez-tools | 2.0~20170911.0.7cb788c-2build1 |
| python2 | 2.7.18 |
| python3 | 3.8.10 |
## ubuntu_XE1000.2.0.11.tar.gz
From [ubuntu_XE1000.2.0.8](README.md#ubuntu_xe1000208targz)
#### Disk/Storage usage in Gateway
| space stat. | size (MB) |
|--|--|
| tarball size | 193MB |
| total file size | 646MB |
| used space | 849MB |
| free space | 1349MB |
#### OS and Tools
| soft info | version |
|--|--|
| Ubuntu| 20.04.6 LTS |
| batctl | 2019.5-1 |
| bluetooth | 5.53-0ubuntu3.8 |
| bluez-tools | 2.0~20170911.0.7cb788c-2build1 |
| i2c-tools | 4.1-2build2 |
| iptables | 1.8.4-3ubuntu2.1 |
| jq | 1.6-1ubuntu0.20.04.1 |
| libbluetooth3 | 5.53-0ubuntu3.8 |
| libsnappy1v5 | 1.1.8-1build1 |
| libubootenv-tool | 0.2-1 |
| rinetd | 0.62.1sam-1.1 |
| s6 | 2.9.0.1-2 |
| screen | 4.8.0-1ubuntu0.1 |
| tinc | 1.0.36-1 |
| unzip | 6.0-25ubuntu1.2 |
## ubuntu_XE1000.2.2.0.tar.gz (preview)
#### Disk/Storage usage in Gateway
| space stat. | size (MB) |
|--|--|
| tarball size | 161MB |
| total file size | 454MB |
| used space | 563MB |
| free space | 1582MB |
#### OS and Tools
| soft info | version |
|--|--|
| Ubuntu | 22.04.4 LTS |
| dotnet | 8.0.4cassia1 |
| nodejs | N/A |
| python2 | N/A |
| python3 | 3.10.12-1~22.04.3 |
## ubuntu_XE1000.2.2.1.tar.gz (preview)
#### Disk/Storage usage in Gateway
| space stat. | size (MB) |
|--|--|
| tarball size | 229MB |
| total file size | 713MB |
| used space | 949MB |
| free space | 1250MB |
#### OS and Tools
| soft info | version | footprint | uninstall |
|--|--|--|--|
| Ubuntu | 22.04.5 LTS | N/A | N/A |
| bluetooth | 5.64-0ubuntu1.3 | N/A | N/A |
| bluez-tools | 2.0~20170911.0.7cb788c-4 | N/A | N/A |
| dotnet | 8.0.4cassia1 | 88MB | dpkg -P dotnet |
| libbluetooth3 | 5.64-0ubuntu1.3 | N/A | N/A |
| nodejs | 20.11.1cassia1 | 159MB | dpkg -P nodejs libatomic1  |
| python3 | 3.10.12-1~22.04.3 | N/A | N/A |
| python3-pip | 22.0.2+dfsg-1ubuntu0.5 | 23MB | dpkg -P python3-wheel python3-setuptools python3-pip<br>dpkg -P python3-pkg-resources ca-certificates<br>dpkg -P python3-distutils python3-lib2to3 |
| rinetd | 0.62.1sam-1.1 | N/A | N/A |
| unzip | 6.0-26ubuntu3.2 | N/A | N/A |
## ubuntu_XE1000.2.2.2.tar.gz(1.22.x)
#### Disk/Storage usage in Gateway
| space stat. | size (MB) |
|--|--|
| tarball size | 275MB |
| total file size | 828MB |
| used space | 1106MB |
| free space | 1092MB |
#### OS and Tools
| soft info | version |
|--|--|
| Ubuntu 22.04.5 LTS |
| gcc | 11.4.0-1ubuntu1~22.04.2 |
| g++ | 11.4.0-1ubuntu1~22.04.2 |
| python3.10 | 3.10.12-1~22.04.11 |
| python3.13 | 3.13.7-1+jammy1 |
#### Python3 libs
| pip3 | version |
|--|--|
| aiofiles | 24.1.0 |
| aiohappyeyeballs | 2.6.1 |
| aiohttp | 3.12.15 |
| aiohttp-sse-client | 0.2.1 |
| aiosignal | 1.4.0 |
| aiosqlite | 0.17.0 |
| attrs | 25.3.0 |
| cffi | 2.0.0 |
| cryptography | 46.0.1 |
| dbus-python | 1.2.18 |
| frozenlist | 1.7.0 |
| gmqtt | 0.6.8 |
| idna | 3.10 |
| iniconfig | 2.1.0 |
| multidict | 6.6.4 |
| netifaces | 0.11.0 |
| packaging | 25.0 |
| pip | 25.2 |
| pluggy | 1.6.0 |
| propcache | 0.3.2 |
| protobuf | 6.31.1 |
| pycairo | 1.28.0 |
| pycparser | 2.23 |
| pydbus | 0.6.0 |
| PyGObject |  3.54.2 |
| pytest | 8.2.0 |
| pytest-asyncio | 0.20.3 |
| PyYAML | 6.0.2 |
| setuptools | 59.6.0 |
| typing_extensions | 4.15.0 |
| urllib3 | 2.5.0 |
| wirepas_mesh_messaging | 1.3.0rc3 |
| yarl | 1.20.1 |
## Ubuntu Container APP
### use bluez
[customize bluez](bluez_dbus.md)
### python3-pip
[customize whl](python3_pip.md)
### dpkg
[customize deb](dpkg_deb.md)
### Node.js
#### AWS SDK for JavaScript
**a, Install and Run ubuntu_XE1000.2.0.1**  
**b, Check Node.js version**  
```
# dpkg -l nodejs
Desired=Unknown/Install/Remove/Purge/Hold
| Status=Not/Inst/Conf-files/Unpacked/halF-conf/Half-inst/trig-aWait/Trig-pend
|/ Err?=(none)/Reinst-required (Status,Err: uppercase=bad)
||/ Name           Version                 Architecture Description
+++-==============-=======================-============-==================================================
ii  nodejs         10.19.0~dfsg-3ubuntu1.6 armhf        evented I/O for V8 javascript - runtime executable
```
**c, Install and Check NPM version**  
```
# dpkg -l npm
Desired=Unknown/Install/Remove/Purge/Hold
| Status=Not/Inst/Conf-files/Unpacked/halF-conf/Half-inst/trig-aWait/Trig-pend
|/ Err?=(none)/Reinst-required (Status,Err: uppercase=bad)
||/ Name           Version            Architecture Description
+++-==============-==================-============-=================================
ii  npm            6.14.4+ds-1ubuntu2 all          package manager for Node.js
```
**d, Install aws-sdk**  
```
# npm install aws-sdk
# npm list --depth=0  
/root
`-- aws-sdk@2.1621.0
```
See also [AWS SDK](https://www.npmjs.com/package/aws-sdk)
