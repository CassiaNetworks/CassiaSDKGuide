## BLE + bluez + ubuntu_XE1000.2.x.x
### switch BLE stack
### check option of dbus-daemon
please make sure the **"ExecStart"** in /lib/systemd/system/dbus.service is exactly same as **"/usr/bin/dbus-daemon --system  --nofork --nopidfile"**
'''
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
'''

### check version of bluez
