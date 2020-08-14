from flask import request
from frasco.ext import *
from frasco.models import db
from frasco.users import get_current_user, is_user_logged_in
import base64
import datetime
import hashlib
import uuid
import functools
import psycopg2
from .service import ApiAuthentificationRequiredError


class ApiKeyModelMixin(object):
    value = db.Column(db.String, index=True)
    last_accessed_at = db.Column(db.DateTime)
    last_accessed_from = db.Column(db.String)
    expires_at = db.Column(db.DateTime)


class FrascoApiKeyAuthentification(Extension):
    name = 'frasco_api_key_auth'

    def _init_app(self, app, state):
        require_extension('frasco_users', app)
        state.Model = state.import_option('model')

        @app.extensions.frasco_users.manager.request_loader
        def load_user_from_request(request):
            api_key = None
            if 'Authorization' in request.headers:
                authz = request.headers['Authorization']
                if authz.startswith('Basic '):
                    try:
                        api_key = base64.b64decode(authz[6:]).split(':')[0]
                    except:
                        return
                elif authz.startswith('Bearer '):
                    api_key = authz[7:]
            elif 'X-Api-Key' in request.headers:
                api_key = request.headers['X-Api-Key']
            if not api_key:
                return

            try:
                key = state.Model.query.filter_by(value=api_key).first()
            except:
                return
            if key:
                now = datetime.datetime.utcnow()
                if key.expires_at and key.expires_at < now:
                    return None
                key.last_accessed_at = now
                key.last_accessed_from = request.remote_addr
                db.session.commit()
                return key.user


def create_api_key(user=None, expires_at=None):
    state = get_extension_state('frasco_api_key_auth')
    if not expires_at and state.options.get('default_key_duration'):
        expires_at = datetime.datetime.now() + datetime.timedelta(
            seconds=state.options['default_key_duration'])
    key = state.Model()
    key.user = get_current_user(user)
    key.value = hashlib.sha1(uuid.uuid4().bytes).hexdigest()
    key.expires_at = expires_at
    return key


def auth_required(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if not is_user_logged_in():
            raise ApiAuthentificationRequiredError()
        return func(*args, **kwargs)
    return wrapper


def authenticated_service(service):
    service.decorators.append(auth_required)
    return service
