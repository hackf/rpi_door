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

    code_re = re.compile("\\n(.+)\\r", re.UNICODE)

    def __init__(self, *args, **kwargs):

        port = kwargs.get("port", "/dev/ttyAMA0")
        baudrate = kwargs.get("baudrate", 2400)

        self.serial_conn = serial.Serial(port, baudrate, timeout=0)

        if not self.serial_conn.isOpen():
            raise SerialConnectionError("Serial connection couldn't be open.")

        # Makes sure the state of the door is locked when first started. This
        # is mostly for security reasons. For example, if the power goes out we
        # want to door to lock when the power comes back on. Trying to remember
        # the door's state in should events would be difficult and not worth
        # the effort.
        self.lock()
        self.toggle_red_led(on=True)

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, data):
        """Check to see if the data to be set is greater than 41. If so it sets
        itsself to an empty bytearray
        """
        if len(data) > 41:
            self._data = b""
        else:
            self._data = data
        return self._data

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
        """ Checks the given string to see if it contains a code (valid or not)

        Args:
            data (str): data to be checked

        Returns:
            None or str::
                None if there isn't a match or the code if there is a match

        """
        match = re.match(self.code_re, data)
        if match:
            return match.groups()[0]
        return None

    def read_RFID(self):
        """reads one byte at a time until it finds a key code
        """
        # flushes to remove any remaining bytes
        self.serial_conn.flushInput()
        self.data = b""

        while True:
            while self.serial_conn.inWaiting() > 0:
                self.data += self.serial_conn.read(1)

                if self.data:
                    str_data = str(self.data, 'utf-8')
                    code = self.find_key_code(str_data)
                    if code:
                        return code

    def check_for_lock_request(self):
        """continuously checks to see if the state is true. If so it calls the
        `lock` method
        """
        while True:
            sleep(0.1)
            if self.get_state():
                sleep(5)
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
