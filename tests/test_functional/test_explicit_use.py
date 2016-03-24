"""test_explicit_use"""
import os, sys, time, unittest
from nose.tools import eq_, assert_raises

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

        eq_({'fred': 'george'}, m.match(environ=env))

    def test_x_forwarded(self):
        m = Mapper()
        m.explicit = True
        m.connect('/hi/{fred}')

        environ = {'HTTP_X_FORWARDED_HOST': 'localhost'}
        url = URLGenerator(m, environ)
        eq_('http://localhost/hi/smith', url(fred='smith', qualified=True))

    def test_server_port(self):
        m = Mapper()
        m.explicit = True
        m.connect('/hi/{fred}')

        environ = {'SERVER_NAME': 'localhost', 'wsgi.url_scheme': 'https',
                   'SERVER_PORT': '993'}
        url = URLGenerator(m, environ)
        eq_('https://localhost:993/hi/smith', url(fred='smith', qualified=True))

    def test_subdomain_screen(self):
        m = Mapper()
        m.explicit = True
        m.sub_domains = True
        m.connect('/hi/{fred}')

        environ = {'HTTP_HOST': 'localhost.com'}
        url = URLGenerator(m, environ)
        eq_('http://home.localhost.com/hi/smith', url(fred='smith', sub_domain=u'home', qualified=True))

        environ = {'HTTP_HOST': 'here.localhost.com', 'PATH_INFO': '/hi/smith'}
        url = URLGenerator(m, environ.copy())
        assert_raises(GenerationException, lambda: url.current(qualified=True))

        environ = {'HTTP_HOST': 'subdomain.localhost.com'}
        url = URLGenerator(m, environ.copy())
        eq_('http://sub.localhost.com/hi/smith', url(fred='smith', sub_domain='sub', qualified=True))

        environ = {'HTTP_HOST': 'sub.sub.localhost.com'}
        url = URLGenerator(m, environ.copy())
        eq_('http://new.localhost.com/hi/smith', url(fred='smith', sub_domain='new', qualified=True))

        url = URLGenerator(m, {})
        eq_('/hi/smith', url(fred='smith', sub_domain=u'home'))

    def test_anchor(self):
        m = Mapper()
        m.explicit = True
        m.connect('/hi/{fred}')

        environ = {'HTTP_HOST': 'localhost.com'}
        url = URLGenerator(m, environ)
        eq_('/hi/smith#here', url(fred='smith', anchor='here'))

    def test_static_args(self):
        m = Mapper()
        m.explicit = True
        m.connect('http://google.com/', _static=True)

        url = URLGenerator(m, {})

        eq_('/here?q=fred&q=here%20now', url('/here', q=[u'fred', 'here now']))

    def test_current(self):
        m = Mapper()
        m.explicit = True
        m.connect('/hi/{fred}')

        environ = {'HTTP_HOST': 'localhost.com', 'PATH_INFO': '/hi/smith'}
        match = m.routematch(environ=environ)[0]
        environ['wsgiorg.routing_args'] = (None, match)
        url = URLGenerator(m, environ)
        eq_('/hi/smith', url.current())

    def test_add_routes(self):
        map = Mapper(explicit=True)
        map.minimization = False
        routes = [
            Route('foo', '/foo',)
        ]
        map.extend(routes)
        eq_(map.match('/foo'), {})

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
        eq_('/hi/smith', url.current())

    def test_using_prefix(self):
        m = Mapper()
        m.explicit = True
        m.connect('/{first}/{last}')

        environ = {'HTTP_HOST': 'localhost.com', 'PATH_INFO': '/content/index',
                   'SCRIPT_NAME': '/jones'}
        match = m.routematch(environ=environ)[0]
        environ['wsgiorg.routing_args'] = (None, match)
        url = URLGenerator(m, environ)

        eq_('/jones/content/index', url.current())
        eq_('/jones/smith/barney', url(first='smith', last='barney'))

    def test_with_host_param(self):
        m = Mapper()
        m.explicit = True
        m.connect('/hi/{fred}')

        environ = {'HTTP_HOST': 'localhost.com'}
        url = URLGenerator(m, environ)
        eq_('/hi/smith?host=here', url(fred='smith', host_='here'))
