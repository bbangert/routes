"""test_generation"""
import sys, time, unittest
from six.moves import urllib

from nose.tools import eq_, assert_raises
from routes import *

class TestGeneration(unittest.TestCase):

    def test_all_static_no_reqs(self):
        m = Mapper()
        m.connect('hello/world')

        eq_('/hello/world', m.generate())

    def test_basic_dynamic(self):
        for path in ['hi/:fred', 'hi/:(fred)']:
            m = Mapper()
            m.connect(path)

            eq_('/hi/index', m.generate(fred='index'))
            eq_('/hi/show', m.generate(fred='show'))
            eq_('/hi/list%20people', m.generate(fred='list people'))
            eq_(None, m.generate())

    def test_relative_url(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.environ = dict(HTTP_HOST='localhost')
        url = URLGenerator(m, m.environ)
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        eq_('about', url('about'))
        eq_('http://localhost/about', url('about', qualified=True))

    def test_basic_dynamic_explicit_use(self):
        m = Mapper()
        m.connect('hi/{fred}')
        url = URLGenerator(m, {})

        eq_('/hi/index', url(fred='index'))
        eq_('/hi/show', url(fred='show'))
        eq_('/hi/list%20people', url(fred='list people'))

    def test_dynamic_with_default(self):
        for path in ['hi/:action', 'hi/:(action)']:
            m = Mapper(explicit=False)
            m.minimization = True
            m.connect(path)

            eq_('/hi', m.generate(action='index'))
            eq_('/hi/show', m.generate(action='show'))
            eq_('/hi/list%20people', m.generate(action='list people'))
            eq_('/hi', m.generate())

    def test_dynamic_with_false_equivs(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('article/:page', page=False)
        m.connect(':controller/:action/:id')

        eq_('/blog/view/0', m.generate(controller="blog", action="view", id="0"))
        eq_('/blog/view/0', m.generate(controller="blog", action="view", id=0))
        eq_('/blog/view/False', m.generate(controller="blog", action="view", id=False))
        eq_('/blog/view/False', m.generate(controller="blog", action="view", id='False'))
        eq_('/blog/view', m.generate(controller="blog", action="view", id=None))
        eq_('/blog/view', m.generate(controller="blog", action="view", id='None'))
        eq_('/article', m.generate(page=None))

        m = Mapper()
        m.minimization = True
        m.connect('view/:home/:area', home="austere", area=None)

        eq_('/view/sumatra', m.generate(home='sumatra'))
        eq_('/view/austere/chicago', m.generate(area='chicago'))

        m = Mapper()
        m.minimization = True
        m.connect('view/:home/:area', home=None, area=None)

        eq_('/view/None/chicago', m.generate(home=None, area='chicago'))

    def test_dynamic_with_underscore_parts(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('article/:small_page', small_page=False)
        m.connect(':(controller)/:(action)/:(id)')

        eq_('/blog/view/0', m.generate(controller="blog", action="view", id="0"))
        eq_('/blog/view/False', m.generate(controller="blog", action="view", id='False'))
        eq_('/blog/view', m.generate(controller="blog", action="view", id='None'))
        eq_('/article', m.generate(small_page=None))
        eq_('/article/hobbes', m.generate(small_page='hobbes'))

    def test_dynamic_with_false_equivs_and_splits(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('article/:(page)', page=False)
        m.connect(':(controller)/:(action)/:(id)')

        eq_('/blog/view/0', m.generate(controller="blog", action="view", id="0"))
        eq_('/blog/view/0', m.generate(controller="blog", action="view", id=0))
        eq_('/blog/view/False', m.generate(controller="blog", action="view", id=False))
        eq_('/blog/view/False', m.generate(controller="blog", action="view", id='False'))
        eq_('/blog/view', m.generate(controller="blog", action="view", id=None))
        eq_('/blog/view', m.generate(controller="blog", action="view", id='None'))
        eq_('/article', m.generate(page=None))

        m = Mapper()
        m.minimization = True
        m.connect('view/:(home)/:(area)', home="austere", area=None)

        eq_('/view/sumatra', m.generate(home='sumatra'))
        eq_('/view/austere/chicago', m.generate(area='chicago'))

        m = Mapper()
        m.minimization = True
        m.connect('view/:(home)/:(area)', home=None, area=None)

        eq_('/view/None/chicago', m.generate(home=None, area='chicago'))

    def test_dynamic_with_regexp_condition(self):
        for path in ['hi/:name', 'hi/:(name)']:
            m = Mapper()
            m.connect(path, requirements = {'name':'[a-z]+'})

            eq_('/hi/index', m.generate(name='index'))
            eq_(None, m.generate(name='fox5'))
            eq_(None, m.generate(name='something_is_up'))
            eq_('/hi/abunchofcharacter', m.generate(name='abunchofcharacter'))
            eq_(None, m.generate())

    def test_dynamic_with_default_and_regexp_condition(self):
        for path in ['hi/:action', 'hi/:(action)']:
            m = Mapper(explicit=False)
            m.minimization = True
            m.connect(path, requirements = {'action':'[a-z]+'})

            eq_('/hi', m.generate(action='index'))
            eq_(None, m.generate(action='fox5'))
            eq_(None, m.generate(action='something_is_up'))
            eq_(None, m.generate(action='list people'))
            eq_('/hi/abunchofcharacter', m.generate(action='abunchofcharacter'))
            eq_('/hi', m.generate())

    def test_path(self):
        for path in ['hi/*file', 'hi/*(file)']:
            m = Mapper()
            m.minimization = True
            m.connect(path)

            eq_('/hi', m.generate(file=None))
            eq_('/hi/books/learning_python.pdf', m.generate(file='books/learning_python.pdf'))
            eq_('/hi/books/development%26whatever/learning_python.pdf',
                m.generate(file='books/development&whatever/learning_python.pdf'))

    def test_path_backwards(self):
        for path in ['*file/hi', '*(file)/hi']:
            m = Mapper()
            m.minimization = True
            m.connect(path)

            eq_('/hi', m.generate(file=None))
            eq_('/books/learning_python.pdf/hi', m.generate(file='books/learning_python.pdf'))
            eq_('/books/development%26whatever/learning_python.pdf/hi',
                m.generate(file='books/development&whatever/learning_python.pdf'))

    def test_controller(self):
        for path in ['hi/:controller', 'hi/:(controller)']:
            m = Mapper()
            m.connect(path)

            eq_('/hi/content', m.generate(controller='content'))
            eq_('/hi/admin/user', m.generate(controller='admin/user'))

    def test_controller_with_static(self):
        for path in ['hi/:controller', 'hi/:(controller)']:
            m = Mapper()
            m.connect(path)
            m.connect('google', 'http://www.google.com', _static=True)

            eq_('/hi/content', m.generate(controller='content'))
            eq_('/hi/admin/user', m.generate(controller='admin/user'))
            eq_('http://www.google.com', url_for('google'))

    def test_standard_route(self):
        for path in [':controller/:action/:id', ':(controller)/:(action)/:(id)']:
            m = Mapper(explicit=False)
            m.minimization = True
            m.connect(path)

            eq_('/content', m.generate(controller='content', action='index'))
            eq_('/content/list', m.generate(controller='content', action='list'))
            eq_('/content/show/10', m.generate(controller='content', action='show', id ='10'))

            eq_('/admin/user', m.generate(controller='admin/user', action='index'))
            eq_('/admin/user/list', m.generate(controller='admin/user', action='list'))
            eq_('/admin/user/show/10', m.generate(controller='admin/user', action='show', id='10'))

    def test_multiroute(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('archive/:year/:month/:day', controller='blog', action='view', month=None, day=None,
                            requirements={'month':'\d{1,2}','day':'\d{1,2}'})
        m.connect('viewpost/:id', controller='post', action='view')
        m.connect(':controller/:action/:id')

        url = m.generate(controller='blog', action='view', year=2004, month='blah')
        assert url == '/blog/view?year=2004&month=blah' or url == '/blog/view?month=blah&year=2004'
        eq_('/archive/2004/11', m.generate(controller='blog', action='view', year=2004, month=11))
        eq_('/archive/2004/11', m.generate(controller='blog', action='view', year=2004, month='11'))
        eq_('/archive/2004', m.generate(controller='blog', action='view', year=2004))
        eq_('/viewpost/3', m.generate(controller='post', action='view', id=3))

    def test_multiroute_with_splits(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('archive/:(year)/:(month)/:(day)', controller='blog', action='view', month=None, day=None,
                            requirements={'month':'\d{1,2}','day':'\d{1,2}'})
        m.connect('viewpost/:(id)', controller='post', action='view')
        m.connect(':(controller)/:(action)/:(id)')

        url = m.generate(controller='blog', action='view', year=2004, month='blah')
        assert url == '/blog/view?year=2004&month=blah' or url == '/blog/view?month=blah&year=2004'
        eq_('/archive/2004/11', m.generate(controller='blog', action='view', year=2004, month=11))
        eq_('/archive/2004/11', m.generate(controller='blog', action='view', year=2004, month='11'))
        eq_('/archive/2004', m.generate(controller='blog', action='view', year=2004))
        eq_('/viewpost/3', m.generate(controller='post', action='view', id=3))

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


        eq_('/pages/the/idiot/has/spoken',
            m.generate(controller='articles', action='view_page', name='the/idiot/has/spoken'))
        eq_('/', m.generate(controller='articles', action='index'))
        eq_('/xml/articlerss/4/feed.xml', m.generate(controller='xml', action='articlerss', id=4))
        eq_('/xml/rss/feed.xml', m.generate(controller='xml', action='rss'))
        eq_('/admin/comments/article/4/view/2',
            m.generate(controller='admin/comments', action='view', article_id=4, id=2))
        eq_('/admin', m.generate(controller='admin/general'))
        eq_('/admin/comments/article/4/index', m.generate(controller='admin/comments', article_id=4))
        eq_('/admin/comments/article/4',
            m.generate(controller='admin/comments', action=None, article_id=4))
        eq_('/articles/2004/2/20/page/1',
            m.generate(controller='articles', action='find_by_date', year=2004, month=2, day=20, page=1))
        eq_('/articles/category', m.generate(controller='articles', action='category'))
        eq_('/xml/index/feed.xml', m.generate(controller='xml'))
        eq_('/xml/articlerss/feed.xml', m.generate(controller='xml', action='articlerss'))

        eq_(None, m.generate(controller='admin/comments', id=2))
        eq_(None, m.generate(controller='articles', action='find_by_date', year=2004))

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


        eq_('/pages/the/idiot/has/spoken',
            m.generate(controller='articles', action='view_page', name='the/idiot/has/spoken'))
        eq_('/', m.generate(controller='articles', action='index'))
        eq_('/xml/articlerss/4/feed.xml', m.generate(controller='xml', action='articlerss', id=4))
        eq_('/xml/rss/feed.xml', m.generate(controller='xml', action='rss'))
        eq_('/admin/comments/article/4/view/2.html',
            m.generate(controller='admin/comments', action='view', article_id=4, id=2))
        eq_('/admin', m.generate(controller='admin/general'))
        eq_('/admin/comments/article/4/edit/3.html',
            m.generate(controller='admin/comments', article_id=4, action='edit', id=3))
        eq_(None, m.generate(controller='admin/comments', action=None, article_id=4))
        eq_('/articles/2004/2/20/page/1',
            m.generate(controller='articles', action='find_by_date', year=2004, month=2, day=20, page=1))
        eq_('/articles/category', m.generate(controller='articles', action='category'))
        eq_('/xml/index/feed.xml', m.generate(controller='xml'))
        eq_('/xml/articlerss/feed.xml', m.generate(controller='xml', action='articlerss'))

        eq_(None, m.generate(controller='admin/comments', id=2))
        eq_(None, m.generate(controller='articles', action='find_by_date', year=2004))

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


        eq_('/pages/the/idiot/has/spoken',
            m.generate(controller='articles', action='view_page', name='the/idiot/has/spoken'))
        eq_('/', m.generate(controller='articles', action='index'))
        eq_('/xml/articlerss/4/feed.xml', m.generate(controller='xml', action='articlerss', id=4))
        eq_('/xml/rss/feed.xml', m.generate(controller='xml', action='rss'))
        eq_('/admin/comments/article/4/view/2',
            m.generate(controller='admin/comments', action='view', article_id=4, id=2))
        eq_('/admin', m.generate(controller='admin/general'))
        eq_('/articles/2004/2/20/page/1',
            m.generate(controller='articles', action='find_by_date', year=2004, month=2, day=20, page=1))
        eq_(None, m.generate(controller='articles', action='category'))
        eq_('/articles/category/4', m.generate(controller='articles', action='category', id=4))
        eq_('/xml/index/feed.xml', m.generate(controller='xml'))
        eq_('/xml/articlerss/feed.xml', m.generate(controller='xml', action='articlerss'))

        eq_(None, m.generate(controller='admin/comments', id=2))
        eq_(None, m.generate(controller='articles', action='find_by_date', year=2004))

    def test_no_extras(self):
        m = Mapper()
        m.minimization = True
        m.connect(':controller/:action/:id')
        m.connect('archive/:year/:month/:day', controller='blog', action='view', month=None, day=None)

        eq_('/archive/2004', m.generate(controller='blog', action='view', year=2004))

    def test_no_extras_with_splits(self):
        m = Mapper()
        m.minimization = True
        m.connect(':(controller)/:(action)/:(id)')
        m.connect('archive/:(year)/:(month)/:(day)', controller='blog', action='view', month=None, day=None)

        eq_('/archive/2004', m.generate(controller='blog', action='view', year=2004))

    def test_the_smallest_route(self):
        for path in ['pages/:title', 'pages/:(title)']:
            m = Mapper()
            m.connect('', controller='page', action='view', title='HomePage')
            m.connect(path, controller='page', action='view')

            eq_('/', m.generate(controller='page', action='view', title='HomePage'))
            eq_('/pages/joe', m.generate(controller='page', action='view', title='joe'))

    def test_extras(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('viewpost/:id', controller='post', action='view')
        m.connect(':controller/:action/:id')

        eq_('/viewpost/2?extra=x%2Fy', m.generate(controller='post', action='view', id=2, extra='x/y'))
        eq_('/blog?extra=3', m.generate(controller='blog', action='index', extra=3))
        eq_('/viewpost/2?extra=3', m.generate(controller='post', action='view', id=2, extra=3))

    def test_extras_with_splits(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('viewpost/:(id)', controller='post', action='view')
        m.connect(':(controller)/:(action)/:(id)')

        eq_('/blog?extra=3', m.generate(controller='blog', action='index', extra=3))
        eq_('/viewpost/2?extra=3', m.generate(controller='post', action='view', id=2, extra=3))

    def test_extras_as_unicode(self):
        m = Mapper()
        m.connect(':something')
        thing = "whatever"
        euro = u"\u20ac" # Euro symbol

        eq_("/%s?extra=%%E2%%82%%AC" % thing, m.generate(something=thing, extra=euro))

    def test_extras_as_list_of_unicodes(self):
        m = Mapper()
        m.connect(':something')
        thing = "whatever"
        euro = [u"\u20ac", u"\xa3"] # Euro and Pound sterling symbols

        eq_("/%s?extra=%%E2%%82%%AC&extra=%%C2%%A3" % thing, m.generate(something=thing, extra=euro))


    def test_static(self):
        m = Mapper()
        m.connect('hello/world',known='known_value',controller='content',action='index')

        eq_('/hello/world', m.generate(controller='content',action= 'index',known ='known_value'))
        eq_('/hello/world?extra=hi',
            m.generate(controller='content',action='index',known='known_value',extra='hi'))

        eq_(None, m.generate(known='foo'))

    def test_typical(self):
        for path in [':controller/:action/:id', ':(controller)/:(action)/:(id)']:
            m = Mapper()
            m.minimization = True
            m.minimization = True
            m.connect(path, action = 'index', id = None)

            eq_('/content', m.generate(controller='content', action='index'))
            eq_('/content/list', m.generate(controller='content', action='list'))
            eq_('/content/show/10', m.generate(controller='content', action='show', id=10))

            eq_('/admin/user', m.generate(controller='admin/user', action='index'))
            eq_('/admin/user', m.generate(controller='admin/user'))
            eq_('/admin/user/show/10', m.generate(controller='admin/user', action='show', id=10))

            eq_('/content', m.generate(controller='content'))

    def test_route_with_fixnum_default(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('page/:id', controller='content', action='show_page', id=1)
        m.connect(':controller/:action/:id')

        eq_('/page', m.generate(controller='content', action='show_page'))
        eq_('/page', m.generate(controller='content', action='show_page', id=1))
        eq_('/page', m.generate(controller='content', action='show_page', id='1'))
        eq_('/page/10', m.generate(controller='content', action='show_page', id=10))

        eq_('/blog/show/4', m.generate(controller='blog', action='show', id=4))
        eq_('/page', m.generate(controller='content', action='show_page'))
        eq_('/page/4', m.generate(controller='content', action='show_page',id=4))
        eq_('/content/show', m.generate(controller='content', action='show'))

    def test_route_with_fixnum_default_with_splits(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('page/:(id)', controller='content', action='show_page', id =1)
        m.connect(':(controller)/:(action)/:(id)')

        eq_('/page', m.generate(controller='content', action='show_page'))
        eq_('/page', m.generate(controller='content', action='show_page', id=1))
        eq_('/page', m.generate(controller='content', action='show_page', id='1'))
        eq_('/page/10', m.generate(controller='content', action='show_page', id=10))

        eq_('/blog/show/4', m.generate(controller='blog', action='show', id=4))
        eq_('/page', m.generate(controller='content', action='show_page'))
        eq_('/page/4', m.generate(controller='content', action='show_page',id=4))
        eq_('/content/show', m.generate(controller='content', action='show'))

    def test_uppercase_recognition(self):
        for path in [':controller/:action/:id', ':(controller)/:(action)/:(id)']:
            m = Mapper(explicit=False)
            m.minimization = True
            m.connect(path)

            eq_('/Content', m.generate(controller='Content', action='index'))
            eq_('/Content/list', m.generate(controller='Content', action='list'))
            eq_('/Content/show/10', m.generate(controller='Content', action='show', id='10'))

            eq_('/Admin/NewsFeed', m.generate(controller='Admin/NewsFeed', action='index'))

    def test_backwards(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('page/:id/:action', controller='pages', action='show')
        m.connect(':controller/:action/:id')

        eq_('/page/20', m.generate(controller='pages', action='show', id=20))
        eq_('/pages/boo', m.generate(controller='pages', action='boo'))

    def test_backwards_with_splits(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('page/:(id)/:(action)', controller='pages', action='show')
        m.connect(':(controller)/:(action)/:(id)')

        eq_('/page/20', m.generate(controller='pages', action='show', id=20))
        eq_('/pages/boo', m.generate(controller='pages', action='boo'))

    def test_both_requirement_and_optional(self):
        m = Mapper()
        m.minimization = True
        m.connect('test/:year', controller='post', action='show', year=None, requirements = {'year':'\d{4}'})

        eq_('/test', m.generate(controller='post', action='show'))
        eq_('/test', m.generate(controller='post', action='show', year=None))

    def test_set_to_nil_forgets(self):
        m = Mapper()
        m.minimization = True
        m.connect('pages/:year/:month/:day', controller='content', action='list_pages', month=None, day=None)
        m.connect(':controller/:action/:id')

        eq_('/pages/2005', m.generate(controller='content', action='list_pages', year=2005))
        eq_('/pages/2005/6', m.generate(controller='content', action='list_pages', year=2005, month=6))
        eq_('/pages/2005/6/12',
            m.generate(controller='content', action='list_pages', year=2005, month=6, day=12))

    def test_url_with_no_action_specified(self):
        m = Mapper()
        m.connect('', controller='content')
        m.connect(':controller/:action/:id')

        eq_('/', m.generate(controller='content', action='index'))
        eq_('/', m.generate(controller='content'))

    def test_url_with_prefix(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.prefix = '/blog'
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        eq_('/blog/content/view', m.generate(controller='content', action='view'))
        eq_('/blog/content', m.generate(controller='content'))
        eq_('/blog/admin/comments', m.generate(controller='admin/comments'))

    def test_url_with_prefix_deeper(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.prefix = '/blog/phil'
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        eq_('/blog/phil/content/view', m.generate(controller='content', action='view'))
        eq_('/blog/phil/content', m.generate(controller='content'))
        eq_('/blog/phil/admin/comments', m.generate(controller='admin/comments'))

    def test_url_with_environ_empty(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.environ = dict(SCRIPT_NAME='')
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        eq_('/content/view', m.generate(controller='content', action='view'))
        eq_('/content', m.generate(controller='content'))
        eq_('/admin/comments', m.generate(controller='admin/comments'))

    def test_url_with_environ(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.environ = dict(SCRIPT_NAME='/blog')
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        eq_('/blog/content/view', m.generate(controller='content', action='view'))
        eq_('/blog/content', m.generate(controller='content'))
        eq_('/blog/content', m.generate(controller='content'))
        eq_('/blog/admin/comments', m.generate(controller='admin/comments'))

        m.environ = dict(SCRIPT_NAME='/notblog')

        eq_('/notblog/content/view', m.generate(controller='content', action='view'))
        eq_('/notblog/content', m.generate(controller='content'))
        eq_('/notblog/content', m.generate(controller='content'))
        eq_('/notblog/admin/comments', m.generate(controller='admin/comments'))

    def test_url_with_environ_and_caching(self):
        m = Mapper()
        m.connect("foo", "/", controller="main", action="index")

        eq_('/', m.generate(controller='main', action='index'))
        eq_('/bar/', m.generate(controller='main', action='index', _environ=dict(SCRIPT_NAME='/bar')))
        eq_('/', m.generate(controller='main', action='index'))

    def test_url_with_environ_and_absolute(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.environ = dict(SCRIPT_NAME='/blog')
        m.connect('image', 'image/:name', _absolute=True)
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        eq_('/blog/content/view', m.generate(controller='content', action='view'))
        eq_('/blog/content', m.generate(controller='content'))
        eq_('/blog/content', m.generate(controller='content'))
        eq_('/blog/admin/comments', m.generate(controller='admin/comments'))
        eq_('/image/topnav.jpg', url_for('image', name='topnav.jpg'))

    def test_route_with_odd_leftovers(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect(':controller/:(action)-:(id)')
        m.create_regs(['content','blog','admin/comments'])

        eq_('/content/view-', m.generate(controller='content', action='view'))
        eq_('/content/index-', m.generate(controller='content'))

    def test_route_with_end_extension(self):
        m = Mapper(explicit=False)
        m.connect(':controller/:(action)-:(id).html')
        m.create_regs(['content','blog','admin/comments'])

        eq_(None, m.generate(controller='content', action='view'))
        eq_(None, m.generate(controller='content'))

        eq_('/content/view-3.html', m.generate(controller='content', action='view', id=3))
        eq_('/content/index-2.html', m.generate(controller='content', id=2))

    def test_unicode(self):
        hoge = u'\u30c6\u30b9\u30c8' # the word test in Japanese
        hoge_enc = urllib.parse.quote(hoge.encode('utf-8'))
        m = Mapper()
        m.connect(':hoge')
        eq_("/%s" % hoge_enc, m.generate(hoge=hoge))
        self.assert_(isinstance(m.generate(hoge=hoge), str))

    def test_unicode_static(self):
        hoge = u'\u30c6\u30b9\u30c8' # the word test in Japanese
        hoge_enc = urllib.parse.quote(hoge.encode('utf-8'))
        m = Mapper()
        m.minimization = True
        m.connect('google-jp', 'http://www.google.co.jp/search', _static=True)
        m.create_regs(['messages'])
        eq_("http://www.google.co.jp/search?q=" + hoge_enc, url_for('google-jp', q=hoge))
        self.assert_(isinstance(url_for('google-jp', q=hoge), str))

    def test_other_special_chars(self):
        m = Mapper()
        m.minimization = True
        m.connect('/:year/:(slug).:(format),:(locale)', locale='en', format='html')
        m.create_regs(['content'])

        eq_('/2007/test', m.generate(year=2007, slug='test'))
        eq_('/2007/test.xml', m.generate(year=2007, slug='test', format='xml'))
        eq_('/2007/test.xml,ja', m.generate(year=2007, slug='test', format='xml', locale='ja'))
        eq_(None, m.generate(year=2007, format='html'))

    def test_dot_format_args(self):
        for minimization in [False, True]:
            m = Mapper(explicit=True)
            m.minimization=minimization
            m.connect('/songs/{title}{.format}')
            m.connect('/stories/{slug}{.format:pdf}')

            eq_('/songs/my-way', m.generate(title='my-way'))
            eq_('/songs/my-way.mp3', m.generate(title='my-way', format='mp3'))
            eq_('/stories/frist-post', m.generate(slug='frist-post'))
            eq_('/stories/frist-post.pdf', m.generate(slug='frist-post', format='pdf'))
            eq_(None, m.generate(slug='frist-post', format='doc'))

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
