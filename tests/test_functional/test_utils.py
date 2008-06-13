"""test_utils"""
import os, sys, time, unittest
from nose.tools import eq_, raises

from routes.util import controller_scan, RouteException
from routes import *

class TestUtils(unittest.TestCase):
    def setUp(self):
        m = Mapper()
        m.connect('archive/:year/:month/:day', controller='blog', action='view', month=None, day=None,
                  requirements={'month':'\d{1,2}','day':'\d{1,2}'})
        m.connect('viewpost/:id', controller='post', action='view')
        m.connect(':controller/:action/:id')
        con = request_config()
        con.mapper = m
        con.host = 'www.test.com'
        con.protocol = 'http'
        self.con = con
    
    def test_url_for_with_unicode(self):
        con = self.con
        con.mapper_dict = {}
        
        assert '/blog' == url_for(controller='blog')
        assert '/blog/view/umulat' == url_for(controller='blog', action='view', id=u'umulat')
        assert '/blog/view/umulat?other=%CE%B1%CF%83%CE%B4%CE%B3' == url_for(controller='blog', action='view', id=u'umulat',
            other=u'\u03b1\u03c3\u03b4\u03b3')
        
        def raise_url():
            return url_for(u'/some/stirng')
        self.assertRaises(Exception, raise_url)
        
        
    def test_url_for(self):
        con = self.con
        con.mapper_dict = {}
        
        self.assertEqual('/blog', url_for(controller='blog'))
        self.assertEqual('/content', url_for())
        self.assertEqual('https://www.test.com/viewpost', url_for(controller='post', action='view', protocol='https'))
        self.assertEqual('http://www.test.org/content', url_for(host='www.test.org'))
    
    @raises(RouteException)
    def test_url_raises(self):
        con = self.con
        con.mapper.explicit = True
        con.mapper_dict = {}
        url_for(action='juice')
    
    def test_url_for_with_defaults(self):
        con = self.con
        con.mapper_dict = {'controller':'blog','action':'view','id':4}
        
        self.assertEqual('/blog/view/4', url_for())
        self.assertEqual('/post/index/4', url_for(controller='post'))
        self.assertEqual('/blog/view/2', url_for(id=2))
        self.assertEqual('/viewpost/4', url_for(controller='post', action='view', id=4))
        
        con.mapper_dict = {'controller':'blog','action':'view','year':2004}
        self.assertEqual('/archive/2004/10', url_for(month=10))
        self.assertEqual('/archive/2004/9/2', url_for(month=9, day=2))
        self.assertEqual('/blog', url_for(controller='blog', year=None))
    
    def test_url_for_with_more_defaults(self):
        con = self.con
        con.mapper_dict = {'controller':'blog','action':'view','id':4}
        
        self.assertEqual('/blog/view/4', url_for())
        self.assertEqual('/post/index/4', url_for(controller='post'))
        self.assertEqual('/blog/view/2', url_for(id=2))
        self.assertEqual('/viewpost/4', url_for(controller='post', action='view', id=4))
        
        con.mapper_dict = {'controller':'blog','action':'view','year':2004}
        self.assertEqual('/archive/2004/10', url_for(month=10))
        self.assertEqual('/archive/2004/9/2', url_for(month=9, day=2))
        self.assertEqual('/blog', url_for(controller='blog', year=None))
        self.assertEqual('/archive/2004', url_for())
    
    def test_url_for_with_defaults_and_qualified(self):
        m = self.con.mapper
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])
        self.con.environ = dict(SCRIPT_NAME='', HTTP_HOST='www.example.com', PATH_INFO='/blog/view/4')
        
        self.assertEqual('/blog/view/4', url_for())
        self.assertEqual('/post/index/4', url_for(controller='post'))
        self.assertEqual('http://www.example.com/blog/view/4', url_for(qualified=True))
        self.assertEqual('/blog/view/2', url_for(id=2))
        self.assertEqual('/viewpost/4', url_for(controller='post', action='view', id=4))
        
        env = dict(SCRIPT_NAME='', SERVER_NAME='www.example.com', SERVER_PORT='8080', PATH_INFO='/blog/view/4')
        env['wsgi.url_scheme'] = 'http'
        self.con.environ = env
        self.assertEqual('/post/index/4', url_for(controller='post'))
        self.assertEqual('http://www.example.com:8080/blog/view/4', url_for(qualified=True))
        
    
    def test_with_route_names(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.create_regs(['content','blog','admin/comments'])

        self.assertEqual('/content/view', url_for(controller='content', action='view'))
        self.assertEqual('/content', url_for(controller='content'))
        self.assertEqual('/admin/comments', url_for(controller='admin/comments'))
        self.assertEqual('/category', url_for('category_home'))
        self.assertEqual('/category/food', url_for('category_home', section='food'))
        self.assertEqual('/', url_for('home'))
        
    def test_with_route_names_and_defaults(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.connect('building', 'building/:campus/:building/alljacks', controller='building', action='showjacks')
        m.create_regs(['content','blog','admin/comments','building'])

        self.con.mapper_dict = dict(controller='building', action='showjacks', campus='wilma', building='port')
        self.assertEqual('/building/wilma/port/alljacks', url_for())
        self.assertEqual('/', url_for('home'))
        
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
        self.assertEqual('/building/wilma/port/alljacks', url_for())
        self.assertEqual('/', url_for('home'))
        self.assertEqual('/gallery/home_thumbnail.jpg', url_for('gallery_thumb', img_id='home'))
        self.assertEqual('/gallery/home_thumbnail.jpg', url_for('gallery', img_id='home'))
        
        m.hardcode_names = True
        self.assertEqual('/gallery/home_thumbnail.jpg', url_for('gallery_thumb', img_id='home'))
        self.assertEqual('/gallery/home.jpg', url_for('gallery', img_id='home'))
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
        self.assertEqual('/content/view', redirect_to.result)
        redirect_to(controller='content', action='lookup', id=4)
        self.assertEqual('/content/lookup/4', redirect_to.result)
        redirect_to(controller='admin/comments',action='splash')
        self.assertEqual('/admin/comments/splash', redirect_to.result)
        redirect_to('http://www.example.com/')
        self.assertEqual('http://www.example.com/', redirect_to.result)
        redirect_to('/somewhere.html', var='keyword')
        self.assertEqual('/somewhere.html?var=keyword', redirect_to.result)

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
        self.assertEqual('/content/view', redirect_to.result)
        redirect_to(controller='content')
        self.assertEqual('/content', redirect_to.result)
        redirect_to(controller='admin/comments')
        self.assertEqual('/admin/comments', redirect_to.result)
        redirect_to('category_home')
        self.assertEqual('/category', redirect_to.result)
        redirect_to('category_home', section='food')
        self.assertEqual('/category/food', redirect_to.result)
        redirect_to('home')
        self.assertEqual('/', redirect_to.result)
    
    def test_static_route(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        self.con.environ = dict(SCRIPT_NAME='', HTTP_HOST='example.com')
        m.connect(':controller/:action/:id')
        m.connect('home', 'http://www.groovie.org/', _static=True)
        m.connect('space', '/nasa/images', _static=True)
        m.create_regs(['content', 'blog'])
        
        self.assertEqual('http://www.groovie.org/', url_for('home'))
        self.assertEqual('http://www.groovie.org/?s=stars', url_for('home', s='stars'))
        self.assertEqual('/content/view', url_for(controller='content', action='view'))
        self.assertEqual('/nasa/images?search=all', url_for('space', search='all'))
    
    def test_static_route_with_script(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        self.con.environ = dict(SCRIPT_NAME='/webapp', HTTP_HOST='example.com')
        m.connect(':controller/:action/:id')
        m.connect('home', 'http://www.groovie.org/', _static=True)
        m.connect('space', '/nasa/images', _static=True)
        m.create_regs(['content', 'blog'])
        
        self.assertEqual('http://www.groovie.org/', url_for('home'))
        self.assertEqual('http://www.groovie.org/?s=stars', url_for('home', s='stars'))
        self.assertEqual('/webapp/content/view', url_for(controller='content', action='view'))
        self.assertEqual('/webapp/nasa/images?search=all', url_for('space', search='all'))
        self.assertEqual('http://example.com/webapp/nasa/images', url_for('space', protocol='http'))
    
    def test_no_named_path(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        self.con.environ = dict(SCRIPT_NAME='', HTTP_HOST='example.com')
        m.connect(':controller/:action/:id')
        m.connect('home', 'http://www.groovie.org/', _static=True)
        m.connect('space', '/nasa/images', _static=True)
        m.create_regs(['content', 'blog'])
        
        self.assertEqual('http://www.google.com/search', url_for('http://www.google.com/search'))
        self.assertEqual('http://www.google.com/search?q=routes', url_for('http://www.google.com/search', q='routes'))
        self.assertEqual('/delicious.jpg', url_for('/delicious.jpg'))
        self.assertEqual('/delicious/search?v=routes', url_for('/delicious/search', v='routes'))
    
    def test_append_slash(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        m.append_slash = True
        self.con.environ = dict(SCRIPT_NAME='', HTTP_HOST='example.com')
        m.connect(':controller/:action/:id')
        m.connect('home', 'http://www.groovie.org/', _static=True)
        m.connect('space', '/nasa/images', _static=True)
        m.create_regs(['content', 'blog'])
        
        self.assertEqual('http://www.google.com/search', url_for('http://www.google.com/search'))
        self.assertEqual('http://www.google.com/search?q=routes', url_for('http://www.google.com/search', q='routes'))
        self.assertEqual('/delicious.jpg', url_for('/delicious.jpg'))
        self.assertEqual('/delicious/search?v=routes', url_for('/delicious/search', v='routes'))
        self.assertEqual('/content/list/', url_for(controller='/content', action='list'))
        self.assertEqual('/content/list/?page=1', url_for(controller='/content', action='list', page='1'))

    def test_no_named_path_with_script(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        self.con.environ = dict(SCRIPT_NAME='/webapp', HTTP_HOST='example.com')
        m.connect(':controller/:action/:id')
        m.connect('home', 'http://www.groovie.org/', _static=True)
        m.connect('space', '/nasa/images', _static=True)
        m.create_regs(['content', 'blog'])
        
        self.assertEqual('http://www.google.com/search', url_for('http://www.google.com/search'))
        self.assertEqual('http://www.google.com/search?q=routes', url_for('http://www.google.com/search', q='routes'))
        self.assertEqual('/webapp/delicious.jpg', url_for('/delicious.jpg'))
        self.assertEqual('/webapp/delicious/search?v=routes', url_for('/delicious/search', v='routes'))

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

        m = Mapper()
        m.connect(':controller/:(action)-:(id).html')
        m.connect('archives', 'archives/:year/:month/:day/:slug', controller='archives', action='view',
                  _filter=article_filter)
        m.create_regs(['content','archives','admin/comments'])
        self.con.mapper = m
        
        self.assertRaises(Exception, url_for, controller='content', action='view')
        self.assertRaises(Exception, url_for, controller='content')
        
        self.assertEqual('/content/view-3.html', url_for(controller='content', action='view', id=3))
        self.assertEqual('/content/index-2.html', url_for(controller='content', id=2))
        
        self.assertEqual('/archives/2005/10/5/happy', 
            url_for('archives',year=2005, month=10, day=5, slug='happy'))
        story = dict(year=2003, month=8, day=2, slug='woopee')
        empty = {}
        self.assertEqual({'controller':'archives','action':'view','year':'2005',
            'month':'10','day':'5','slug':'happy'}, m.match('/archives/2005/10/5/happy'))
        self.assertEqual('/archives/2003/8/2/woopee', url_for('archives', article=story))
        self.assertEqual('/archives/2004/12/20/default', url_for('archives', article=empty))
    
    def test_with_ssl_environ(self):
        base_environ = dict(SCRIPT_NAME='', HTTPS='on', SERVER_PORT='443', PATH_INFO='/', 
            HTTP_HOST='example.com', SERVER_NAME='example.com')
        self.con.mapper_dict = {}
        self.con.environ = base_environ.copy()

        m = Mapper()
        m.connect(':controller/:action/:id')
        m.create_regs(['content','archives','admin/comments'])
        self.con.mapper = m
        
        # HTTPS is on, but we're running on a different port internally
        self.assertEqual(self.con.protocol, 'https')
        self.assertEqual('/content/view', url_for(controller='content', action='view'))
        self.assertEqual('/content/index/2', url_for(controller='content', id=2))
        self.assertEqual('https://nowhere.com/content', url_for(host='nowhere.com', controller='content'))
        
        # If HTTPS is on, but the port isn't 443, we'll need to include the port info
        environ = base_environ.copy()
        environ.update(dict(SERVER_PORT='8080'))
        self.con.environ = environ
        self.con.mapper_dict = {}
        self.assertEqual('/content/index/2', url_for(controller='content', id=2))
        self.assertEqual('https://nowhere.com/content', url_for(host='nowhere.com', controller='content'))
        self.assertEqual('https://nowhere.com:8080/content', url_for(host='nowhere.com:8080', controller='content'))
        self.assertEqual('http://nowhere.com/content', url_for(host='nowhere.com', protocol='http', controller='content'))
    
    def test_with_http_environ(self):
        base_environ = dict(SCRIPT_NAME='', SERVER_PORT='1080', PATH_INFO='/', 
            HTTP_HOST='example.com', SERVER_NAME='example.com')
        base_environ['wsgi.url_scheme'] = 'http'
        self.con.environ = base_environ.copy()
        self.con.mapper_dict = {}

        m = Mapper()
        m.connect(':controller/:action/:id')
        m.create_regs(['content','archives','admin/comments'])
        self.con.mapper = m
        
        self.assertEqual(self.con.protocol, 'http')
        self.assertEqual('/content/view', url_for(controller='content', action='view'))
        self.assertEqual('/content/index/2', url_for(controller='content', id=2))
        self.assertEqual('https://example.com/content', url_for(protocol='https', controller='content'))
    
        
    def test_subdomains(self):
        base_environ = dict(SCRIPT_NAME='', PATH_INFO='/', HTTP_HOST='example.com', SERVER_NAME='example.com')
        self.con.mapper_dict = {}
        self.con.environ = base_environ.copy()

        m = Mapper()
        m.sub_domains = True
        m.connect(':controller/:action/:id')
        m.create_regs(['content','archives','admin/comments'])
        self.con.mapper = m
        
        self.assertEqual('/content/view', url_for(controller='content', action='view'))
        self.assertEqual('/content/index/2', url_for(controller='content', id=2))
        
        environ = base_environ.copy()
        environ.update(dict(HTTP_HOST='sub.example.com'))
        self.con.environ = environ
        self.con.mapper_dict = {'sub_domain':'sub'}
        self.assertEqual('/content/view/3', url_for(controller='content', action='view', id=3))
        self.assertEqual('http://new.example.com/content', url_for(controller='content', sub_domain='new'))

    def test_subdomains_with_exceptions(self):
        base_environ = dict(SCRIPT_NAME='', PATH_INFO='/', HTTP_HOST='example.com', SERVER_NAME='example.com')
        self.con.mapper_dict = {}
        self.con.environ = base_environ.copy()

        m = Mapper()
        m.sub_domains = True
        m.sub_domains_ignore = ['www']
        m.connect(':controller/:action/:id')
        m.create_regs(['content','archives','admin/comments'])
        self.con.mapper = m
        
        self.assertEqual('/content/view', url_for(controller='content', action='view'))
        self.assertEqual('/content/index/2', url_for(controller='content', id=2))
        
        environ = base_environ.copy()
        environ.update(dict(HTTP_HOST='sub.example.com'))
        self.con.environ = environ
        self.con.mapper_dict = {'sub_domain':'sub'}
        self.assertEqual('/content/view/3', url_for(controller='content', action='view', id=3))
        self.assertEqual('http://new.example.com/content', url_for(controller='content', sub_domain='new'))
        self.assertEqual('http://example.com/content', url_for(controller='content', sub_domain='www'))
        
        self.con.mapper_dict = {'sub_domain':'www'}
        self.assertEqual('http://example.com/content/view/3', url_for(controller='content', action='view', id=3))
        self.assertEqual('http://new.example.com/content', url_for(controller='content', sub_domain='new'))
        self.assertEqual('/content', url_for(controller='content', sub_domain='sub'))
    
    def test_subdomains_with_named_routes(self):
        base_environ = dict(SCRIPT_NAME='', PATH_INFO='/', HTTP_HOST='example.com', SERVER_NAME='example.com')
        self.con.mapper_dict = {}
        self.con.environ = base_environ.copy()

        m = Mapper()
        m.sub_domains = True
        m.connect(':controller/:action/:id')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.connect('building', 'building/:campus/:building/alljacks', controller='building', action='showjacks')
        m.create_regs(['content','blog','admin/comments','building'])
        self.con.mapper = m
        
        self.assertEqual('/content/view', url_for(controller='content', action='view'))
        self.assertEqual('/content/index/2', url_for(controller='content', id=2))
        self.assertEqual('/category', url_for('category_home'))
        self.assertEqual('http://new.example.com/category', url_for('category_home', sub_domain='new'))
        
        environ = base_environ.copy()
        environ.update(dict(HTTP_HOST='sub.example.com'))
        self.con.environ = environ
        self.con.mapper_dict = {'sub_domain':'sub'}
        self.assertEqual('/content/view/3', url_for(controller='content', action='view', id=3))
        self.assertEqual('http://joy.example.com/building/west/merlot/alljacks', 
            url_for('building', campus='west', building='merlot', sub_domain='joy'))
        self.assertEqual('http://example.com/category/feeds', url_for('category_home', section='feeds', sub_domain=None))
    
    def test_subdomains_with_ports(self):
        base_environ = dict(SCRIPT_NAME='', PATH_INFO='/', HTTP_HOST='example.com:8000', SERVER_NAME='example.com')
        self.con.mapper_dict = {}
        self.con.environ = base_environ.copy()

        m = Mapper()
        m.sub_domains = True
        m.connect(':controller/:action/:id')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.connect('building', 'building/:campus/:building/alljacks', controller='building', action='showjacks')
        m.create_regs(['content','blog','admin/comments','building'])
        self.con.mapper = m
        
        self.assertEqual('/content/view', url_for(controller='content', action='view'))
        self.assertEqual('/category', url_for('category_home'))
        self.assertEqual('http://new.example.com:8000/category', url_for('category_home', sub_domain='new'))
        self.assertEqual('http://joy.example.com:8000/building/west/merlot/alljacks', 
            url_for('building', campus='west', building='merlot', sub_domain='joy'))
        
        self.con.environ['HTTP_HOST'] = 'example.com'
        self.assertEqual('http://new.example.com/category', url_for('category_home', sub_domain='new'))
    
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
        m = Mapper(directory=controller_dir)
        m.always_scan = True
        m.connect(':controller/:action/:id')
        
        assert {'action':'index', 'controller':'content','id':None} == m.match('/content')
        assert {'action':'index', 'controller':'users','id':None} == m.match('/users')
        assert {'action':'index', 'controller':'admin/users','id':None} == m.match('/admin/users')        

class TestUtilsWithExplicit(unittest.TestCase):
    def setUp(self):
        m = Mapper(explicit=True)
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
        
        self.assertRaises(Exception, url_for, controller='blog')
        self.assertRaises(Exception, url_for)
        self.assertEqual('/blog/view/3', url_for(controller='blog', action='view', id=3))
        self.assertEqual('https://www.test.com/viewpost', url_for(controller='post', action='view', protocol='https'))
        self.assertEqual('http://www.test.org/content/view/2', url_for(host='www.test.org', controller='content', action='view', id=2))
    
    def test_url_for_with_defaults(self):
        con = self.con
        con.mapper_dict = {'controller':'blog','action':'view','id':4}
        
        self.assertRaises(Exception, url_for)
        self.assertRaises(Exception, url_for, controller='post')
        self.assertRaises(Exception, url_for, id=2)
        self.assertEqual('/viewpost/4', url_for(controller='post', action='view', id=4))
        
        con.mapper_dict = {'controller':'blog','action':'view','year':2004}
        self.assertRaises(Exception, url_for, month=10)
        self.assertRaises(Exception, url_for, month=9, day=2)
        self.assertRaises(Exception, url_for, controller='blog', year=None)
    
    def test_url_for_with_more_defaults(self):
        con = self.con
        con.mapper_dict = {'controller':'blog','action':'view','id':4}
        
        self.assertRaises(Exception, url_for)
        self.assertRaises(Exception, url_for, controller='post')
        self.assertRaises(Exception, url_for, id=2)
        self.assertEqual('/viewpost/4', url_for(controller='post', action='view', id=4))
        
        con.mapper_dict = {'controller':'blog','action':'view','year':2004}
        self.assertRaises(Exception, url_for, month=10)
        self.assertRaises(Exception, url_for)
    
    def test_url_for_with_defaults_and_qualified(self):
        m = self.con.mapper
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])
        env = dict(SCRIPT_NAME='', SERVER_NAME='www.example.com', SERVER_PORT='80', PATH_INFO='/blog/view/4')
        env['wsgi.url_scheme'] = 'http'
        
        self.con.environ = env
        
        self.assertRaises(Exception, url_for)
        self.assertRaises(Exception, url_for, controller='post')
        self.assertRaises(Exception, url_for, id=2)
        self.assertRaises(Exception, url_for, qualified=True, controller='blog', id=4)
        self.assertEqual('http://www.example.com/blog/view/4', url_for(qualified=True, controller='blog', action='view', id=4))
        self.assertEqual('/viewpost/4', url_for(controller='post', action='view', id=4))
        
        env = dict(SCRIPT_NAME='', SERVER_NAME='www.example.com', SERVER_PORT='8080', PATH_INFO='/blog/view/4')
        env['wsgi.url_scheme'] = 'http'
        self.con.environ = env
        self.assertRaises(Exception, url_for, controller='post')
        self.assertEqual('http://www.example.com:8080/blog/view/4', url_for(qualified=True, controller='blog', action='view', id=4))
        
    
    def test_with_route_names(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.create_regs(['content','blog','admin/comments'])

        self.assertRaises(Exception, url_for, controller='content', action='view')
        self.assertRaises(Exception, url_for, controller='content')
        self.assertRaises(Exception, url_for, controller='admin/comments')
        self.assertEqual('/category', url_for('category_home'))
        self.assertEqual('/category/food', url_for('category_home', section='food'))
        self.assertRaises(Exception, url_for, 'home', controller='content')
        self.assertEqual('/', url_for('home'))

    def test_with_route_names_and_nomin(self):
        m = self.con.mapper
        m.minimization = False
        self.con.mapper_dict = {}
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.create_regs(['content','blog','admin/comments'])

        self.assertRaises(Exception, url_for, controller='content', action='view')
        self.assertRaises(Exception, url_for, controller='content')
        self.assertRaises(Exception, url_for, controller='admin/comments')
        self.assertEqual('/category/home', url_for('category_home'))
        self.assertEqual('/category/food', url_for('category_home', section='food'))
        self.assertRaises(Exception, url_for, 'home', controller='content')
        self.assertEqual('/', url_for('home'))

    def test_with_route_names_and_defaults(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        m.connect('home', '', controller='blog', action='splash')
        m.connect('category_home', 'category/:section', controller='blog', action='view', section='home')
        m.connect('building', 'building/:campus/:building/alljacks', controller='building', action='showjacks')
        m.create_regs(['content','blog','admin/comments','building'])

        self.con.mapper_dict = dict(controller='building', action='showjacks', campus='wilma', building='port')
        self.assertRaises(Exception, url_for)
        self.assertEqual('/building/wilma/port/alljacks', url_for(controller='building', action='showjacks', campus='wilma', building='port'))
        self.assertEqual('/', url_for('home'))

    def test_with_resource_route_names(self):
        m = Mapper()
        self.con.mapper = m
        self.con.mapper_dict = {}
        m.resource('message', 'messages', member={'mark':'GET'}, collection={'rss':'GET'})
        m.create_regs(['messages'])

        self.assertRaises(Exception, url_for, controller='content', action='view')
        self.assertRaises(Exception, url_for, controller='content')
        self.assertRaises(Exception, url_for, controller='admin/comments')
        self.assertEqual('/messages', url_for('messages'))
        self.assertEqual('/messages/rss', url_for('rss_messages'))
        self.assertEqual('/messages/4', url_for('message', id=4))
        self.assertEqual('/messages/4/edit', url_for('edit_message', id=4))
        self.assertEqual('/messages/4/mark', url_for('mark_message', id=4))
        self.assertEqual('/messages/new', url_for('new_message'))
        
        self.assertEqual('/messages.xml', url_for('formatted_messages', format='xml'))
        self.assertEqual('/messages/rss.xml', url_for('formatted_rss_messages', format='xml'))
        self.assertEqual('/messages/4.xml', url_for('formatted_message', id=4, format='xml'))
        self.assertEqual('/messages/4/edit.xml', url_for('formatted_edit_message', id=4, format='xml'))
        self.assertEqual('/messages/4/mark.xml', url_for('formatted_mark_message', id=4, format='xml'))
        self.assertEqual('/messages/new.xml', url_for('formatted_new_message', format='xml'))

    def test_with_resource_route_names_and_nomin(self):
        m = Mapper()
        self.con.mapper = m
        self.con.mapper_dict = {}
        m.minimization = False
        m.resource('message', 'messages', member={'mark':'GET'}, collection={'rss':'GET'})
        m.create_regs(['messages'])

        self.assertRaises(Exception, url_for, controller='content', action='view')
        self.assertRaises(Exception, url_for, controller='content')
        self.assertRaises(Exception, url_for, controller='admin/comments')
        self.assertEqual('/messages', url_for('messages'))
        self.assertEqual('/messages/rss', url_for('rss_messages'))
        self.assertEqual('/messages/4', url_for('message', id=4))
        self.assertEqual('/messages/4/edit', url_for('edit_message', id=4))
        self.assertEqual('/messages/4/mark', url_for('mark_message', id=4))
        self.assertEqual('/messages/new', url_for('new_message'))
        
        self.assertEqual('/messages.xml', url_for('formatted_messages', format='xml'))
        self.assertEqual('/messages/rss.xml', url_for('formatted_rss_messages', format='xml'))
        self.assertEqual('/messages/4.xml', url_for('formatted_message', id=4, format='xml'))
        self.assertEqual('/messages/4/edit.xml', url_for('formatted_edit_message', id=4, format='xml'))
        self.assertEqual('/messages/4/mark.xml', url_for('formatted_mark_message', id=4, format='xml'))
        self.assertEqual('/messages/new.xml', url_for('formatted_new_message', format='xml'))
        

if __name__ == '__main__':
    unittest.main()
else:
    def bench_gen(withcache = False):
        m = Mapper()
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
        print "Generation (%s URLs) RouteSet" % (n*6)
        print "%s ms/url" % (per_url*1000)
        print "%s urls/s\n" % (1.00/per_url)
