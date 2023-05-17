"""test_generation"""
import sys, time, unittest
from six.moves import urllib

from routes import *

class TestGeneration(unittest.TestCase):

    def test_all_static_no_reqs(self):
        m = Mapper()
        m.connect('hello/world')

        assert m.generate() == '/hello/world'

    def test_basic_dynamic(self):
        for path in ['hi/:fred', 'hi/:(fred)']:
            m = Mapper()
            m.connect(path)

            assert m.generate(fred='index') == '/hi/index'
            assert m.generate(fred='show') == '/hi/show'
            assert m.generate(fred='list people') == '/hi/list%20people'
            assert m.generate() is None

    def test_relative_url(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.environ = dict(HTTP_HOST='localhost')
        url = URLGenerator(m, m.environ)
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        assert url('about') == 'about'
        assert url('about', qualified=True) == 'http://localhost/about'

    def test_basic_dynamic_explicit_use(self):
        m = Mapper()
        m.connect('hi/{fred}')
        url = URLGenerator(m, {})

        assert url(fred='index') == '/hi/index'
        assert url(fred='show') == '/hi/show'
        assert url(fred='list people') == '/hi/list%20people'

    def test_dynamic_with_default(self):
        for path in ['hi/:action', 'hi/:(action)']:
            m = Mapper(explicit=False)
            m.minimization = True
            m.connect(path)

            assert m.generate(action='index') == '/hi'
            assert m.generate(action='show') == '/hi/show'
            assert m.generate(action='list people') == '/hi/list%20people'
            assert m.generate() == '/hi'

    def test_dynamic_with_false_equivs(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('article/:page', page=False)
        m.connect(':controller/:action/:id')

        assert m.generate(controller="blog", action="view", id="0") == '/blog/view/0'
        assert m.generate(controller="blog", action="view", id=0) == '/blog/view/0'
        assert m.generate(controller="blog", action="view", id=False) == '/blog/view/False'
        assert m.generate(controller="blog", action="view", id='False') == '/blog/view/False'
        assert m.generate(controller="blog", action="view", id=None) == '/blog/view'
        assert m.generate(controller="blog", action="view", id='None') == '/blog/view'
        assert m.generate(page=None) == '/article'

        m = Mapper()
        m.minimization = True
        m.connect('view/:home/:area', home="austere", area=None)

        assert m.generate(home='sumatra') == '/view/sumatra'
        assert m.generate(area='chicago') == '/view/austere/chicago'

        m = Mapper()
        m.minimization = True
        m.connect('view/:home/:area', home=None, area=None)

        assert m.generate(home=None, area='chicago') == '/view/None/chicago'

    def test_dynamic_with_underscore_parts(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('article/:small_page', small_page=False)
        m.connect(':(controller)/:(action)/:(id)')

        assert m.generate(controller="blog", action="view", id="0") == '/blog/view/0'
        assert m.generate(controller="blog", action="view", id='False') == '/blog/view/False'
        assert m.generate(controller="blog", action="view", id='None') == '/blog/view'
        assert m.generate(small_page=None) == '/article'
        assert m.generate(small_page='hobbes') == '/article/hobbes'

    def test_dynamic_with_false_equivs_and_splits(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('article/:(page)', page=False)
        m.connect(':(controller)/:(action)/:(id)')

        assert m.generate(controller="blog", action="view", id="0") == '/blog/view/0'
        assert m.generate(controller="blog", action="view", id=0) == '/blog/view/0'
        assert m.generate(controller="blog", action="view", id=False) == '/blog/view/False'
        assert m.generate(controller="blog", action="view", id='False') == '/blog/view/False'
        assert m.generate(controller="blog", action="view", id=None) == '/blog/view'
        assert m.generate(controller="blog", action="view", id='None') == '/blog/view'
        assert m.generate(page=None) == '/article'

        m = Mapper()
        m.minimization = True
        m.connect('view/:(home)/:(area)', home="austere", area=None)

        assert m.generate(home='sumatra') == '/view/sumatra'
        assert m.generate(area='chicago') == '/view/austere/chicago'

        m = Mapper()
        m.minimization = True
        m.connect('view/:(home)/:(area)', home=None, area=None)

        assert m.generate(home=None, area='chicago') == '/view/None/chicago'

    def test_dynamic_with_regexp_condition(self):
        for path in ['hi/:name', 'hi/:(name)']:
            m = Mapper()
            m.connect(path, requirements = {'name':'[a-z]+'})

            assert m.generate(name='index') == '/hi/index'
            assert m.generate(name='fox5') is None
            assert m.generate(name='something_is_up') is None
            assert m.generate(name='abunchofcharacter') == '/hi/abunchofcharacter'
            assert m.generate() is None

    def test_dynamic_with_default_and_regexp_condition(self):
        for path in ['hi/:action', 'hi/:(action)']:
            m = Mapper(explicit=False)
            m.minimization = True
            m.connect(path, requirements = {'action':'[a-z]+'})

            assert m.generate(action='index') == '/hi'
            assert m.generate(action='fox5') is None
            assert m.generate(action='something_is_up') is None
            assert m.generate(action='list people') is None
            assert m.generate(action='abunchofcharacter') == '/hi/abunchofcharacter'
            assert m.generate() == '/hi'

    def test_path(self):
        for path in ['hi/*file', 'hi/*(file)']:
            m = Mapper()
            m.minimization = True
            m.connect(path)

            assert m.generate(file=None) == '/hi'
            assert m.generate(file='books/learning_python.pdf') == '/hi/books/learning_python.pdf'
            assert m.generate(file='books/development&whatever/learning_python.pdf') == \
                '/hi/books/development%26whatever/learning_python.pdf'

    def test_path_backwards(self):
        for path in ['*file/hi', '*(file)/hi']:
            m = Mapper()
            m.minimization = True
            m.connect(path)

            assert m.generate(file=None) == '/hi'
            assert m.generate(file='books/learning_python.pdf') == '/books/learning_python.pdf/hi'
            assert m.generate(file='books/development&whatever/learning_python.pdf') == \
                '/books/development%26whatever/learning_python.pdf/hi'

    def test_controller(self):
        for path in ['hi/:controller', 'hi/:(controller)']:
            m = Mapper()
            m.connect(path)

            assert m.generate(controller='content') == '/hi/content'
            assert m.generate(controller='admin/user') == '/hi/admin/user'

    def test_controller_with_static(self):
        for path in ['hi/:controller', 'hi/:(controller)']:
            m = Mapper()
            m.connect(path)
            m.connect('google', 'http://www.google.com', _static=True)

            assert m.generate(controller='content') == '/hi/content'
            assert m.generate(controller='admin/user') == '/hi/admin/user'
            assert url_for('google') == 'http://www.google.com'

    def test_standard_route(self):
        for path in [':controller/:action/:id', ':(controller)/:(action)/:(id)']:
            m = Mapper(explicit=False)
            m.minimization = True
            m.connect(path)

            '/content', m.generate(controller='content', action='index')
            '/content/list', m.generate(controller='content', action='list')
            '/content/show/10', m.generate(controller='content', action='show', id ='10')

            '/admin/user', m.generate(controller='admin/user', action='index')
            '/admin/user/list', m.generate(controller='admin/user', action='list')
            '/admin/user/show/10', m.generate(controller='admin/user', action='show', id='10')

    def test_multiroute(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('archive/:year/:month/:day', controller='blog', action='view', month=None, day=None,
                            requirements={'month':'\d{1,2}','day':'\d{1,2}'})
        m.connect('viewpost/:id', controller='post', action='view')
        m.connect(':controller/:action/:id')

        url = m.generate(controller='blog', action='view', year=2004, month='blah')
        assert url == '/blog/view?year=2004&month=blah' or url == '/blog/view?month=blah&year=2004'
        assert m.generate(controller='blog', action='view', year=2004, month=11) == '/archive/2004/11'
        assert m.generate(controller='blog', action='view', year=2004, month='11') == '/archive/2004/11'
        assert m.generate(controller='blog', action='view', year=2004) == '/archive/2004'
        assert m.generate(controller='post', action='view', id=3) == '/viewpost/3'

    def test_multiroute_with_splits(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('archive/:(year)/:(month)/:(day)', controller='blog', action='view', month=None, day=None,
                            requirements={'month':'\d{1,2}','day':'\d{1,2}'})
        m.connect('viewpost/:(id)', controller='post', action='view')
        m.connect(':(controller)/:(action)/:(id)')

        url = m.generate(controller='blog', action='view', year=2004, month='blah')
        assert url == '/blog/view?year=2004&month=blah' or url == '/blog/view?month=blah&year=2004'
        assert m.generate(controller='blog', action='view', year=2004, month=11) == '/archive/2004/11'
        assert m.generate(controller='blog', action='view', year=2004, month='11') == '/archive/2004/11'
        assert m.generate(controller='blog', action='view', year=2004) == '/archive/2004'
        assert m.generate(controller='post', action='view', id=3) == '/viewpost/3'

    def test_big_multiroute(self):
        m = Mapper(explicit=False)
        m.minimization = True
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


        assert m.generate(controller='articles', action='view_page', name='the/idiot/has/spoken') == '/pages/the/idiot/has/spoken'
        assert m.generate(controller='articles', action='index') == '/'
        assert m.generate(controller='xml', action='articlerss', id=4) == '/xml/articlerss/4/feed.xml'
        assert m.generate(controller='xml', action='rss') == '/xml/rss/feed.xml'
        assert m.generate(controller='admin/comments', action='view', article_id=4, id=2) == '/admin/comments/article/4/view/2'
        assert m.generate(controller='admin/general') == '/admin'
        assert m.generate(controller='admin/comments', article_id=4) == '/admin/comments/article/4/index'
        assert m.generate(controller='admin/comments', action=None, article_id=4) == '/admin/comments/article/4'
        assert m.generate(controller='articles', action='find_by_date', year=2004, month=2, day=20, page=1) == '/articles/2004/2/20/page/1'
        assert m.generate(controller='articles', action='category') == '/articles/category'
        assert m.generate(controller='xml') == '/xml/index/feed.xml'
        assert m.generate(controller='xml', action='articlerss') == '/xml/articlerss/feed.xml'

        assert m.generate(controller='admin/comments', id=2) is None
        assert m.generate(controller='articles', action='find_by_date', year=2004) is None

    def test_big_multiroute_with_splits(self):
        m = Mapper(explicit=False)
        m.minimization = True
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

        assert m.generate(controller='articles', action='view_page', name='the/idiot/has/spoken') == '/pages/the/idiot/has/spoken'
        assert m.generate(controller='articles', action='index') == '/'
        assert m.generate(controller='xml', action='articlerss', id=4) == '/xml/articlerss/4/feed.xml'
        assert m.generate(controller='xml', action='rss') == '/xml/rss/feed.xml'
        assert m.generate(controller='admin/comments', action='view', article_id=4, id=2) == '/admin/comments/article/4/view/2.html'
        assert m.generate(controller='admin/general') == '/admin'
        assert m.generate(controller='admin/comments', article_id=4, action='edit', id=3) == '/admin/comments/article/4/edit/3.html'

        assert m.generate(controller='admin/comments', action=None, article_id=4) is None
        assert m.generate(controller='articles', action='find_by_date', year=2004, month=2, day=20, page=1) == '/articles/2004/2/20/page/1'
        assert m.generate(controller='articles', action='category') == '/articles/category'
        assert m.generate(controller='xml') == '/xml/index/feed.xml'
        assert m.generate(controller='xml', action='articlerss') == '/xml/articlerss/feed.xml'

        assert m.generate(controller='admin/comments', id=2) is None
        assert m.generate(controller='articles', action='find_by_date', year=2004) is None

    def test_big_multiroute_with_nomin(self):
        m = Mapper(explicit=False)
        m.minimization = False
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


        assert m.generate(controller='articles', action='view_page', name='the/idiot/has/spoken') == '/pages/the/idiot/has/spoken'
        assert m.generate(controller='articles', action='index') == '/'
        assert m.generate(controller='xml', action='articlerss', id=4) == '/xml/articlerss/4/feed.xml'
        assert m.generate(controller='xml', action='rss') == '/xml/rss/feed.xml'
        assert m.generate(controller='admin/comments', action='view', article_id=4, id=2) == '/admin/comments/article/4/view/2'
        assert m.generate(controller='admin/general') == '/admin'
        assert m.generate(controller='articles', action='find_by_date', year=2004, month=2, day=20, page=1) == '/articles/2004/2/20/page/1'
        assert m.generate(controller='articles', action='category') is None
        assert m.generate(controller='articles', action='category', id=4) == '/articles/category/4'
        assert m.generate(controller='xml') == '/xml/index/feed.xml'
        assert m.generate(controller='xml', action='articlerss') == '/xml/articlerss/feed.xml'

        assert m.generate(controller='admin/comments', id=2) is None
        assert m.generate(controller='articles', action='find_by_date', year=2004) is None

    def test_no_extras(self):
        m = Mapper()
        m.minimization = True
        m.connect(':controller/:action/:id')
        m.connect('archive/:year/:month/:day', controller='blog', action='view', month=None, day=None)

        assert m.generate(controller='blog', action='view', year=2004) == '/archive/2004'

    def test_no_extras_with_splits(self):
        m = Mapper()
        m.minimization = True
        m.connect(':(controller)/:(action)/:(id)')
        m.connect('archive/:(year)/:(month)/:(day)', controller='blog', action='view', month=None, day=None)

        assert m.generate(controller='blog', action='view', year=2004) == '/archive/2004'

    def test_the_smallest_route(self):
        for path in ['pages/:title', 'pages/:(title)']:
            m = Mapper()
            m.connect('', controller='page', action='view', title='HomePage')
            m.connect(path, controller='page', action='view')

            assert m.generate(controller='page', action='view', title='HomePage') == '/'
            assert m.generate(controller='page', action='view', title='joe') == '/pages/joe'

    def test_extras(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('viewpost/:id', controller='post', action='view')
        m.connect(':controller/:action/:id')

        assert m.generate(controller='post', action='view', id=2, extra='x/y') == '/viewpost/2?extra=x%2Fy'
        assert m.generate(controller='blog', action='index', extra=3) == '/blog?extra=3'
        assert m.generate(controller='post', action='view', id=2, extra=3) == '/viewpost/2?extra=3'

    def test_extras_with_splits(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('viewpost/:(id)', controller='post', action='view')
        m.connect(':(controller)/:(action)/:(id)')

        assert m.generate(controller='blog', action='index', extra=3) == '/blog?extra=3'
        assert m.generate(controller='post', action='view', id=2, extra=3) == '/viewpost/2?extra=3'

    def test_extras_as_unicode(self):
        m = Mapper()
        m.connect(':something')
        thing = "whatever"
        euro = u"\u20ac" # Euro symbol

        assert m.generate(something=thing, extra=euro) == "/%s?extra=%%E2%%82%%AC" % thing

    def test_extras_as_list_of_unicodes(self):
        m = Mapper()
        m.connect(':something')
        thing = "whatever"
        euro = [u"\u20ac", u"\xa3"] # Euro and Pound sterling symbols

        assert m.generate(something=thing, extra=euro) == "/%s?extra=%%E2%%82%%AC&extra=%%C2%%A3" % thing


    def test_static(self):
        m = Mapper()
        m.connect('hello/world',known='known_value',controller='content',action='index')

        assert m.generate(controller='content',action= 'index',known ='known_value') == '/hello/world'
        assert m.generate(controller='content',action='index',known='known_value',extra='hi') == '/hello/world?extra=hi'

        assert m.generate(known='foo') is None

    def test_typical(self):
        for path in [':controller/:action/:id', ':(controller)/:(action)/:(id)']:
            m = Mapper()
            m.minimization = True
            m.minimization = True
            m.connect(path, action = 'index', id = None)

            assert m.generate(controller='content', action='index') == '/content'
            assert m.generate(controller='content', action='list') == '/content/list'
            assert m.generate(controller='content', action='show', id=10) == '/content/show/10'

            assert m.generate(controller='admin/user', action='index') == '/admin/user'
            assert m.generate(controller='admin/user') == '/admin/user'
            assert m.generate(controller='admin/user', action='show', id=10) == '/admin/user/show/10'

            assert m.generate(controller='content') == '/content'

    def test_route_with_fixnum_default(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('page/:id', controller='content', action='show_page', id=1)
        m.connect(':controller/:action/:id')

        assert m.generate(controller='content', action='show_page') == '/page'
        assert m.generate(controller='content', action='show_page', id=1) == '/page'
        assert m.generate(controller='content', action='show_page', id='1') == '/page'
        assert m.generate(controller='content', action='show_page', id=10) == '/page/10'

        assert m.generate(controller='blog', action='show', id=4) == '/blog/show/4'
        assert m.generate(controller='content', action='show_page') == '/page'
        assert m.generate(controller='content', action='show_page',id=4) == '/page/4'
        assert m.generate(controller='content', action='show') == '/content/show'

    def test_route_with_fixnum_default_with_splits(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('page/:(id)', controller='content', action='show_page', id =1)
        m.connect(':(controller)/:(action)/:(id)')

        assert m.generate(controller='content', action='show_page') == '/page'
        assert m.generate(controller='content', action='show_page', id=1) == '/page'
        assert m.generate(controller='content', action='show_page', id='1') == '/page'
        assert m.generate(controller='content', action='show_page', id=10) == '/page/10'

        assert m.generate(controller='blog', action='show', id=4) == '/blog/show/4'
        assert m.generate(controller='content', action='show_page') == '/page'
        assert m.generate(controller='content', action='show_page',id=4) == '/page/4'
        assert m.generate(controller='content', action='show') == '/content/show'

    def test_uppercase_recognition(self):
        for path in [':controller/:action/:id', ':(controller)/:(action)/:(id)']:
            m = Mapper(explicit=False)
            m.minimization = True
            m.connect(path)

            assert m.generate(controller='Content', action='index') == '/Content'
            assert m.generate(controller='Content', action='list') == '/Content/list'
            assert m.generate(controller='Content', action='show', id='10') == '/Content/show/10'
            assert m.generate(controller='Admin/NewsFeed', action='index') == '/Admin/NewsFeed'

    def test_backwards(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('page/:id/:action', controller='pages', action='show')
        m.connect(':controller/:action/:id')

        assert m.generate(controller='pages', action='show', id=20) == '/page/20'
        assert m.generate(controller='pages', action='boo') == '/pages/boo'

    def test_backwards_with_splits(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('page/:(id)/:(action)', controller='pages', action='show')
        m.connect(':(controller)/:(action)/:(id)')

        assert m.generate(controller='pages', action='show', id=20) == '/page/20'
        assert m.generate(controller='pages', action='boo') == '/pages/boo'

    def test_both_requirement_and_optional(self):
        m = Mapper()
        m.minimization = True
        m.connect('test/:year', controller='post', action='show', year=None, requirements = {'year':'\d{4}'})

        assert m.generate(controller='post', action='show') == '/test'
        assert m.generate(controller='post', action='show', year=None) == '/test'

    def test_set_to_nil_forgets(self):
        m = Mapper()
        m.minimization = True
        m.connect('pages/:year/:month/:day', controller='content', action='list_pages', month=None, day=None)
        m.connect(':controller/:action/:id')

        assert m.generate(controller='content', action='list_pages', year=2005) == '/pages/2005'
        assert m.generate(controller='content', action='list_pages', year=2005, month=6) == '/pages/2005/6'
        assert m.generate(controller='content', action='list_pages', year=2005, month=6, day=12) == '/pages/2005/6/12'

    def test_url_with_no_action_specified(self):
        m = Mapper()
        m.connect('', controller='content')
        m.connect(':controller/:action/:id')

        assert m.generate(controller='content', action='index') == '/'
        assert m.generate(controller='content') == '/'

    def test_url_with_prefix(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.prefix = '/blog'
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        assert m.generate(controller='content', action='view') == '/blog/content/view'
        assert m.generate(controller='content') == '/blog/content'
        assert m.generate(controller='admin/comments') == '/blog/admin/comments'

    def test_url_with_prefix_deeper(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.prefix = '/blog/phil'
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        assert m.generate(controller='content', action='view') == '/blog/phil/content/view'
        assert m.generate(controller='content') == '/blog/phil/content'
        assert m.generate(controller='admin/comments') == '/blog/phil/admin/comments'

    def test_url_with_environ_empty(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.environ = dict(SCRIPT_NAME='')
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        assert m.generate(controller='content', action='view') == '/content/view'
        assert m.generate(controller='content') == '/content'
        assert m.generate(controller='admin/comments') == '/admin/comments'

    def test_url_with_environ(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.environ = dict(SCRIPT_NAME='/blog')
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        assert m.generate(controller='content', action='view') == '/blog/content/view'
        assert m.generate(controller='content') == '/blog/content'
        assert m.generate(controller='content') == '/blog/content'
        assert m.generate(controller='admin/comments') == '/blog/admin/comments'

        m.environ = dict(SCRIPT_NAME='/notblog')

        assert m.generate(controller='content', action='view') == '/notblog/content/view'
        assert m.generate(controller='content') == '/notblog/content'
        assert m.generate(controller='content') == '/notblog/content'
        assert m.generate(controller='admin/comments') == '/notblog/admin/comments'

    def test_url_with_environ_and_caching(self):
        m = Mapper()
        m.connect("foo", "/", controller="main", action="index")

        assert m.generate(controller='main', action='index') == '/'
        assert m.generate(controller='main', action='index', _environ=dict(SCRIPT_NAME='/bar')) == '/bar/'
        assert m.generate(controller='main', action='index') == '/'

    def test_url_with_environ_and_absolute(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.environ = dict(SCRIPT_NAME='/blog')
        m.connect('image', 'image/:name', _absolute=True)
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        assert m.generate(controller='content', action='view') == '/blog/content/view'
        assert m.generate(controller='content') == '/blog/content'
        assert m.generate(controller='content') == '/blog/content'
        assert m.generate(controller='admin/comments') == '/blog/admin/comments'
        assert url_for('image', name='topnav.jpg') == '/image/topnav.jpg'

    def test_route_with_odd_leftovers(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect(':controller/:(action)-:(id)')
        m.create_regs(['content','blog','admin/comments'])

        assert m.generate(controller='content', action='view') == '/content/view-'
        assert m.generate(controller='content') == '/content/index-'

    def test_route_with_end_extension(self):
        m = Mapper(explicit=False)
        m.connect(':controller/:(action)-:(id).html')
        m.create_regs(['content','blog','admin/comments'])

        assert m.generate(controller='content', action='view') is None
        assert m.generate(controller='content') is None

        assert m.generate(controller='content', action='view', id=3) == '/content/view-3.html'
        assert m.generate(controller='content', id=2) == '/content/index-2.html'

    def test_unicode(self):
        hoge = u'\u30c6\u30b9\u30c8' # the word test in Japanese
        hoge_enc = urllib.parse.quote(hoge.encode('utf-8'))
        m = Mapper()
        m.connect(':hoge')
        assert m.generate(hoge=hoge) == "/%s" % hoge_enc
        assert isinstance(m.generate(hoge=hoge), str)

    def test_unicode_static(self):
        hoge = u'\u30c6\u30b9\u30c8' # the word test in Japanese
        hoge_enc = urllib.parse.quote(hoge.encode('utf-8'))
        m = Mapper()
        m.minimization = True
        m.connect('google-jp', 'http://www.google.co.jp/search', _static=True)
        m.create_regs(['messages'])
        assert url_for('google-jp', q=hoge) == "http://www.google.co.jp/search?q=" + hoge_enc
        assert isinstance(url_for('google-jp', q=hoge), str)

    def test_other_special_chars(self):
        m = Mapper()
        m.minimization = True
        m.connect('/:year/:(slug).:(format),:(locale)', locale='en', format='html')
        m.create_regs(['content'])

        assert m.generate(year=2007, slug='test') == '/2007/test'
        assert m.generate(year=2007, slug='test', format='xml') == '/2007/test.xml'
        assert m.generate(year=2007, slug='test', format='xml', locale='ja') == '/2007/test.xml,ja'
        assert m.generate(year=2007, format='html') is None

    def test_dot_format_args(self):
        for minimization in [False, True]:
            m = Mapper(explicit=True)
            m.minimization=minimization
            m.connect('/songs/{title}{.format}')
            m.connect('/stories/{slug}{.format:pdf}')

            assert m.generate(title='my-way') == '/songs/my-way'
            assert m.generate(title='my-way', format='mp3') == '/songs/my-way.mp3'
            assert m.generate(slug='frist-post') == '/stories/frist-post'
            assert m.generate(slug='frist-post', format='pdf') == '/stories/frist-post.pdf'
            assert m.generate(slug='frist-post', format='doc') is None

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
        print("Generation (%s URLs)" % (n*6))
        print("%s ms/url" % (per_url*1000))
        print("%s urls/s\n" % (1.00/per_url))
