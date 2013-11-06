import RPi.GPIO as GPIO
from . import AbstractDoor
from ..models import SQLAlchemyBinding


class RPiDoor(SQLAlchemyBinding, AbstractDoor):

    GREEN = 23
    RED = 24
    DOOR = 25
    BUTTON = 17

    def __init__(self, *args, **kwargs):

        GPIO.setmode(GPIO.BCM)
        GPIO.setwarnings(False)

        GPIO.setup(self.GREEN, GPIO.OUT)
        GPIO.setup(self.RED, GPIO.OUT)
        GPIO.setup(self.DOOR, GPIO.OUT)
        GPIO.setup(self.BUTTON, GPIO.IN)

        super(RPiDoor, self).__init__(*args, **kwargs)

    @property
    def get_state(self):
        # pin 17 returns 1 when not pressed and 0 when pressed
        # ie: switch is "normally closed"
        return not GPIO.input(self.BUTTON)

    def unlock(self):
        GPIO.output(self.DOOR, GPIO.LOW)

    def lock(self):
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
