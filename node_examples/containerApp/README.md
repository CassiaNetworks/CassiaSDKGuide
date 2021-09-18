## sample for Cassia Router Container App
this example use Cassia Router API for scan, connect, collect notification from devices,
and send data to custom endpoint

to use this example:
  1. run package.sh under folder /containerApp (require node > 6 and npm)
  2. it will generate SampleApp.1.0.tar.gz under folder node_examples
  3. install SampleApp.1.0.tar.gz on Router Web page

## container custom config
1. place meta.json at /root/config/<app name>/(in app package) which defines config items
example:
{
    "name": "my app",
    "config_items" : [
      {"name": "param1", "type":"string", "require": true}
    ]
}

2. config parameters above on Router web page
3. after step 2, router will generate config.json file at /root/config/<app name>/config.json
example:
{
    "param1": "somestring"
}