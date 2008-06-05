"""test_generation"""

import sys, time, unittest
import urllib
from routes import *

class TestGeneration(unittest.TestCase):
    
    def test_all_static_no_reqs(self):
        m = Mapper()
        m.connect('hello/world')
        
        assert '/hello/world' == m.generate()
    
    def test_basic_dynamic(self):
        for path in ['hi/:fred', 'hi/:(fred)']:
            m = Mapper()
            m.connect(path)
        
            assert '/hi/index' == m.generate(fred='index')
            assert '/hi/show' == m.generate(fred='show')
            assert '/hi/list%20people' == m.generate(fred='list people')
            assert None == m.generate()
    
    def test_dynamic_with_default(self):
        for path in ['hi/:action', 'hi/:(action)']:
            m = Mapper()
            m.connect(path)
        
            assert '/hi' == m.generate(action='index')
            assert '/hi/show' == m.generate(action='show')
            assert '/hi/list%20people' == m.generate(action='list people')
            assert '/hi' == m.generate()
    
    def test_dynamic_with_false_equivs(self):
        m = Mapper()
        m.connect('article/:page', page=False)
        m.connect(':controller/:action/:id')
        
        assert '/blog/view/0' == m.generate(controller="blog", action="view", id="0")
        assert '/blog/view/0' == m.generate(controller="blog", action="view", id=0)
        assert '/blog/view/False' == m.generate(controller="blog", action="view", id=False)
        assert '/blog/view/False' == m.generate(controller="blog", action="view", id='False')
        assert '/blog/view' == m.generate(controller="blog", action="view", id=None)
        assert '/blog/view' == m.generate(controller="blog", action="view", id='None')
        assert '/article' == m.generate(page=None)
        
        m = Mapper()
        m.connect('view/:home/:area', home="austere", area=None)
        
        assert '/view/sumatra' == m.generate(home='sumatra')
        assert '/view/austere/chicago' == m.generate(area='chicago')
        
        m = Mapper()
        m.connect('view/:home/:area', home=None, area=None)
        
        assert '/view/None/chicago' == m.generate(home=None, area='chicago')
    
    def test_dynamic_with_underscore_parts(self):
        m = Mapper()
        m.connect('article/:small_page', small_page=False)
        m.connect(':(controller)/:(action)/:(id)')
        
        assert '/blog/view/0' == m.generate(controller="blog", action="view", id="0")
        assert '/blog/view/False' == m.generate(controller="blog", action="view", id='False')
        assert '/blog/view' == m.generate(controller="blog", action="view", id='None')
        assert '/article' == m.generate(small_page=None)
        assert '/article/hobbes' == m.generate(small_page='hobbes')
        
    def test_dynamic_with_false_equivs_and_splits(self):
        m = Mapper()
        m.connect('article/:(page)', page=False)
        m.connect(':(controller)/:(action)/:(id)')
        
        assert '/blog/view/0' == m.generate(controller="blog", action="view", id="0")
        assert '/blog/view/0' == m.generate(controller="blog", action="view", id=0)
        assert '/blog/view/False' == m.generate(controller="blog", action="view", id=False)
        assert '/blog/view/False' == m.generate(controller="blog", action="view", id='False')
        assert '/blog/view' == m.generate(controller="blog", action="view", id=None)
        assert '/blog/view' == m.generate(controller="blog", action="view", id='None')
        assert '/article' == m.generate(page=None)
        
        m = Mapper()
        m.connect('view/:(home)/:(area)', home="austere", area=None)
        
        assert '/view/sumatra' == m.generate(home='sumatra')
        assert '/view/austere/chicago' == m.generate(area='chicago')
        
        m = Mapper()
        m.connect('view/:(home)/:(area)', home=None, area=None)
        
        assert '/view/None/chicago' == m.generate(home=None, area='chicago')

    def test_dynamic_with_regexp_condition(self):
        for path in ['hi/:name', 'hi/:(name)']:
            m = Mapper()
            m.connect(path, requirements = {'name':'[a-z]+'})
        
            assert '/hi/index' == m.generate(name='index')
            assert None == m.generate(name='fox5')
            assert None == m.generate(name='something_is_up')
            assert '/hi/abunchofcharacter' == m.generate(name='abunchofcharacter')
            assert None == m.generate()
    
    def test_dynamic_with_default_and_regexp_condition(self):
        for path in ['hi/:action', 'hi/:(action)']:
            m = Mapper()
            m.connect(path, requirements = {'action':'[a-z]+'})
        
            assert '/hi' == m.generate(action='index')
            assert None == m.generate(action='fox5')
            assert None == m.generate(action='something_is_up')
            assert None == m.generate(action='list people')
            assert '/hi/abunchofcharacter' == m.generate(action='abunchofcharacter')
            assert '/hi' == m.generate()
    
    def test_path(self):
        for path in ['hi/*file', 'hi/*(file)']:
            m = Mapper()
            m.connect(path)
        
            assert '/hi' == m.generate(file=None)
            assert '/hi/books/learning_python.pdf' == m.generate(file='books/learning_python.pdf')
            assert '/hi/books/development%26whatever/learning_python.pdf' == m.generate(file='books/development&whatever/learning_python.pdf')
    
    def test_path_backwards(self):
        for path in ['*file/hi', '*(file)/hi']:
            m = Mapper()
            m.connect(path)

            assert '/hi' == m.generate(file=None)
            assert '/books/learning_python.pdf/hi' == m.generate(file='books/learning_python.pdf')
            assert '/books/development%26whatever/learning_python.pdf/hi' == m.generate(file='books/development&whatever/learning_python.pdf')
    
    def test_controller(self):
        for path in ['hi/:controller', 'hi/:(controller)']:
            m = Mapper()
            m.connect(path)
        
            assert '/hi/content' == m.generate(controller='content')
            assert '/hi/admin/user' == m.generate(controller='admin/user')
    
    def test_controller_with_static(self):
        for path in ['hi/:controller', 'hi/:(controller)']:
            m = Mapper()
            m.connect(path)
            m.connect('google', 'http://www.google.com', _static=True)
        
            assert '/hi/content' == m.generate(controller='content')
            assert '/hi/admin/user' == m.generate(controller='admin/user')
            assert 'http://www.google.com' == url_for('google')
    
    def test_standard_route(self):
        for path in [':controller/:action/:id', ':(controller)/:(action)/:(id)']:
            m = Mapper()
            m.connect(path)
        
            assert '/content' == m.generate(controller='content', action='index')
            assert '/content/list' == m.generate(controller='content', action='list')
            assert '/content/show/10' == m.generate(controller='content', action='show', id ='10')
        
            assert '/admin/user' == m.generate(controller='admin/user', action='index')
            assert '/admin/user/list' == m.generate(controller='admin/user', action='list')
            assert '/admin/user/show/10' == m.generate(controller='admin/user', action='show', id='10')
    
    def test_multiroute(self):
        m = Mapper()
        m.connect('archive/:year/:month/:day', controller='blog', action='view', month=None, day=None,
                            requirements={'month':'\d{1,2}','day':'\d{1,2}'})
        m.connect('viewpost/:id', controller='post', action='view')
        m.connect(':controller/:action/:id')
        
        assert '/blog/view?year=2004&month=blah' == m.generate(controller='blog', action='view', year=2004, month='blah')
        assert '/archive/2004/11' == m.generate(controller='blog', action='view', year=2004, month=11)
        assert '/archive/2004/11' == m.generate(controller='blog', action='view', year=2004, month='11')
        assert '/archive/2004' == m.generate(controller='blog', action='view', year=2004)
        assert '/viewpost/3' == m.generate(controller='post', action='view', id=3)
    
    def test_multiroute_with_splits(self):
        m = Mapper()
        m.connect('archive/:(year)/:(month)/:(day)', controller='blog', action='view', month=None, day=None,
                            requirements={'month':'\d{1,2}','day':'\d{1,2}'})
        m.connect('viewpost/:(id)', controller='post', action='view')
        m.connect(':(controller)/:(action)/:(id)')
        
        assert '/blog/view?year=2004&month=blah' == m.generate(controller='blog', action='view', year=2004, month='blah')
        assert '/archive/2004/11' == m.generate(controller='blog', action='view', year=2004, month=11)
        assert '/archive/2004/11' == m.generate(controller='blog', action='view', year=2004, month='11')
        assert '/archive/2004' == m.generate(controller='blog', action='view', year=2004)
        assert '/viewpost/3' == m.generate(controller='post', action='view', id=3)
    
    def test_big_multiroute(self):
        m = Mapper()
        m.connect('', controller='articles', action='index')
        m.connect('admin', controller='admin/general', action='index')

        m.connect('admin/comments/article/:article_id/:action/:id', controller = 'admin/comments', action=None, id=None)
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
        
        
        assert '/pages/the/idiot/has/spoken' == m.generate(controller='articles', action='view_page',
                            name='the/idiot/has/spoken')
        assert '/' == m.generate(controller='articles', action='index')
        assert '/xml/articlerss/4/feed.xml' == m.generate(controller='xml', action='articlerss', id=4)
        assert '/xml/rss/feed.xml' == m.generate(controller='xml', action='rss')
        assert '/admin/comments/article/4/view/2' == m.generate(controller='admin/comments', action='view', article_id=4, id=2)
        assert '/admin' == m.generate(controller='admin/general')
        assert '/admin/comments/article/4/index' == m.generate(controller='admin/comments', article_id=4)
        assert '/admin/comments/article/4' == m.generate(controller='admin/comments', action=None, article_id=4)
        assert '/articles/2004/2/20/page/1' == m.generate(controller='articles', action='find_by_date', 
                    year=2004, month=2, day=20, page=1)
        assert '/articles/category' == m.generate(controller='articles', action='category')
        assert '/xml/index/feed.xml' == m.generate(controller='xml')
        assert '/xml/articlerss/feed.xml' == m.generate(controller='xml', action='articlerss')
        
        assert None == m.generate(controller='admin/comments', id=2)
        assert None == m.generate(controller='articles', action='find_by_date', year=2004)
    
    def test_big_multiroute_with_splits(self):
        m = Mapper()
        m.connect('', controller='articles', action='index')
        m.connect('admin', controller='admin/general', action='index')

        m.connect('admin/comments/article/:(article_id)/:(action)/:(id).html', controller = 'admin/comments', action=None, id=None)
        m.connect('admin/trackback/article/:(article_id)/:action/:(id).html', controller='admin/trackback', action=None, id=None)
        m.connect('admin/content/:(action)/:(id)', controller='admin/content')

        m.connect('xml/:(action)/feed.xml', controller='xml')
        m.connect('xml/articlerss/:(id)/feed.xml', controller='xml', action='articlerss')
        m.connect('index.rdf', controller='xml', action='rss')

        m.connect('articles', controller='articles', action='index')
        m.connect('articles/page/:(page).myt', controller='articles', action='index', requirements = {'page':'\d+'})

        m.connect('articles/:(year)/:month/:(day)/page/:page', controller='articles', action='find_by_date', month = None, day = None,
                            requirements = {'year':'\d{4}', 'month':'\d{1,2}','day':'\d{1,2}'})
        m.connect('articles/category/:id', controller='articles', action='category')
        m.connect('pages/*name', controller='articles', action='view_page')
        
        
        assert '/pages/the/idiot/has/spoken' == m.generate(controller='articles', action='view_page',
                            name='the/idiot/has/spoken')
        assert '/' == m.generate(controller='articles', action='index')
        assert '/xml/articlerss/4/feed.xml' == m.generate(controller='xml', action='articlerss', id=4)
        assert '/xml/rss/feed.xml' == m.generate(controller='xml', action='rss')
        assert '/admin/comments/article/4/view/2.html' == m.generate(controller='admin/comments', action='view', article_id=4, id=2)
        assert '/admin' == m.generate(controller='admin/general')
        assert '/admin/comments/article/4/edit/3.html' == m.generate(controller='admin/comments', article_id=4, action='edit', id=3)
        assert None == m.generate(controller='admin/comments', action=None, article_id=4)
        assert '/articles/2004/2/20/page/1' == m.generate(controller='articles', action='find_by_date', 
                    year=2004, month=2, day=20, page=1)
        assert '/articles/category' == m.generate(controller='articles', action='category')
        assert '/xml/index/feed.xml' == m.generate(controller='xml')
        assert '/xml/articlerss/feed.xml' == m.generate(controller='xml', action='articlerss')
        
        assert None == m.generate(controller='admin/comments', id=2)
        assert None == m.generate(controller='articles', action='find_by_date', year=2004)

    def test_no_extras(self):
        m = Mapper()
        m.connect(':controller/:action/:id')
        m.connect('archive/:year/:month/:day', controller='blog', action='view', month=None, day=None)
        
        assert '/archive/2004' == m.generate(controller='blog', action='view', year=2004)
    
    def test_no_extras_with_splits(self):
        m = Mapper()
        m.connect(':(controller)/:(action)/:(id)')
        m.connect('archive/:(year)/:(month)/:(day)', controller='blog', action='view', month=None, day=None)
        
        assert '/archive/2004' == m.generate(controller='blog', action='view', year=2004)
    
    def test_the_smallest_route(self):
        for path in ['pages/:title', 'pages/:(title)']:
            m = Mapper()
            m.connect('', controller='page', action='view', title='HomePage')
            m.connect(path, controller='page', action='view')
        
            assert '/' == m.generate(controller='page', action='view', title='HomePage')
            assert '/pages/joe' == m.generate(controller='page', action='view', title='joe')
    
    def test_extras(self):
        m = Mapper()
        m.connect('viewpost/:id', controller='post', action='view')
        m.connect(':controller/:action/:id')
        
        assert '/viewpost/2?extra=x%2Fy' == m.generate(controller='post', action='view', id=2, extra='x/y')
        assert '/blog?extra=3' == m.generate(controller='blog', action='index', extra=3)
        assert '/viewpost/2?extra=3' == m.generate(controller='post', action='view', id=2, extra=3)
    
    def test_extras_with_splits(self):
        m = Mapper()
        m.connect('viewpost/:(id)', controller='post', action='view')
        m.connect(':(controller)/:(action)/:(id)')
        
        assert '/blog?extra=3' == m.generate(controller='blog', action='index', extra=3)
        assert '/viewpost/2?extra=3' == m.generate(controller='post', action='view', id=2, extra=3)
    
    def test_static(self):
        m = Mapper()
        m.connect('hello/world',known='known_value',controller='content',action='index')
        
        assert '/hello/world' == m.generate(controller='content',action= 'index',known ='known_value')
        assert '/hello/world?extra=hi' == m.generate(controller='content',action='index',known='known_value',extra='hi')
        
        assert None == m.generate(known='foo')
    
    def test_typical(self):
        for path in [':controller/:action/:id', ':(controller)/:(action)/:(id)']:
            m = Mapper()
            m.connect(path, action = 'index', id = None)
        
            assert '/content' == m.generate(controller='content', action='index')
            assert '/content/list' == m.generate(controller='content', action='list')
            assert '/content/show/10' == m.generate(controller='content', action='show', id=10)
        
            assert '/admin/user' == m.generate(controller='admin/user', action='index')
            assert '/admin/user' == m.generate(controller='admin/user')
            assert '/admin/user/show/10' == m.generate(controller='admin/user', action='show', id=10)
        
            assert '/content' == m.generate(controller='content')
    
    def test_route_with_fixnum_default(self):
        m = Mapper()
        m.connect('page/:id', controller='content', action='show_page', id =1)
        m.connect(':controller/:action/:id')
        
        assert '/page' == m.generate(controller='content', action='show_page')
        assert '/page' == m.generate(controller='content', action='show_page', id=1)
        assert '/page' == m.generate(controller='content', action='show_page', id='1')
        assert '/page/10' == m.generate(controller='content', action='show_page', id=10)
        
        assert '/blog/show/4' == m.generate(controller='blog', action='show', id=4)
        assert '/page' == m.generate(controller='content', action='show_page')
        assert '/page/4' == m.generate(controller='content', action='show_page',id=4)
        assert '/content/show' == m.generate(controller='content', action='show')
    
    def test_route_with_fixnum_default_with_splits(self):
        m = Mapper()
        m.connect('page/:(id)', controller='content', action='show_page', id =1)
        m.connect(':(controller)/:(action)/:(id)')
        
        assert '/page' == m.generate(controller='content', action='show_page')
        assert '/page' == m.generate(controller='content', action='show_page', id=1)
        assert '/page' == m.generate(controller='content', action='show_page', id='1')
        assert '/page/10' == m.generate(controller='content', action='show_page', id=10)
        
        assert '/blog/show/4' == m.generate(controller='blog', action='show', id=4)
        assert '/page' == m.generate(controller='content', action='show_page')
        assert '/page/4' == m.generate(controller='content', action='show_page',id=4)
        assert '/content/show' == m.generate(controller='content', action='show')
    
    def test_uppercase_recognition(self):
        for path in [':controller/:action/:id', ':(controller)/:(action)/:(id)']:
            m = Mapper()
            m.connect(path)

            assert '/Content' == m.generate(controller='Content', action='index')
            assert '/Content/list' == m.generate(controller='Content', action='list')
            assert '/Content/show/10' == m.generate(controller='Content', action='show', id='10')

            assert '/Admin/NewsFeed' == m.generate(controller='Admin/NewsFeed', action='index')
    
    def test_backwards(self):
        m = Mapper()
        m.connect('page/:id/:action', controller='pages', action='show')
        m.connect(':controller/:action/:id')

        assert '/page/20' == m.generate(controller='pages', action='show', id=20)
        assert '/pages/boo' == m.generate(controller='pages', action='boo')

    def test_backwards_with_splits(self):
        m = Mapper()
        m.connect('page/:(id)/:(action)', controller='pages', action='show')
        m.connect(':(controller)/:(action)/:(id)')

        assert '/page/20' == m.generate(controller='pages', action='show', id=20)
        assert '/pages/boo' == m.generate(controller='pages', action='boo')
    
    def test_both_requirement_and_optional(self):
        m = Mapper()
        m.connect('test/:year', controller='post', action='show', year=None, requirements = {'year':'\d{4}'})

        assert '/test' == m.generate(controller='post', action='show')
        assert '/test' == m.generate(controller='post', action='show', year=None)
    
    def test_set_to_nil_forgets(self):
        m = Mapper()
        m.connect('pages/:year/:month/:day', controller='content', action='list_pages', month=None, day=None)
        m.connect(':controller/:action/:id')

        assert '/pages/2005' == m.generate(controller='content', action='list_pages', year=2005)
        assert '/pages/2005/6' == m.generate(controller='content', action='list_pages', year=2005, month=6)
        assert '/pages/2005/6/12' == m.generate(controller='content', action='list_pages', year=2005, month=6, day=12)
    
    def test_url_with_no_action_specified(self):
        m = Mapper()
        m.connect('', controller='content')
        m.connect(':controller/:action/:id')

        assert '/' == m.generate(controller='content', action='index')
        assert '/' == m.generate(controller='content')
    
    def test_url_with_prefix(self):
        m = Mapper()
        m.prefix = '/blog'
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        assert '/blog/content/view' == m.generate(controller='content', action='view')
        assert '/blog/content' == m.generate(controller='content')
        assert '/blog/admin/comments' == m.generate(controller='admin/comments')

    def test_url_with_prefix_deeper(self):
        m = Mapper()
        m.prefix = '/blog/phil'
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        assert '/blog/phil/content/view' == m.generate(controller='content', action='view')
        assert '/blog/phil/content' == m.generate(controller='content')
        assert '/blog/phil/admin/comments' == m.generate(controller='admin/comments')

    def test_url_with_environ_empty(self):
        m = Mapper()
        m.environ = dict(SCRIPT_NAME='')
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        assert '/content/view' == m.generate(controller='content', action='view')
        assert '/content' == m.generate(controller='content')
        assert '/admin/comments' == m.generate(controller='admin/comments')

    def test_url_with_environ(self):
        m = Mapper()
        m.environ = dict(SCRIPT_NAME='/blog')
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        assert '/blog/content/view' == m.generate(controller='content', action='view')
        assert '/blog/content' == m.generate(controller='content')
        assert '/blog/content' == m.generate(controller='content')
        assert '/blog/admin/comments' == m.generate(controller='admin/comments')

        m.environ = dict(SCRIPT_NAME='/notblog')

        assert '/notblog/content/view' == m.generate(controller='content', action='view')
        assert '/notblog/content' == m.generate(controller='content')
        assert '/notblog/content' == m.generate(controller='content')
        assert '/notblog/admin/comments' == m.generate(controller='admin/comments')
        

    def test_url_with_environ_and_absolute(self):
        m = Mapper()
        m.environ = dict(SCRIPT_NAME='/blog')
        m.connect('image', 'image/:name', _absolute=True)
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        assert '/blog/content/view' == m.generate(controller='content', action='view')
        assert '/blog/content' == m.generate(controller='content')
        assert '/blog/content' == m.generate(controller='content')
        assert '/blog/admin/comments' == m.generate(controller='admin/comments')
        assert '/image/topnav.jpg' == url_for('image', name='topnav.jpg')
    
    def test_route_with_odd_leftovers(self):
        m = Mapper()
        m.connect(':controller/:(action)-:(id)')
        m.create_regs(['content','blog','admin/comments'])
        
        assert '/content/view-' == m.generate(controller='content', action='view')
        assert '/content/index-' == m.generate(controller='content')
    
    def test_route_with_end_extension(self):
        m = Mapper()
        m.connect(':controller/:(action)-:(id).html')
        m.create_regs(['content','blog','admin/comments'])
        
        assert None == m.generate(controller='content', action='view')
        assert None == m.generate(controller='content')
        
        assert '/content/view-3.html' == m.generate(controller='content', action='view', id=3)
        assert '/content/index-2.html' == m.generate(controller='content', id=2)
    
    def _assert_restful_routes(self, m, options, path_prefix=''):
        baseroute = '/' + path_prefix + options['controller']
        assert baseroute == m.generate(action='index', **options)
        assert baseroute + '.xml' == m.generate(action='index', format='xml', **options)
        assert baseroute + '/new' == m.generate(action='new', **options)
        assert baseroute + '/1' == m.generate(action='show', id='1', **options)
        assert baseroute + '/1/edit' == m.generate(action='edit',id='1', **options)
        assert baseroute + '/1.xml' == m.generate(action='show', id='1',format='xml', **options)
        
        assert baseroute == m.generate(action='create', method='post', **options)
        assert baseroute + '/1' == m.generate(action='update', method='put', id='1', **options)
        assert baseroute + '/1' == m.generate(action='delete', method='delete', id='1', **options)
    
    def test_resources(self):
        m = Mapper()
        m.resource('message', 'messages')
        m.create_regs(['messages'])
        options = dict(controller='messages')
        assert '/messages' == url_for('messages')
        assert '/messages.xml' == url_for('formatted_messages', format='xml')
        assert '/messages/1' == url_for('message', id=1)
        assert '/messages/1.xml' == url_for('formatted_message', id=1, format='xml')
        assert '/messages/new' == url_for('new_message')
        assert '/messages/1.xml' == url_for('formatted_message', id=1, format='xml')
        assert '/messages/1/edit' == url_for('edit_message', id=1)
        assert '/messages/1/edit.xml' == url_for('formatted_edit_message', id=1, format='xml')
        self._assert_restful_routes(m, options)
    
    def test_resources_with_path_prefix(self):
        m = Mapper()
        m.resource('message', 'messages', path_prefix='/thread/:threadid')
        m.create_regs(['messages'])
        options = dict(controller='messages', threadid='5')
        self._assert_restful_routes(m, options, path_prefix='thread/5/')
    
    def test_resources_with_collection_action(self):
        m = Mapper()
        m.resource('message', 'messages', collection=dict(rss='GET'))
        m.create_regs(['messages'])
        options = dict(controller='messages')
        self._assert_restful_routes(m, options)
        assert '/messages/rss' == m.generate(controller='messages', action='rss')
        assert '/messages/rss' == url_for('rss_messages')
        assert '/messages/rss.xml' == m.generate(controller='messages', action='rss', format='xml')
        assert '/messages/rss.xml' == url_for('formatted_rss_messages', format='xml')
    
    def test_resources_with_member_action(self):
        for method in ['put', 'post']:
            m = Mapper()
            m.resource('message', 'messages', member=dict(mark=method))
            m.create_regs(['messages'])
            options = dict(controller='messages')
            self._assert_restful_routes(m, options)
            assert '/messages/1/mark' == m.generate(method=method, action='mark', id='1', **options)
            assert '/messages/1/mark.xml' == m.generate(method=method, action='mark', id='1', format='xml', **options)
    
    def test_resources_with_new_action(self):
        m = Mapper()
        m.resource('message', 'messages/', new=dict(preview='POST'))
        m.create_regs(['messages'])
        options = dict(controller='messages')
        self._assert_restful_routes(m, options)
        assert '/messages/new/preview' == m.generate(controller='messages', action='preview', method='post')
        assert '/messages/new/preview' == url_for('preview_new_message')
        assert '/messages/new/preview.xml' == m.generate(controller='messages', action='preview', method='post', format='xml')
        assert '/messages/new/preview.xml' == url_for('formatted_preview_new_message', format='xml')
    
    def test_resources_with_name_prefix(self):
        m = Mapper()
        m.resource('message', 'messages', name_prefix='category_', new=dict(preview='POST'))
        m.create_regs(['messages'])
        options = dict(controller='messages')
        self._assert_restful_routes(m, options)
        assert '/messages/new/preview' == url_for('category_preview_new_message')
        self.assertRaises(Exception, url_for, 'category_preview_new_message', method='get')

    def test_unicode(self):
        hoge = u'\u30c6\u30b9\u30c8' # the word test in Japanese
        hoge_enc = urllib.quote(hoge.encode('utf-8'))
        m = Mapper()
        m.connect(':hoge')
        self.assertEqual("/%s" % hoge_enc, m.generate(hoge=hoge))
        self.assert_(isinstance(m.generate(hoge=hoge), str))

    def test_unicode_static(self):
        hoge = u'\u30c6\u30b9\u30c8' # the word test in Japanese
        hoge_enc = urllib.quote(hoge.encode('utf-8'))
        m = Mapper()
        m.connect('google-jp', 'http://www.google.co.jp/search', _static=True)
        self.assertEqual("http://www.google.co.jp/search?q=" + hoge_enc,
                         url_for('google-jp', q=hoge))
        self.assert_(isinstance(url_for('google-jp', q=hoge), str))

    def test_other_special_chars(self):
        m = Mapper()
        m.connect('/:year/:(slug).:(format),:(locale)', locale='en', format='html')
        m.create_regs(['content'])
        
        assert '/2007/test' == m.generate(year=2007, slug='test')
        assert '/2007/test.xml' == m.generate(year=2007, slug='test', format='xml')
        assert '/2007/test.xml,ja' == m.generate(year=2007, slug='test', format='xml', locale='ja')
        assert None == m.generate(year=2007, format='html')

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
        if withcache:
            m.urlcache = {}
        m._create_gens()
        n = 5000
        start = time.time()
        for x in range(1,n):
            m.generate(controller='articles', action='index', page=4)
            m.generate(controller='admin/general', action='index')
            m.generate(controller='admin/comments', action='show', article_id=2)

            m.generate(controller='articles', action='find_by_date', year=2004, page=1)
            m.generate(controller='articles', action='category', id=4)
            m.generate(controller='xml', action='articlerss', id=2)
        end = time.time()
        ts = time.time()
        for x in range(1,n*6):
            pass
        en = time.time()
        total = end-start-(en-ts)
        per_url = total / (n*6)
        print "Generation (%s URLs)" % (n*6)
        print "%s ms/url" % (per_url*1000)
        print "%s urls/s\n" % (1.00/per_url)
