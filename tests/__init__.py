from unitcase import TestCase
from rpi_door.drivers import AbstractDoor
from rpi_door.models import init_db, drop_db, SQLAlchemyMixin


class BaseSuite(TestCase):

    def setUp(self):
        init_db()

    def tearDown(self):
        drop_db()


class TestDoor(AbstractDoor, SQLAlchemyMixin):

    def __init__(self, *args, **kwargs):
        super(TestDoor, self).__init__(*args, **kwargs)

    def check_for_lock_request(self):
        pass

    def read_RFID(self):
        pass

    def unlock(self):
        pass

    def lock(self):
        pass

    def toggle_red_led(self):
        pass

    def toggle_green_led(self):
        pass
