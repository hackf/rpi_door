from unittest import TestCase
from unittest.mock import patch
from rpi_door.models import SQLAlchemyMixin
from rpi_door.drivers import AbstractDoor


class TestDoor(SQLAlchemyMixin, AbstractDoor):

    def __init__(self, *args, **kwargs):

        super(TestDoor, self).__init__(*args, **kwargs)


class BaseSuite(TestCase):

    def setUp(self):
        self.door = TestDoor(**{
            "sqlalchemy.url": "sqlite://",
            "sqlalchemy.echo": False,
            "sqlalchemy.pool_recycle": 3600
        })

    def tearDown(self):
        self.door.drop_db()

    def test_test(self):
        print(dir(self.door))
        self.door.main_loop()
