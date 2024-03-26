## BLE + bluez + ubuntu_XE1000.2.x.x
### switch BLE stack
### check option of dbus-daemon
please make sure the **"ExecStart"** in /lib/systemd/system/dbus.service is exactly same as **"/usr/bin/dbus-daemon --system  --nofork --nopidfile"**  
```
# cat /lib/systemd/system/dbus.service 
[Unit]
Description=D-Bus System Message Bus
Documentation=man:dbus-daemon(1)
Requires=dbus.socket
# we don't properly stop D-Bus (see ExecStop=), thus disallow restart
RefuseManualStart=yes

[Service]
ExecStart=/usr/bin/dbus-daemon --system  --nofork --nopidfile  
ExecReload=/usr/bin/dbus-send --print-reply --system --type=method_call --dest=org.freedesktop.DBus / org.freedesktop.DBus.ReloadConfig
ExecStop=/bin/true
KillMode=none
OOMScoreAdjust=-900
```
### check version of bluez
```
# dpkg -l bluez
Desired=Unknown/Install/Remove/Purge/Hold
| Status=Not/Inst/Conf-files/Unpacked/halF-conf/Half-inst/trig-aWait/Trig-pend
|/ Err?=(none)/Reinst-required (Status,Err: uppercase=bad)
||/ Name           Version         Architecture Description
+++-==============-===============-============-=================================
ii  bluez          5.53-1cassia3.7 armhf        Bluetooth tools and daemons
```
### update bluez up to newest
```
# dpkg -P bluez
# dpkg -i 
```
