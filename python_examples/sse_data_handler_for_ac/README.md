## SSE Stream Handler for Scanned Advertisement Data Packets using AC Managed Mode

Please make sure to run:

pip install -r requirements.txt


## Obtaining the access_token for AC RESTful API Requests
Since the Cassia RESTful API on AC Managed Mode requires communication to the AC, an access_token is needed per API call.

Please follow the instructions in this following link to generate an access_token: <br>
[Access Cassia Router through the Cassia AC](https://github.com/CassiaNetworks/CassiaSDKGuide/wiki/Getting-Started#access-cassia-router-through-the-cassia-ac)

**NOTE**: The access_token expires every 60 minutes (1 hour). Be sure to handle the expiration by generating the token every hour.