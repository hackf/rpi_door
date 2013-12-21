from unittest import TestCase
from unittest.mock import patch
from rpi_door.models import SQLAlchemyMixin
from rpi_door.drivers import AbstractDoor


class TestDoor(SQLAlchemyMixin, AbstractDoor):

    def __init__(self, *args, **kwargs):

        super(TestDoor, self).__init__(*args, **kwargs)

    def get_state(self):
        pass

    def unlock(self):
        pass

    def lock(self):
        pass

    def toggle_red_led(self, **kwargs):
        pass

    def toggle_green_led(self, **kwargs):
        pass


class MockRead():

    def __init__(self, data):
        self.data = data
        self.generator = self._generator()

    def _generator(self):
        byte_array = bytearray(self.data, "utf8")
        for i in range(len(byte_array)):
            yield byte_array[i:i + 1]

    def next_byte(self, *args):
        return next(self.generator)


class BaseSuite(TestCase):

    def patch_read(self, data):
        with patch("rpi_door.drivers.serial.Serial"):
            import serial
            ser = serial.Serial(0)
            ser.isOpen.return_value = True
            ser.inWaiting.return_value = 1
            ser.read = MockRead(data).next_byte
            self.door = TestDoor(**{
                "sqlalchemy.url": "sqlite://",
                "sqlalchemy.echo": False,
                "sqlalchemy.pool_recycle": 3600,
                "port": 0,
                "baudrate": None,
            })

    def create_user_and_key(self, code="12345"):
        from rpi_door.models import User, KeyCode

        with self.door.session_context() as session:
            user = User(first_name="Jimmy",
                        last_name="Heap",
                        email="jimmy.heap@test.com")
            key_code = KeyCode(code=code)
            user.key_code = key_code
            session.add(user)
            session.commit()

    def tearDown(self):
        if self.door:
            self.door.drop_db()

    def test_read_RFID(self):
        self.patch_read("\n12345\r\n67890\r")
        try:
            code = self.door.read_RFID()
        except StopIteration:
            raise RuntimeError("Read ran out of bytes")
        else:
            self.assertEqual(code, "12345")

    def test_continuos_read(self):
        self.patch_read("1234567890")
        self.assertRaises(StopIteration, self.door.read_RFID)
