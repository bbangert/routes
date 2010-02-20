"""test_explicit_use"""
import os, sys, time, unittest
from nose.tools import eq_, assert_raises

from routes import *
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
        url = URLGenerator(m, environ)
        assert_raises(GenerationException, lambda: url.current(qualified=True))

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
