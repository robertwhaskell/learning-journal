# -*- coding: utf-8 -*-
import psycopg2
import os
from datetime import datetime
from pyramid.config import Configurator
from pyramid.session import SignedCookieSessionFactory
from pyramid.view import view_config
from waitress import serve
from pyramid.httpexceptions import HTTPFound, HTTPInternalServerError, HTTPUnauthorized
from pyramid.authentication import AuthTktAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from cryptacular.bcrypt import BCRYPTPasswordManager
from pyramid.security import remember, forget
import markdown
import jinja2
import tweepy
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import (
    scoped_session,
    sessionmaker,
    )
from zope.sqlalchemy import ZopeTransactionExtension

here = os.path.dirname(os.path.abspath(__file__))


DBSession = scoped_session(sessionmaker(extension=ZopeTransactionExtension()))
Base = declarative_base()


class Entry(Base):
    __tablename__ = 'entries'
    id = sa.Column(sa.Integer, primary_key=True, autoincrement=True)
    title = sa.Column(sa.Unicode(127), nullable=False)
    text = sa.Column(sa.UnicodeText, nullable=False)
    created = sa.Column(
        sa.DateTime, nullable=False, default=datetime.today
    )

    def __repr__(self):
        return u"{}: {}".format(self.__class__.__name__, self.title)

    @classmethod
    def all(cls):
        return DBSession.query(cls).order_by(cls.created.desc()).all()

    @classmethod
    def by_id(cls, id):
        return DBSession.query(cls).filter(cls.id == id).one()

    @classmethod
    def delete_by_id(cls, id):
        entry = DBSession.query(cls).filter(cls.id == id).one()
        DBSession.delete(entry)

    @classmethod
    def from_request(cls, request):
        title = request.params.get('title', None)
        text = request.params.get('text', None)
        created = datetime.today()
        new_entry = cls(title=title, text=text, created=created)
        DBSession.add(new_entry)
        return new_entry


@view_config(route_name='add', request_method='POST', renderer="json")
def add_entry(request):
    if request.authenticated_userid:
        if request.method == 'POST':
            new = None
            try:
                Entry.from_request(request)
                new = DBSession.query(Entry).order_by(Entry.id.desc()).first()
            except psycopg2.Error:
                return HTTPInternalServerError
            entry = {
                'id': new.id,
                'title': new.title,
                'text': markdown.markdown(new.text, extensions=('codehilite', 'fenced_code')),
                'created': new.created.strftime('%b. %d, %Y')
                }
            return entry


@view_config(route_name='home', renderer='templates/list.jinja2')
def read_entries(request):
    """return a list of all entries as dicts"""
    entries_from_db = Entry.all()
    entries = []
    for entry in entries_from_db:
        entries.append({
            'title': entry.title,
            'text': markdown.markdown(entry.text, extensions=('codehilite', 'fenced_code')),
            'created': entry.created,
            'id': entry.id})
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


@view_config(route_name='editor', renderer="templates/editor.jinja2")
def editor(request):
    print "at page"
    if request.authenticated_userid:
        print request.matchdict.get('id', -1)
        entry = Entry.by_id(request.matchdict.get('id', -1))
        if request.method == 'POST':
            entry.title = request.params['title']
            entry.text = request.params['text']
        return {'entry': entry}
    else:
        raise HTTPUnauthorized


@view_config(route_name='delete')
def delete(request):
    param = request.matchdict.get('id', -1)
    Entry.delete_by_id(param)
    return HTTPFound(request.route_url('home'))


@view_config(route_name='details', renderer="templates/details.jinja2")
def details(request):
    entry = Entry.by_id(request.matchdict.get('id', -1))
    return {'entry': entry}


@view_config(route_name='tweet', renderer='json')
def tweet_all_about_it(request):

    with open('twitterkeys.txt', 'r') as tk:
        consumer_key = tk.readline().rstrip()
        consumer_secret = tk.readline().rstrip()
        access_token = tk.readline().rstrip()
        access_token_secret = tk.readline().rstrip()
    tk.close()

    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_token, access_token_secret)

    api = tweepy.API(auth)

    api.update_status(status=request.params['title'])


def main():
    """Create a configured wsgi app"""
    settings = {}
    settings['reload_all'] = os.environ.get('DEBUG', True)
    settings['debug_all'] = os.environ.get('DEBUG', True)
    settings['sqlalchemy.url'] = os.environ.get(
        'DATABASE_URL', 'postgresql://roberthaskell:@localhost:5432/learning_journal'  #'dbname=learning_journal user=cewing'
    )
    engine = sa.engine_from_config(settings, 'sqlalchemy.')
    DBSession.configure(bind=engine)
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
    config.include('pyramid_tm')
    config.include('pyramid_jinja2')
    config.add_static_view('static', os.path.join(here, 'static'))
    config.add_route('home', '/')
    config.add_route('add', '/add')
    config.add_route('login', '/login')
    config.add_route('logout', '/logout')
    config.add_route('details', '/details/{id}')
    config.add_route('editor', '/editor/{id}')
    config.add_route('delete', '/delete/{id}')
    config.add_route('tweet', '/tweet')
    config.scan()
    app = config.make_wsgi_app()
    return app


def markd(input):
    return markdown.markdown(input, extension=['CodeHilite'])

if __name__ == '__main__':
    app = main()
    port = os.environ.get('PORT', 5002)
    serve(app, host='0.0.0.0', port=port)
