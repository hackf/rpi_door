import serial
import RPi.GPIO as GPIO
import re
from . import AbstractDoor


class SerialConnectionError(Exception):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class RPiDoor(AbstractDoor):

    GREEN = 23
    RED = 24
    DOOR = 25
    BUTTON = 17
    # \\n.+\\r
    code_re = re.compile("\\n(.+)\\r", re.UNICODE)

    def __init__(self, *args, **kwargs):

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.GREEN, GPIO.OUT)
        GPIO.setup(self.RED, GPIO.OUT)
        GPIO.setup(self.DOOR, GPIO.OUT)
        GPIO.setup(self.BUTTON, GPIO.IN)

        super(RPiDoor, self).__init__(*args, **kwargs)

        self.serial_conn = serial.Serial("/dev/ttyAMA0", 2400, timeout=0)

        if not self.serial_conn.isOpen():
            raise SerialConnectionError("")

        #GPIO.output(channel, state) GPIO.HIGH/LOW

    def check_key_code(self, data):
        return True

    def check_lock_request(self):
        # pin 17 returns 1 when not pressed and 0 when pressed
        if not GPIO.input(self.BUTTON) and not self.check_for_codes:
            self.lock()

    def _read_RFID(self):
        self.ser.flushInput()
        data = b""

        while True:
            while self.serial_conn.inWaiting() > 0:
                data += self.serial_conn.read(1)

            if data:
                str_data = str(data, 'utf-8')
                match = re.match(self.code_re, str_data)
                if match:
                    return match.groups()[0]

    def unlock(self):
        super(RPiDoor, self).unlock()
        GPIO.output(self.DOOR, GPIO.LOW)

    def lock(self):
        super(RPiDoor, self).lock()
        GPIO.output(self.DOOR, GPIO.HIGH)

    def toggle_red_led(self, on=False):
        if on:
            GPIO.output(self.RED, GPIO.HIGH)
        else:
            GPIO.output(self.RED, GPIO.LOW)

    def toggle_green_led(self, on=False):
        if on:
            GPIO.output(self.GREEN, GPIO.HIGH)
        else:
            GPIO.output(self.GREEN, GPIO.LOW)
