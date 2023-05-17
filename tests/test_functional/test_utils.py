"""test_utils"""
import os, sys, time, unittest

import pytest
from routes.util import controller_scan, GenerationException
from routes import *

class TestUtils(unittest.TestCase):
    def setUp(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('archive/:year/:month/:day', controller='blog', action='view', month=None, day=None,
                  requirements={'month':'\d{1,2}','day':'\d{1,2}'})
        m.connect('viewpost/:id', controller='post', action='view')
        m.connect(':controller/:action/:id')
        con = request_config()
        con.mapper = m
        con.host = 'www.test.com'
        con.protocol = 'http'
        if hasattr(con, 'environ'):
            del con.environ
        self.con = con

    def test_url_for_with_nongen(self):
        con = self.con
        con.mapper_dict = {}

        assert url_for('/blog') == '/blog'
        assert url_for('/blog', q=['fred', u'here now']) == '/blog?q=fred&q=here%20now'
        assert url_for('/blog', anchor='here') == '/blog#here'

    def test_url_for_with_nongen_no_encoding(self):
        con = self.con
        con.mapper_dict = {}
        con.mapper.encoding = None

        assert url_for('/blog') == '/blog'
        assert url_for('/blog', anchor='here') == '/blog#here'

    def test_url_for_with_unicode(self):
        con = self.con
        con.mapper_dict = {}

        assert url_for(controller='blog') == '/blog'
        assert url_for(controller='blog', action='view', id=u'umulat') == '/blog/view/umulat'
        assert url_for(controller='blog', action='view', id=u'umulat', other=u'\u03b1\u03c3\u03b4\u03b3') == '/blog/view/umulat?other=%CE%B1%CF%83%CE%B4%CE%B3'

        url = URLGenerator(con.mapper, {})
        for urlobj in [url_for, url]:
            def raise_url():
                return urlobj(u'/some/st\xc3rng')
            with pytest.raises(Exception):
                raise_url()

    def test_url_for(self):
        con = self.con
        con.mapper_dict = {}
        url = URLGenerator(con.mapper, {'HTTP_HOST':'www.test.com:80'})

        for urlobj in [url_for, url]:
            assert urlobj(controller='blog') == '/blog'
            assert urlobj() == '/content'
            assert urlobj(controller='post', action='view', protocol='https') == 'https://www.test.com/viewpost'
            assert urlobj(host='www.test.org') == 'http://www.test.org/content'
            assert urlobj(controller='post', action='view', protocol='') == '//www.test.com/viewpost'
            assert urlobj(host='www.test.org', protocol='') == '//www.test.org/content'

    def test_url_raises(self):
        con = self.con
        con.mapper.explicit = True
        con.mapper_dict = {}
        url = URLGenerator(con.mapper, {})
        with pytest.raises(GenerationException):
            url_for(action='juice')
        with pytest.raises(GenerationException):
            url(action='juice')

    def test_url_for_with_defaults(self):
        con = self.con
        con.mapper_dict = {'controller':'blog','action':'view','id':4}
        url = URLGenerator(con.mapper, {'wsgiorg.routing_args':((), con.mapper_dict)})

        assert url_for() == '/blog/view/4'
        assert url_for(controller='post') == '/post/index/4'
        assert url_for(id=2) == '/blog/view/2'
        assert url_for(controller='post', action='view', id=4) == '/viewpost/4'

        assert url.current() == '/blog/view/4'
        assert url.current(controller='post') == '/post/index/4'
        assert url.current(id=2) == '/blog/view/2'
        assert url.current(controller='post', action='view', id=4) == '/viewpost/4'

        con.mapper_dict = {'controller':'blog','action':'view','year':2004}
        url = URLGenerator(con.mapper, {'wsgiorg.routing_args':((), con.mapper_dict)})

        assert url_for(month=10) == '/archive/2004/10'
        assert url_for(month=9, day=2) == '/archive/2004/9/2'
        assert url_for(controller='blog', year=None) == '/blog'

        assert url.current(month=10) == '/archive/2004/10'
        assert url.current(month=9, day=2) == '/archive/2004/9/2'
        assert url.current(controller='blog', year=None) == '/blog'

    def test_url_for_with_more_defaults(self):
        con = self.con
        con.mapper_dict = {'controller':'blog','action':'view','id':4}
        url = URLGenerator(con.mapper, {'wsgiorg.routing_args':((), con.mapper_dict)})

        assert url_for() == '/blog/view/4'
        assert url_for(controller='post') == '/post/index/4'
        assert url_for(id=2) == '/blog/view/2'
        assert url_for(controller='post', action='view', id=4) == '/viewpost/4'

        assert url.current() == '/blog/view/4'
        assert url.current(controller='post') == '/post/index/4'
        assert url.current(id=2) == '/blog/view/2'
        assert url.current(controller='post', action='view', id=4) == '/viewpost/4'

        con.mapper_dict = {'controller':'blog','action':'view','year':2004}
        url = URLGenerator(con.mapper, {'wsgiorg.routing_args':((), con.mapper_dict)})
        assert url_for(month=10) == '/archive/2004/10'
        assert url_for(month=9, day=2) == '/archive/2004/9/2'
        assert url_for(controller='blog', year=None) == '/blog'
        assert url_for() == '/archive/2004'

        assert url.current(month=10) == '/archive/2004/10'
        assert url.current(month=9, day=2) == '/archive/2004/9/2'
        assert url.current(controller='blog', year=None) == '/blog'
        assert url.current() == '/archive/2004'

    def test_url_for_with_defaults_and_qualified(self):
        m = self.con.mapper
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])
        self.con.environ = dict(SCRIPT_NAME='', HTTP_HOST='www.example.com', PATH_INFO='/blog/view/4')
        self.con.environ.update({'wsgiorg.routing_args':((), self.con.mapper_dict)})
        url = URLGenerator(m, self.con.environ)

        assert url_for() == '/blog/view/4'
        assert url_for(controller='post') == '/post/index/4'
        assert url_for(qualified=True) == 'http://www.example.com/blog/view/4'
        assert url_for(id=2) == '/blog/view/2'
        assert url_for(controller='post', action='view', id=4) == '/viewpost/4'

        assert url.current() == '/blog/view/4'
        assert url.current(controller='post') == '/post/index/4'
        assert url.current(qualified=True) == 'http://www.example.com/blog/view/4'
        assert url.current(id=2) == '/blog/view/2'
        assert url.current(controller='post', action='view', id=4) == '/viewpost/4'

        env = dict(SCRIPT_NAME='', SERVER_NAME='www.example.com', SERVER_PORT='8080', PATH_INFO='/blog/view/4')
        env['wsgi.url_scheme'] = 'http'
        self.con.environ = env
        self.con.environ.update({'wsgiorg.routing_args':((), self.con.mapper_dict)})
        url = URLGenerator(m, self.con.environ)

        assert url_for(controller='post') == '/post/index/4'
        assert url_for(qualified=True) == 'http://www.example.com:8080/blog/view/4'

        assert url.current(controller='post') == '/post/index/4'
        assert url.current(qualified=True) == 'http://www.example.com:8080/blog/view/4'

    def test_route_overflow(self):
        m = self.con.mapper
        m.create_regs(["x"*50000])
        m.connect('route-overflow', "x"*50000)
        url = URLGenerator(m, {})
        assert url('route-overflow') == "/%s" % ("x"*50000)

    def test_with_route_names(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.create_regs(['content','blog','admin/comments'])
        url = URLGenerator(m, {})

        for urlobj in [url, url_for]:
            assert urlobj(controller='content', action='view') == '/content/view'
            assert urlobj(controller='content') == '/content'
            assert urlobj(controller='admin/comments') == '/admin/comments'
            assert urlobj('category_home') == '/category'
            assert urlobj('category_home', section='food') == '/category/food'
            assert urlobj('home') == '/'

    def test_with_route_names_and_defaults(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.connect('building', 'building/:campus/:building/alljacks', controller='building', action='showjacks')
        m.create_regs(['content','blog','admin/comments','building'])

        self.con.mapper_dict = dict(controller='building', action='showjacks', campus='wilma', building='port')
        url = URLGenerator(m, {'wsgiorg.routing_args':((), self.con.mapper_dict)})

        assert url_for() == '/building/wilma/port/alljacks'
        assert url_for('home') == '/'
        assert url.current() == '/building/wilma/port/alljacks'
        assert url.current('home') == '/'

    def test_with_route_names_and_hardcode(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        m.hardcode_names = False

        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.connect('building', 'building/:campus/:building/alljacks', controller='building', action='showjacks')
        m.connect('gallery_thumb', 'gallery/:(img_id)_thumbnail.jpg')
        m.connect('gallery', 'gallery/:(img_id).jpg')
        m.create_regs(['content','blog','admin/comments','building'])

        self.con.mapper_dict = dict(controller='building', action='showjacks', campus='wilma', building='port')
        url = URLGenerator(m, {'wsgiorg.routing_args':((), self.con.mapper_dict)})
        assert url_for() == '/building/wilma/port/alljacks'
        assert url_for('home') == '/'
        assert url_for('gallery_thumb', img_id='home') == '/gallery/home_thumbnail.jpg'
        assert url_for('gallery', img_id='home') == '/gallery/home_thumbnail.jpg'

        assert url.current() == '/building/wilma/port/alljacks'
        assert url.current('home') == '/'
        assert url.current('gallery_thumb', img_id='home') == '/gallery/home_thumbnail.jpg'
        assert url.current('gallery', img_id='home') == '/gallery/home_thumbnail.jpg'

        m.hardcode_names = True
        assert url_for('gallery_thumb', img_id='home') == '/gallery/home_thumbnail.jpg'
        assert url_for('gallery', img_id='home') == '/gallery/home.jpg'

        assert url.current('gallery_thumb', img_id='home') == '/gallery/home_thumbnail.jpg'
        assert url.current('gallery', img_id='home') == '/gallery/home.jpg'
        m.hardcode_names = False

    def test_redirect_to(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        self.con.environ = dict(SCRIPT_NAME='', HTTP_HOST='www.example.com')
        result = None
        def printer(echo):
            redirect_to.result = echo
        self.con.redirect = printer
        m.create_regs(['content','blog','admin/comments'])

        redirect_to(controller='content', action='view')
        assert redirect_to.result == '/content/view'
        redirect_to(controller='content', action='lookup', id=4)
        assert redirect_to.result == '/content/lookup/4'
        redirect_to(controller='admin/comments',action='splash')
        assert redirect_to.result == '/admin/comments/splash'
        redirect_to('http://www.example.com/')
        assert redirect_to.result == 'http://www.example.com/'
        redirect_to('/somewhere.html', var='keyword')
        assert redirect_to.result == '/somewhere.html?var=keyword'

    def test_redirect_to_with_route_names(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        result = None
        def printer(echo):
            redirect_to.result = echo
        self.con.redirect = printer
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.create_regs(['content','blog','admin/comments'])

        redirect_to(controller='content', action='view')
        assert redirect_to.result == '/content/view'
        redirect_to(controller='content')
        assert redirect_to.result == '/content'
        redirect_to(controller='admin/comments')
        assert redirect_to.result == '/admin/comments'
        redirect_to('category_home')
        assert redirect_to.result == '/category'
        redirect_to('category_home', section='food')
        assert redirect_to.result == '/category/food'
        redirect_to('home')
        assert redirect_to.result == '/'

    def test_static_route(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        self.con.environ = dict(SCRIPT_NAME='', HTTP_HOST='example.com')
        m.connect(':controller/:action/:id')
        m.connect('home', 'http://www.groovie.org/', _static=True)
        m.connect('space', '/nasa/images', _static=True)
        m.create_regs(['content', 'blog'])

        url = URLGenerator(m, {})
        for urlobj in [url_for, url]:
            assert urlobj('home') == 'http://www.groovie.org/'
            assert urlobj('home', s='stars') == 'http://www.groovie.org/?s=stars'
            assert urlobj(controller='content', action='view') == '/content/view'
            assert urlobj('space', search='all') == '/nasa/images?search=all'

    def test_static_route_with_script(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        self.con.environ = dict(SCRIPT_NAME='/webapp', HTTP_HOST='example.com')
        m.connect(':controller/:action/:id')
        m.connect('home', 'http://www.groovie.org/', _static=True)
        m.connect('space', '/nasa/images', _static=True)
        m.connect('login', '/login', action='nowhereville')
        m.create_regs(['content', 'blog'])

        self.con.environ.update({'wsgiorg.routing_args':((), {})})
        url = URLGenerator(m, self.con.environ)
        for urlobj in [url_for, url]:
            assert urlobj('home') == 'http://www.groovie.org/'
            assert urlobj('home', s='stars') == 'http://www.groovie.org/?s=stars'
            assert urlobj(controller='content', action='view') == '/webapp/content/view'
            assert urlobj('space', search='all') == '/webapp/nasa/images?search=all'
            assert urlobj('space', protocol='http') == 'http://example.com/webapp/nasa/images'
            assert urlobj('login', qualified=True) == 'http://example.com/webapp/login'

    def test_static_route_with_vars(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        self.con.environ = dict(SCRIPT_NAME='/webapp', HTTP_HOST='example.com')
        m.connect('home', 'http://{domain}.groovie.org/{location}', _static=True)
        m.connect('space', '/nasa/{location}', _static=True)
        m.create_regs(['home', 'space'])

        self.con.environ.update({'wsgiorg.routing_args':((), {})})
        url = URLGenerator(m, self.con.environ)
        for urlobj in [url_for, url]:
            with pytest.raises(GenerationException):
                urlobj('home')
            with pytest.raises(GenerationException):
                urlobj('home', domain='fred')
            with pytest.raises(GenerationException):
                urlobj('home', location='index')
            assert urlobj('home', domain='fred', location='index') == 'http://fred.groovie.org/index'
            assert urlobj('home', domain='fred', location='index', search='all') == 'http://fred.groovie.org/index?search=all'
            assert urlobj('space', location='images', search='all') == '/webapp/nasa/images?search=all'
            assert urlobj('space', location='images', protocol='http') == 'http://example.com/webapp/nasa/images'

    def test_static_route_with_vars_and_defaults(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        self.con.environ = dict(SCRIPT_NAME='/webapp', HTTP_HOST='example.com')
        m.connect('home', 'http://{domain}.groovie.org/{location}', domain='routes', _static=True)
        m.connect('space', '/nasa/{location}', location='images', _static=True)
        m.create_regs(['home', 'space'])

        self.con.environ.update({'wsgiorg.routing_args':((), {})})
        url = URLGenerator(m, self.con.environ)

        with pytest.raises(GenerationException):
            url_for('home')
        with pytest.raises(GenerationException):
            url_for('home', domain='fred')
        assert url_for('home', location='index') == 'http://routes.groovie.org/index'
        assert url_for('home', domain='fred', location='index') == 'http://fred.groovie.org/index'
        assert url_for('home', location='index', search='all') == 'http://routes.groovie.org/index?search=all'
        assert url_for('home', domain='fred', location='index', search='all') == 'http://fred.groovie.org/index?search=all'
        assert url_for('space', location='articles', search='all') == '/webapp/nasa/articles?search=all'
        assert url_for('space', location='articles', protocol='http') == 'http://example.com/webapp/nasa/articles'
        assert url_for('space', search='all') == '/webapp/nasa/images?search=all'
        assert url_for('space', protocol='http') == 'http://example.com/webapp/nasa/images'

        with pytest.raises(GenerationException):
            url.current('home')
        with pytest.raises(GenerationException):
            url.current('home', domain='fred')
        assert url.current('home', location='index') == 'http://routes.groovie.org/index'
        assert url.current('home', domain='fred', location='index') == 'http://fred.groovie.org/index'
        assert url.current('home', location='index', search='all') == 'http://routes.groovie.org/index?search=all'
        assert url.current('home', domain='fred', location='index', search='all') == 'http://fred.groovie.org/index?search=all'
        assert url.current('space', location='articles', search='all') == '/webapp/nasa/articles?search=all'
        assert url.current('space', location='articles', protocol='http') == 'http://example.com/webapp/nasa/articles'
        assert url.current('space', search='all') == '/webapp/nasa/images?search=all'
        assert url.current('space', protocol='http') == 'http://example.com/webapp/nasa/images'


    def test_static_route_with_vars_and_requirements(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        self.con.environ = dict(SCRIPT_NAME='/webapp', HTTP_HOST='example.com')
        m.connect('home', 'http://{domain}.groovie.org/{location}', requirements=dict(domain='fred|bob'), _static=True)
        m.connect('space', '/nasa/articles/{year}/{month}', requirements=dict(year=r'\d{2,4}', month=r'\d{1,2}'), _static=True)
        m.create_regs(['home', 'space'])


        self.con.environ.update({'wsgiorg.routing_args':((), {})})
        url = URLGenerator(m, self.con.environ)

        with pytest.raises(GenerationException):
            url_for('home', domain='george', location='index')
        with pytest.raises(GenerationException):
            url_for('space', year='asdf', month='1')
        with pytest.raises(GenerationException):
            url_for('space', year='2004', month='a')
        with pytest.raises(GenerationException):
            url_for('space', year='1', month='1')
        with pytest.raises(GenerationException):
            url_for('space', year='20045', month='1')
        with pytest.raises(GenerationException):
            url_for('space', year='2004', month='123')
        assert url_for('home', domain='fred', location='index') == 'http://fred.groovie.org/index'
        assert url_for('home', domain='bob', location='index') == 'http://bob.groovie.org/index'
        assert url_for('home', domain='fred', location='asdf') == 'http://fred.groovie.org/asdf'
        assert url_for('space', year='2004', month='6') == '/webapp/nasa/articles/2004/6'
        assert url_for('space', year='2004', month='12') == '/webapp/nasa/articles/2004/12'
        assert url_for('space', year='89', month='6') == '/webapp/nasa/articles/89/6'

        with pytest.raises(GenerationException):
            url.current('home', domain='george', location='index')
        with pytest.raises(GenerationException):
            url.current('space', year='asdf', month='1')
        with pytest.raises(GenerationException):
            url.current('space', year='2004', month='a')
        with pytest.raises(GenerationException):
            url.current('space', year='1', month='1')
        with pytest.raises(GenerationException):
            url.current('space', year='20045', month='1')
        with pytest.raises(GenerationException):
            url.current('space', year='2004', month='123')
        assert url.current('home', domain='fred', location='index') == 'http://fred.groovie.org/index'
        assert url.current('home', domain='bob', location='index') == 'http://bob.groovie.org/index'
        assert url.current('home', domain='fred', location='asdf') == 'http://fred.groovie.org/asdf'
        assert url.current('space', year='2004', month='6') == '/webapp/nasa/articles/2004/6'
        assert url.current('space', year='2004', month='12') == '/webapp/nasa/articles/2004/12'
        assert url.current('space', year='89', month='6') == '/webapp/nasa/articles/89/6'

    def test_no_named_path(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        self.con.environ = dict(SCRIPT_NAME='', HTTP_HOST='example.com')
        m.connect(':controller/:action/:id')
        m.connect('home', 'http://www.groovie.org/', _static=True)
        m.connect('space', '/nasa/images', _static=True)
        m.create_regs(['content', 'blog'])

        url = URLGenerator(m, {})
        for urlobj in [url_for, url]:
            assert urlobj('http://www.google.com/search') == 'http://www.google.com/search'
            assert urlobj('http://www.google.com/search', q='routes') == 'http://www.google.com/search?q=routes'
            assert urlobj('/delicious.jpg') == '/delicious.jpg'
            assert urlobj('/delicious/search', v='routes') == '/delicious/search?v=routes'

    def test_append_slash(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        m.append_slash = True
        self.con.environ = dict(SCRIPT_NAME='', HTTP_HOST='example.com')
        m.connect(':controller/:action/:id')
        m.connect('home', 'http://www.groovie.org/', _static=True)
        m.connect('space', '/nasa/images', _static=True)
        m.create_regs(['content', 'blog'])

        url = URLGenerator(m, {})
        for urlobj in [url_for, url]:
            assert urlobj('http://www.google.com/search') == 'http://www.google.com/search'
            assert urlobj('http://www.google.com/search', q='routes') == 'http://www.google.com/search?q=routes'
            assert urlobj('/delicious.jpg') == '/delicious.jpg'
            assert urlobj('/delicious/search', v='routes') == '/delicious/search?v=routes'
            assert urlobj(controller='/content', action='list') == '/content/list/'
            assert urlobj(controller='/content', action='list', page='1') == '/content/list/?page=1'

    def test_no_named_path_with_script(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        self.con.environ = dict(SCRIPT_NAME='/webapp', HTTP_HOST='example.com')
        m.connect(':controller/:action/:id')
        m.connect('home', 'http://www.groovie.org/', _static=True)
        m.connect('space', '/nasa/images', _static=True)
        m.create_regs(['content', 'blog'])

        url = URLGenerator(m, self.con.environ)
        for urlobj in [url_for, url]:
            assert urlobj('http://www.google.com/search') == 'http://www.google.com/search'
            assert urlobj('http://www.google.com/search', q='routes') == 'http://www.google.com/search?q=routes'
            assert urlobj('/delicious.jpg') == '/webapp/delicious.jpg'
            assert urlobj('/delicious/search', v='routes') == '/webapp/delicious/search?v=routes'

    def test_route_filter(self):
        def article_filter(kargs):
            article = kargs.pop('article', None)
            if article is not None:
                kargs.update(
                    dict(year=article.get('year', 2004),
                         month=article.get('month', 12),
                         day=article.get('day', 20),
                         slug=article.get('slug', 'default')
                    )
                )
            return kargs

        self.con.mapper_dict = {}
        self.con.environ = dict(SCRIPT_NAME='', HTTP_HOST='example.com')

        m = Mapper(explicit=False)
        m.minimization = True
        m.connect(':controller/:(action)-:(id).html')
        m.connect('archives', 'archives/:year/:month/:day/:slug', controller='archives', action='view',
                  _filter=article_filter)
        m.create_regs(['content','archives','admin/comments'])
        self.con.mapper = m

        url = URLGenerator(m, self.con.environ)
        for urlobj in [url_for, url]:
            with pytest.raises(Exception):
                urlobj(controller='content', action='view')
            with pytest.raises(Exception):
                urlobj(controller='content')

            assert urlobj(controller='content', action='view', id=3) == '/content/view-3.html'
            assert urlobj(controller='content', id=2) == '/content/index-2.html'

            assert urlobj('archives', year=2005, month=10, day=5, slug='happy') == '/archives/2005/10/5/happy'
            story = dict(year=2003, month=8, day=2, slug='woopee')
            empty = {}
            assert m.match('/archives/2005/10/5/happy') == {'controller':'archives','action':'view','year':'2005','month':'10','day':'5','slug':'happy'}
            assert urlobj('archives', article=story) == '/archives/2003/8/2/woopee'
            assert urlobj('archives', article=empty) == '/archives/2004/12/20/default'

    def test_with_ssl_environ(self):
        base_environ = dict(SCRIPT_NAME='', HTTPS='on', SERVER_PORT='443', PATH_INFO='/',
            HTTP_HOST='example.com', SERVER_NAME='example.com')
        self.con.mapper_dict = {}
        self.con.environ = base_environ.copy()

        m = Mapper(explicit=False)
        m.minimization = True
        m.connect(':controller/:action/:id')
        m.create_regs(['content','archives','admin/comments'])
        m.sub_domains = True
        self.con.mapper = m

        url = URLGenerator(m, self.con.environ)
        for urlobj in [url_for, url]:

            # HTTPS is on, but we're running on a different port internally
            assert self.con.protocol == 'https'
            assert urlobj(controller='content', action='view') == '/content/view'
            assert urlobj(controller='content', id=2) == '/content/index/2'
            assert urlobj(host='nowhere.com', controller='content') == 'https://nowhere.com/content'

            # If HTTPS is on, but the port isn't 443, we'll need to include the port info
            environ = base_environ.copy()
            environ.update(dict(SERVER_PORT='8080'))
            self.con.environ = environ
            self.con.mapper_dict = {}
            assert urlobj(controller='content', id=2) == '/content/index/2'
            assert urlobj(host='nowhere.com', controller='content') == 'https://nowhere.com/content'
            assert urlobj(host='nowhere.com:8080', controller='content') == 'https://nowhere.com:8080/content'
            assert urlobj(host='nowhere.com', protocol='http', controller='content') == 'http://nowhere.com/content'
            assert urlobj(host='home.com', protocol='http', controller='content') == 'http://home.com/content'


    def test_with_http_environ(self):
        base_environ = dict(SCRIPT_NAME='', SERVER_PORT='1080', PATH_INFO='/',
            HTTP_HOST='example.com', SERVER_NAME='example.com')
        base_environ['wsgi.url_scheme'] = 'http'
        self.con.environ = base_environ.copy()
        self.con.mapper_dict = {}

        m = Mapper(explicit=False)
        m.minimization = True
        m.connect(':controller/:action/:id')
        m.create_regs(['content','archives','admin/comments'])
        self.con.mapper = m

        url = URLGenerator(m, self.con.environ)
        for urlobj in [url_for, url]:
            assert self.con.protocol == 'http'
            assert urlobj(controller='content', action='view') == '/content/view'
            assert urlobj(controller='content', id=2) == '/content/index/2'
            assert urlobj(protocol='https', controller='content') == 'https://example.com/content'


    def test_subdomains(self):
        base_environ = dict(SCRIPT_NAME='', PATH_INFO='/', HTTP_HOST='example.com', SERVER_NAME='example.com')
        self.con.mapper_dict = {}
        self.con.environ = base_environ.copy()

        m = Mapper(explicit=False)
        m.minimization = True
        m.sub_domains = True
        m.connect(':controller/:action/:id')
        m.create_regs(['content','archives','admin/comments'])
        self.con.mapper = m

        url = URLGenerator(m, self.con.environ)
        for urlobj in [url_for, url]:
            assert urlobj(controller='content', action='view') == '/content/view'
            assert urlobj(controller='content', id=2) == '/content/index/2'
            environ = base_environ.copy()
            environ.update(dict(HTTP_HOST='sub.example.com'))
            self.con.environ = environ
            self.con.mapper_dict = {'sub_domain':'sub'}
            assert urlobj(controller='content', action='view', id=3) == '/content/view/3'
            assert urlobj(controller='content', sub_domain='new') == 'http://new.example.com/content'

    def test_subdomains_with_exceptions(self):
        base_environ = dict(SCRIPT_NAME='', PATH_INFO='/', HTTP_HOST='example.com', SERVER_NAME='example.com')
        self.con.mapper_dict = {}
        self.con.environ = base_environ.copy()

        m = Mapper(explicit=False)
        m.minimization = True
        m.sub_domains = True
        m.sub_domains_ignore = ['www']
        m.connect(':controller/:action/:id')
        m.create_regs(['content','archives','admin/comments'])
        self.con.mapper = m

        url = URLGenerator(m, self.con.environ)
        assert url_for(controller='content', action='view') == '/content/view'
        assert url_for(controller='content', id=2) == '/content/index/2'
        assert url(controller='content', action='view') == '/content/view'
        assert url(controller='content', id=2) == '/content/index/2'

        environ = base_environ.copy()
        environ.update(dict(HTTP_HOST='sub.example.com'))
        self.con.environ = environ
        self.con.mapper_dict = {'sub_domain':'sub'}
        self.con.environ.update({'wsgiorg.routing_args':((), self.con.mapper_dict)})
        url = URLGenerator(m, self.con.environ)

        assert url_for(controller='content', action='view', id=3) == '/content/view/3'
        assert url_for(controller='content', sub_domain='new') == 'http://new.example.com/content'
        assert url_for(controller='content', sub_domain='www') == 'http://example.com/content'
        assert url(controller='content', action='view', id=3) == '/content/view/3'
        assert url(controller='content', sub_domain='new') == 'http://new.example.com/content'
        assert url(controller='content', sub_domain='www') == 'http://example.com/content'

        self.con.mapper_dict = {'sub_domain':'www'}
        self.con.environ.update({'wsgiorg.routing_args':((), self.con.mapper_dict)})
        url = URLGenerator(m, self.con.environ)

        assert url_for(controller='content', action='view', id=3) == 'http://example.com/content/view/3'
        assert url_for(controller='content', sub_domain='new') == 'http://new.example.com/content'
        assert url_for(controller='content', sub_domain='sub') == '/content'

        # This requires the sub-domain, because we don't automatically go to the existing match dict
        assert url(controller='content', action='view', id=3, sub_domain='www') == 'http://example.com/content/view/3'
        assert url(controller='content', sub_domain='new') == 'http://new.example.com/content'
        assert url(controller='content', sub_domain='sub') == '/content'

    def test_subdomains_with_named_routes(self):
        base_environ = dict(SCRIPT_NAME='', PATH_INFO='/', HTTP_HOST='example.com', SERVER_NAME='example.com')
        self.con.mapper_dict = {}
        self.con.environ = base_environ.copy()

        m = Mapper(explicit=False)
        m.minimization = True
        m.sub_domains = True
        m.connect(':controller/:action/:id')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.connect('building', 'building/:campus/:building/alljacks', controller='building', action='showjacks')
        m.create_regs(['content','blog','admin/comments','building'])
        self.con.mapper = m

        url = URLGenerator(m, self.con.environ)
        for urlobj in [url_for, url]:
            assert urlobj(controller='content', action='view') == '/content/view'
            assert urlobj(controller='content', id=2) == '/content/index/2'
            assert urlobj('category_home') == '/category'
            assert urlobj('category_home', sub_domain='new') == 'http://new.example.com/category'

        environ = base_environ.copy()
        environ.update(dict(HTTP_HOST='sub.example.com'))
        self.con.environ = environ
        self.con.mapper_dict = {'sub_domain':'sub'}
        self.con.environ.update({'wsgiorg.routing_args':((), self.con.mapper_dict)})
        url = URLGenerator(m, self.con.environ)

        assert url_for(controller='content', action='view', id=3) == '/content/view/3'
        assert url_for('building', campus='west', building='merlot', sub_domain='joy') == 'http://joy.example.com/building/west/merlot/alljacks'
        assert url_for('category_home', section='feeds', sub_domain=None) == 'http://example.com/category/feeds'

        assert url(controller='content', action='view', id=3) == '/content/view/3'
        assert url('building', campus='west', building='merlot', sub_domain='joy') == 'http://joy.example.com/building/west/merlot/alljacks'
        assert url('category_home', section='feeds', sub_domain=None) == 'http://example.com/category/feeds'


    def test_subdomains_with_ports(self):
        base_environ = dict(SCRIPT_NAME='', PATH_INFO='/', HTTP_HOST='example.com:8000', SERVER_NAME='example.com')
        self.con.mapper_dict = {}
        self.con.environ = base_environ.copy()

        m = Mapper(explicit=False)
        m.minimization = True
        m.sub_domains = True
        m.connect(':controller/:action/:id')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.connect('building', 'building/:campus/:building/alljacks', controller='building', action='showjacks')
        m.create_regs(['content','blog','admin/comments','building'])
        self.con.mapper = m

        url = URLGenerator(m, self.con.environ)
        for urlobj in [url, url_for]:
            self.con.environ['HTTP_HOST'] = 'example.com:8000'
            assert urlobj(controller='content', action='view') == '/content/view'
            assert urlobj('category_home') == '/category'
            assert urlobj('category_home', sub_domain='new') == 'http://new.example.com:8000/category'
            assert urlobj('building', campus='west', building='merlot', sub_domain='joy') == 'http://joy.example.com:8000/building/west/merlot/alljacks'

            self.con.environ['HTTP_HOST'] = 'example.com'
            del self.con.environ['routes.cached_hostinfo']
            assert urlobj('category_home', sub_domain='new') == 'http://new.example.com/category'

    def test_subdomains_with_default(self):
        base_environ = dict(SCRIPT_NAME='', PATH_INFO='/', HTTP_HOST='example.com:8000', SERVER_NAME='example.com')
        self.con.mapper_dict = {}
        self.con.environ = base_environ.copy()

        m = Mapper(explicit=False)
        m.minimization = True
        m.sub_domains = True
        m.connect(':controller/:action/:id')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home',
                  sub_domain='cat', conditions=dict(sub_domain=['cat']))
        m.connect('building', 'building/:campus/:building/alljacks', controller='building', action='showjacks')
        m.create_regs(['content','blog','admin/comments','building'])
        self.con.mapper = m

        urlobj = URLGenerator(m, self.con.environ)
        self.con.environ['HTTP_HOST'] = 'example.com:8000'
        assert urlobj(controller='content', action='view') == '/content/view'
        assert urlobj('category_home') == 'http://cat.example.com:8000/category'

        self.con.environ['HTTP_HOST'] = 'example.com'
        del self.con.environ['routes.cached_hostinfo']

        with pytest.raises(GenerationException):
            urlobj('category_home', sub_domain='new')


    def test_controller_scan(self):
        here_dir = os.path.dirname(__file__)
        controller_dir = os.path.join(os.path.dirname(here_dir),
            os.path.join('test_files', 'controller_files'))
        controllers = controller_scan(controller_dir)
        assert len(controllers) == 3
        assert controllers[0] == 'admin/users'
        assert controllers[1] == 'content'
        assert controllers[2] == 'users'

    def test_auto_controller_scan(self):
        here_dir = os.path.dirname(__file__)
        controller_dir = os.path.join(os.path.dirname(here_dir),
            os.path.join('test_files', 'controller_files'))
        m = Mapper(directory=controller_dir, explicit=False)
        m.minimization = True
        m.always_scan = True
        m.connect(':controller/:action/:id')

        assert m.match('/content') == {'action':'index', 'controller':'content','id':None}
        assert m.match('/users') == {'action':'index', 'controller':'users','id':None}
        assert m.match('/admin/users') == {'action':'index', 'controller':'admin/users','id':None}

class TestUtilsWithExplicit(unittest.TestCase):
    def setUp(self):
        m = Mapper(explicit=True)
        m.minimization = True
        m.connect('archive/:year/:month/:day', controller='blog', action='view', month=None, day=None,
                  requirements={'month':'\d{1,2}','day':'\d{1,2}'})
        m.connect('viewpost/:id', controller='post', action='view', id=None)
        m.connect(':controller/:action/:id')
        con = request_config()
        con.mapper = m
        con.host = 'www.test.com'
        con.protocol = 'http'
        self.con = con

    def test_url_for(self):
        con = self.con
        con.mapper_dict = {}

        with pytest.raises(Exception):
            url_for(controller='blog')
        with pytest.raises(Exception):
            url_for()
        assert url_for(controller='blog', action='view', id=3) == '/blog/view/3'
        assert url_for(controller='post', action='view', protocol='https') == 'https://www.test.com/viewpost'
        assert url_for(host='www.test.org', controller='content', action='view', id=2) == 'http://www.test.org/content/view/2'

    def test_url_for_with_defaults(self):
        con = self.con
        con.mapper_dict = {'controller':'blog','action':'view','id':4}

        with pytest.raises(Exception):
            url_for()
        with pytest.raises(Exception):
            url_for(controller='post')
        with pytest.raises(Exception):
            url_for(id=2)
        assert url_for(controller='post', action='view', id=4) == '/viewpost/4'

        con.mapper_dict = {'controller':'blog','action':'view','year':2004}
        with pytest.raises(Exception):
            url_for(month=10)
        with pytest.raises(Exception):
            url_for(month=9, day=2)
        with pytest.raises(Exception):
            url_for(controller='blog', year=None)

    def test_url_for_with_more_defaults(self):
        con = self.con
        con.mapper_dict = {'controller':'blog','action':'view','id':4}

        with pytest.raises(Exception):
            url_for()
        with pytest.raises(Exception):
            url_for(controller='post')
        with pytest.raises(Exception):
            url_for(id=2)
        assert url_for(controller='post', action='view', id=4) == '/viewpost/4'

        con.mapper_dict = {'controller':'blog','action':'view','year':2004}
        with pytest.raises(Exception):
            url_for(month=10)
        with pytest.raises(Exception):
            url_for()

    def test_url_for_with_defaults_and_qualified(self):
        m = self.con.mapper
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])
        env = dict(SCRIPT_NAME='', SERVER_NAME='www.example.com', SERVER_PORT='80', PATH_INFO='/blog/view/4')
        env['wsgi.url_scheme'] = 'http'

        self.con.environ = env

        with pytest.raises(Exception):
            url_for()
        with pytest.raises(Exception):
            url_for(controller='post')
        with pytest.raises(Exception):
            url_for(id=2)
        with pytest.raises(Exception):
            url_for(qualified=True, controller='blog', id=4)
        assert url_for(qualified=True, controller='blog', action='view', id=4) == 'http://www.example.com/blog/view/4'
        assert url_for(controller='post', action='view', id=4) == '/viewpost/4'

        env = dict(SCRIPT_NAME='', SERVER_NAME='www.example.com', SERVER_PORT='8080', PATH_INFO='/blog/view/4')
        env['wsgi.url_scheme'] = 'http'
        self.con.environ = env
        with pytest.raises(Exception):
            url_for(controller='post')
        assert url_for(qualified=True, controller='blog', action='view', id=4) == 'http://www.example.com:8080/blog/view/4'


    def test_with_route_names(self):
        m = self.con.mapper
        m.minimization = True
        self.con.mapper_dict = {}
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.create_regs(['content','blog','admin/comments'])

        with pytest.raises(Exception):
            url_for(controller='content', action='view')
        with pytest.raises(Exception):
            url_for(controller='content')
        with pytest.raises(Exception):
            url_for(controller='admin/comments')
        assert url_for('category_home') == '/category'
        assert url_for('category_home', section='food') == '/category/food'
        with pytest.raises(Exception):
            url_for('home', controller='content')
        assert url_for('home') == '/'

    def test_with_route_names_and_nomin(self):
        m = self.con.mapper
        m.minimization = False
        self.con.mapper_dict = {}
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.create_regs(['content','blog','admin/comments'])

        with pytest.raises(Exception):
            url_for(controller='content', action='view')
        with pytest.raises(Exception):
            url_for(controller='content')
        with pytest.raises(Exception):
            url_for(controller='admin/comments')
        assert url_for('category_home') == '/category/home'
        assert url_for('category_home', section='food') == '/category/food'
        with pytest.raises(Exception):
            url_for('home', controller='content')
        assert url_for('home') == '/'

    def test_with_route_names_and_defaults(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.connect('building', 'building/:campus/:building/alljacks', controller='building', action='showjacks')
        m.create_regs(['content','blog','admin/comments','building'])

        self.con.mapper_dict = dict(controller='building', action='showjacks', campus='wilma', building='port')
        with pytest.raises(Exception):
            url_for()
        assert url_for(controller='building', action='showjacks', campus='wilma', building='port') == '/building/wilma/port/alljacks'
        assert url_for('home') == '/'

    def test_with_resource_route_names(self):
        m = Mapper()
        self.con.mapper = m
        self.con.mapper_dict = {}
        m.resource('message', 'messages', member={'mark':'GET'}, collection={'rss':'GET'})
        m.create_regs(['messages'])

        with pytest.raises(Exception):
            url_for(controller='content', action='view')
        with pytest.raises(Exception):
            url_for(controller='content')
        with pytest.raises(Exception):
            url_for(controller='admin/comments')
        assert url_for('messages') == '/messages'
        assert url_for('rss_messages') == '/messages/rss'
        assert url_for('message', id=4) == '/messages/4'
        assert url_for('edit_message', id=4) == '/messages/4/edit'
        assert url_for('mark_message', id=4) == '/messages/4/mark'
        assert url_for('new_message') == '/messages/new'

        assert url_for('formatted_messages', format='xml') == '/messages.xml'
        assert url_for('formatted_rss_messages', format='xml') == '/messages/rss.xml'
        assert url_for('formatted_message', id=4, format='xml') == '/messages/4.xml'
        assert url_for('formatted_edit_message', id=4, format='xml') == '/messages/4/edit.xml'
        assert url_for('formatted_mark_message', id=4, format='xml') == '/messages/4/mark.xml'
        assert url_for('formatted_new_message', format='xml') == '/messages/new.xml'

    def test_with_resource_route_names_and_nomin(self):
        m = Mapper()
        self.con.mapper = m
        self.con.mapper_dict = {}
        m.minimization = False
        m.resource('message', 'messages', member={'mark':'GET'}, collection={'rss':'GET'})
        m.create_regs(['messages'])

        with pytest.raises(Exception):
            url_for(controller='content', action='view')
        with pytest.raises(Exception):
            url_for(controller='content')
        with pytest.raises(Exception):
            url_for(controller='admin/comments')
        assert url_for('messages') == '/messages'
        assert url_for('rss_messages') == '/messages/rss'
        assert url_for('message', id=4) == '/messages/4'
        assert url_for('edit_message', id=4) == '/messages/4/edit'
        assert url_for('mark_message', id=4) == '/messages/4/mark'
        assert url_for('new_message') == '/messages/new'

        assert url_for('formatted_messages', format='xml') == '/messages.xml'
        assert url_for('formatted_rss_messages', format='xml') == '/messages/rss.xml'
        assert url_for('formatted_message', id=4, format='xml') == '/messages/4.xml'
        assert url_for('formatted_edit_message', id=4, format='xml') == '/messages/4/edit.xml'
        assert url_for('formatted_mark_message', id=4, format='xml') == '/messages/4/mark.xml'
        assert url_for('formatted_new_message', format='xml') == '/messages/new.xml'


if __name__ == '__main__':
    unittest.main()
else:
    def bench_gen(withcache = False):
        m = Mapper(explicit=False)
        m.connect('', controller='articles', action='index')
        m.connect('admin', controller='admin/general', action='index')

        m.connect('admin/comments/article/:article_id/:action/:id', controller = 'admin/comments', action = None, id=None)
        m.connect('admin/trackback/article/:article_id/:action/:id', controller='admin/trackback', action=None, id=None)
        m.connect('admin/content/:action/:id', controller='admin/content')

        m.connect('xml/:action/feed.xml', controller='xml')
        m.connect('xml/articlerss/:id/feed.xml', controller='xml', action='articlerss')
        m.connect('index.rdf', controller='xml', action='rss')

        m.connect('articles', controller='articles', action='index')
        m.connect('articles/page/:page', controller='articles', action='index', requirements = {'page':'\d+'})

        m.connect('articles/:year/:month/:day/page/:page', controller='articles', action='find_by_date', month = None, day = None,
                            requirements = {'year':'\d{4}', 'month':'\d{1,2}','day':'\d{1,2}'})
        m.connect('articles/category/:id', controller='articles', action='category')
        m.connect('pages/*name', controller='articles', action='view_page')
        con = Config()
        con.mapper = m
        con.host = 'www.test.com'
        con.protocol = 'http'
        con.mapper_dict = {'controller':'xml','action':'articlerss'}

        if withcache:
            m.urlcache = {}
        m._create_gens()
        n = 5000
        start = time.time()
        for x in range(1,n):
            url_for(controller='/articles', action='index', page=4)
            url_for(controller='admin/general', action='index')
            url_for(controller='admin/comments', action='show', article_id=2)

            url_for(controller='articles', action='find_by_date', year=2004, page=1)
            url_for(controller='articles', action='category', id=4)
            url_for(id=2)
        end = time.time()
        ts = time.time()
        for x in range(1,n*6):
            pass
        en = time.time()
        total = end-start-(en-ts)
        per_url = total / (n*6)
        print("Generation (%s URLs) RouteSet" % (n*6))
        print("%s ms/url" % (per_url*1000))
        print("%s urls/s\n" % (1.00/per_url))
