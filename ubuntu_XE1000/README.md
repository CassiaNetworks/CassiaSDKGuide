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
| tarball size | 229B |
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
| rinetd | 0.62.1sam-1.1 | N/A | N/A |
| unzip | 6.0-26ubuntu3.2 | N/A | N/A |
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

