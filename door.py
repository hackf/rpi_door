#!/usr/bin/python
from rpi_door.drivers.GPIO import RPiDoor

rpi_door = RPiDoor(**{
    "sqlalchemy.url": "sqlite://database.db",
    "sqlalchemy.echo": True,
    "sqlalchemy.pool_recycle": 3600
})

if __name__ == "__main__":
    rpi_door.main_loop()
