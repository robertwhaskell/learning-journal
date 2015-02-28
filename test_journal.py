
# -*- coding: utf-8 -*-
from contextlib import closing
from pyramid import testing
import pytest
import datetime
import os
from journal import Entry
import transaction
from journal import DBSession
TEST_DSN = 'postgresql://roberthaskell:@/test_learning_journal'


def clear_entries():
    entries = Entry.all()
    for entry in entries:
        Entry.delete_by_id(entry.id)


@pytest.fixture(scope='session')
def db(request):
    """set up and tear down a database"""
    def cleanup():
        clear_entries()

    request.addfinalizer(cleanup)


@pytest.fixture(scope='function')
def app(db):
    from journal import main
    from webtest import TestApp
    os.environ['DATABASE_URL'] = TEST_DSN
    app = main()
    return TestApp(app)


@pytest.fixture(scope='function')
def entry(request, req_context):
    """provide a single entry in the database"""
    req_context.params['title'] = 'Test Title'
    req_context.params['text'] = 'Test Text'
    Entry.from_request(req_context)


def test_listing(app, entry):
    response = app.get('/')
    assert response.status_code == 200
    actual = response.body
    assert 'Test Title' in actual


@pytest.yield_fixture(scope='function')
def req_context(request):
    """mock a request with a database attached"""
    req = testing.DummyRequest()
    req.exception = None
    yield req


def test_add_entry(req_context):
    # assert that there are no entries when we start
    clear_entries()
    req_context.params['title'] = 'Test Title'
    req_context.params['text'] = 'Test Text'

    Entry.from_request(req_context)
    rows = Entry.all()
    assert len(rows) == 1
    for row in rows:
        assert row.text == 'Test Text'
        assert row.title == 'Test Title'


# def test_read_entries_empty(req_context):
#     # call the function under test
#     clear_entries()
#     from journal import read_entries
#     result = read_entries(req_context)
#     # make assertions about the result
#     assert 'entries' in result
#     assert len(result['entries']) == 0


# def test_read_entries(req_context):
#     # prepare data for testing
#     req_context.params['title'] = 'Test Title'
#     req_context.params['text'] = 'Test Text'
#     Entry.from_request(req_context)
#     from journal import read_entries
#     result = read_entries(req_context)
#     # make assertions about the result
#     assert 'entries' in result
#     assert len(result['entries']) == 1
#     for entry in result['entries']:
#         assert entry.title == 'Test Title'
#         assert entry.text == 'Test Text'


def test_empty_listing(app):
    response = app.get('/')
    assert response.status_code == 200
    actual = response.body
    expected = 'No entries here so far'
    assert expected in actual


# def test_post_to_add_view(app):
#     entry_data = {
#         'title': 'Hello there',
#         'text': 'This is a post',
#     }
#     response = app.post('/add', params=entry_data, status='3*')
#     redirected = response.follow()
#     actual = redirected.body
#     for expected in entry_data.values():
#         assert expected in actual
