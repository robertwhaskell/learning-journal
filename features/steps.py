# -*- coding: utf-8 -*-
from contextlib import closing
from pyramid import testing
import datetime
import os
from journal import INSERT_ENTRY
from journal import connect_db
from journal import DB_SCHEMA
from cryptacular.bcrypt import BCRYPTPasswordManager
from lettuce import world
from lettuce import step
from lettuce import before
from lettuce import after

TEST_DSN = 'dbname=test_learning_journal user=roberthaskell'


# Before we do anything, we want to build a db, and stock it
# lorem ipsum entries.

# After everything runs, we want to tear the database down


def init_db(settings):
    with closing(connect_db(settings)) as db:
        db.cursor().execute(DB_SCHEMA)
        db.commit()


def clear_db(settings):
    with closing(connect_db(settings)) as db:
        db.cursor().execute("DROP TABLE entries")
        db.commit()


def clear_entries(settings):
    with closing(connect_db(settings)) as db:
        db.cursor().execute("DELETE FROM entries")
        db.commit()


@before.all
def db():
    """set up a database"""
    settings = {'db': TEST_DSN}
    init_db(settings)
    world.settings = settings


@before.all
def app():
    from journal import main
    from webtest import TestApp
    os.environ['DATABASE_URL'] = TEST_DSN
    app = main()
    world.app = TestApp(app)


@before.all
def req_context():
    """mock a request with a database attached"""
    settings = world.settings
    req = testing.DummyRequest()
    with closing(connect_db(settings)) as db:
        req.db = db
        req.exception = None
        yield req
        # after a test has run, we clear out entries for isolation
        clear_entries(settings)


@after.all
def cleanup():
    clear_db(world.settings)


@step('an entry with the title "(.*)"')
def get_entry(step, title):
    # get entry date, text, title, assign it to world

    assert True
    pass


@step('I press the detail button')
def press_button(step):
    # press the detail button associated with the entry held in world
    assert True
    pass


@step('I see the detail page for that entry')
def see_detail(step):
    # check that the details being displayed on the page are the
    # same as what the world is holding.
    assert True
    pass
