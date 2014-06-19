#!/usr/bin/python
from rpi_door.GPIO import RPiDoor

rpi_door = RPiDoor(**{
    "sqlalchemy.url": "sqlite:///database.db",
    "sqlalchemy.echo": False,
    "sqlalchemy.pool_recycle": 3600
})

if __name__ == "__main__":
    rpi_door.main_loop()
