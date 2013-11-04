#!/bin/python
from rpi_door.drivers.GPIO import RPiDoor
import getpass

print(getpass.getuser())
rpi_door = RPiDoor()

if __name__ == "__main__":
    rpi_door.main_loop()
