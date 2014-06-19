from unittest import TestCase
from unittest.mock import patch
from testfixtures import ShouldRaise
from rpi_database.models import SQLAlchemyMixin
from rpi_door import AbstractDoor


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

        with patch("rpi_door.serial.Serial"):
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
        with patch("rpi_door.serial.Serial"):
            import serial
            from rpi_door import SerialConnectionError

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


class TestUser(TestCase):

    def setUp(self):
        self.configuration = {
            "sqlalchemy.url": "sqlite://",
            "sqlalchemy.echo": False,
            "sqlalchemy.pool_recycle": 3600,
        }

        from rpi_database.models import SQLAlchemyMixin, User, KeyCode

        self.sqlmixin = SQLAlchemyMixin(**self.configuration)
        self.sqlmixin.init_db()

        # use defaults for the first user save for the code

        self.user_data = {
            'first_name': "Derp",
            'last_name': "Derps",
            'email': "derp.derps@fakeaddress.org",
        }

        self.key_data = {
            'code': '67890',
            'enabled': False,
        }

        self.key = KeyCode(**self.key_data)
        self.user = User(**self.user_data)
        self.user.key_code = self.key

        with self.sqlmixin.session_context() as session:
            session.add(self.user)
            session.commit()

    def test_first_name(self):
        self.assertIsNotNone(self.user.first_name)
        self.assertEquals(self.user.first_name, self.user_data['first_name'])

    def test_last_name(self):
        self.assertIsNotNone(self.user.last_name)
        self.assertEquals(self.user.last_name, self.user_data['last_name'])

    def test_email(self):
        self.assertIsNotNone(self.user.email)
        self.assertEquals(self.user.email, self.user_data['email'])

    def test_unique_email(self):
        from rpi_database.models import User
        from sqlalchemy.exc import IntegrityError
        user = User(**self.user_data)
        with self.sqlmixin.session_context() as session:
            session.add(user)
            with ShouldRaise(IntegrityError):
                session.commit()

    def test_key_code(self):
        self.assertIsNotNone(self.user.key_code)
        self.assertEquals(self.user.key_code_id, 1)

    def tearDown(self):
        if self.sqlmixin:
            self.sqlmixin.drop_db()


class TestKeyCode(TestCase):

    def setUp(self):
        self.configuration = {
            "sqlalchemy.url": "sqlite://",
            "sqlalchemy.echo": False,
            "sqlalchemy.pool_recycle": 3600,
        }

        from rpi_database.models import SQLAlchemyMixin, KeyCode

        self.sqlmixin = SQLAlchemyMixin(**self.configuration)
        self.sqlmixin.init_db()

        # use defaults for the first user save for the code

        self.key_data = {
            'code': '67890',
            'enabled': False,
        }

        self.key = KeyCode(**self.key_data)

        with self.sqlmixin.session_context() as session:
            session.add(self.key)
            session.commit()

    def test_enabled(self):
        self.assertIsNotNone(self.key.code)
        self.assertEquals(self.key.enabled, self.key_data['enabled'])
        self.assertIsInstance(self.key.enabled, bool)

    def test_code(self):
        self.assertIsNotNone(self.key.code)
        self.assertEquals(self.key.code, self.key_data['code'])

    def test_code_unique(self):
        from rpi_database.models import KeyCode
        from sqlalchemy.exc import IntegrityError
        key = KeyCode(**self.key_data)
        with self.sqlmixin.session_context() as session:
            session.add(key)
            with ShouldRaise(IntegrityError):
                session.commit()

    def tearDown(self):
        if self.sqlmixin:
            self.sqlmixin.drop_db()


class TestSQLAlchemyMixin(TestCase):

    def setUp(self):
        self.configuration = {
            "sqlalchemy.url": "sqlite://",
            "sqlalchemy.echo": False,
            "sqlalchemy.pool_recycle": 3600,
        }

        self.sqlmixin = None

    def create_user_and_key(self, sqla_instance, **kwargs):
        from rpi_database.models import User, KeyCode

        first_name = kwargs.get('first_name', 'Derp')
        last_name = kwargs.get('last_name', 'Heaps')
        email = kwargs.get('email', 'derp.heaps@fakeaddress.org')

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

    def test_sqlalchemyminxin_init_stack(self):
        from rpi_database.models import SQLAlchemyMixin

        class TestClass():

            def __init__(self, *args, **kwargs):
                self.numbers += 5

        class MixinTest(SQLAlchemyMixin, TestClass):

            def __init__(self, *args, **kwargs):
                self.numbers = 5
                super(MixinTest, self).__init__(*args, **kwargs)

        self.sqlmixin = MixinTest(**self.configuration)
        self.sqlmixin.init_db()

        self.assertEquals(self.sqlmixin.numbers, 10)

    def test_validate_key_code(self):
        from rpi_database.models import SQLAlchemyMixin

        self.sqlmixin = SQLAlchemyMixin(**self.configuration)
        self.sqlmixin.init_db()

        # use defaults for the first user save for the code
        user_one = {
            'code': '12345'
        }

        self.create_user_and_key(self.sqlmixin, **user_one)

        user_two = {
            'first_name': "Derp",
            'last_name': "Derps",
            'email': "derp.derps@fakeaddress.org",
            'code': '67890',
            'enabled': False,
        }

        self.create_user_and_key(self.sqlmixin, **user_two)

        self.assertTrue(self.sqlmixin.validate_key_code(user_one['code']))

        self.assertFalse(self.sqlmixin.validate_key_code(user_two['code']))

    def test_create_user(self):
        from rpi_database.models import SQLAlchemyMixin, User

        self.sqlmixin = SQLAlchemyMixin(**self.configuration)
        self.sqlmixin.init_db()

        data = {
            'first_name': 'Derp',
            'last_name': 'Derps',
            'email': 'derp.derps@fakeaddress.org',
        }

        self.sqlmixin.create_user(data)
        user = User.query.filter_by(email=data['email']).one()
        self.assertIsNotNone(user)
        self.assertEquals(user.first_name, data['first_name'])
        self.assertEquals(user.last_name, data['last_name'])
        self.assertEquals(user.email, data['email'])

    def tearDown(self):
        if self.sqlmixin:
            self.sqlmixin.drop_db()
