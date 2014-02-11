from unittest import TestCase
from unittest.mock import patch
from testfixtures import ShouldRaise
from rpi_door.models import SQLAlchemyMixin
from rpi_door.drivers import AbstractDoor


class TestDoor(SQLAlchemyMixin, AbstractDoor):

    def __init__(self, *args, **kwargs):

        super(TestDoor, self).__init__(*args, **kwargs)

    def get_state(self):
        return True

    def unlock(self):
        pass

    def lock(self):
        pass

    def toggle_red_led(self, **kwargs):
        pass

    def toggle_green_led(self, **kwargs):
        pass


class NotImplementedTestDoor(AbstractDoor):

    def __init__(self, *args, **kwargs):
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

    def setUp(self):
        self.door = None

    def patch_serial_read(self, data):
        """ Patches serial.Serial so that so serial connection is required for
        testing. `Serial.isOpen` is set to True, `Serial.inWaiting` always
        returns 1, and `Serial.read` is a generator that returns one byte at a
        time (from a give string). This allows to fully control what data is
        read and procressed."""

        with patch("rpi_door.drivers.serial.Serial"):
            import serial

            ser = serial.Serial(0)
            ser.isOpen.return_value = True
            ser.inWaiting.return_value = 1
            ser.read = MockRead(data).next_byte

            # TestDoor needs to be called within the patch so that the patched
            # `serial.Serial` object is used instead.
            self.door = TestDoor(**{
                "sqlalchemy.url": "sqlite://",
                "sqlalchemy.echo": False,
                "sqlalchemy.pool_recycle": 3600,
                "port": 0,
                "baudrate": None,
            })

    def tearDown(self):
        if self.door:
            self.door.drop_db()

    def test_serial_connection_error(self):
        with patch("rpi_door.drivers.serial.Serial"):
            import serial
            from rpi_door.drivers import SerialConnectionError

            ser = serial.Serial(0)
            ser.isOpen.return_value = False

            with ShouldRaise(SerialConnectionError):
                self.door = TestDoor(**{
                    "sqlalchemy.url": "sqlite://",
                    "sqlalchemy.echo": False,
                    "sqlalchemy.pool_recycle": 3600,
                })

    def test_read_RFID(self):
        """ Tests to make sure the code is found within the give string.
        A valid code matches \\n(.+)\\r """
        self.patch_serial_read("\n12345\r\n67890\r")
        try:
            code = self.door.read_RFID()
        except StopIteration:
            raise RuntimeError("Read ran out of bytes")
        else:
            self.assertEqual(code, "12345")

    def test_continuos_read(self):
        self.patch_serial_read("1234567890")
        self.assertRaises(StopIteration, self.door.read_RFID)

    def test_data_property(self):
        self.patch_serial_read("")
        self.door.data = bytearray(range(50))
        self.assertEquals(self.door.data, b"")
        data = bytearray(range(30))
        self.door.data = data
        self.assertEquals(self.door.data, data)
        self.door.data += bytearray(range(20))
        self.assertEquals(self.door.data, b"")


class TestSQLAlchemyMixin(TestCase):

    def setUp(self):
        self.configuration = {
            "sqlalchemy.url": "sqlite://",
            "sqlalchemy.echo": False,
            "sqlalchemy.pool_recycle": 3600,
        }

    def test_sqlalchemyminxin_init_stack(self):
        from rpi_door.models import SQLAlchemyMixin

        class TestClass():

            def __init__(self, *args, **kwargs):
                self.numbers += 5

        class MixinTest(SQLAlchemyMixin, TestClass):

            def __init__(self, *args, **kwargs):
                self.numbers = 5
                super(MixinTest, self).__init__(*args, **kwargs)

        sqlmixin = MixinTest(**self.configuration)
        sqlmixin.init_db()

        from rpi_door.models import User

        print(User.query.all())

        self.assertEquals(sqlmixin.numbers, 10)

        sqlmixin.drop_db()

    def create_user_and_key(self, sqla_instance, **kwargs):
        from rpi_door.models import User, KeyCode

        first_name = kwargs.get('first_name', 'Jimmy')
        last_name = kwargs.get('last_name', 'Heaps')
        email = kwargs.get('email', 'jimmy.heaps@fakeaddress.org')

        code = kwargs.get('code', '12345')
        enabled = kwargs.get('enabled', True)

        with sqla_instance.session_context() as session:
            user = User(first_name=first_name,
                        last_name=last_name,
                        email=email)
            key_code = KeyCode(code=code, enabled=enabled)
            user.key_code = key_code
            session.add(user)
            session.commit()

    def test_validate_key_code(self):
        from rpi_door.models import SQLAlchemyMixin

        sqlmixin = SQLAlchemyMixin(**self.configuration)
        sqlmixin.init_db()

        # use defaults for the first user save for the code
        user_one = {
            'code': '12345'
        }

        self.create_user_and_key(sqlmixin, **user_one)

        user_two = {
            'first_name': "Derpina",
            'last_name': "Derps",
            'email': "derpina.derps@fakeaddress.org",
            'code': '67890',
            'enabled': False,
        }

        self.create_user_and_key(sqlmixin, **user_two)

        self.assertTrue(sqlmixin.validate_key_code(user_one['code']))

        self.assertFalse(sqlmixin.validate_key_code(user_two['code']))

        sqlmixin.drop_db()
