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
    entry('Delete Title', 'Delete Text')


@before.each_feature
def log_in(step):
    world.homepage = world.app.get('/')
    world.loginpage = world.homepage.click(linkid='login')
    f = world.loginpage.form
    f['username'] = 'admin'
    f['password'] = 'secret'
    f.submit('submit')


@after.each_feature
def logout(*args):
    world.app.get('/').click(linkid='logout')


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


def mkdn(text):
    return markdown.markdown(text, extensions=('codehilite', 'fenced_code'))


# Steps:
@step('I see an entry on the "(.*)" page with the text "(.*)"')
def confirm_title_on_homepage(step, page, text):
    world.page = page
    world.text = text
    assert text in world.app.get(page)


@step('I see that it "(.*)" a markdown entry')
def confirm_markdown(step, is_or_isnt):
    if is_or_isnt == 'is':
        assert mkdn(world.text) in world.app.get(world.page)
    else:
        assert mkdn(world.text) not in world.app.get(world.page)


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


@step("Go to an entry's edit page")
def goto_edit_page(step):
    assert 'Delete Title' in world.app.get('/')
    world.editpage = world.app.get('/editor/3')
    assert 'Delete Title' in world.editpage
    assert 'Delete Text' in world.editpage


@step('Press the delete button')
def press_delete(step):
    world.homepage = world.editpage.click(linkid='delete')


@step('Then I see that the entry is gone from the homepage')
def check_homepage(step):
    assert 'Delete Title' not in world.app.get('/')
    assert 'Delete Text' not in world.app.get('/')


@step('Then I see that the entry is gone from the database')
def check_database(step):
    pass
