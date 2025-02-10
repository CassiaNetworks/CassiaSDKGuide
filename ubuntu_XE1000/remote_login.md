## Description  
The SSH remote login feature allows users to access containers deployed within a LAN through an AC server deployed on the public network. Its basic principle is SSH reverse proxy.  
The remote login is triggered through a button on the AC portal, requiring the Gateway to be in an online state. The Gateway actively initiates a reverse proxy request to the AC. Upon successful request, a new input box will pop up, prompting for the user's credentials. After successful authentication, the user will continue to access the Shell of the Container in a new browser window, with the green text "SSH CONNECTION ESTABLISHED" displayed in the lower left corner.  
## Trouble Shooting
### sshd: ssh3rd [priv]
When the gateway and AC successfully establish an SSH reverse proxy, a subprocess named "sshd: ssh3rd" will appear on the AC. This indicates that the SSH server has accepted a session from the user "ssh3rd".
### 0.0.0.0:8001 LISTEN
After the reverse proxy is successfully established, the SSH server on AC begins to LISTEN on port 8001.
### 127.0.0.1:8001 ESTABLISHED
When using the remote login function via a web page and successfully opening a browser window for the container shell, a connection to 127.0.0.1:8001 can be detected. This is because the local web process, node, serves as an SSH client accessing the container through the reverse proxy.
