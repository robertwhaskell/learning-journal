
# -*- coding: utf-8 -*-
from contextlib import closing
from pyramid import testing
import pytest
import datetime
import os
from journal import Entry
import transaction
from journal import DBSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import markdown
from cryptacular.bcrypt import BCRYPTPasswordManager
from pyramid.httpexceptions import HTTPUnauthorized

TEST_DSN = 'postgresql://roberthaskell:@/test_learning_journal'


def login_helper(username, password, app):
    """encapsulate app login for reuse in tests
    Accept all status codes so that we can make assertions in tests
    """
    login_data = {'username': username, 'password': password}
    return app.post('/login', params=login_data, status='*')


def clear_entries(db):
    for entry in Entry.all():
        Entry.delete_by_id(entry.id)
    Entry.delete_all(session=db)


@pytest.fixture(scope='function')
def auth_req(request):
    manager = BCRYPTPasswordManager()
    settings = {
        'auth.username': 'admin',
        'auth.password': manager.encode('secret'),
    }
    testing.setUp(settings=settings)
    req = testing.DummyRequest()

    def cleanup():
        testing.tearDown()

    request.addfinalizer(cleanup)

    return req


@pytest.fixture(scope='session')
def db(request):
    """tear down db"""
    engine = create_engine('postgresql://roberthaskell:@/test_learning_journal')
    Session = sessionmaker(bind=engine)

    def cleanup():
        clear_entries(Session)

    request.addfinalizer(cleanup)

    return Session()


@pytest.fixture(scope='function')
def app(db):
    from journal import main
    from webtest import TestApp
    os.environ['DATABASE_URL'] = TEST_DSN
    app = main()
    return TestApp(app)


@pytest.fixture()
def entry(request, req_context, db):
    """provide a single entry in the database"""
    req_context.params['title'] = 'Test Title'
    req_context.params['text'] = 'Test Text'
    Entry.from_request(request=req_context, session=db)
    transaction.commit()


def test_listing(app, entry):

    response = app.get('/')
    assert response.status_code == 200
    actual = response.body
    assert 'Test Title' in actual


@pytest.fixture(scope='function')
def req_context(request):
    """mock a request with a database attached"""
    req = testing.DummyRequest()
    req.exception = None
    req.params['title'] = 'Test Title'
    req.params['text'] = 'Test Text'
    return req


def test_add_entry(req_context, db):
    # assert that there are no entries when we start
    clear_entries(db)
    Entry.from_request(req_context)
    rows = Entry.all()
    assert len(rows) == 1
    for row in rows:
        assert row.text == 'Test Text'
        assert row.title == 'Test Title'


def test_read_entries_empty(req_context, db):
    # call the function under test
    clear_entries(db)
    from journal import read_entries
    result = read_entries(req_context)
    # make assertions about the result
    assert 'entries' in result
    assert len(result['entries']) == 0


def test_read_entries(req_context):
    clear_entries(db)
    Entry.from_request(req_context)
    transaction.commit()
    from journal import read_entries
    result = read_entries(req_context)
    # make assertions about the result
    assert 'entries' in result
    assert len(result['entries']) == 1
    for entry in result['entries']:
        assert entry['title'] == 'Test Title'
        assert entry['text'] == markdown.markdown('Test Text', extensions=('codehilite', 'fenced_code'))


def test_empty_listing(app, db):
    clear_entries(db)
    transaction.commit()
    response = app.get('/')
    assert response.status_code == 200
    actual = response.body
    expected = 'No entries here so far'
    assert expected in actual


def test_post_to_add_view(app):
    login_helper('admin', 'secret', app)
    entry_data = {
        'title': 'Hello there',
        'text': 'This is a post',
    }
    response = app.post('/add', params=entry_data, status='2*')
    actual = response.body
    for expected in entry_data.values():
        assert expected in actual

def test_post_to_add_view_unauthorized(app):
    entry_data = {
        'title': 'Hello there',
        'text': 'This is a post',
    }
    response = app.post('/add', params=entry_data).body
    assert response == 'null'
