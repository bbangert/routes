"""test_explicit_use"""
import os, sys, time, unittest

import pytest
from routes import *
from routes.route import Route
from routes.util import GenerationException

class TestUtils(unittest.TestCase):
    def test_route_dict_use(self):
        m = Mapper()
        m.explicit = True
        m.connect('/hi/{fred}')

        environ = {'HTTP_HOST': 'localhost'}

        env = environ.copy()
        env['PATH_INFO'] = '/hi/george'

        assert m.match(environ=env) == {'fred': 'george'}

    def test_x_forwarded(self):
        m = Mapper()
        m.explicit = True
        m.connect('/hi/{fred}')

        environ = {'HTTP_X_FORWARDED_HOST': 'localhost'}
        url = URLGenerator(m, environ)
        assert url(fred='smith', qualified=True) == 'http://localhost/hi/smith'

    def test_server_port(self):
        m = Mapper()
        m.explicit = True
        m.connect('/hi/{fred}')

        environ = {'SERVER_NAME': 'localhost', 'wsgi.url_scheme': 'https',
                   'SERVER_PORT': '993'}
        url = URLGenerator(m, environ)
        assert url(fred='smith', qualified=True) == 'https://localhost:993/hi/smith'

    def test_subdomain_screen(self):
        m = Mapper()
        m.explicit = True
        m.sub_domains = True
        m.connect('/hi/{fred}')

        environ = {'HTTP_HOST': 'localhost.com'}
        url = URLGenerator(m, environ)
        assert url(fred='smith', sub_domain=u'home', qualified=True) == 'http://home.localhost.com/hi/smith'

        environ = {'HTTP_HOST': 'here.localhost.com', 'PATH_INFO': '/hi/smith'}
        url = URLGenerator(m, environ.copy())
        with pytest.raises(GenerationException):
            url.current(qualified=True)

        environ = {'HTTP_HOST': 'subdomain.localhost.com'}
        url = URLGenerator(m, environ.copy())
        assert url(fred='smith', sub_domain='sub', qualified=True) == 'http://sub.localhost.com/hi/smith'

        environ = {'HTTP_HOST': 'sub.sub.localhost.com'}
        url = URLGenerator(m, environ.copy())
        assert url(fred='smith', sub_domain='new', qualified=True) == 'http://new.localhost.com/hi/smith'

        url = URLGenerator(m, {})
        assert url(fred='smith', sub_domain=u'home') == '/hi/smith'

    def test_anchor(self):
        m = Mapper()
        m.explicit = True
        m.connect('/hi/{fred}')

        environ = {'HTTP_HOST': 'localhost.com'}
        url = URLGenerator(m, environ)
        assert url(fred='smith', anchor='here') == '/hi/smith#here'

    def test_static_args(self):
        m = Mapper()
        m.explicit = True
        m.connect('http://google.com/', _static=True)

        url = URLGenerator(m, {})

        assert url('/here', q=[u'fred', 'here now']) == '/here?q=fred&q=here%20now'

    def test_current(self):
        m = Mapper()
        m.explicit = True
        m.connect('/hi/{fred}')

        environ = {'HTTP_HOST': 'localhost.com', 'PATH_INFO': '/hi/smith'}
        match = m.routematch(environ=environ)[0]
        environ['wsgiorg.routing_args'] = (None, match)
        url = URLGenerator(m, environ)
        assert url.current() == '/hi/smith'

    def test_add_routes(self):
        map = Mapper(explicit=True)
        map.minimization = False
        routes = [
            Route('foo', '/foo',)
        ]
        map.extend(routes)
        assert map.match('/foo') == {}

    def test_add_routes_conditions_unmet(self):
        map = Mapper(explicit=True)
        map.minimization = False
        routes = [
            Route('foo', '/foo', conditions=dict(method=["POST"]))
        ]
        environ = {
            'HTTP_HOST': 'localhost.com',
            'PATH_INFO': '/foo',
            'REQUEST_METHOD': 'GET',
        }
        map.extend(routes)
        assert map.match('/foo', environ=environ) is None

    def test_add_routes_conditions_met(self):
        map = Mapper(explicit=True)
        map.minimization = False
        routes = [
            Route('foo', '/foo', conditions=dict(method=["POST"]))
        ]
        environ = {
            'HTTP_HOST': 'localhost.com',
            'PATH_INFO': '/foo',
            'REQUEST_METHOD': 'POST',
        }
        map.extend(routes)
        assert map.match('/foo', environ=environ) == {}

    def test_using_func(self):
        def fred(view):
            pass

        m = Mapper()
        m.explicit = True
        m.connect('/hi/{fred}', controller=fred)

        environ = {'HTTP_HOST': 'localhost.com', 'PATH_INFO': '/hi/smith'}
        match = m.routematch(environ=environ)[0]
        environ['wsgiorg.routing_args'] = (None, match)
        url = URLGenerator(m, environ)
        assert url.current() == '/hi/smith'

    def test_using_prefix(self):
        m = Mapper()
        m.explicit = True
        m.connect('/{first}/{last}')

        environ = {'HTTP_HOST': 'localhost.com', 'PATH_INFO': '/content/index',
                   'SCRIPT_NAME': '/jones'}
        match = m.routematch(environ=environ)[0]
        environ['wsgiorg.routing_args'] = (None, match)
        url = URLGenerator(m, environ)

        assert url.current() == '/jones/content/index'
        assert url(first='smith', last='barney') == '/jones/smith/barney'

    def test_with_host_param(self):
        m = Mapper()
        m.explicit = True
        m.connect('/hi/{fred}')

        environ = {'HTTP_HOST': 'localhost.com'}
        url = URLGenerator(m, environ)
        assert url(fred='smith', host_='here') == '/hi/smith?host=here'
