from flask import json, make_response, Blueprint, url_for, jsonify, g
from frasco.utils import cached_property
from frasco.request_params import disable_request_params
from frasco.marshaller import disable_marshaller
from werkzeug.wrappers import Response
import functools
from .swagger import build_swagger_spec, build_swagger_client
from .errors import *


def wrap_service_func_for_endpoint(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            rv = func(*args, **kwargs)
        except ApiError as e:
            return make_response(json.dumps({"error": unicode(e)}), e.http_code)
        if isinstance(rv, Response):
            return rv
        return json.dumps(rv), {'Content-Type': 'application/json;charset=UTF-8'}
    return wrapper


def wrap_service_func_for_internal_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with disable_marshaller(), disable_request_params():
            return func(*args, **kwargs)
    return wrapper


def join_url_rule(rule1, rule2):
    if not rule1:
        return rule2
    if not rule2:
        return rule1
    return (rule1.rstrip('/') + '/' + rule2.lstrip('/')).rstrip('/')


class ApiService(object):
    def __init__(self, name=None, url_prefix=None):
        self.name = name
        self.url_prefix = url_prefix
        self.rules = []
        self.endpoint_funcs = {}
        self.decorators = []

    def add_endpoint(self, rule, func, **options):
        endpoint = options.pop("endpoint", func.__name__)
        self.rules.append((rule, endpoint, options))
        self.endpoint_funcs[endpoint] = self._apply_decorators(func)

    def iter_endpoints(self):
        for rule, endpoint, options in self.rules:
            yield rule, endpoint, self.endpoint_funcs[endpoint], options

    def route(self, rule, **options):
        def decorator(func):
            self.add_endpoint(rule, func, **options)
            return func
        return decorator

    def __getattr__(self, name):
        if name not in self.endpoint_funcs:
            raise ValueError("Endpoint '%s' does not exist in service '%s'" % (name, self.name))
        return wrap_service_func_for_internal_call(self.endpoint_funcs[name])

    def mixin(self, service, decorator=None, url_prefix=None):
        for rule, endpoint, func, options in service.iter_endpoints():
            rule = join_url_rule(url_prefix, rule)
            if decorator:
                func = decorator(func)
            self.add_endpoint(rule, func, endpoint=endpoint, **options)

    def decorator(self, func):
        self.decorators.append(func)
        return func

    def before_request(self, before_request_func):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                before_request_func()
                return func(*args, **kwargs)
            return wrapper
        self.decorators.append(decorator)
        return before_request_func

    def _apply_decorators(self, func):
        for decorator in reversed(self.decorators):
            func = decorator(func)
        return func


class ApiVersion(ApiService):
    blueprint_class = Blueprint

    @classmethod
    def inherit(cls, parent_api, *args, **kwargs):
        api = cls(*args, **kwargs)
        api.mixin(parent_api)
        api.services.update(parent_api.services)
        return api

    def __init__(self, version, import_name, url_prefix=None):
        if url_prefix is None:
            url_prefix = '/api/%s' % version
        super(ApiVersion, self).__init__('', url_prefix)
        self.version = version
        self.import_name = import_name
        self.services = {}

    @cached_property
    def apispec_as_json(self):
        return build_swagger_spec(self).to_dict()

    def add_service(self, service):
        self.services[service.name] = service

    def iter_services(self):
        return self.services.values()

    def service(self, name, **kwargs):
        service = ApiService(name, **kwargs)
        self.add_service(service)
        return service

    def __getattr__(self, name):
        if name in self.services:
            return self.services[name]
        raise ValueError("Service '%s' does not exist in API %s" % (name, self.version))

    def _merge_services_endpoints(self):
        rules = list(self.rules)
        endpoint_funcs = dict(self.endpoint_funcs)
        for service in self.services.values():
            for rule, endpoint, func, options in service.iter_endpoints():
                endpoint = service.name + '_' + endpoint
                rules.append((join_url_rule(service.url_prefix, rule), endpoint, options))
                endpoint_funcs[endpoint] = func
        return rules, endpoint_funcs

    def iter_all_endpoints(self):
        rules, endpoint_funcs = self._merge_services_endpoints()
        for rule, endpoint, options in rules:
            yield rule, endpoint, endpoint_funcs[endpoint], options

    def as_blueprint(self, name=None, client_var_name="API", client_class_name="SwaggerClient"):
        if not name:
            name = "api_%s" % self.version.replace('.', '_')
        bp = self.blueprint_class(name, self.import_name, url_prefix=self.url_prefix)

        @bp.before_request
        def before_request():
            g.is_api_call = True

        @bp.after_request
        def after_request(resp):
            resp.headers.add('Cache-Control', 'no-cache')
            resp.headers.add('X-Api-Version', self.version)
            return resp

        endpoint_funcs = {}
        for rule, endpoint, func, options in self.iter_all_endpoints():
            endpoint_funcs.setdefault(endpoint, wrap_service_func_for_endpoint(func))
            bp.add_url_rule(rule, endpoint, endpoint_funcs[endpoint], **options)

        @bp.route('/spec.json')
        def get_spec():
            return jsonify(**self.apispec_as_json)

        @bp.route("/client.js")
        def get_client():
            return build_swagger_client(self.apispec_as_json, url_for('.get_spec', _external=True),
                client_var_name, client_class_name)

        return bp
