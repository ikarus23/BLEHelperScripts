#!/bin/bash

if [ "$#" != "2" ]; then
  echo "Usage: $0 <address> <name>"
  echo "(This tool works only for Bluetooth classic.)"
  exit 1
fi

sudo systemctl stop bluetooth
sudo systemctl start bluetooth
sleep 2
sudo btmgmt -i hci0 public-addr "$1"
# sudo btmgmt -i hci0 name "$2"
bluetoothctl system-alias "$2"
bluetoothctl power on
bluetoothctl discoverable on