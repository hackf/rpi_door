# Copyright (C) 2013 Windsor Hackforge
#
# This module is part of RPi Door and is released under
# the MIT License: http://www.opensource.org/licenses/mit-license.php

from sqlalchemy.ext.declarative import declarative_base, DeferredReflection
from sqlalchemy.schema import (
    MetaData,
    Table,
    DropTable,
    ForeignKeyConstraint,
    DropConstraint,
)
from sqlalchemy import (
    engine_from_config,
    engine,
    Column,
    Integer,
    Unicode,
    Boolean,
    ForeignKey,
)
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    relationship,
    joinedload,
    backref,
)
from sqlalchemy.exc import NoSuchTableError
from contextlib import contextmanager


Base = declarative_base()


class SQLAlchemyBase():

    def __init__(self, *args, **kwargs):

        self.engine = engine_from_config(kwargs, prefix="sqlalchemy.")

        # Tries to call the next object's __init__ in the inheritance
        # If it throws an TypeError than we can assume the parent object is
        # object or another object that doesn't accept *args and **kwargs. This
        # is a bit of a draw back but works fine in this case.
        try:
            super(SQLAlchemyBase, self).__init__(*args, **kwargs)
        except TypeError:
            pass

        # prepare expects the tables to exist in the database already
        # this is kind of a hack. I'll need to think of a better way
        # later on
        try:
            DeferredReflection.prepare(self.engine)
        except NoSuchTableError:
            self.init_db()
            DeferredReflection.prepare(self.engine)

        self._session = scoped_session(sessionmaker(autocommit=False,
                                                    autoflush=True,
                                                    expire_on_commit=False,
                                                    bind=self.engine))

        Base.query = self._session.query_property()

    def init_db(self):
        Base.metadata.create_all(self.engine)

    def drop_db(self):
        """
        It is a workaround for dropping all tables in sqlalchemy.
        """
        if self.engine is None:
            raise Exception("Engine doesn't exist!")
        conn = self.engine.connect()
        trans = conn.begin()
        inspector = engine.reflection.Inspector.from_engine(self.engine)
        # gather all data first before dropping anything.
        # some DBs lock after things have been dropped in
        # a transaction.

        metadata = MetaData()

        tbs = []
        all_fks = []

        for table_name in inspector.get_table_names():
            fks = []

            for fk in inspector.get_foreign_keys(table_name):
                if not fk['name']:
                    continue
                fks.append(ForeignKeyConstraint((), (), name=fk['name']))
                t = Table(table_name, metadata, *fks)
                tbs.append(t)
                all_fks.extend(fks)

        for fkc in all_fks:
            conn.execute(DropConstraint(fkc))

        for table in tbs:
            conn.execute(DropTable(table))

        trans.commit()

    @contextmanager
    def session_context(self):
        yield self._session
        self._session.remove()


class SQLAlchemyMixin(SQLAlchemyBase):

    def validate_key_code(self, data):
        with self.session_context():
            key = KeyCode.query\
                         .options(joinedload(KeyCode.user))\
                         .filter(KeyCode.code == data)\
                         .first()

            if key and (key.user and key.enabled):
                return True
            return False


class User(DeferredReflection, Base):
    __tablename__ = "user"

    id = Column(Integer, primary_key=True)
    first_name = Column(Unicode(255))
    last_name = Column(Unicode(255))
    email = Column(Unicode(255))
    key_code_id = Column(Integer, ForeignKey("key_code.id"))
    key_code = relationship("KeyCode", backref=backref("user", uselist=False))


class KeyCode(DeferredReflection, Base):
    __tablename__ = "key_code"

    id = Column(Integer, primary_key=True)
    enabled = Column(Boolean, default=True)
    code = Column(Unicode(26))
