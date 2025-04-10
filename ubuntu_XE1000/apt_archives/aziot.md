## aziot offical source
https://github.com/Azure/azure-iotedge/releases  
https://learn.microsoft.com/en-us/azure/iot-edge/how-to-provision-single-device-linux-symmetric?tabs=azure-portal%2Cubuntu#install-iot-edge
## ubuntu_XE1000_2.0.x (Ubuntu 20)
```
# apt-get update
# apt-get install -y wget libtss2-esys0 psmisc
# wget https://packages.microsoft.com/config/ubuntu/20.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
# dpkg -i packages-microsoft-prod.deb
# apt-get update
# apt-get install -y moby-engine
# wget --no-check-certificate https://github.com/Azure/azure-iotedge/releases/download/1.5.16/aziot-identity-service_1.5.5-1_ubuntu20.04_armhf.deb
# wget --no-check-certificate https://github.com/Azure/azure-iotedge/releases/download/1.5.16/aziot-edge_1.5.16-1_ubuntu20.04_armhf.deb
# dpkg -i aziot-identity-service_1.5.5-1_ubuntu20.04_armhf.deb
# dpkg -i aziot-edge_1.5.16-1_ubuntu20.04_armhf.deb
```
## ubuntu_XE1000_2.2.x (Ubuntu 22)
```
# apt-get update
# apt-get install -y wget psmisc
# wget https://packages.microsoft.com/config/ubuntu/22.04/packages-microsoft-prod.deb -O packages-microsoft-prod.deb
# dpkg -i packages-microsoft-prod.deb
# apt-get update
# apt-get install -y moby-engine

# apt-get install -y libtss2-esys-3.0.2-0 libtss2-mu0 libtss2-rc0 libtss2-sys1 libtss2-tcti-cmd0 libtss2-tcti-device0 libtss2-tcti-mssim0 libtss2-tcti-swtpm0 libtss2-tctildr0 tpm-udev
# wget --no-check-certificate https://packages.microsoft.com/debian/12/prod/pool/main/a/aziot-edge/aziot-edge_1.5.16-1_armhf.deb
# wget --no-check-certificate https://packages.microsoft.com/debian/12/prod/pool/main/a/aziot-identity-service/aziot-identity-service_1.5.5-1_armhf.deb
# dpkg -i aziot-identity-service_1.5.5-1_armhf.deb
# dpkg -i aziot-edge_1.5.16-1_armhf.deb
```
