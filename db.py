# -*- coding: utf-8 -*-

from dal import DAL, Field


def create_db_connection(migrate=False):
    """Connect to the database. Returns the connection.
    """
    db = DAL('sqlite://db.sqlite', migrate=migrate)

    db.define_table(
        'users',
        Field('username', 'string', length=50, required=True, unique=True),
        Field('password', 'string', length=128, required=True))

    return db


def close_db_connection(db):
    """Close database connection.
    """
    db._adapter.connection.close()
