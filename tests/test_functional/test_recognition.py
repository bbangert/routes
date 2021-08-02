"""test_recognition"""

import sys
import time
import unittest
import pytest
from six.moves import urllib
from routes import *
from routes.util import RoutesException

class TestRecognition(unittest.TestCase):

    def test_regexp_char_escaping(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect(':controller/:(action).:(id)')
        m.create_regs(['content'])

        assert m.match('/content/view.2') == {'action':'view','controller':'content','id':'2'}

        m.connect(':controller/:action/:id')
        m.create_regs(['content', 'find.all'])
        assert m.match('/find.all/view') == {'action':'view','controller':'find.all','id':None}
        assert m.match('/findzall/view') is None

    def test_all_static(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('hello/world/how/are/you', controller='content', action='index')
        m.create_regs([])

        assert m.match('/x') is None
        assert m.match('/hello/world/how') is None
        assert m.match('/hello/world/how/are') is None
        assert m.match('/hello/world/how/are/you/today') is None
        assert m.match('/hello/world/how/are/you') == {'controller':'content','action':'index'}

    def test_unicode(self):
        hoge = u'\u30c6\u30b9\u30c8' # the word test in Japanese
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect(':hoge')
        assert m.match('/' + hoge) == {'controller': 'content', 'action': 'index', 'hoge': hoge}

    def test_disabling_unicode(self):
        hoge = u'\u30c6\u30b9\u30c8' # the word test in Japanese
        hoge_enc = urllib.parse.quote(hoge.encode('utf-8'))
        m = Mapper(explicit=False)
        m.minimization = True
        m.encoding = None
        m.connect(':hoge')
        assert m.match('/' + hoge_enc) == {'controller': 'content', 'action': 'index', 'hoge': hoge_enc}

    def test_basic_dynamic(self):
        for path in ['hi/:name', 'hi/:(name)']:
            m = Mapper(explicit=False)
            m.minimization = True
            m.connect(path, controller='content')
            m.create_regs([])

            assert m.match('/boo') is None
            assert m.match('/boo/blah') is None
            assert m.match('/hi') is None
            assert m.match('/hi/dude/what') is None
            assert m.match('/hi/dude') == {'controller':'content','name':'dude','action':'index'}
            assert m.match('/hi/dude/') == {'controller':'content','name':'dude','action':'index'}

    def test_basic_dynamic_backwards(self):
        for path in [':name/hi', ':(name)/hi']:
            m = Mapper(explicit=False)
            m.minimization = True
            m.connect(path)
            m.create_regs([])

            assert m.match('/') is None
            assert m.match('/hi') is None
            assert m.match('/boo') is None
            assert m.match('/boo/blah') is None
            assert m.match('/shop/wallmart/hi') is None
            assert m.match('/fred/hi') == {'name':'fred','action':'index', 'controller':'content'}
            assert m.match('/index/hi') == {'name':'index','action':'index', 'controller':'content'}

    def test_dynamic_with_underscores(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('article/:small_page', small_page=False)
        m.connect(':(controller)/:(action)/:(id)')
        m.create_regs(['article', 'blog'])

        assert m.match('/blog/view/0') == {'controller':'blog','action':'view','id':'0'}
        assert m.match('/blog/view') == {'controller':'blog','action':'view','id':None}

    def test_dynamic_with_default(self):
        for path in ['hi/:action', 'hi/:(action)']:
            m = Mapper(explicit=False)
            m.minimization = True
            m.connect(path, controller='content')
            m.create_regs([])

            assert m.match('/boo') is None
            assert m.match('/boo/blah') is None
            assert m.match('/hi/dude/what') is None
            assert m.match('/hi') == {'controller':'content','action':'index'}
            assert m.match('/hi/index') == {'controller':'content','action':'index'}
            assert m.match('/hi/dude') == {'controller':'content','action':'dude'}

    def test_dynamic_with_default_backwards(self):
        for path in [':action/hi', ':(action)/hi']:
            m = Mapper(explicit=False)
            m.minimization = True
            m.connect(path, controller='content')
            m.create_regs([])

            assert m.match('/') is None
            assert m.match('/boo') is None
            assert m.match('/boo/blah') is None
            assert m.match('/hi') is None
            assert m.match('/index/hi') == {'controller':'content','action':'index'}
            assert m.match('/index/hi/') == {'controller':'content','action':'index'}
            assert m.match('/dude/hi') == {'controller':'content','action':'dude'}

    def test_dynamic_with_string_condition(self):
        for path in [':name/hi', ':(name)/hi']:
            m = Mapper(explicit=False)
            m.minimization = True
            m.connect(path, controller='content', requirements={'name':'index'})
            m.create_regs([])

            assert m.match('/boo') is None
            assert m.match('/boo/blah') is None
            assert m.match('/hi') is None
            assert m.match('/dude/what/hi') is None
            assert m.match('/index/hi') == {'controller':'content','name':'index','action':'index'}
            assert m.match('/dude/hi') is None

    def test_dynamic_with_string_condition_backwards(self):
        for path in ['hi/:name', 'hi/:(name)']:
            m = Mapper(explicit=False)
            m.minimization = True
            m.connect(path, controller='content', requirements={'name':'index'})
            m.create_regs([])

            assert m.match('/boo') is None
            assert m.match('/boo/blah') is None
            assert m.match('/hi') is None
            assert m.match('/hi/dude/what') is None
            assert m.match('/hi/index') == {'controller':'content','name':'index','action':'index'}
            assert m.match('/hi/dude') is None

    def test_dynamic_with_regexp_condition(self):
        for path in ['hi/:name', 'hi/:(name)']:
            m = Mapper(explicit=False)
            m.minimization = True
            m.connect(path, controller='content', requirements={'name':'[a-z]+'})
            m.create_regs([])

            assert m.match('/boo') is None
            assert m.match('/boo/blah') is None
            assert m.match('/hi') is None
            assert m.match('/hi/FOXY') is None
            assert m.match('/hi/138708jkhdf') is None
            assert m.match('/hi/dkjfl8792343dfsf') is None
            assert m.match('/hi/dude/what') is None
            assert m.match('/hi/dude/what/') is None
            assert m.match('/hi/index') == {'controller':'content','name':'index','action':'index'}
            assert m.match('/hi/dude') == {'controller':'content','name':'dude','action':'index'}

    def test_dynamic_with_regexp_and_default(self):
        for path in ['hi/:action', 'hi/:(action)']:
            m = Mapper(explicit=False)
            m.minimization = True
            m.connect(path, controller='content', requirements={'action':'[a-z]+'})
            m.create_regs([])

            assert m.match('/boo') is None
            assert m.match('/boo/blah') is None
            assert m.match('/hi/FOXY') is None
            assert m.match('/hi/138708jkhdf') is None
            assert m.match('/hi/dkjfl8792343dfsf') is None
            assert m.match('/hi/dude/what/') is None
            assert m.match('/hi') == {'controller':'content','action':'index'}
            assert m.match('/hi/index') == {'controller':'content','action':'index'}
            assert m.match('/hi/dude') == {'controller':'content','action':'dude'}

    def test_dynamic_with_default_and_string_condition_backwards(self):
        for path in [':action/hi', ':(action)/hi']:
            m = Mapper(explicit=False)
            m.minimization = True
            m.connect(path)
            m.create_regs([])

            assert m.match('/') is None
            assert m.match('/boo') is None
            assert m.match('/boo/blah') is None
            assert m.match('/hi') is None
            assert m.match('/index/hi') == {'action':'index', 'controller':'content'}

    def test_dynamic_and_controller_with_string_and_default_backwards(self):
        for path in [':controller/:action/hi', ':(controller)/:(action)/hi']:
            m = Mapper()
            m.connect(path, controller='content')
            m.create_regs(['content','admin/user'])

            assert m.match('/') is None
            assert m.match('/fred') is None


    def test_multiroute(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('archive/:year/:month/:day', controller='blog', action='view', month=None, day=None,
                                    requirements={'month':'\d{1,2}','day':'\d{1,2}'})
        m.connect('viewpost/:id', controller='post', action='view')
        m.connect(':controller/:action/:id')
        m.create_regs(['post','blog','admin/user'])

        assert m.match('/') is None
        assert m.match('/archive') is None
        assert m.match('/archive/2004/ab') is None
        assert m.match('/blog/view') == {'controller':'blog','action':'view','id':None}
        assert m.match('/archive/2004') == {'controller':'blog','action':'view','month':None,'day':None,'year':'2004'}
        assert m.match('/archive/2004/4') == {'controller':'blog','action':'view', 'month':'4', 'day':None,'year':'2004'}

    def test_multiroute_with_nomin(self):
        m = Mapper()
        m.minimization = False
        m.connect('/archive/:year/:month/:day', controller='blog', action='view', month=None, day=None,
                                    requirements={'month':'\d{1,2}','day':'\d{1,2}'})
        m.connect('/viewpost/:id', controller='post', action='view')
        m.connect('/:controller/:action/:id')
        m.create_regs(['post','blog','admin/user'])

        assert m.match('/') is None
        assert m.match('/archive') is None
        assert m.match('/archive/2004/ab') is None
        assert m.match('/archive/2004/4') is None
        assert m.match('/archive/2004') is None
        assert m.match('/blog/view/3') == {'controller':'blog','action':'view','id':'3'}
        assert m.match('/archive/2004/10/23') == {'controller':'blog','action':'view','month':'10','day':'23','year':'2004'}

    def test_multiroute_with_splits(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('archive/:(year)/:(month)/:(day)', controller='blog', action='view', month=None, day=None,
                                    requirements={'month':'\d{1,2}','day':'\d{1,2}'})
        m.connect('viewpost/:(id)', controller='post', action='view')
        m.connect(':(controller)/:(action)/:(id)')
        m.create_regs(['post','blog','admin/user'])

        assert m.match('/') is None
        assert m.match('/archive') is None
        assert m.match('/archive/2004/ab') is None
        assert m.match('/blog/view') == {'controller':'blog','action':'view','id':None}
        assert m.match('/archive/2004') == {'controller':'blog','action':'view','month':None,'day':None,'year':'2004'}
        assert m.match('/archive/2004/4') == {'controller':'blog','action':'view', 'month':'4', 'day':None,'year':'2004'}

    def test_dynamic_with_regexp_defaults_and_gaps(self):
        m = Mapper()
        m.minimization = True
        m.connect('archive/:year/:month/:day', controller='blog', action='view', month=None, day=None,
                                    requirements={'month':'\d{1,2}'})
        m.connect('view/:id/:controller', controller='blog', id=2, action='view', requirements={'id':'\d{1,2}'})
        m.create_regs(['post','blog','admin/user'])

        assert m.match('/') is None
        assert m.match('/archive') is None
        assert m.match('/archive/2004/haha') is None
        assert m.match('/view/blog') is None
        assert m.match('/view') == {'controller':'blog', 'action':'view', 'id':'2'}
        assert m.match('/archive/2004') == {'controller':'blog','action':'view','month':None,'day':None,'year':'2004'}

    def test_dynamic_with_regexp_defaults_and_gaps_and_splits(self):
        m = Mapper()
        m.minimization = True
        m.connect('archive/:(year)/:(month)/:(day)', controller='blog', action='view', month=None, day=None,
                                    requirements={'month':'\d{1,2}'})
        m.connect('view/:(id)/:(controller)', controller='blog', id=2, action='view', requirements={'id':'\d{1,2}'})
        m.create_regs(['post','blog','admin/user'])

        assert m.match('/') is None
        assert m.match('/archive') is None
        assert m.match('/archive/2004/haha') is None
        assert m.match('/view/blog') is None
        assert m.match('/view') == {'controller':'blog', 'action':'view', 'id':'2'}
        assert m.match('/archive/2004') == {'controller':'blog','action':'view','month':None,'day':None,'year':'2004'}

    def test_dynamic_with_regexp_gaps_controllers(self):
        for path in ['view/:id/:controller', 'view/:(id)/:(controller)']:
            m = Mapper()
            m.minimization = True
            m.connect(path, id=2, action='view', requirements={'id':'\d{1,2}'})
            m.create_regs(['post','blog','admin/user'])

            assert m.match('/') is None
            assert m.match('/view') is None
            assert m.match('/view/blog') is None
            assert m.match('/view/3') is None
            assert m.match('/view/4/honker') is None
            assert m.match('/view/2/blog') == {'controller':'blog','action':'view','id':'2'}

    def test_dynamic_with_trailing_strings(self):
        for path in ['view/:id/:controller/super', 'view/:(id)/:(controller)/super']:
            m = Mapper()
            m.minimization = True
            m.connect(path, controller='blog', id=2, action='view', requirements={'id':'\d{1,2}'})
            m.create_regs(['post','blog','admin/user'])

            assert m.match('/') is None
            assert m.match('/view') is None
            assert m.match('/view/blah/blog/super') is None
            assert m.match('/view/ha/super') is None
            assert m.match('/view/super') is None
            assert m.match('/view/4/super') is None
            assert m.match('/view/2/blog/super') == {'controller':'blog','action':'view','id':'2'}
            assert m.match('/view/4/admin/user/super') == {'controller':'admin/user','action':'view','id':'4'}

    def test_dynamic_with_trailing_non_keyword_strings(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('somewhere/:over/rainbow', controller='blog')
        m.connect('somewhere/:over', controller='post')
        m.create_regs(['post','blog','admin/user'])

        assert m.match('/') is None
        assert m.match('/somewhere') is None
        assert m.match('/somewhere/near/rainbow') == {'controller':'blog','action':'index','over':'near'}
        assert m.match('/somewhere/tomorrow') == {'controller':'post','action':'index','over':'tomorrow'}

    def test_dynamic_with_trailing_dyanmic_defaults(self):
        for path in ['archives/:action/:article', 'archives/:(action)/:(article)']:
            m = Mapper()
            m.minimization = True
            m.connect(path, controller='blog')
            m.create_regs(['blog'])

            assert m.match('/') is None
            assert m.match('/archives') is None
            assert m.match('/archives/introduction') is None
            assert m.match('/archives/sample') is None
            assert m.match('/view/super') is None
            assert m.match('/view/4/super') is None
            assert m.match('/archives/view/introduction') == {'controller':'blog','action':'view','article':'introduction'}
            assert m.match('/archives/edit/recipes') == {'controller':'blog','action':'edit','article':'recipes'}

    def test_path(self):
        for path in ['hi/*file', 'hi/*(file)']:
            m = Mapper()
            m.minimization = True
            m.connect(path, controller='content', action='download')
            m.create_regs([])

            assert m.match('/boo') is None
            assert m.match('/boo/blah') is None
            assert m.match('/hi') is None
            assert m.match('/hi/books/learning_python.pdf') == {'controller':'content','action':'download','file':'books/learning_python.pdf'}
            assert m.match('/hi/dude') == {'controller':'content','action':'download','file':'dude'}
            assert m.match('/hi/dude/what') == {'controller':'content','action':'download','file':'dude/what'}

    def test_path_with_dynamic(self):
        for path in [':controller/:action/*url', ':(controller)/:(action)/*(url)']:
            m = Mapper()
            m.minimization = True
            m.connect(path)
            m.create_regs(['content','admin/user'])

            assert m.match('/') is None
            assert m.match('/blog') is None
            assert m.match('/content') is None
            assert m.match('/content/view') is None
            assert m.match('/content/view/blob') == {'controller':'content','action':'view','url':'blob'}
            assert m.match('/admin/user') is None
            assert m.match('/admin/user/view') is None
            assert m.match('/admin/user/view/blob/check') == {'controller':'admin/user','action':'view','url':'blob/check'}


    def test_path_with_dyanmic_and_default(self):
        for path in [':controller/:action/*url', ':(controller)/:(action)/*(url)']:
            m = Mapper()
            m.minimization = True
            m.connect(path, controller='content', action='view', url=None)
            m.create_regs(['content','admin/user'])

            assert m.match('/goober/view/here') is None
            assert m.match('/') == {'controller':'content','action':'view','url':None}
            assert m.match('/content') == {'controller':'content','action':'view','url':None}
            assert m.match('/content/') == {'controller':'content','action':'view','url':None}
            assert m.match('/content/view') == {'controller':'content','action':'view','url':None}
            assert m.match('/content/view/fred') == {'controller':'content','action':'view','url':'fred'}
            assert m.match('/admin/user') == {'controller':'admin/user','action':'view','url':None}
            assert m.match('/admin/user/view') == {'controller':'admin/user','action':'view','url':None}

    def test_path_with_dynamic_and_default_backwards(self):
        for path in ['*file/login', '*(file)/login']:
            m = Mapper()
            m.minimization = True
            m.connect(path, controller='content', action='download', file=None)
            m.create_regs([])

            assert m.match('/boo') is None
            assert m.match('/boo/blah') is None
            assert m.match('//login') == {'controller':'content','action':'download','file':''}
            assert m.match('/books/learning_python.pdf/login') == {'controller':'content','action':'download','file':'books/learning_python.pdf'}
            assert m.match('/dude/login') == {'controller':'content','action':'download','file':'dude'}
            assert m.match('/dude/what/login') == {'controller':'content','action':'download','file':'dude/what'}

    def test_path_backwards(self):
        for path in ['*file/login', '*(file)/login']:
            m = Mapper()
            m.minimization = True
            m.connect(path, controller='content', action='download')
            m.create_regs([])

            assert m.match('/boo') is None
            assert m.match('/boo/blah') is None
            assert m.match('/login') is None
            assert m.match('/books/learning_python.pdf/login') == {'controller':'content','action':'download','file':'books/learning_python.pdf'}
            assert m.match('/dude/login') == {'controller':'content','action':'download','file':'dude'}
            assert m.match('/dude/what/login') == {'controller':'content','action':'download','file':'dude/what'}

    def test_path_backwards_with_controller(self):
        m = Mapper()
        m.minimization = True
        m.connect('*url/login', controller='content', action='check_access')
        m.connect('*url/:controller', action='view')
        m.create_regs(['content', 'admin/user'])

        assert m.match('/boo') is None
        assert m.match('/boo/blah') is None
        assert m.match('/login') is None
        assert m.match('/books/learning_python.pdf/login') == {'controller':'content','action':'check_access','url':'books/learning_python.pdf'}
        assert m.match('/dude/login') == {'controller':'content','action':'check_access','url':'dude'}
        assert m.match('/dude/what/login') == {'controller':'content','action':'check_access','url':'dude/what'}

        assert m.match('/admin/user') is None
        assert m.match('/books/learning_python.pdf/admin/user') == {'controller':'admin/user','action':'view','url':'books/learning_python.pdf'}
        assert m.match('/dude/admin/user') == {'controller':'admin/user','action':'view','url':'dude'}
        assert m.match('/dude/what/admin/user') == {'controller':'admin/user','action':'view','url':'dude/what'}

    def test_path_backwards_with_controller_and_splits(self):
        m = Mapper()
        m.minimization = True
        m.connect('*(url)/login', controller='content', action='check_access')
        m.connect('*(url)/:(controller)', action='view')
        m.create_regs(['content', 'admin/user'])

        assert m.match('/boo') is None
        assert m.match('/boo/blah') is None
        assert m.match('/login') is None
        assert m.match('/books/learning_python.pdf/login') == {'controller':'content','action':'check_access','url':'books/learning_python.pdf'}
        assert m.match('/dude/login') == {'controller':'content','action':'check_access','url':'dude'}
        assert m.match('/dude/what/login') == {'controller':'content','action':'check_access','url':'dude/what'}

        assert m.match('/admin/user') is None
        assert m.match('/books/learning_python.pdf/admin/user') == {'controller':'admin/user','action':'view','url':'books/learning_python.pdf'}
        assert m.match('/dude/admin/user') == {'controller':'admin/user','action':'view','url':'dude'}
        assert m.match('/dude/what/admin/user') == {'controller':'admin/user','action':'view','url':'dude/what'}

    def test_controller(self):
        m = Mapper()
        m.minimization = True
        m.connect('hi/:controller', action='hi')
        m.create_regs(['content','admin/user'])

        assert m.match('/boo') is None
        assert m.match('/boo/blah') is None
        assert m.match('/hi/13870948') is None
        assert m.match('/hi/content/dog') is None
        assert m.match('/hi/admin/user/foo') is None
        assert m.match('/hi/admin/user/foo/') is None
        assert m.match('/hi/content') == {'controller': 'content', 'action': 'hi'}
        assert m.match('/hi/admin/user') == {'controller': 'admin/user', 'action': 'hi'}

    def test_standard_route(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect(':controller/:action/:id')
        m.create_regs(['content','admin/user'])

        assert m.match('/content') == {'controller':'content','action':'index', 'id': None}
        assert m.match('/content/list') == {'controller':'content','action':'list', 'id':None}
        assert m.match('/content/show/10') == {'controller':'content','action':'show','id':'10'}

        assert m.match('/admin/user') == {'controller':'admin/user','action':'index', 'id': None}
        assert m.match('/admin/user/list') == {'controller':'admin/user','action':'list', 'id':None}
        assert m.match('/admin/user/show/bbangert') == {'controller':'admin/user','action':'show','id':'bbangert'}

        assert m.match('/content/show/10/20') is None
        assert m.match('/food') is None

    def test_standard_route_with_gaps(self):
        m = Mapper()
        m.minimization = True
        m.connect(':controller/:action/:(id).py')
        m.create_regs(['content','admin/user'])

        assert m.match('/content/index/None.py') == {'controller':'content','action':'index', 'id': 'None'}
        assert m.match('/content/list/None.py') == {'controller':'content','action':'list', 'id':'None'}
        assert m.match('/content/show/10.py') == {'controller':'content','action':'show','id':'10'}

    def test_standard_route_with_gaps_and_domains(self):
        m = Mapper()
        m.minimization = True
        m.connect('manage/:domain.:ext', controller='admin/user', action='view', ext='html')
        m.connect(':controller/:action/:id')
        m.create_regs(['content','admin/user'])

        assert m.match('/content/index/None.py') == {'controller':'content','action':'index', 'id': 'None.py'}
        assert m.match('/content/list/None.py') == {'controller':'content','action':'list', 'id':'None.py'}
        assert m.match('/content/show/10.py') == {'controller':'content','action':'show','id':'10.py'}
        assert m.match('/content/show.all/10.py') == {'controller':'content','action':'show.all','id':'10.py'}
        assert m.match('/content/show/www.groovie.org') == {'controller':'content','action':'show','id':'www.groovie.org'}

        assert m.match('/manage/groovie') == {'controller':'admin/user','action':'view', 'ext': 'html', 'domain': 'groovie'}
        assert m.match('/manage/groovie.xml') == {'controller':'admin/user','action':'view', 'ext': 'xml', 'domain': 'groovie'}

    def test_standard_with_domains(self):
        m = Mapper()
        m.minimization = True
        m.connect('manage/:domain', controller='domains', action='view')
        m.create_regs(['domains'])

        assert m.match('/manage/www.groovie.org') == {'controller':'domains','action':'view','domain':'www.groovie.org'}

    def test_default_route(self):
        m = Mapper()
        m.minimization = True
        m.connect('',controller='content',action='index')
        m.create_regs(['content'])

        assert m.match('/x') is None
        assert m.match('/hello/world') is None
        assert m.match('/hello/world/how/are') is None
        assert m.match('/hello/world/how/are/you/today') is None

        assert m.match('/') == {'controller':'content','action':'index'}

    def test_dynamic_with_prefix(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.prefix = '/blog'
        m.connect(':controller/:action/:id')
        m.connect('', controller='content', action='index')
        m.create_regs(['content', 'archive', 'admin/comments'])

        assert m.match('/x') is None
        assert m.match('/admin/comments') is None
        assert m.match('/content/view') is None
        assert m.match('/archive/view/4') is None

        assert m.match('/blog') == {'controller':'content','action':'index'}
        assert m.match('/blog/content') == {'controller':'content','action':'index','id':None}
        assert m.match('/blog/admin/comments/view') == {'controller':'admin/comments','action':'view','id':None}
        assert m.match('/blog/archive') == {'controller':'archive','action':'index','id':None}
        assert m.match('/blog/archive/view/4') == {'controller':'archive','action':'view', 'id':'4'}

    def test_dynamic_with_multiple_and_prefix(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.prefix = '/blog'
        m.connect(':controller/:action/:id')
        m.connect('home/:action', controller='archive')
        m.connect('', controller='content')
        m.create_regs(['content', 'archive', 'admin/comments'])

        assert m.match('/x') is None
        assert m.match('/admin/comments') is None
        assert m.match('/content/view') is None
        assert m.match('/archive/view/4') is None

        assert m.match('/blog/') == {'controller': 'content', 'action': 'index'}
        assert m.match('/blog/home/view') == {'controller': 'archive', 'action': 'view'}
        assert m.match('/blog/content') == {'controller': 'content', 'action': 'index', 'id':None}
        assert m.match('/blog/admin/comments/view') == {'controller': 'admin/comments', 'action': 'view', 'id':None}
        assert m.match('/blog/archive') == {'controller': 'archive', 'action': 'index', 'id':None}
        assert m.match('/blog/archive/view/4') == {'controller': 'archive', 'action': 'view', 'id': '4'}


    def test_splits_with_extension(self):
        m = Mapper()
        m.minimization = True
        m.connect('hi/:(action).html', controller='content')
        m.create_regs([])

        assert m.match('/boo') is None
        assert m.match('/boo/blah') is None
        assert m.match('/hi/dude/what') is None
        assert m.match('/hi') is None
        assert m.match('/hi/index.html') == {'controller':'content','action':'index'}
        assert m.match('/hi/dude.html') == {'controller':'content','action':'dude'}

    def test_splits_with_dashes(self):
        m = Mapper()
        m.minimization = True
        m.connect('archives/:(year)-:(month)-:(day).html', controller='archives', action='view')
        m.create_regs([])

        assert m.match('/boo') is None
        assert m.match('/archives') is None

        assert m.match('/archives/2004-12-4.html') == {'controller':'archives','action':'view','year':'2004','month':'12','day':'4'}
        assert m.match('/archives/04-10-4.html') == {'controller':'archives','action':'view','year':'04','month':'10','day':'4'}
        assert m.match('/archives/04-1-1.html') == {'controller':'archives','action':'view','year':'04','month':'1','day':'1'}

    def test_splits_packed_with_regexps(self):
        m = Mapper()
        m.minimization = True
        m.connect('archives/:(year):(month):(day).html', controller='archives', action='view',
               requirements=dict(year=r'\d{4}',month=r'\d{2}',day=r'\d{2}'))
        m.create_regs([])

        assert m.match('/boo') is None
        assert m.match('/archives') is None
        assert m.match('/archives/2004020.html') is None
        assert m.match('/archives/200502.html') is None

        assert m.match('/archives/20041204.html') == {'controller':'archives','action':'view','year':'2004','month':'12','day':'04'}
        assert m.match('/archives/20051004.html') == {'controller':'archives','action':'view','year':'2005','month':'10','day':'04'}
        assert m.match('/archives/20060101.html') == {'controller':'archives','action':'view','year':'2006','month':'01','day':'01'}

    def test_splits_with_slashes(self):
        m = Mapper()
        m.minimization = True
        m.connect(':name/:(action)-:(day)', controller='content')
        m.create_regs([])

        assert m.match('/something') is None
        assert m.match('/something/is-') is None

        assert m.match('/group/view-3') == {'controller':'content','action':'view','day':'3','name':'group'}
        assert m.match('/group/view-5') == {'controller':'content','action':'view','day':'5','name':'group'}

    def test_splits_with_slashes_and_default(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect(':name/:(action)-:(id)', controller='content')
        m.create_regs([])

        assert m.match('/something') is None
        assert m.match('/something/is') is None

        assert m.match('/group/view-3') == {'controller':'content','action':'view','id':'3','name':'group'}
        assert m.match('/group/view-') == {'controller':'content','action':'view','id':None,'name':'group'}

    def test_no_reg_make(self):
        m = Mapper()
        m.connect(':name/:(action)-:(id)', controller='content')
        m.controller_scan = False
        def call_func():
            m.match('/group/view-3')
        with pytest.raises(RoutesException):
            call_func()

    def test_routematch(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect(':controller/:action/:id')
        m.create_regs(['content'])
        route = m.matchlist[0]

        resultdict, route_obj = m.routematch('/content')
        assert resultdict == {'action':'index', 'controller':'content','id':None}
        assert route_obj == route
        assert m.routematch('/nowhere') is None

    def test_routematch_debug(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect(':controller/:action/:id')
        m.debug = True
        m.create_regs(['content'])
        route = m.matchlist[0]

        resultdict, route_obj, debug = m.routematch('/content')
        assert resultdict == {'action':'index', 'controller':'content','id':None}
        assert route_obj == route
        resultdict, route_obj, debug = m.routematch('/nowhere')
        assert resultdict is None
        assert route_obj is None
        assert len(debug) == 0

    def test_match_debug(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('nowhere', 'http://nowhere.com/', _static=True)
        m.connect(':controller/:action/:id')
        m.debug = True
        m.create_regs(['content'])
        route = m.matchlist[0]

        resultdict, route_obj, debug = m.match('/content')
        assert resultdict == {'action':'index', 'controller':'content','id':None}
        assert route_obj == route
        resultdict, route_obj, debug = m.match('/nowhere')
        assert resultdict is None
        assert route_obj is None
        assert len(debug) == 0

    def test_conditions(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('home/upload', controller='content', action='upload', conditions=dict(method=['POST']))
        m.connect(':controller/:action/:id')
        m.create_regs(['content', 'blog'])

        con = request_config()
        con.mapper = m
        env = dict(PATH_INFO='/nowhere', HTTP_HOST='example.com', REQUEST_METHOD='GET')
        con.mapper_dict = {}
        con.environ = env
        assert con.mapper_dict is None

        env['PATH_INFO'] = '/content'
        con.environ = env
        assert con.mapper_dict == {'action':'index','controller':'content','id':None}

        env['PATH_INFO'] = '/home/upload'
        con.environ = env
        assert con.mapper_dict is None

        env['REQUEST_METHOD'] = 'POST'
        con.environ = env
        assert con.mapper_dict == {'action':'upload','controller':'content'}

    def test_subdomains(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.sub_domains = True
        m.connect(':controller/:action/:id')
        m.create_regs(['content', 'blog'])

        con = request_config()
        con.mapper = m
        env = dict(PATH_INFO='/nowhere', HTTP_HOST='example.com')
        con.mapper_dict = {}
        con.environ = env

        assert con.mapper_dict is None

        env['PATH_INFO'] = '/content'
        con.environ = env
        assert con.mapper_dict == {'action': 'index', 'controller': 'content', 'sub_domain': None, 'id': None}

        env['HTTP_HOST'] = 'fred.example.com'
        con.environ = env
        assert con.mapper_dict == {'action': 'index', 'controller': 'content', 'sub_domain': 'fred', 'id': None}

        env['HTTP_HOST'] = 'www.example.com'
        con.environ = env
        assert con.mapper_dict == {'action': 'index', 'controller': 'content', 'sub_domain': 'www', 'id': None}

    def test_subdomains_with_conditions(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.sub_domains = True
        m.connect(':controller/:action/:id')
        m.create_regs(['content', 'blog'])

        con = request_config()
        con.mapper = m
        env = dict(PATH_INFO='/nowhere', HTTP_HOST='example.com')
        con.mapper_dict = {}
        con.environ = env

        assert con.mapper_dict is None

        env['PATH_INFO'] = '/content'
        con.environ = env
        assert con.mapper_dict == {'action': 'index', 'controller': 'content', 'sub_domain': None, 'id': None}

        m.connect('', controller='users', action='home', conditions={'sub_domain':True})
        m.create_regs(['content', 'users', 'blog'])
        env['PATH_INFO'] = '/'
        con.environ = env
        assert con.mapper_dict is None

        env['HTTP_HOST'] = 'fred.example.com'
        con.environ = env
        assert con.mapper_dict == {'action': 'home', 'controller': 'users', 'sub_domain': 'fred'}

        m.sub_domains_ignore = ['www']
        env['HTTP_HOST'] = 'www.example.com'
        con.environ = env
        assert con.mapper_dict is None

    def test_subdomain_with_conditions2(self):
        m = Mapper()
        m.minimization = True
        m.sub_domains = True
        m.connect('admin/comments', controller='admin', action='comments',
                  conditions={'sub_domain':True})
        m.connect('admin/comments', controller='blog_admin', action='comments')
        m.connect('admin/view', controller='blog_admin', action='view',
                  conditions={'sub_domain':False})
        m.connect('admin/view', controller='admin', action='view')
        m.create_regs(['content', 'blog_admin', 'admin'])

        con = request_config()
        con.mapper = m
        env = dict(PATH_INFO='/nowhere', HTTP_HOST='example.com')
        con.mapper_dict = {}
        con.environ = env

        assert con.mapper_dict is None

        env['PATH_INFO'] = '/admin/comments'
        con.environ = env
        assert con.mapper_dict == {'action': 'comments', 'controller':'blog_admin', 'sub_domain': None}

        env['PATH_INFO'] = '/admin/view'
        env['HTTP_HOST'] = 'fred.example.com'
        con.environ = env
        assert con.mapper_dict == {'action': 'view', 'controller':'admin', 'sub_domain': 'fred'}

    def test_subdomains_with_ignore(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.sub_domains = True
        m.sub_domains_ignore = ['www']
        m.connect(':controller/:action/:id')
        m.create_regs(['content', 'blog'])

        con = request_config()
        con.mapper = m
        env = dict(PATH_INFO='/nowhere', HTTP_HOST='example.com')
        con.mapper_dict = {}
        con.environ = env

        assert con.mapper_dict is None

        env['PATH_INFO'] = '/content'
        con.environ = env
        assert con.mapper_dict == {'action': 'index', 'controller': 'content', 'sub_domain': None, 'id': None}

        env['HTTP_HOST'] = 'fred.example.com'
        con.environ = env
        assert con.mapper_dict == {'action': 'index', 'controller': 'content', 'sub_domain': 'fred', 'id': None}

        env['HTTP_HOST'] = 'www.example.com'
        con.environ = env
        assert con.mapper_dict == {'action': 'index', 'controller': 'content', 'sub_domain': None, 'id': None}

    def test_other_special_chars(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('/:year/:(slug).:(format),:(locale)', format='html', locale='en')
        m.connect('/error/:action/:id', controller='error')
        m.create_regs(['content'])

        assert m.match('/2007/test') == {'year': '2007', 'slug': 'test', 'locale': 'en', 'format': 'html', 'controller': 'content', 'action': 'index'}
        assert m.match('/2007/test.html') == {'year': '2007', 'slug': 'test', 'format': 'html', 'locale': 'en', 'controller': 'content', 'action': 'index'}
        assert m.match('/2007/test.html,en') == {'year': '2007', 'slug': 'test', 'format': 'html', 'locale': 'en', 'controller': 'content', 'action': 'index'}
        assert m.match('/2007/test.') is None
        assert m.match('/error/img/icon-16.png') == {'controller': 'error', 'action': 'img', 'id': 'icon-16.png'}

    def test_various_periods(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('sites/:site/pages/:page')
        m.create_regs(['content'])

        assert m.match('/sites/python.com/pages/index.html') == {'action': u'index', 'controller': u'content', 'site': u'python.com', 'page': u'index.html'}
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect('sites/:site/pages/:page.:format', format='html')
        m.create_regs(['content'])

        assert m.match('/sites/python.com/pages/index.html') == {'action': u'index', 'controller': u'content', 'site': u'python.com', 'page': u'index', 'format': u'html'}

    def test_empty_fails(self):
        m = Mapper(explicit=False)
        m.minimization = True
        m.connect(':controller/:action/:id')
        m.connect('', controller='content', action='view', id=4)
        m.create_regs(['content'])

        assert m.match('/content') == {'controller':'content','action':'index','id':None}
        assert m.match('/') == {'controller':'content','action':'view','id':'4'}
        def call_func():
            m.match(None)
        with pytest.raises(RoutesException):
            call_func()

    def test_home_noargs(self):
        m = Mapper(controller_scan=None, directory=None, always_scan=False)
        m.minimization = True
        m.explicit = True
        m.connect('')
        m.create_regs([])

        assert m.match('/content') is None
        assert m.match('/') == {}
        def call_func():
            m.match(None)
        with pytest.raises(RoutesException):
            call_func()

    def test_dot_format_args(self):
        for minimization in [False, True]:
            m = Mapper(explicit=True)
            m.minimization=minimization
            m.connect('/songs/{title}{.format}')
            m.connect('/stories/{slug:[^./]+?}{.format:pdf}')

            assert m.match('/songs/my-way') == {'title': 'my-way', 'format': None}
            assert m.match('/songs/my-way.mp3') == {'title': 'my-way', 'format': 'mp3'}
            assert m.match('/stories/frist-post') == {'slug': 'frist-post', 'format': None}
            assert m.match('/stories/frist-post.pdf') == {'slug': 'frist-post', 'format': 'pdf'}
            assert m.match('/stories/frist-post.doc') is None


if __name__ == '__main__':
    unittest.main()
else:
    def bench_rec():
        n = 1000
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
        m.create_regs(['content','admin/why', 'admin/user'])
        start = time.time()
        for x in range(1,n):
            a = m.match('/admin/comments/article/42/show/52')
            a = m.match('/admin/content/view/5')
            a = m.match('/index.rdf')

            a = m.match('/xml/view/feed.xml')
            a = m.match('/xml/articlerss/42/feed.xml')
            a = m.match('/articles')

            a = m.match('/articles/2004/12/20/page/2')
            a = m.match('/articles/category/42')
            a = m.match('/pages/this/is/long')
            a = m.match('/miss')
        end = time.time()
        ts = time.time()
        for x in range(1,n):
            pass
        en = time.time()
        total = end-start-(en-ts)
        per_url = total / (n*10)
        print("Recognition\n")
        print("%s ms/url" % (per_url*1000))
        print("%s urls/s\n" % (1.00/per_url))

"""
Copyright (c) 2005 Ben Bangert <ben@groovie.org>, Parachute
All rights reserved.

Redistribution and use in source and binary forms, with or without
modification, are permitted provided that the following conditions
are met:
1. Redistributions of source code must retain the above copyright
   notice, this list of conditions and the following disclaimer.
2. Redistributions in binary form must reproduce the above copyright
   notice, this list of conditions and the following disclaimer in the
   documentation and/or other materials provided with the distribution.
3. The name of the author or contributors may not be used to endorse or
   promote products derived from this software without specific prior
   written permission.

THIS SOFTWARE IS PROVIDED BY THE AUTHOR AND CONTRIBUTORS ``AS IS'' AND
ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
ARE DISCLAIMED.  IN NO EVENT SHALL THE AUTHOR OR CONTRIBUTORS BE LIABLE
FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS
OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION)
HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY
OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF
SUCH DAMAGE.
"""
