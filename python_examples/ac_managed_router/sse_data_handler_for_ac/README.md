## SSE Stream Handler for Scanned Advertisement Data Packets using AC Managed Mode

### About
This is an example Python program to handle the SSE stream from the Standalone (Local) [Scan API](https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/RESTful-API#scan-bluetooth-devices). 


The program will generate a text file called example_output.txt in the same directory as main.py.
The file will contain a list of adData values on each line.


Please make sure to run:

pip install -r requirements.txt


## Obtaining the access_token for AC RESTful API Requests
Since the Cassia RESTful API on AC Managed Mode requires communication to the AC, an access_token is needed per API call.

Please follow the instructions in this following link to generate an access_token: <br>
[Access Cassia Router through the Cassia AC](https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/Getting-Started#access-cassia-router-through-the-cassia-ac)

**NOTE**: The access_token expires every 60 minutes (1 hour). Be sure to handle the expiration by generating the token every hour.