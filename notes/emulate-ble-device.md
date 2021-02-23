Emulate a BLE Peripheral (Setup a GATT Server)
==============================================

This document aims to help you with setting up a custom GATT server. The approach is to simulate/emulate
a known device. This might trick e.g. a mobile app to connect to your device instead of the original device.

This approch and the used commands were tested using Arch Linux and BlueZ 5.55-3.



Steps to emulate a BLE Device
-----------------------------

* Starting the Bluetooth service.  
  `sudo systemctl start bluetooth`
* Change the Bluetooth address to match the official device.  
  `sudo btmgmt --index hci0 public-addr 00:11:22:33:44:55`
* Run the interactive `bluetoothctl` programm for further configuration.  
* Power on the Bluetooth controller.  
  `power on`
* Enter the sub-menu for GATT configuration.  
  `menu gatt`
* Register a service you want to emulate.  
  `register-service 00001234-0000-1000-8000-00805f9b34fb`
* Register a characteristic you want to emulate.  
  `register-characteristic 00005678-0000-1000-8000-00805f9b34fb read,write`
* Register the profile.  
  `register-application 00001234-0000-1000-8000-00805f9b34fb`
* (Register more services, characteristics, descriptors, etc. The `clone` command might also be helpful.)
* Go back to the main menu of `bluetoothctl`.  
  `back`
* Enter the sub-menu for advertisement configuration.  
  `menu advertise`
* Set the name to match the original device.  
  `name "Some Device"`
* Set the the manufacturer data (if there are any) to match the original device.  
  `manufacturer 0xffff 0x01 0x02 0x03 0x04 0x05`
* (Configure more advertisement specific data if needed.)
* Go back to the main menu of `bluetoothctl`.  
  `back`
* Enable advertisement.  
  `advertise on`



Output
------

If e.g. a mobile app connects to your emulated devices and writes data to a characteristic you will see it in the
output of `bluetoothctl` in hex and ASCII representation.

```
[NEW] Device AA:BB:CC:DD:EE:FF AA-BB-CC-DD-EE-FF
[/org/bluez/app/service0/chrc0 (Unknown)] WriteValue: AA:BB:CC:DD:EE:FF offset 0 link LE
  33 30 38 35 37 38  308578
[CHG] Device AA:BB:CC:DD:EE:FF Connected: no
```

