#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright 2020 Gerhard Klostermeier (@iiiikarus)
#
# Edit this scirpt to your needs. Right now it does:
# * Search for close by BLE devices (MINIMUM_RSSI).
# * Connect to close devices.
# * Discover the characteristics of the device.
# * Search for specific characteristics. If they are not there, disconnect.
# * Subscribes to characteristics for notifications.
# * Send data to a characteristic.
# * Wait for responses in the form of notifications.
#
# If the client (the device you connect to) want to initiale pairing/bonding,
# please make your bluetooth agent accepts all requests. This can be done by:
# * (Un-pair if allready paired via "bluetoothctl remove <client-MAC>".)
# * bluetoothctl agent off
# * bluetoothctl agent NoInputNoOutput
# * bluetoothctl default-agent
#
# Short UUID format:
# BLE base UUID: 00000000-0000-1000-8000-00805F9B34FB
# BLE UUID abcd: 0000abcd-0000-1000-8000-00805F9B34FB
#
# License:
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
# MA 02110-1301, USA.


from time import sleep
from os import system
from threading import Thread
from bluepy.btle import Scanner, Peripheral, DefaultDelegate, BTLEManagementError, ADDR_TYPE_RANDOM, ADDR_TYPE_PUBLIC


# Config.
SCAN_TIME = 3.0         # Time to search for close by devices.
MINIMUM_RSSI = -70      # Minimum signal strength of devices.
CONNECTION_TIMOUT = 5   # Timout if connection fails.
BT_INTERFACE_INDEX = 0  # 0 = /dev/hci0, 1 = /dev/hci1, etc.
DEBUG = True            # Show debug output.


def main(args):
    log("[*] Setting up bluetoothctl")
    system("bluetoothctl power on")
    # Setup bluetoothctl to accept any paring initialted by the client.
    # (It might be necessary to "bluetoothctl remove <MAC>".)
    # TODO: This is not working yet. Maybe because of an agent conflict.
    #system("bluetoothctl agent off")
    #system("bluetoothctl agent NoInputNoOutput")
    #system("bluetoothctl default-agent")

    try:
        devices = scan()
        for dev in devices:

            # Is device close enough?
            if dev.rssi < MINIMUM_RSSI:
                continue

            # Connect (address type might need chainging).
            peripheral = connect(dev, ADDR_TYPE_PUBLIC)
            if peripheral is None:
                continue

            # Discover everything. Some devices need this before we can search for e.g. a characteristic.
            discover_device(peripheral)

            # Find characteristic.
            characteristic = get_characteristic(peripheral,
                                                "0000abcd-0000-1000-8000-00805F9B34FB",
                                                "00001234-0000-1000-8000-00805F9B34FB")
            if characteristic is None:
                peripheral.disconnect()
                continue

            # Subscribe for notifications on characteristic.
            subscribe_to_characteristic(peripheral,
                                        "0000abcd-0000-1000-8000-00805F9B34FB",
                                        "00001234-0000-1000-8000-00805F9B34FB")

            # Send data.
            data = ["00112233445566778899",
                    "aabbccddeeff",
                    "a1a2a3a4a5",
                    "deadbeef",
                    "foodbabe"]
            for packet in data:
                packet = bytes.fromhex(packet)
                write_data(characteristic, packet)

            # Wait for 10 notifications (or 2.5 seconds)..
            log("[*] Waiting for notifications...")
            for i in range(10):
                peripheral.waitForNotifications(0.25)

            # Send more data.
            packet = bytes.fromhex("a0b1c3e4f5")
            write_data(characteristic, packet)

            # Stay connected and wait for notifications.
            while True:
                peripheral.waitForNotifications(0.25)

    except KeyboardInterrupt:
        print("")
        log("[*] Disconnecting.")
        peripheral.disconnect()
        log("[*] Shutting down.")
    except BTLEManagementError as ex:
        # Might be triggered because your OS shuts down the power to the BLE controller.
        log("[-] Bluetooth interface is powered down.", True)
        raise ex
    return 0


# ----------------------------------------------------------------------------------------------------------------------


# Show output if DEBUG is True.
def log(text, force=False):
    if DEBUG or force:
        print(text)


# Scan for BLE devices for SCAN_TIME seconds.
def scan():
    scanner = Scanner(BT_INTERFACE_INDEX)
    log(f"[*] Starting scanner for {SCAN_TIME} seconds.")
    devices = scanner.scan(SCAN_TIME)
    log(f"[*] Scan finished. Found {len(devices)} devices.")
    return devices


# Global variable for connecting. Yes, I know it's ugly...
connection_error = False

# Connect to addr using peripheral (will be called in a thread).
def connect_peripheral(peripheral, addr, addr_type):
    global connection_error
    try:
        peripheral.connect(addr, addr_type)
    except:
        connection_error = True


# Connect.
def connect(dev, addr_type):
    try:
        log(f"[*] Connecting to {dev.addr}.")
        peripheral = Peripheral(iface=BT_INTERFACE_INDEX)
        connection_error = False
        # Ugly hack to control the connection timout (only possible with threads).
        thread = Thread(target=connect_peripheral, args=[
                        peripheral, dev.addr, addr_type])
        thread.start()
        thread.join(CONNECTION_TIMOUT)
        if thread.is_alive() or connection_error:
            raise Exception()
        log(f"[*] Connected to {dev.addr}.")
        return peripheral
    except KeyboardInterrupt:
        raise
    except:
        try:
            peripheral.disconnect()
        except:
            pass
        log("[-] Could not connect.")
        return None


# Discovery services, characteristics and descriptors.
def discover_device(peripheral):
    peripheral.getServices()
    peripheral.getCharacteristics()
    peripheral.getDescriptors()


# Search for services and characteristic.
def get_characteristic(peripheral, service_uid, characteristic_uid):
    log(("[*] Searching for service/characteristic:"
         f"\n    {service_uid}\n    {characteristic_uid}"))
    try:
        service = peripheral.getServiceByUUID(service_uid)
        characteristics = service.getCharacteristics(characteristic_uid)
        characteristic = characteristics[0]
        log("[*] Characteristic found.")
        return characteristic
    except:
        log("[-] Service or characteristic not found.")
        return None


# Write data.
def write_data(characteristic, data):
    try:
        log(("[*] Writing data to handle "
             f"0x{characteristic.getHandle():04x}."))
        characteristic.write(data)
        # Sleep is needed if the device was already paired (e.g. to a mobile phone) before.
        # Without the sleep the file will not be saved. I don't know why...
        sleep(0.1)
        return True
    except:
        log("[-] Error on writing.")
        return False


# Subscribe to notification.
def subscribe_to_characteristic(peripheral, service_uid, characteristic_uid):
    # Get characteristic.
    characteristic = get_characteristic(
        peripheral, service_uid, characteristic_uid)
    if characteristic is None:
        log("[-] Error subscribing to characteristic.")
        return False
    # Get Client Characteristic Configuration descriptor.
    descriptor = characteristic.getDescriptors()[0]
    # TODO: Check if there is a descriptor.
    # Write to descriptor.
    try:
        log("[*] Trying to subscribe to characteristic.")
        descriptor.write(b'\x01\x00')
    except:
        log("[-] Error subscribing to characteristic.")
        return False
    peripheral.setDelegate(NotificationDelegate(None))
    log("[*] Subscribed to characteristic.")
    return True


class NotificationDelegate(DefaultDelegate):
    def __init__(self, params):
        DefaultDelegate.__init__(self)

    def handleNotification(self, cHandle, data):
        print(f"[*] Notification from handle {cHandle:04x}: {data.hex()}")


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
