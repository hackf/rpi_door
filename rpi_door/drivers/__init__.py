# Copyright (C) 2013 Windsor Hackforge
#
# This module is part of RPi Door and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

import re
import serial
from time import sleep


class SerialConnectionError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class AbstractDoor():

    # \\n.+\\r
    code_re = re.compile("\\n(.+)\\r", re.UNICODE)

    def __init__(self, *args, **kwargs):

        port = kwargs.get("port", "/dev/ttyAMA0")
        baudrate = kwargs.get("baudrate", 2400)

        self.serial_conn = serial.Serial(port, baudrate, timeout=0)

        if not self.serial_conn.isOpen():
            raise SerialConnectionError("Serial connection couldn't be open.")

        self.lock()
        self.toggle_red_led(on=True)

    def main_loop(self):
        while True:
            data = self.read_RFID()
            if data and self.validate_key_code(data):
                self.toggle_red_led()
                self.toggle_green_led(on=True)
                self.unlock()
                sleep(1)
                self.toggle_red_led(on=True)
                self.toggle_green_led()
                self.check_for_lock_request()

    def find_key_code(self, data):
        match = re.match(self.code_re, data)
        if match:
            return match.groups()[0]
        return None

    def read_RFID(self):
        # flushes to remove any remaining bytes
        self.serial_conn.flushInput()
        data = b""

        while True:
            while self.serial_conn.inWaiting() > 0:
                data += self.serial_conn.read(1)

                if data:
                    str_data = str(data, 'utf-8')
                    code = self.find_key_code(str_data)
                    if code:
                        return code
                    if len(data) > 30:
                        data = b""

    def check_for_lock_request(self):
        while True:
            sleep(0.1)
            if self.get_state():
                sleep(30)
                self.lock()
                break

    def get_state(self):
        raise NotImplementedError("Not implemented.")

    def validate_key_code(self, data):
        raise NotImplementedError("Not implemented.")

    def unlock(self):
        raise NotImplementedError("Not implemented.")

    def lock(self):
        raise NotImplementedError("Not implemented.")

    def toggle_red_led(self, on=False):
        raise NotImplementedError("Not implemented.")

    def toggle_green_led(self, on=False):
        raise NotImplementedError("Not implemented.")
