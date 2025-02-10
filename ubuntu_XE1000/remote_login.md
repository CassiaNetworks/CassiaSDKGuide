## Description  
The SSH remote login feature allows users to access containers deployed within a LAN through an AC server deployed on the public network. Its basic principle is SSH reverse proxy.  
The remote login is triggered through a button on the AC portal, requiring the Gateway to be in an online state. The Gateway actively initiates a reverse proxy request to the AC. Upon successful request, a new input box will pop up, prompting for the user's credentials. After successful authentication, the user will continue to access the Shell of the Container in a new browser window, with the green text "SSH CONNECTION ESTABLISHED" displayed in the lower left corner.  
## Trouble Shooting
### sshd: ssh3rd [priv]
```
root@cassia-ac:~# ps -ef | grep sshd
root         690       1  0  2024 ?        00:00:00 sshd: /usr/sbin/sshd -D [listener] 0 of 10-100 startups
root      983208     690  0 05:07 ?        00:00:00 sshd: ssh3rd [priv]
ssh3rd    983237  983208  0 05:07 ?        00:00:00 sshd: ssh3rd
root@cassia-ac:~# ps -ef | grep ssh3rd
root      983208     690  0 05:07 ?        00:00:00 sshd: ssh3rd [priv]
ssh3rd    983211       1  0 05:07 ?        00:00:00 /lib/systemd/systemd --user
ssh3rd    983212  983211  0 05:07 ?        00:00:00 (sd-pam)
ssh3rd    983237  983208  0 05:07 ?        00:00:00 sshd: ssh3rd
```
When the gateway and AC successfully establish an SSH reverse proxy, a subprocess named "sshd: ssh3rd" will appear on the AC. This indicates that the SSH server has accepted a session from the user "ssh3rd".
### 0.0.0.0:8001 LISTEN
```
root@cassia-ac:~# netstat -anpl | grep 8001 | grep LISTEN
tcp        0      0 0.0.0.0:8001            0.0.0.0:*               LISTEN      983237/sshd: ssh3rd 
tcp6       0      0 :::8001                 :::*                    LISTEN      983237/sshd: ssh3rd 
```
After the reverse proxy is successfully established, the SSH server on AC begins to LISTEN on port 8001.
### 127.0.0.1:8001 ESTABLISHED
```
root@cassia-ac:~# netstat -anpl | grep 127.0.0.1:8001
tcp        0      0 127.0.0.1:58198         127.0.0.1:8001          ESTABLISHED 918/node            
tcp        0      0 127.0.0.1:8001          127.0.0.1:58198         ESTABLISHED 983237/sshd: ssh3rd
```
When using the remote login function via a web page and successfully opening a browser window for the container shell, a connection to 127.0.0.1:8001 can be detected. This is because the local web process, node, serves as an SSH client accessing the container through the reverse proxy.
