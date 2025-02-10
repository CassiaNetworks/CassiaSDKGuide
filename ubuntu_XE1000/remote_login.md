## Description  
The SSH remote login feature allows users to access containers deployed within a LAN through an AC server deployed on the public network. Its basic principle is SSH reverse proxy.  
The remote login is triggered through a button on the AC portal, requiring the Gateway to be in an online state. The Gateway actively initiates a reverse proxy request to the AC. Upon successful request, a new input box will pop up, prompting for the user's credentials. After successful authentication, the user will continue to access the Shell of the Container in a new browser window, with the green text "SSH CONNECTION ESTABLISHED" displayed in the lower left corner.  
## Trouble Shooting
### sshd: ssh3rd [priv]
### 0.0.0.0:8001 LISTEN
### 127.0.0.1:8001 ESTABLISHED
