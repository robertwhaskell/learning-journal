# -*- coding: utf-8 -*-
from pyramid.events import NewRequest, subscriber
import psycopg2
import os
import logging
from datetime import date
from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory
from pyramid.view import view_config
from waitress import serve
from contextlib import closing
from pyramid.httpexceptions import HTTPFound, HTTPInternalServerError, HTTPUnauthorized
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from cryptacular.bcrypt import BCRYPTPasswordManager
from pyramid.security import remember, forget
import markdown
import jinja2
here = os.path.dirname(os.path.abspath(__file__))

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id serial PRIMARY KEY,
    title VARCHAR (127) NOT NULL,
    text TEXT NOT NULL,
    created TIMESTAMP NOT NULL
)
"""

DB_ENTRIES_LIST = """
SELECT id, title, text, created FROM entries ORDER BY created DESC
"""

DB_FILTER = """
SELECT id, title, text, created FROM entries WHERE id=%s
"""

INSERT_ENTRY = """
INSERT INTO entries (title, text, created) VALUES(%s, %s, %s);
"""

UPDATE_ENTRY = """
UPDATE entries SET title=%s, text=%s, created=%s WHERE id=%s;
"""

logging.basicConfig()
log = logging.getLogger(__file__)


def connect_db(settings):
    """Return a connection to the configured database"""
    return psycopg2.connect(settings['db'])


def init_db():
    """Create database tables defined by DB_SCHEMA
    """
    settings = {}
    settings['db'] = os.environ.get(
        'DATABASE_URL', 'dbname=learning_journal user=roberthaskell'
    )
    with closing(connect_db(settings)) as db:
        db.cursor().execute(DB_SCHEMA)
        db.commit()


@subscriber(NewRequest)
def open_connection(event):
    request = event.request
    settings = request.registry.settings
    request.db = connect_db(settings)
    request.add_finished_callback(close_connection)


def close_connection(request):
    """close the database connection for this request

    If there has been an error in the processing of the request, abort any
    open transactions.
    """
    db = getattr(request, 'db', None)
    if db is not None:
        if request.exception is not None:
            db.rollback()
        else:
            db.commit()
        request.db.close()


def write_entry(request):
    """write a single entry to the database"""
    title = request.params['title']
    text = request.params['text']
    created = date.today()
    request.db.cursor().execute(INSERT_ENTRY, (title, text, created))
    return {}


def update(request, identification):
    title = request.params['title']
    text = request.params['text']
    created = date.today()
    request.db.cursor().execute(UPDATE_ENTRY, (title, text, created, identification))
    return {}


@view_config(route_name='add', request_method='POST')
def add_entry(request):
    try:
        write_entry(request)
    except psycopg2.Error:
        # this will catch any errors generated by the database
        return HTTPInternalServerError
    return HTTPFound(request.route_url('home'))


@view_config(route_name='update', request_method='POST')
def update_entry(request):
    identification = (request.matchdict.get('id', -1),)
    try:
        update(request, identification)
    except psycopg2.Error:
        # this will catch any errors generated by the database
        return HTTPInternalServerError
    return HTTPFound(request.route_url('home'))


@view_config(route_name='home', renderer='templates/list.jinja2')
def read_entries(request):
    """return a list of all entries as dicts"""
    cursor = request.db.cursor()
    cursor.execute(DB_ENTRIES_LIST)
    keys = ('id', 'title', 'text', 'created')
    entries = [dict(zip(keys, row)) for row in cursor.fetchall()]
    for entry in entries:
        entry['text'] = markdown.markdown(entry['text'], extensions=('codehilite', 'fenced_code'))
    return {'entries': entries}


def do_login(request):
    username = request.params.get('username', None)
    password = request.params.get('password', None)
    if not (username and password):
        raise ValueError('both username and password are required')

    settings = request.registry.settings
    manager = BCRYPTPasswordManager()
    if username == settings.get('auth.username', ''):
        hashed = settings.get('auth.password', '')
        return manager.check(hashed, password)


@view_config(route_name='login', renderer="templates/login.jinja2")
def login(request):
    """authenticate a user by username/password"""
    username = request.params.get('username', '')
    error = ''
    if request.method == 'POST':
        error = "Login Failed"
        authenticated = False
        try:
            authenticated = do_login(request)
        except ValueError as e:
            error = str(e)

        if authenticated:
            headers = remember(request, username)
            return HTTPFound(request.route_url('home'), headers=headers)
    return {'error': error, 'username': username}


@view_config(route_name='logout')
def logout(request):
    headers = forget(request)
    return HTTPFound(request.route_url('home'), headers=headers)


def get_entry(request):
    param = (request.matchdict.get('id', -1),)
    cursor = request.db.cursor()
    cursor.execute(DB_FILTER, param)
    keys = ('id', 'title', 'text', 'created')
    return [dict(zip(keys, cursor.fetchone()))]


@view_config(route_name='editor', renderer="templates/editor.jinja2")
def editor(request):
    if request.authenticated_userid:
        entry = {'entries': get_entry(request)}
        if request.method == 'POST':
            update(request, request.matchdict.get('id', -1))
            return HTTPFound(request.route_url('home'))
        return entry
    else:
        raise HTTPUnauthorized


@view_config(route_name='details', renderer="templates/details.jinja2")
def details(request):
    entry = get_entry(request)
    entry[0]['text'] = markdown.markdown(entry[0]['text'], extensions=('codehilite', 'fenced_code')) 
    return {'entries': entry}


def main():
    """Create a configured wsgi app"""
    settings = {}
    settings['reload_all'] = os.environ.get('DEBUG', True)
    settings['debug_all'] = os.environ.get('DEBUG', True)
    settings['db'] = os.environ.get(
        'DATABASE_URL', 'dbname=learning_journal user=roberthaskell'
        )
    settings['auth.username'] = os.environ.get('AUTH_USERNAME', 'admin')
    manager = BCRYPTPasswordManager()
    settings['auth.password'] = os.environ.get(
        'AUTH_PASSWORD', manager.encode('secret')
    )
    # secret value for session signing:
    secret = os.environ.get('JOURNAL_SESSION_SECRET', 'itsaseekrit')
    session_factory = SignedCookieSessionFactory(secret)
    auth_secret = os.environ.get('JOURNAL_AUTH_SECRET', 'anotherseekrit')
    # configuration setup
    config = Configurator(
        settings=settings,
        session_factory=session_factory,
        authentication_policy=AuthTktAuthenticationPolicy(
            secret=auth_secret,
            hashalg='sha512'
        ),
        authorization_policy=ACLAuthorizationPolicy(),

    )
    jinja2.filters.FILTERS['markdown'] = markd
    config.include('pyramid_jinja2')
    config.add_static_view('static', os.path.join(here, 'static'))
    config.add_route('home', '/')
    config.add_route('add', '/add')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('details', '/details/{id}')
    config.add_route('editor', '/editor/{id}')
    config.add_route('update', '/update/{id}')
    config.scan()
    app = config.make_wsgi_app()
    return app


def markd(input):
    return markdown.markdown(input, extension=['CodeHilite'])

if __name__ == '__main__':
    app = main()
    port = os.environ.get('PORT', 5001)
    serve(app, host='0.0.0.0', port=port)
