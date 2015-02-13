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


def run_query(db, query, params=(), get_results=True):
    cursor = db.cursor()
    cursor.execute(query, params)
    db.commit()
    results = None
    if get_results:
        results = cursor.fetchall()
    return results


@before.all
def entry():
    """provide a single entry in the database"""
    settings = world.settings
    now = datetime.datetime.utcnow()
    expected = ('Test Title', 'Test Text', now)
    with closing(connect_db(settings)) as db:
        run_query(db, INSERT_ENTRY, expected, False)
        db.commit()
    world.expected = expected

@before.all
def entry_2():
    """provide a single entry in the database"""
    settings = world.settings
    now = datetime.datetime.utcnow()
    expected = ('Markdown Test', '### Header3', now)
    with closing(connect_db(settings)) as db:
        run_query(db, INSERT_ENTRY, expected, False)
        db.commit()
    world.expected = expected

@before.all
def entry_3():
    """provide a single entry in the database"""
    settings = world.settings
    now = datetime.datetime.utcnow()
    mkdn = """
    ```python
        def thing():
        pass ```
    """
    expected = ('Color Testing', mkdn, now)
    with closing(connect_db(settings)) as db:
        run_query(db, INSERT_ENTRY, expected, False)
        db.commit()
    world.expected = expected


@after.all
def cleanup(step):
    clear_db(world.settings)


@step('an entry with the title "(.*)"')
def get_entry(step, title):
    # get entry date, text, title, assign it to world
    response = world.app.get('/')
    assert title in response.body


@step('I press the detail button')
def press_button(step):
    # press the detail button associated with the entry held in world
    world.response = world.app.get('/details/1')


@step('I see the detail page for that entry')
def see_detail(step):
    assert 'Test Title' in world.response.body

# Markdown steps

@step('I see the entry on the index page')
def check_entry(step):
    pass


@step('I see that it is a markdown entry')
def see_changes(step):
    assert '<h3>Header3</h3>' in world.app.get('/').body


@step('When I press the edit button')
def press_edit_button(step):
    entry_data = {
        'title': 'Edited Title Text',
        'text': 'Edited Post',
    }
    world.app.post('/update/1', params=entry_data, status='3*')


@step('I see the changes I made to the entry')
def see_changes(step):
    assert "Edited Title Text" in world.app.get('/details/1').body


@step('I see the entry is colorized')
def see_changes(step):
    print world.app.get('/').body
    assert '<div class="codehilite"><pre>```python' in world.app.get('/')


@step('a detail page')
def go_to_detail(step):
    world.response = world.app.get('/details/1')


@step("I'm not logged in")
def check_login(step):
    pass


@step("I don't see an edit button")
def check_for_button(step):
    assert '<button>Edit</button>' not in world.response


@step("a login page")
def login_page(step):
    entry_data = {
        'username': 'admin',
        'password': 'secret',
    }
    world.app.post('/login', params=entry_data, status='3*')


@step("I log in and go to an editing page")
def goto_edit(step):
    pass


@step("I see the edit button")
def see_edit_button(step):
    print world.app.get('/details/1')
    assert '<button>Edit</button>' in world.app.get('/details/1')
    world.app.post('/logout')
