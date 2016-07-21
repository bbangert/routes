"""test_utils"""
import os, sys, time, unittest
from nose.tools import eq_, assert_raises

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

        eq_('/blog', url_for('/blog'))
        eq_('/blog?q=fred&q=here%20now', url_for('/blog', q=['fred', u'here now']))
        eq_('/blog#here', url_for('/blog', anchor='here'))

    def test_url_for_with_nongen_no_encoding(self):
        con = self.con
        con.mapper_dict = {}
        con.mapper.encoding = None

        eq_('/blog', url_for('/blog'))
        eq_('/blog#here', url_for('/blog', anchor='here'))

    def test_url_for_with_unicode(self):
        con = self.con
        con.mapper_dict = {}

        eq_('/blog', url_for(controller='blog'))
        eq_('/blog/view/umulat', url_for(controller='blog', action='view', id=u'umulat'))
        eq_('/blog/view/umulat?other=%CE%B1%CF%83%CE%B4%CE%B3',
            url_for(controller='blog', action='view', id=u'umulat', other=u'\u03b1\u03c3\u03b4\u03b3'))

        url = URLGenerator(con.mapper, {})
        for urlobj in [url_for, url]:
            def raise_url():
                return urlobj(u'/some/st\xc3rng')
            assert_raises(Exception, raise_url)

    def test_url_for(self):
        con = self.con
        con.mapper_dict = {}
        url = URLGenerator(con.mapper, {'HTTP_HOST':'www.test.com:80'})

        for urlobj in [url_for, url]:
            eq_('/blog', urlobj(controller='blog'))
            eq_('/content', urlobj())
            eq_('https://www.test.com/viewpost', urlobj(controller='post', action='view', protocol='https'))
            eq_('http://www.test.org/content', urlobj(host='www.test.org'))
            eq_('//www.test.com/viewpost', urlobj(controller='post', action='view', protocol=''))
            eq_('//www.test.org/content', urlobj(host='www.test.org', protocol=''))

    def test_url_raises(self):
        con = self.con
        con.mapper.explicit = True
        con.mapper_dict = {}
        url = URLGenerator(con.mapper, {})
        assert_raises(GenerationException, url_for, action='juice')
        assert_raises(GenerationException, url, action='juice')

    def test_url_for_with_defaults(self):
        con = self.con
        con.mapper_dict = {'controller':'blog','action':'view','id':4}
        url = URLGenerator(con.mapper, {'wsgiorg.routing_args':((), con.mapper_dict)})

        eq_('/blog/view/4', url_for())
        eq_('/post/index/4', url_for(controller='post'))
        eq_('/blog/view/2', url_for(id=2))
        eq_('/viewpost/4', url_for(controller='post', action='view', id=4))

        eq_('/blog/view/4', url.current())
        eq_('/post/index/4', url.current(controller='post'))
        eq_('/blog/view/2', url.current(id=2))
        eq_('/viewpost/4', url.current(controller='post', action='view', id=4))

        con.mapper_dict = {'controller':'blog','action':'view','year':2004}
        url = URLGenerator(con.mapper, {'wsgiorg.routing_args':((), con.mapper_dict)})

        eq_('/archive/2004/10', url_for(month=10))
        eq_('/archive/2004/9/2', url_for(month=9, day=2))
        eq_('/blog', url_for(controller='blog', year=None))

        eq_('/archive/2004/10', url.current(month=10))
        eq_('/archive/2004/9/2', url.current(month=9, day=2))
        eq_('/blog', url.current(controller='blog', year=None))

    def test_url_for_with_more_defaults(self):
        con = self.con
        con.mapper_dict = {'controller':'blog','action':'view','id':4}
        url = URLGenerator(con.mapper, {'wsgiorg.routing_args':((), con.mapper_dict)})

        eq_('/blog/view/4', url_for())
        eq_('/post/index/4', url_for(controller='post'))
        eq_('/blog/view/2', url_for(id=2))
        eq_('/viewpost/4', url_for(controller='post', action='view', id=4))

        eq_('/blog/view/4', url.current())
        eq_('/post/index/4', url.current(controller='post'))
        eq_('/blog/view/2', url.current(id=2))
        eq_('/viewpost/4', url.current(controller='post', action='view', id=4))

        con.mapper_dict = {'controller':'blog','action':'view','year':2004}
        url = URLGenerator(con.mapper, {'wsgiorg.routing_args':((), con.mapper_dict)})
        eq_('/archive/2004/10', url_for(month=10))
        eq_('/archive/2004/9/2', url_for(month=9, day=2))
        eq_('/blog', url_for(controller='blog', year=None))
        eq_('/archive/2004', url_for())

        eq_('/archive/2004/10', url.current(month=10))
        eq_('/archive/2004/9/2', url.current(month=9, day=2))
        eq_('/blog', url.current(controller='blog', year=None))
        eq_('/archive/2004', url.current())

    def test_url_for_with_defaults_and_qualified(self):
        m = self.con.mapper
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])
        self.con.environ = dict(SCRIPT_NAME='', HTTP_HOST='www.example.com', PATH_INFO='/blog/view/4')
        self.con.environ.update({'wsgiorg.routing_args':((), self.con.mapper_dict)})
        url = URLGenerator(m, self.con.environ)

        eq_('/blog/view/4', url_for())
        eq_('/post/index/4', url_for(controller='post'))
        eq_('http://www.example.com/blog/view/4', url_for(qualified=True))
        eq_('/blog/view/2', url_for(id=2))
        eq_('/viewpost/4', url_for(controller='post', action='view', id=4))

        eq_('/blog/view/4', url.current())
        eq_('/post/index/4', url.current(controller='post'))
        eq_('http://www.example.com/blog/view/4', url.current(qualified=True))
        eq_('/blog/view/2', url.current(id=2))
        eq_('/viewpost/4', url.current(controller='post', action='view', id=4))

        env = dict(SCRIPT_NAME='', SERVER_NAME='www.example.com', SERVER_PORT='8080', PATH_INFO='/blog/view/4')
        env['wsgi.url_scheme'] = 'http'
        self.con.environ = env
        self.con.environ.update({'wsgiorg.routing_args':((), self.con.mapper_dict)})
        url = URLGenerator(m, self.con.environ)

        eq_('/post/index/4', url_for(controller='post'))
        eq_('http://www.example.com:8080/blog/view/4', url_for(qualified=True))

        eq_('/post/index/4', url.current(controller='post'))
        eq_('http://www.example.com:8080/blog/view/4', url.current(qualified=True))

    def test_route_overflow(self):
        m = self.con.mapper
        m.create_regs(["x"*50000])
        m.connect('route-overflow', "x"*50000)
        url = URLGenerator(m, {})
        eq_("/%s" % ("x"*50000), url('route-overflow'))

    def test_with_route_names(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.create_regs(['content','blog','admin/comments'])
        url = URLGenerator(m, {})

        for urlobj in [url, url_for]:
            eq_('/content/view', urlobj(controller='content', action='view'))
            eq_('/content', urlobj(controller='content'))
            eq_('/admin/comments', urlobj(controller='admin/comments'))
            eq_('/category', urlobj('category_home'))
            eq_('/category/food', urlobj('category_home', section='food'))
            eq_('/', urlobj('home'))

    def test_with_route_names_and_defaults(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.connect('building', 'building/:campus/:building/alljacks', controller='building', action='showjacks')
        m.create_regs(['content','blog','admin/comments','building'])

        self.con.mapper_dict = dict(controller='building', action='showjacks', campus='wilma', building='port')
        url = URLGenerator(m, {'wsgiorg.routing_args':((), self.con.mapper_dict)})

        eq_('/building/wilma/port/alljacks', url_for())
        eq_('/', url_for('home'))
        eq_('/building/wilma/port/alljacks', url.current())
        eq_('/', url.current('home'))

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
        eq_('/building/wilma/port/alljacks', url_for())
        eq_('/', url_for('home'))
        eq_('/gallery/home_thumbnail.jpg', url_for('gallery_thumb', img_id='home'))
        eq_('/gallery/home_thumbnail.jpg', url_for('gallery', img_id='home'))

        eq_('/building/wilma/port/alljacks', url.current())
        eq_('/', url.current('home'))
        eq_('/gallery/home_thumbnail.jpg', url.current('gallery_thumb', img_id='home'))
        eq_('/gallery/home_thumbnail.jpg', url.current('gallery', img_id='home'))

        m.hardcode_names = True
        eq_('/gallery/home_thumbnail.jpg', url_for('gallery_thumb', img_id='home'))
        eq_('/gallery/home.jpg', url_for('gallery', img_id='home'))

        eq_('/gallery/home_thumbnail.jpg', url.current('gallery_thumb', img_id='home'))
        eq_('/gallery/home.jpg', url.current('gallery', img_id='home'))
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
        eq_('/content/view', redirect_to.result)
        redirect_to(controller='content', action='lookup', id=4)
        eq_('/content/lookup/4', redirect_to.result)
        redirect_to(controller='admin/comments',action='splash')
        eq_('/admin/comments/splash', redirect_to.result)
        redirect_to('http://www.example.com/')
        eq_('http://www.example.com/', redirect_to.result)
        redirect_to('/somewhere.html', var='keyword')
        eq_('/somewhere.html?var=keyword', redirect_to.result)

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
        eq_('/content/view', redirect_to.result)
        redirect_to(controller='content')
        eq_('/content', redirect_to.result)
        redirect_to(controller='admin/comments')
        eq_('/admin/comments', redirect_to.result)
        redirect_to('category_home')
        eq_('/category', redirect_to.result)
        redirect_to('category_home', section='food')
        eq_('/category/food', redirect_to.result)
        redirect_to('home')
        eq_('/', redirect_to.result)

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
            eq_('http://www.groovie.org/', urlobj('home'))
            eq_('http://www.groovie.org/?s=stars', urlobj('home', s='stars'))
            eq_('/content/view', urlobj(controller='content', action='view'))
            eq_('/nasa/images?search=all', urlobj('space', search='all'))

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
            eq_('http://www.groovie.org/', urlobj('home'))
            eq_('http://www.groovie.org/?s=stars', urlobj('home', s='stars'))
            eq_('/webapp/content/view', urlobj(controller='content', action='view'))
            eq_('/webapp/nasa/images?search=all', urlobj('space', search='all'))
            eq_('http://example.com/webapp/nasa/images', urlobj('space', protocol='http'))
            eq_('http://example.com/webapp/login', urlobj('login', qualified=True))

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
            assert_raises(GenerationException, urlobj, 'home')
            assert_raises(GenerationException, urlobj, 'home', domain='fred')
            assert_raises(GenerationException, urlobj, 'home', location='index')
            eq_('http://fred.groovie.org/index', urlobj('home', domain='fred', location='index'))
            eq_('http://fred.groovie.org/index?search=all', urlobj('home', domain='fred', location='index', search='all'))
            eq_('/webapp/nasa/images?search=all', urlobj('space', location='images', search='all'))
            eq_('http://example.com/webapp/nasa/images', urlobj('space', location='images', protocol='http'))

    def test_static_route_with_vars_and_defaults(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        self.con.environ = dict(SCRIPT_NAME='/webapp', HTTP_HOST='example.com')
        m.connect('home', 'http://{domain}.groovie.org/{location}', domain='routes', _static=True)
        m.connect('space', '/nasa/{location}', location='images', _static=True)
        m.create_regs(['home', 'space'])

        self.con.environ.update({'wsgiorg.routing_args':((), {})})
        url = URLGenerator(m, self.con.environ)

        assert_raises(GenerationException, url_for, 'home')
        assert_raises(GenerationException, url_for, 'home', domain='fred')
        eq_('http://routes.groovie.org/index', url_for('home', location='index'))
        eq_('http://fred.groovie.org/index', url_for('home', domain='fred', location='index'))
        eq_('http://routes.groovie.org/index?search=all', url_for('home', location='index', search='all'))
        eq_('http://fred.groovie.org/index?search=all', url_for('home', domain='fred', location='index', search='all'))
        eq_('/webapp/nasa/articles?search=all', url_for('space', location='articles', search='all'))
        eq_('http://example.com/webapp/nasa/articles', url_for('space', location='articles', protocol='http'))
        eq_('/webapp/nasa/images?search=all', url_for('space', search='all'))
        eq_('http://example.com/webapp/nasa/images', url_for('space', protocol='http'))

        assert_raises(GenerationException, url.current, 'home')
        assert_raises(GenerationException, url.current, 'home', domain='fred')
        eq_('http://routes.groovie.org/index', url.current('home', location='index'))
        eq_('http://fred.groovie.org/index', url.current('home', domain='fred', location='index'))
        eq_('http://routes.groovie.org/index?search=all', url.current('home', location='index', search='all'))
        eq_('http://fred.groovie.org/index?search=all', url.current('home', domain='fred', location='index', search='all'))
        eq_('/webapp/nasa/articles?search=all', url.current('space', location='articles', search='all'))
        eq_('http://example.com/webapp/nasa/articles', url.current('space', location='articles', protocol='http'))
        eq_('/webapp/nasa/images?search=all', url.current('space', search='all'))
        eq_('http://example.com/webapp/nasa/images', url.current('space', protocol='http'))


    def test_static_route_with_vars_and_requirements(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        self.con.environ = dict(SCRIPT_NAME='/webapp', HTTP_HOST='example.com')
        m.connect('home', 'http://{domain}.groovie.org/{location}', requirements=dict(domain='fred|bob'), _static=True)
        m.connect('space', '/nasa/articles/{year}/{month}', requirements=dict(year=r'\d{2,4}', month=r'\d{1,2}'), _static=True)
        m.create_regs(['home', 'space'])


        self.con.environ.update({'wsgiorg.routing_args':((), {})})
        url = URLGenerator(m, self.con.environ)

        assert_raises(GenerationException, url_for, 'home', domain='george', location='index')
        assert_raises(GenerationException, url_for, 'space', year='asdf', month='1')
        assert_raises(GenerationException, url_for, 'space', year='2004', month='a')
        assert_raises(GenerationException, url_for, 'space', year='1', month='1')
        assert_raises(GenerationException, url_for, 'space', year='20045', month='1')
        assert_raises(GenerationException, url_for, 'space', year='2004', month='123')
        eq_('http://fred.groovie.org/index', url_for('home', domain='fred', location='index'))
        eq_('http://bob.groovie.org/index', url_for('home', domain='bob', location='index'))
        eq_('http://fred.groovie.org/asdf', url_for('home', domain='fred', location='asdf'))
        eq_('/webapp/nasa/articles/2004/6', url_for('space', year='2004', month='6'))
        eq_('/webapp/nasa/articles/2004/12', url_for('space', year='2004', month='12'))
        eq_('/webapp/nasa/articles/89/6', url_for('space', year='89', month='6'))

        assert_raises(GenerationException, url.current, 'home', domain='george', location='index')
        assert_raises(GenerationException, url.current, 'space', year='asdf', month='1')
        assert_raises(GenerationException, url.current, 'space', year='2004', month='a')
        assert_raises(GenerationException, url.current, 'space', year='1', month='1')
        assert_raises(GenerationException, url.current, 'space', year='20045', month='1')
        assert_raises(GenerationException, url.current, 'space', year='2004', month='123')
        eq_('http://fred.groovie.org/index', url.current('home', domain='fred', location='index'))
        eq_('http://bob.groovie.org/index', url.current('home', domain='bob', location='index'))
        eq_('http://fred.groovie.org/asdf', url.current('home', domain='fred', location='asdf'))
        eq_('/webapp/nasa/articles/2004/6', url.current('space', year='2004', month='6'))
        eq_('/webapp/nasa/articles/2004/12', url.current('space', year='2004', month='12'))
        eq_('/webapp/nasa/articles/89/6', url.current('space', year='89', month='6'))

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
            eq_('http://www.google.com/search', urlobj('http://www.google.com/search'))
            eq_('http://www.google.com/search?q=routes', urlobj('http://www.google.com/search', q='routes'))
            eq_('/delicious.jpg', urlobj('/delicious.jpg'))
            eq_('/delicious/search?v=routes', urlobj('/delicious/search', v='routes'))

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
            eq_('http://www.google.com/search', urlobj('http://www.google.com/search'))
            eq_('http://www.google.com/search?q=routes', urlobj('http://www.google.com/search', q='routes'))
            eq_('/delicious.jpg', urlobj('/delicious.jpg'))
            eq_('/delicious/search?v=routes', urlobj('/delicious/search', v='routes'))
            eq_('/content/list/', urlobj(controller='/content', action='list'))
            eq_('/content/list/?page=1', urlobj(controller='/content', action='list', page='1'))

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
            eq_('http://www.google.com/search', urlobj('http://www.google.com/search'))
            eq_('http://www.google.com/search?q=routes', urlobj('http://www.google.com/search', q='routes'))
            eq_('/webapp/delicious.jpg', urlobj('/delicious.jpg'))
            eq_('/webapp/delicious/search?v=routes', urlobj('/delicious/search', v='routes'))

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
            assert_raises(Exception, urlobj, controller='content', action='view')
            assert_raises(Exception, urlobj, controller='content')

            eq_('/content/view-3.html', urlobj(controller='content', action='view', id=3))
            eq_('/content/index-2.html', urlobj(controller='content', id=2))

            eq_('/archives/2005/10/5/happy',
                urlobj('archives',year=2005, month=10, day=5, slug='happy'))
            story = dict(year=2003, month=8, day=2, slug='woopee')
            empty = {}
            eq_({'controller':'archives','action':'view','year':'2005',
                'month':'10','day':'5','slug':'happy'}, m.match('/archives/2005/10/5/happy'))
            eq_('/archives/2003/8/2/woopee', urlobj('archives', article=story))
            eq_('/archives/2004/12/20/default', urlobj('archives', article=empty))

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
            eq_(self.con.protocol, 'https')
            eq_('/content/view', urlobj(controller='content', action='view'))
            eq_('/content/index/2', urlobj(controller='content', id=2))
            eq_('https://nowhere.com/content', urlobj(host='nowhere.com', controller='content'))

            # If HTTPS is on, but the port isn't 443, we'll need to include the port info
            environ = base_environ.copy()
            environ.update(dict(SERVER_PORT='8080'))
            self.con.environ = environ
            self.con.mapper_dict = {}
            eq_('/content/index/2', urlobj(controller='content', id=2))
            eq_('https://nowhere.com/content', urlobj(host='nowhere.com', controller='content'))
            eq_('https://nowhere.com:8080/content', urlobj(host='nowhere.com:8080', controller='content'))
            eq_('http://nowhere.com/content', urlobj(host='nowhere.com', protocol='http', controller='content'))
            eq_('http://home.com/content', urlobj(host='home.com', protocol='http', controller='content'))


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
            eq_(self.con.protocol, 'http')
            eq_('/content/view', urlobj(controller='content', action='view'))
            eq_('/content/index/2', urlobj(controller='content', id=2))
            eq_('https://example.com/content', urlobj(protocol='https', controller='content'))


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
            eq_('/content/view', urlobj(controller='content', action='view'))
            eq_('/content/index/2', urlobj(controller='content', id=2))
            environ = base_environ.copy()
            environ.update(dict(HTTP_HOST='sub.example.com'))
            self.con.environ = environ
            self.con.mapper_dict = {'sub_domain':'sub'}
            eq_('/content/view/3', urlobj(controller='content', action='view', id=3))
            eq_('http://new.example.com/content', urlobj(controller='content', sub_domain='new'))

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
        eq_('/content/view', url_for(controller='content', action='view'))
        eq_('/content/index/2', url_for(controller='content', id=2))
        eq_('/content/view', url(controller='content', action='view'))
        eq_('/content/index/2', url(controller='content', id=2))

        environ = base_environ.copy()
        environ.update(dict(HTTP_HOST='sub.example.com'))
        self.con.environ = environ
        self.con.mapper_dict = {'sub_domain':'sub'}
        self.con.environ.update({'wsgiorg.routing_args':((), self.con.mapper_dict)})
        url = URLGenerator(m, self.con.environ)

        eq_('/content/view/3', url_for(controller='content', action='view', id=3))
        eq_('http://new.example.com/content', url_for(controller='content', sub_domain='new'))
        eq_('http://example.com/content', url_for(controller='content', sub_domain='www'))
        eq_('/content/view/3', url(controller='content', action='view', id=3))
        eq_('http://new.example.com/content', url(controller='content', sub_domain='new'))
        eq_('http://example.com/content', url(controller='content', sub_domain='www'))

        self.con.mapper_dict = {'sub_domain':'www'}
        self.con.environ.update({'wsgiorg.routing_args':((), self.con.mapper_dict)})
        url = URLGenerator(m, self.con.environ)

        eq_('http://example.com/content/view/3', url_for(controller='content', action='view', id=3))
        eq_('http://new.example.com/content', url_for(controller='content', sub_domain='new'))
        eq_('/content', url_for(controller='content', sub_domain='sub'))

        # This requires the sub-domain, because we don't automatically go to the existing match dict
        eq_('http://example.com/content/view/3', url(controller='content', action='view', id=3, sub_domain='www'))
        eq_('http://new.example.com/content', url(controller='content', sub_domain='new'))
        eq_('/content', url(controller='content', sub_domain='sub'))

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
            eq_('/content/view', urlobj(controller='content', action='view'))
            eq_('/content/index/2', urlobj(controller='content', id=2))
            eq_('/category', urlobj('category_home'))
            eq_('http://new.example.com/category', urlobj('category_home', sub_domain='new'))

        environ = base_environ.copy()
        environ.update(dict(HTTP_HOST='sub.example.com'))
        self.con.environ = environ
        self.con.mapper_dict = {'sub_domain':'sub'}
        self.con.environ.update({'wsgiorg.routing_args':((), self.con.mapper_dict)})
        url = URLGenerator(m, self.con.environ)

        eq_('/content/view/3', url_for(controller='content', action='view', id=3))
        eq_('http://joy.example.com/building/west/merlot/alljacks',
            url_for('building', campus='west', building='merlot', sub_domain='joy'))
        eq_('http://example.com/category/feeds', url_for('category_home', section='feeds', sub_domain=None))

        eq_('/content/view/3', url(controller='content', action='view', id=3))
        eq_('http://joy.example.com/building/west/merlot/alljacks',
            url('building', campus='west', building='merlot', sub_domain='joy'))
        eq_('http://example.com/category/feeds', url('category_home', section='feeds', sub_domain=None))


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
            eq_('/content/view', urlobj(controller='content', action='view'))
            eq_('/category', urlobj('category_home'))
            eq_('http://new.example.com:8000/category', urlobj('category_home', sub_domain='new'))
            eq_('http://joy.example.com:8000/building/west/merlot/alljacks',
                urlobj('building', campus='west', building='merlot', sub_domain='joy'))

            self.con.environ['HTTP_HOST'] = 'example.com'
            del self.con.environ['routes.cached_hostinfo']
            eq_('http://new.example.com/category', urlobj('category_home', sub_domain='new'))

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
        eq_('/content/view', urlobj(controller='content', action='view'))
        eq_('http://cat.example.com:8000/category', urlobj('category_home'))

        self.con.environ['HTTP_HOST'] = 'example.com'
        del self.con.environ['routes.cached_hostinfo']

        assert_raises(GenerationException, lambda: urlobj('category_home', sub_domain='new'))


    def test_controller_scan(self):
        here_dir = os.path.dirname(__file__)
        controller_dir = os.path.join(os.path.dirname(here_dir),
            os.path.join('test_files', 'controller_files'))
        controllers = controller_scan(controller_dir)
        eq_(len(controllers), 3)
        eq_(controllers[0], 'admin/users')
        eq_(controllers[1], 'content')
        eq_(controllers[2], 'users')

    def test_auto_controller_scan(self):
        here_dir = os.path.dirname(__file__)
        controller_dir = os.path.join(os.path.dirname(here_dir),
            os.path.join('test_files', 'controller_files'))
        m = Mapper(directory=controller_dir, explicit=False)
        m.minimization = True
        m.always_scan = True
        m.connect(':controller/:action/:id')

        eq_({'action':'index', 'controller':'content','id':None}, m.match('/content'))
        eq_({'action':'index', 'controller':'users','id':None}, m.match('/users'))
        eq_({'action':'index', 'controller':'admin/users','id':None}, m.match('/admin/users'))

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

        assert_raises(Exception, url_for, controller='blog')
        assert_raises(Exception, url_for)
        eq_('/blog/view/3', url_for(controller='blog', action='view', id=3))
        eq_('https://www.test.com/viewpost', url_for(controller='post', action='view', protocol='https'))
        eq_('http://www.test.org/content/view/2', url_for(host='www.test.org', controller='content', action='view', id=2))

    def test_url_for_with_defaults(self):
        con = self.con
        con.mapper_dict = {'controller':'blog','action':'view','id':4}

        assert_raises(Exception, url_for)
        assert_raises(Exception, url_for, controller='post')
        assert_raises(Exception, url_for, id=2)
        eq_('/viewpost/4', url_for(controller='post', action='view', id=4))

        con.mapper_dict = {'controller':'blog','action':'view','year':2004}
        assert_raises(Exception, url_for, month=10)
        assert_raises(Exception, url_for, month=9, day=2)
        assert_raises(Exception, url_for, controller='blog', year=None)

    def test_url_for_with_more_defaults(self):
        con = self.con
        con.mapper_dict = {'controller':'blog','action':'view','id':4}

        assert_raises(Exception, url_for)
        assert_raises(Exception, url_for, controller='post')
        assert_raises(Exception, url_for, id=2)
        eq_('/viewpost/4', url_for(controller='post', action='view', id=4))

        con.mapper_dict = {'controller':'blog','action':'view','year':2004}
        assert_raises(Exception, url_for, month=10)
        assert_raises(Exception, url_for)

    def test_url_for_with_defaults_and_qualified(self):
        m = self.con.mapper
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])
        env = dict(SCRIPT_NAME='', SERVER_NAME='www.example.com', SERVER_PORT='80', PATH_INFO='/blog/view/4')
        env['wsgi.url_scheme'] = 'http'

        self.con.environ = env

        assert_raises(Exception, url_for)
        assert_raises(Exception, url_for, controller='post')
        assert_raises(Exception, url_for, id=2)
        assert_raises(Exception, url_for, qualified=True, controller='blog', id=4)
        eq_('http://www.example.com/blog/view/4', url_for(qualified=True, controller='blog', action='view', id=4))
        eq_('/viewpost/4', url_for(controller='post', action='view', id=4))

        env = dict(SCRIPT_NAME='', SERVER_NAME='www.example.com', SERVER_PORT='8080', PATH_INFO='/blog/view/4')
        env['wsgi.url_scheme'] = 'http'
        self.con.environ = env
        assert_raises(Exception, url_for, controller='post')
        eq_('http://www.example.com:8080/blog/view/4', url_for(qualified=True, controller='blog', action='view', id=4))


    def test_with_route_names(self):
        m = self.con.mapper
        m.minimization = True
        self.con.mapper_dict = {}
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.create_regs(['content','blog','admin/comments'])

        assert_raises(Exception, url_for, controller='content', action='view')
        assert_raises(Exception, url_for, controller='content')
        assert_raises(Exception, url_for, controller='admin/comments')
        eq_('/category', url_for('category_home'))
        eq_('/category/food', url_for('category_home', section='food'))
        assert_raises(Exception, url_for, 'home', controller='content')
        eq_('/', url_for('home'))

    def test_with_route_names_and_nomin(self):
        m = self.con.mapper
        m.minimization = False
        self.con.mapper_dict = {}
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.create_regs(['content','blog','admin/comments'])

        assert_raises(Exception, url_for, controller='content', action='view')
        assert_raises(Exception, url_for, controller='content')
        assert_raises(Exception, url_for, controller='admin/comments')
        eq_('/category/home', url_for('category_home'))
        eq_('/category/food', url_for('category_home', section='food'))
        assert_raises(Exception, url_for, 'home', controller='content')
        eq_('/', url_for('home'))

    def test_with_route_names_and_defaults(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.connect('building', 'building/:campus/:building/alljacks', controller='building', action='showjacks')
        m.create_regs(['content','blog','admin/comments','building'])

        self.con.mapper_dict = dict(controller='building', action='showjacks', campus='wilma', building='port')
        assert_raises(Exception, url_for)
        eq_('/building/wilma/port/alljacks', url_for(controller='building', action='showjacks', campus='wilma', building='port'))
        eq_('/', url_for('home'))

    def test_with_resource_route_names(self):
        m = Mapper()
        self.con.mapper = m
        self.con.mapper_dict = {}
        m.resource('message', 'messages', member={'mark':'GET'}, collection={'rss':'GET'})
        m.create_regs(['messages'])

        assert_raises(Exception, url_for, controller='content', action='view')
        assert_raises(Exception, url_for, controller='content')
        assert_raises(Exception, url_for, controller='admin/comments')
        eq_('/messages', url_for('messages'))
        eq_('/messages/rss', url_for('rss_messages'))
        eq_('/messages/4', url_for('message', id=4))
        eq_('/messages/4/edit', url_for('edit_message', id=4))
        eq_('/messages/4/mark', url_for('mark_message', id=4))
        eq_('/messages/new', url_for('new_message'))

        eq_('/messages.xml', url_for('formatted_messages', format='xml'))
        eq_('/messages/rss.xml', url_for('formatted_rss_messages', format='xml'))
        eq_('/messages/4.xml', url_for('formatted_message', id=4, format='xml'))
        eq_('/messages/4/edit.xml', url_for('formatted_edit_message', id=4, format='xml'))
        eq_('/messages/4/mark.xml', url_for('formatted_mark_message', id=4, format='xml'))
        eq_('/messages/new.xml', url_for('formatted_new_message', format='xml'))

    def test_with_resource_route_names_and_nomin(self):
        m = Mapper()
        self.con.mapper = m
        self.con.mapper_dict = {}
        m.minimization = False
        m.resource('message', 'messages', member={'mark':'GET'}, collection={'rss':'GET'})
        m.create_regs(['messages'])

        assert_raises(Exception, url_for, controller='content', action='view')
        assert_raises(Exception, url_for, controller='content')
        assert_raises(Exception, url_for, controller='admin/comments')
        eq_('/messages', url_for('messages'))
        eq_('/messages/rss', url_for('rss_messages'))
        eq_('/messages/4', url_for('message', id=4))
        eq_('/messages/4/edit', url_for('edit_message', id=4))
        eq_('/messages/4/mark', url_for('mark_message', id=4))
        eq_('/messages/new', url_for('new_message'))

        eq_('/messages.xml', url_for('formatted_messages', format='xml'))
        eq_('/messages/rss.xml', url_for('formatted_rss_messages', format='xml'))
        eq_('/messages/4.xml', url_for('formatted_message', id=4, format='xml'))
        eq_('/messages/4/edit.xml', url_for('formatted_edit_message', id=4, format='xml'))
        eq_('/messages/4/mark.xml', url_for('formatted_mark_message', id=4, format='xml'))
        eq_('/messages/new.xml', url_for('formatted_new_message', format='xml'))


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
