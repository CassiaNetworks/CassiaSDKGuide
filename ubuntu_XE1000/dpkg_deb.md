`DEBNAME=hello-ble && mkdir -p  /$DEBNAME/{build,extract/DEBIAN}`
**b, copy your bin file to extract/usr/bin , etc file to extrack/etc , lib file (*.so) to extract /usr/lib**
**c, prepare an empty control file**
`touch extract/DEBIAN/control`
**d, edit control file**
```
package: hello-ble
version: 1.2cassia1
architecture: armhf
Maintainer: Cassia Developers <cassia-dev@cassianetworks.com>
Homepage: http://nodejs.org/
Description: this is a demo
```
**e, build your deb package in dir hello-ble and you could find it in dir build**
the structure of hello-ble should like below:
```
hello-ble/
|-- build
|   `-- hello-ble_1.2cassia1_armhf.deb
`-- extract
    |-- DEBIAN
    |   `-- control
    |-- etc
    |   `-- hello-ble.conf
    `-- usr
        |-- bin
        |   |-- hello-ble
        |   |-- hello-ble.py
        |   `-- hello-ble.sh
        `-- lib
            `-- hello-ble.so
