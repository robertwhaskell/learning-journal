# -*- coding: utf-8 -*-
from contextlib import closing
import datetime
import os
from journal import INSERT_ENTRY
from journal import connect_db
from journal import DB_SCHEMA
from lettuce import world
from lettuce import step
from lettuce import before
from lettuce import after
import markdown

TEST_DSN = 'dbname=test_learning_journal user=roberthaskell'


@before.all
def db():
    """set up a database"""
    settings = {'db': TEST_DSN}
    init_db(settings)
    world.settings = settings


@before.all
def app():
    """cofigure an app, then set up a fake server"""
    from journal import main
    from webtest import TestApp
    os.environ['DATABASE_URL'] = TEST_DSN
    app = main()
    world.app = TestApp(app)


@before.each_feature
def enter_data(step):
    """populate the database"""
    entry('Test Title', 'Test Text')
    entry('Unedited Title', 'Unedited Text')
    entry('Markdown Test', '### Header3')
    mkdn = """
    ```python
        def thing():
        pass ```
    """
    entry('Color Testing', mkdn)


@after.all
def clear_entries(settings):
    """clear the database"""
    with closing(connect_db(world.settings)) as db:
        db.cursor().execute("DELETE FROM entries")
        db.commit()


@after.all
def cleanup(step):
    clear_db(world.settings)


def init_db(settings):
    with closing(connect_db(settings)) as db:
        db.cursor().execute(DB_SCHEMA)
        db.commit()


def clear_db(settings):
    with closing(connect_db(settings)) as db:
        db.cursor().execute("DROP TABLE entries")
        db.commit()


def run_query(db, query, params=(), get_results=True):
    cursor = db.cursor()
    cursor.execute(query, params)
    db.commit()
    results = None
    if get_results:
        results = cursor.fetchall()
    return results


def entry(title, text):
    """provide a single entry in the database"""
    settings = world.settings
    now = datetime.datetime.utcnow()
    expected = (title, text, now)
    with closing(connect_db(settings)) as db:
        run_query(db, INSERT_ENTRY, expected, False)
        db.commit()
    world.expected = expected


# Steps:

@step('I see an entry on the "(.*)" page with the title "(.*)"')
def confirm_title_on_homepage(step, page, title):
    world.page = page
    assert title in world.app.get(page)


@step('I see that it is a markdown entry')
def confirm_markdown(step):
    assert markdown.markdown('Test Text', extensions=('codehilite', 'fenced_code')) in world.app.get(world.page)


@step('logged in')
def log_in(step):
    world.homepage = world.app.get('/')
    world.loginpage = world.homepage.click(linkid='login')
    f = world.loginpage.form
    f['username'] = 'admin'
    f['password'] = 'secret'
    f.submit('submit')


@step('Go to the home page')
def Go_to_home_page(step):
    world.homepage = world.app.get('/')
    assert '<h2>Entries</h2>' in world.homepage


@step('Click the detail button of an entry')
def click_detail(step):
    world.detailpage = world.homepage.click('Detail', linkid='2')
    assert 'Details' in world.detailpage


@step('Then I see the entries text and title on the detail page')
def confirm_entry(step):
    assert 'Unedited Title' in world.detailpage
    assert 'Unedited Text' in world.detailpage


@step('Click the edit button on the detail page')
def click_edit(step):
    assert 'Edit' in world.detailpage
    world.editpage = world.detailpage.click('Edit')
    assert 'Edit' in world.editpage


@step('Edit the entry')
def edit_entry(step):
    f = world.editpage.form
    f['title'] = 'Edited Title'
    f['text'] = 'Edited Text'
    f.submit('submit')


@step('Then I see the change on the home page')
def confirm_change(step):
    world.homepage = world.app.get('/')
    assert 'Edited Title' in world.homepage
    assert 'Edited Text' in world.homepage
