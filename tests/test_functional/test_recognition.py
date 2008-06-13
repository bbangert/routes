"""test_recognition"""

import sys
import time
import unittest
import urllib
from nose.tools import eq_
from routes import *
from routes.util import RouteException

class TestRecognition(unittest.TestCase):
    
    def test_regexp_char_escaping(self):
        m = Mapper()
        m.connect(':controller/:(action).:(id)')
        m.create_regs(['content'])
        
        assert {'action':'view','controller':'content','id':'2'} == m.match('/content/view.2')
        
        m.connect(':controller/:action/:id')
        m.create_regs(['content', 'find.all'])
        assert {'action':'view','controller':'find.all','id':None} == m.match('/find.all/view')
        assert None == m.match('/findzall/view')
        
    def test_all_static(self):
        m = Mapper()
        m.connect('hello/world/how/are/you', controller='content', action='index')
        m.create_regs([])
        
        self.assertEqual(None, m.match('/x'))
        self.assertEqual(None, m.match('/hello/world/how'))
        self.assertEqual(None, m.match('/hello/world/how/are'))
        self.assertEqual(None, m.match('/hello/world/how/are/you/today'))
        self.assertEqual({'controller':'content','action':'index'}, m.match('/hello/world/how/are/you'))
    
    def test_unicode(self):
        hoge = u'\u30c6\u30b9\u30c8' # the word test in Japanese
        hoge_enc = hoge.encode('utf-8')
        m = Mapper()
        m.connect(':hoge')
        self.assertEqual({'controller': 'content', 'action': 'index', 'hoge': hoge},
                         m.match('/' + hoge_enc))
    
    def test_disabling_unicode(self):
        hoge = u'\u30c6\u30b9\u30c8' # the word test in Japanese
        hoge_enc = urllib.quote(hoge.encode('utf-8'))
        m = Mapper()
        m.encoding = None
        m.connect(':hoge')
        self.assertEqual({'controller': 'content', 'action': 'index', 'hoge': hoge_enc},
                         m.match('/' + hoge_enc))
            
    def test_basic_dynamic(self):
        for path in ['hi/:name', 'hi/:(name)']:
            m = Mapper()
            m.connect(path, controller='content')
            m.create_regs([])
        
            self.assertEqual(None, m.match('/boo'))
            self.assertEqual(None, m.match('/boo/blah'))
            self.assertEqual(None, m.match('/hi'))
            self.assertEqual(None, m.match('/hi/dude/what'))
            self.assertEqual({'controller':'content','name':'dude','action':'index'}, m.match('/hi/dude'))
            self.assertEqual({'controller':'content','name':'dude','action':'index'}, m.match('/hi/dude/'))
    
    def test_basic_dynamic_backwards(self):
        for path in [':name/hi', ':(name)/hi']:
            m = Mapper()
            m.connect(path)
            m.create_regs([])

            self.assertEqual(None, m.match('/'))
            self.assertEqual(None, m.match('/hi'))
            self.assertEqual(None, m.match('/boo'))
            self.assertEqual(None, m.match('/boo/blah'))
            self.assertEqual(None, m.match('/shop/wallmart/hi'))
            self.assertEqual({'name':'fred', 'action':'index', 'controller':'content'}, m.match('/fred/hi'))
            self.assertEqual({'name':'index', 'action':'index', 'controller':'content'}, m.match('/index/hi'))
    
    def test_dynamic_with_underscores(self):
        m = Mapper()
        m.connect('article/:small_page', small_page=False)
        m.connect(':(controller)/:(action)/:(id)')
        m.create_regs(['article', 'blog'])
        
        assert {'controller':'blog','action':'view','id':'0'} == m.match('/blog/view/0')
        assert {'controller':'blog','action':'view','id':None} == m.match('/blog/view')
        
    def test_dynamic_with_default(self):
        for path in ['hi/:action', 'hi/:(action)']:
            m = Mapper()
            m.connect(path, controller='content')
            m.create_regs([])
        
            self.assertEqual(None, m.match('/boo'))
            self.assertEqual(None, m.match('/boo/blah'))
            self.assertEqual(None, m.match('/hi/dude/what'))
            self.assertEqual({'controller':'content','action':'index'}, m.match('/hi'))
            self.assertEqual({'controller':'content','action':'index'}, m.match('/hi/index'))
            self.assertEqual({'controller':'content','action':'dude'}, m.match('/hi/dude'))
    
    def test_dynamic_with_default_backwards(self):
        for path in [':action/hi', ':(action)/hi']:
            m = Mapper()
            m.connect(path, controller='content')
            m.create_regs([])

            self.assertEqual(None, m.match('/'))
            self.assertEqual(None, m.match('/boo'))
            self.assertEqual(None, m.match('/boo/blah'))
            self.assertEqual(None, m.match('/hi'))
            self.assertEqual({'controller':'content','action':'index'}, m.match('/index/hi'))
            self.assertEqual({'controller':'content','action':'index'}, m.match('/index/hi/'))
            self.assertEqual({'controller':'content','action':'dude'}, m.match('/dude/hi'))
    
    def test_dynamic_with_string_condition(self):
        for path in [':name/hi', ':(name)/hi']:
            m = Mapper()
            m.connect(path, controller='content', requirements={'name':'index'})
            m.create_regs([])
        
            self.assertEqual(None, m.match('/boo'))
            self.assertEqual(None, m.match('/boo/blah'))
            self.assertEqual(None, m.match('/hi'))
            self.assertEqual(None, m.match('/dude/what/hi'))
            self.assertEqual({'controller':'content','name':'index','action':'index'}, m.match('/index/hi'))
            self.assertEqual(None, m.match('/dude/hi'))
    
    def test_dynamic_with_string_condition_backwards(self):
        for path in ['hi/:name', 'hi/:(name)']:
            m = Mapper()
            m.connect(path, controller='content', requirements={'name':'index'})
            m.create_regs([])

            self.assertEqual(None, m.match('/boo'))
            self.assertEqual(None, m.match('/boo/blah'))
            self.assertEqual(None, m.match('/hi'))
            self.assertEqual(None, m.match('/hi/dude/what'))
            self.assertEqual({'controller':'content','name':'index','action':'index'}, m.match('/hi/index'))
            self.assertEqual(None, m.match('/hi/dude'))
    
    def test_dynamic_with_regexp_condition(self):
        for path in ['hi/:name', 'hi/:(name)']:
            m = Mapper()
            m.connect(path, controller='content', requirements={'name':'[a-z]+'})
            m.create_regs([])
        
            self.assertEqual(None, m.match('/boo'))
            self.assertEqual(None, m.match('/boo/blah'))
            self.assertEqual(None, m.match('/hi'))
            self.assertEqual(None, m.match('/hi/FOXY'))
            self.assertEqual(None, m.match('/hi/138708jkhdf'))
            self.assertEqual(None, m.match('/hi/dkjfl8792343dfsf'))
            self.assertEqual(None, m.match('/hi/dude/what'))
            self.assertEqual(None, m.match('/hi/dude/what/'))
            self.assertEqual({'controller':'content','name':'index','action':'index'}, m.match('/hi/index'))
            self.assertEqual({'controller':'content','name':'dude','action':'index'}, m.match('/hi/dude'))
    
    def test_dynamic_with_regexp_and_default(self):
        for path in ['hi/:action', 'hi/:(action)']:
            m = Mapper()
            m.connect(path, controller='content', requirements={'action':'[a-z]+'})
            m.create_regs([])
        
            self.assertEqual(None, m.match('/boo'))
            self.assertEqual(None, m.match('/boo/blah'))
            self.assertEqual(None, m.match('/hi/FOXY'))
            self.assertEqual(None, m.match('/hi/138708jkhdf'))
            self.assertEqual(None, m.match('/hi/dkjfl8792343dfsf'))
            self.assertEqual(None, m.match('/hi/dude/what/'))
            self.assertEqual({'controller':'content','action':'index'}, m.match('/hi'))
            self.assertEqual({'controller':'content','action':'index'}, m.match('/hi/index'))
            self.assertEqual({'controller':'content','action':'dude'}, m.match('/hi/dude'))
    
    def test_dynamic_with_default_and_string_condition_backwards(self):
        for path in [':action/hi', ':(action)/hi']:
            m = Mapper()
            m.connect(path)
            m.create_regs([])

            self.assertEqual(None, m.match('/'))
            self.assertEqual(None, m.match('/boo'))
            self.assertEqual(None, m.match('/boo/blah'))
            self.assertEqual(None, m.match('/hi'))
            self.assertEqual({'action':'index', 'controller':'content'}, m.match('/index/hi'))

    def test_dynamic_and_controller_with_string_and_default_backwards(self):
        for path in [':controller/:action/hi', ':(controller)/:(action)/hi']:
            m = Mapper()
            m.connect(path, controller='content')
            m.create_regs(['content','admin/user'])

            self.assertEqual(None, m.match('/'))
            self.assertEqual(None, m.match('/fred'))

    
    def test_multiroute(self):
        m = Mapper()
        m.connect('archive/:year/:month/:day', controller='blog', action='view', month=None, day=None,
                                    requirements={'month':'\d{1,2}','day':'\d{1,2}'})
        m.connect('viewpost/:id', controller='post', action='view')
        m.connect(':controller/:action/:id')
        m.create_regs(['post','blog','admin/user'])
        
        self.assertEqual(None, m.match('/'))
        self.assertEqual(None, m.match('/archive'))
        self.assertEqual(None, m.match('/archive/2004/ab'))
        self.assertEqual({'controller':'blog','action':'view','id':None}, m.match('/blog/view'))
        self.assertEqual({'controller':'blog','action':'view','month':None,'day':None,'year':'2004'}, 
                         m.match('/archive/2004'))
        self.assertEqual({'controller':'blog','action':'view', 'month':'4', 'day':None,'year':'2004'}, 
                         m.match('/archive/2004/4'))

    def test_multiroute_with_nomin(self):
        m = Mapper()
        m.minimization = False
        m.connect('/archive/:year/:month/:day', controller='blog', action='view', month=None, day=None,
                                    requirements={'month':'\d{1,2}','day':'\d{1,2}'})
        m.connect('/viewpost/:id', controller='post', action='view')
        m.connect('/:controller/:action/:id')
        m.create_regs(['post','blog','admin/user'])
        
        self.assertEqual(None, m.match('/'))
        self.assertEqual(None, m.match('/archive'))
        self.assertEqual(None, m.match('/archive/2004/ab'))
        self.assertEqual(None, m.match('/archive/2004/4'))
        self.assertEqual(None, m.match('/archive/2004'))
        eq_({'controller':'blog','action':'view','id':'3'}, m.match('/blog/view/3'))
        eq_({'controller':'blog','action':'view','month':'10','day':'23','year':'2004'}, 
                         m.match('/archive/2004/10/23'))

    def test_multiroute_with_splits(self):
        m = Mapper()
        m.connect('archive/:(year)/:(month)/:(day)', controller='blog', action='view', month=None, day=None,
                                    requirements={'month':'\d{1,2}','day':'\d{1,2}'})
        m.connect('viewpost/:(id)', controller='post', action='view')
        m.connect(':(controller)/:(action)/:(id)')
        m.create_regs(['post','blog','admin/user'])
        
        self.assertEqual(None, m.match('/'))
        self.assertEqual(None, m.match('/archive'))
        self.assertEqual(None, m.match('/archive/2004/ab'))
        self.assertEqual({'controller':'blog','action':'view','id':None}, m.match('/blog/view'))
        self.assertEqual({'controller':'blog','action':'view','month':None,'day':None,'year':'2004'}, 
                         m.match('/archive/2004'))
        self.assertEqual({'controller':'blog','action':'view', 'month':'4', 'day':None,'year':'2004'}, 
                         m.match('/archive/2004/4'))
    
    def test_dynamic_with_regexp_defaults_and_gaps(self):
        m = Mapper()
        m.connect('archive/:year/:month/:day', controller='blog', action='view', month=None, day=None,
                                    requirements={'month':'\d{1,2}'})
        m.connect('view/:id/:controller', controller='blog', id=2, action='view', requirements={'id':'\d{1,2}'})
        m.create_regs(['post','blog','admin/user'])

        self.assertEqual(None, m.match('/'))
        self.assertEqual(None, m.match('/archive'))
        self.assertEqual(None, m.match('/archive/2004/haha'))
        self.assertEqual(None, m.match('/view/blog'))
        self.assertEqual({'controller':'blog', 'action':'view', 'id':'2'}, m.match('/view'))
        self.assertEqual({'controller':'blog','action':'view','month':None,'day':None,'year':'2004'}, m.match('/archive/2004'))

    def test_dynamic_with_regexp_defaults_and_gaps_and_splits(self):
        m = Mapper()
        m.connect('archive/:(year)/:(month)/:(day)', controller='blog', action='view', month=None, day=None,
                                    requirements={'month':'\d{1,2}'})
        m.connect('view/:(id)/:(controller)', controller='blog', id=2, action='view', requirements={'id':'\d{1,2}'})
        m.create_regs(['post','blog','admin/user'])

        self.assertEqual(None, m.match('/'))
        self.assertEqual(None, m.match('/archive'))
        self.assertEqual(None, m.match('/archive/2004/haha'))
        self.assertEqual(None, m.match('/view/blog'))
        self.assertEqual({'controller':'blog', 'action':'view', 'id':'2'}, m.match('/view'))
        self.assertEqual({'controller':'blog','action':'view','month':None,'day':None,'year':'2004'}, m.match('/archive/2004'))

    def test_dynamic_with_regexp_gaps_controllers(self):
        for path in ['view/:id/:controller', 'view/:(id)/:(controller)']:
            m = Mapper()
            m.connect(path, id=2, action='view', requirements={'id':'\d{1,2}'})
            m.create_regs(['post','blog','admin/user'])
        
            self.assertEqual(None, m.match('/'))
            self.assertEqual(None, m.match('/view'))
            self.assertEqual(None, m.match('/view/blog'))
            self.assertEqual(None, m.match('/view/3'))
            self.assertEqual(None, m.match('/view/4/honker'))
            self.assertEqual({'controller':'blog','action':'view','id':'2'}, m.match('/view/2/blog'))
    
    def test_dynamic_with_trailing_strings(self):
        for path in ['view/:id/:controller/super', 'view/:(id)/:(controller)/super']:
            m = Mapper()
            m.connect(path, controller='blog', id=2, action='view', requirements={'id':'\d{1,2}'})
            m.create_regs(['post','blog','admin/user'])
        
            self.assertEqual(None, m.match('/'))
            self.assertEqual(None, m.match('/view'))
            self.assertEqual(None, m.match('/view/blah/blog/super'))
            self.assertEqual(None, m.match('/view/ha/super'))
            self.assertEqual(None, m.match('/view/super'))
            self.assertEqual(None, m.match('/view/4/super'))
            self.assertEqual({'controller':'blog','action':'view','id':'2'}, m.match('/view/2/blog/super'))
            self.assertEqual({'controller':'admin/user','action':'view','id':'4'}, m.match('/view/4/admin/user/super'))
    
    def test_dynamic_with_trailing_non_keyword_strings(self):
        m = Mapper()
        m.connect('somewhere/:over/rainbow', controller='blog')
        m.connect('somewhere/:over', controller='post')
        m.create_regs(['post','blog','admin/user'])
    
        self.assertEqual(None, m.match('/'))
        self.assertEqual(None, m.match('/somewhere'))
        self.assertEqual({'controller':'blog','action':'index','over':'near'}, m.match('/somewhere/near/rainbow'))
        self.assertEqual({'controller':'post','action':'index','over':'tomorrow'}, m.match('/somewhere/tomorrow'))
        
    def test_dynamic_with_trailing_dyanmic_defaults(self):
        for path in ['archives/:action/:article', 'archives/:(action)/:(article)']:
            m = Mapper()
            m.connect(path, controller='blog')
            m.create_regs(['blog'])
        
            self.assertEqual(None, m.match('/'))
            self.assertEqual(None, m.match('/archives'))
            self.assertEqual(None, m.match('/archives/introduction'))
            self.assertEqual(None, m.match('/archives/sample'))
            self.assertEqual(None, m.match('/view/super'))
            self.assertEqual(None, m.match('/view/4/super'))
            self.assertEqual({'controller':'blog','action':'view','article':'introduction'}, 
                             m.match('/archives/view/introduction'))
            self.assertEqual({'controller':'blog','action':'edit','article':'recipes'}, 
                             m.match('/archives/edit/recipes'))
    
    def test_path(self):
        for path in ['hi/*file', 'hi/*(file)']:
            m = Mapper()
            m.connect(path, controller='content', action='download')
            m.create_regs([])
        
            self.assertEqual(None, m.match('/boo'))
            self.assertEqual(None, m.match('/boo/blah'))
            self.assertEqual(None, m.match('/hi'))
            self.assertEqual({'controller':'content','action':'download','file':'books/learning_python.pdf'}, m.match('/hi/books/learning_python.pdf'))
            self.assertEqual({'controller':'content','action':'download','file':'dude'}, m.match('/hi/dude'))
            self.assertEqual({'controller':'content','action':'download','file':'dude/what'}, m.match('/hi/dude/what'))
    
    def test_path_with_dynamic(self):
        for path in [':controller/:action/*url', ':(controller)/:(action)/*(url)']:
            m = Mapper()
            m.connect(path)
            m.create_regs(['content','admin/user'])
        
            self.assertEqual(None, m.match('/'))
            self.assertEqual(None, m.match('/blog'))
            self.assertEqual(None, m.match('/content'))
            self.assertEqual(None, m.match('/content/view'))
            self.assertEqual({'controller':'content','action':'view','url':'blob'}, m.match('/content/view/blob'))
            self.assertEqual(None, m.match('/admin/user'))
            self.assertEqual(None, m.match('/admin/user/view'))
            self.assertEqual({'controller':'admin/user','action':'view','url':'blob/check'}, m.match('/admin/user/view/blob/check'))
    
    
    def test_path_with_dyanmic_and_default(self):
        for path in [':controller/:action/*url', ':(controller)/:(action)/*(url)']:
            m = Mapper()
            m.connect(path, controller='content', action='view', url=None)
            m.create_regs(['content','admin/user'])
        
            self.assertEqual(None, m.match('/goober/view/here'))
            self.assertEqual({'controller':'content','action':'view','url':None}, m.match('/'))
            self.assertEqual({'controller':'content','action':'view','url':None}, m.match('/content'))
            self.assertEqual({'controller':'content','action':'view','url':None}, m.match('/content/'))
            self.assertEqual({'controller':'content','action':'view','url':None}, m.match('/content/view'))
            self.assertEqual({'controller':'content','action':'view','url':'fred'}, m.match('/content/view/fred'))
            self.assertEqual({'controller':'admin/user','action':'view','url':None}, m.match('/admin/user'))
            self.assertEqual({'controller':'admin/user','action':'view','url':None}, m.match('/admin/user/view'))
    
    def test_path_with_dynamic_and_default_backwards(self):
        for path in ['*file/login', '*(file)/login']:
            m = Mapper()
            m.connect(path, controller='content', action='download', file=None)
            m.create_regs([])

            self.assertEqual(None, m.match('/boo'))
            self.assertEqual(None, m.match('/boo/blah'))
            self.assertEqual({'controller':'content','action':'download','file':''}, m.match('//login'))
            self.assertEqual({'controller':'content','action':'download','file':'books/learning_python.pdf'}, m.match('/books/learning_python.pdf/login'))
            self.assertEqual({'controller':'content','action':'download','file':'dude'}, m.match('/dude/login'))
            self.assertEqual({'controller':'content','action':'download','file':'dude/what'}, m.match('/dude/what/login'))
        
    def test_path_backwards(self):
        for path in ['*file/login', '*(file)/login']:
            m = Mapper()
            m.connect(path, controller='content', action='download')
            m.create_regs([])
        
            self.assertEqual(None, m.match('/boo'))
            self.assertEqual(None, m.match('/boo/blah'))
            self.assertEqual(None, m.match('/login'))
            self.assertEqual({'controller':'content','action':'download','file':'books/learning_python.pdf'}, m.match('/books/learning_python.pdf/login'))
            self.assertEqual({'controller':'content','action':'download','file':'dude'}, m.match('/dude/login'))
            self.assertEqual({'controller':'content','action':'download','file':'dude/what'}, m.match('/dude/what/login'))
    
    def test_path_backwards_with_controller(self):
        m = Mapper()
        m.connect('*url/login', controller='content', action='check_access')
        m.connect('*url/:controller', action='view')
        m.create_regs(['content', 'admin/user'])

        self.assertEqual(None, m.match('/boo'))
        self.assertEqual(None, m.match('/boo/blah'))
        self.assertEqual(None, m.match('/login'))
        self.assertEqual({'controller':'content','action':'check_access','url':'books/learning_python.pdf'}, m.match('/books/learning_python.pdf/login'))
        self.assertEqual({'controller':'content','action':'check_access','url':'dude'}, m.match('/dude/login'))
        self.assertEqual({'controller':'content','action':'check_access','url':'dude/what'}, m.match('/dude/what/login'))
        
        self.assertEqual(None, m.match('/admin/user'))
        self.assertEqual({'controller':'admin/user','action':'view','url':'books/learning_python.pdf'}, m.match('/books/learning_python.pdf/admin/user'))
        self.assertEqual({'controller':'admin/user','action':'view','url':'dude'}, m.match('/dude/admin/user'))
        self.assertEqual({'controller':'admin/user','action':'view','url':'dude/what'}, m.match('/dude/what/admin/user'))
    
    def test_path_backwards_with_controller_and_splits(self):
        m = Mapper()
        m.connect('*(url)/login', controller='content', action='check_access')
        m.connect('*(url)/:(controller)', action='view')
        m.create_regs(['content', 'admin/user'])

        self.assertEqual(None, m.match('/boo'))
        self.assertEqual(None, m.match('/boo/blah'))
        self.assertEqual(None, m.match('/login'))
        self.assertEqual({'controller':'content','action':'check_access','url':'books/learning_python.pdf'}, m.match('/books/learning_python.pdf/login'))
        self.assertEqual({'controller':'content','action':'check_access','url':'dude'}, m.match('/dude/login'))
        self.assertEqual({'controller':'content','action':'check_access','url':'dude/what'}, m.match('/dude/what/login'))
        
        self.assertEqual(None, m.match('/admin/user'))
        self.assertEqual({'controller':'admin/user','action':'view','url':'books/learning_python.pdf'}, m.match('/books/learning_python.pdf/admin/user'))
        self.assertEqual({'controller':'admin/user','action':'view','url':'dude'}, m.match('/dude/admin/user'))
        self.assertEqual({'controller':'admin/user','action':'view','url':'dude/what'}, m.match('/dude/what/admin/user'))
    
    def test_controller(self):
        m = Mapper()
        m.connect('hi/:controller', action='hi')
        m.create_regs(['content','admin/user'])
        
        self.assertEqual(None, m.match('/boo'))
        self.assertEqual(None, m.match('/boo/blah'))
        self.assertEqual(None, m.match('/hi/13870948'))
        self.assertEqual(None, m.match('/hi/content/dog'))
        self.assertEqual(None, m.match('/hi/admin/user/foo'))
        self.assertEqual(None, m.match('/hi/admin/user/foo/'))
        self.assertEqual({'controller':'content','action':'hi'}, m.match('/hi/content'))
        self.assertEqual({'controller':'admin/user', 'action':'hi'}, m.match('/hi/admin/user'))
    
    def test_standard_route(self):
        m = Mapper()
        m.connect(':controller/:action/:id')
        m.create_regs(['content','admin/user'])
        
        self.assertEqual({'controller':'content','action':'index', 'id': None}, m.match('/content'))
        self.assertEqual({'controller':'content','action':'list', 'id':None}, m.match('/content/list'))
        self.assertEqual({'controller':'content','action':'show','id':'10'}, m.match('/content/show/10'))

        self.assertEqual({'controller':'admin/user','action':'index', 'id': None}, m.match('/admin/user'))
        self.assertEqual({'controller':'admin/user','action':'list', 'id':None}, m.match('/admin/user/list'))
        self.assertEqual({'controller':'admin/user','action':'show','id':'bbangert'}, m.match('/admin/user/show/bbangert'))

        self.assertEqual(None, m.match('/content/show/10/20'))
        self.assertEqual(None, m.match('/food'))
    
    def test_standard_route_with_gaps(self):
        m = Mapper()
        m.connect(':controller/:action/:(id).py')
        m.create_regs(['content','admin/user'])
        
        self.assertEqual({'controller':'content','action':'index', 'id': 'None'}, m.match('/content/index/None.py'))
        self.assertEqual({'controller':'content','action':'list', 'id':'None'}, m.match('/content/list/None.py'))
        self.assertEqual({'controller':'content','action':'show','id':'10'}, m.match('/content/show/10.py'))

    def test_standard_route_with_gaps_and_domains(self):
        m = Mapper()
        m.connect('manage/:domain.:ext', controller='admin/user', action='view', ext='html')
        m.connect(':controller/:action/:id')
        m.create_regs(['content','admin/user'])
        
        self.assertEqual({'controller':'content','action':'index', 'id': 'None.py'}, m.match('/content/index/None.py'))
        self.assertEqual({'controller':'content','action':'list', 'id':'None.py'}, m.match('/content/list/None.py'))
        self.assertEqual({'controller':'content','action':'show','id':'10.py'}, m.match('/content/show/10.py'))
        self.assertEqual({'controller':'content','action':'show.all','id':'10.py'}, m.match('/content/show.all/10.py'))
        self.assertEqual({'controller':'content','action':'show','id':'www.groovie.org'}, m.match('/content/show/www.groovie.org'))
        
        self.assertEqual({'controller':'admin/user','action':'view', 'ext': 'html', 'domain': 'groovie'}, m.match('/manage/groovie'))
        self.assertEqual({'controller':'admin/user','action':'view', 'ext': 'xml', 'domain': 'groovie'}, m.match('/manage/groovie.xml'))
    
    def test_standard_with_domains(self):
        m = Mapper()
        m.connect('manage/:domain', controller='domains', action='view')
        m.create_regs(['domains'])
        
        self.assertEqual({'controller':'domains','action':'view','domain':'www.groovie.org'}, m.match('/manage/www.groovie.org'))
    
    def test_default_route(self):
        m = Mapper()
        m.connect('',controller='content',action='index')
        m.create_regs(['content'])
        
        self.assertEqual(None, m.match('/x'))
        self.assertEqual(None, m.match('/hello/world'))
        self.assertEqual(None, m.match('/hello/world/how/are'))
        self.assertEqual(None, m.match('/hello/world/how/are/you/today'))
        
        self.assertEqual({'controller':'content','action':'index'}, m.match('/'))

    def test_dynamic_with_prefix(self):
        m = Mapper()
        m.prefix = '/blog'
        m.connect(':controller/:action/:id')
        m.connect('', controller='content', action='index')
        m.create_regs(['content', 'archive', 'admin/comments'])

        self.assertEqual(None, m.match('/x'))
        self.assertEqual(None, m.match('/admin/comments'))
        self.assertEqual(None, m.match('/content/view'))
        self.assertEqual(None, m.match('/archive/view/4'))
        
        self.assertEqual({'controller':'content','action':'index'}, m.match('/blog'))
        self.assertEqual({'controller':'content','action':'index','id':None}, m.match('/blog/content'))
        self.assertEqual({'controller':'admin/comments','action':'view','id':None}, m.match('/blog/admin/comments/view'))
        self.assertEqual({'controller':'archive','action':'index','id':None}, m.match('/blog/archive'))
        self.assertEqual({'controller':'archive','action':'view', 'id':'4'}, m.match('/blog/archive/view/4'))
    
    def test_dynamic_with_multiple_and_prefix(self):
        m = Mapper()
        m.prefix = '/blog'
        m.connect(':controller/:action/:id')
        m.connect('home/:action', controller='archive')
        m.connect('', controller='content')
        m.create_regs(['content', 'archive', 'admin/comments'])

        self.assertEqual(None, m.match('/x'))
        self.assertEqual(None, m.match('/admin/comments'))
        self.assertEqual(None, m.match('/content/view'))
        self.assertEqual(None, m.match('/archive/view/4'))
        
        self.assertEqual({'controller':'content', 'action':'index'}, m.match('/blog/'))
        self.assertEqual({'controller':'archive', 'action':'view'}, m.match('/blog/home/view'))
        self.assertEqual({'controller':'content','action':'index','id':None}, m.match('/blog/content'))
        self.assertEqual({'controller':'admin/comments','action':'view','id':None}, m.match('/blog/admin/comments/view'))
        self.assertEqual({'controller':'archive','action':'index','id':None}, m.match('/blog/archive'))
        self.assertEqual({'controller':'archive','action':'view', 'id':'4'}, m.match('/blog/archive/view/4'))
        
    
    def test_splits_with_extension(self):
        m = Mapper()
        m.connect('hi/:(action).html', controller='content')
        m.create_regs([])

        self.assertEqual(None, m.match('/boo'))
        self.assertEqual(None, m.match('/boo/blah'))
        self.assertEqual(None, m.match('/hi/dude/what'))
        self.assertEqual(None, m.match('/hi'))
        self.assertEqual({'controller':'content','action':'index'}, m.match('/hi/index.html'))
        self.assertEqual({'controller':'content','action':'dude'}, m.match('/hi/dude.html'))
    
    def test_splits_with_dashes(self):
        m = Mapper()
        m.connect('archives/:(year)-:(month)-:(day).html', controller='archives', action='view')
        m.create_regs([])
        
        self.assertEqual(None, m.match('/boo'))
        self.assertEqual(None, m.match('/archives'))
        
        self.assertEqual({'controller':'archives','action':'view','year':'2004','month':'12','day':'4'},
                         m.match('/archives/2004-12-4.html'))
        self.assertEqual({'controller':'archives','action':'view','year':'04','month':'10','day':'4'},
                         m.match('/archives/04-10-4.html'))
        self.assertEqual({'controller':'archives','action':'view','year':'04','month':'1','day':'1'},
                         m.match('/archives/04-1-1.html'))
    
    def test_splits_packed_with_regexps(self):
        m = Mapper()
        m.connect('archives/:(year):(month):(day).html', controller='archives', action='view',
               requirements=dict(year=r'\d{4}',month=r'\d{2}',day=r'\d{2}'))
        m.create_regs([])

        self.assertEqual(None, m.match('/boo'))
        self.assertEqual(None, m.match('/archives'))
        self.assertEqual(None, m.match('/archives/2004020.html'))
        self.assertEqual(None, m.match('/archives/200502.html'))

        self.assertEqual({'controller':'archives','action':'view','year':'2004','month':'12','day':'04'},
                      m.match('/archives/20041204.html'))
        self.assertEqual({'controller':'archives','action':'view','year':'2005','month':'10','day':'04'},
                      m.match('/archives/20051004.html'))
        self.assertEqual({'controller':'archives','action':'view','year':'2006','month':'01','day':'01'},
                      m.match('/archives/20060101.html'))

    def test_splits_with_slashes(self):
        m = Mapper()
        m.connect(':name/:(action)-:(day)', controller='content')
        m.create_regs([])
        
        self.assertEqual(None, m.match('/something'))
        self.assertEqual(None, m.match('/something/is-'))
        
        self.assertEqual({'controller':'content','action':'view','day':'3','name':'group'},
                         m.match('/group/view-3'))
        self.assertEqual({'controller':'content','action':'view','day':'5','name':'group'},
                         m.match('/group/view-5'))
    
    def test_splits_with_slashes_and_default(self):
        m = Mapper()
        m.connect(':name/:(action)-:(id)', controller='content')
        m.create_regs([])
        
        self.assertEqual(None, m.match('/something'))
        self.assertEqual(None, m.match('/something/is'))
        
        self.assertEqual({'controller':'content','action':'view','id':'3','name':'group'},
                         m.match('/group/view-3'))
        self.assertEqual({'controller':'content','action':'view','id':None,'name':'group'},
                         m.match('/group/view-'))
    
    def test_no_reg_make(self):
        m = Mapper()
        m.connect(':name/:(action)-:(id)', controller='content')
        m.controller_scan = False
        def call_func():
            m.match('/group/view-3')
        self.assertRaises(RouteException, call_func)        
    
    def test_routematch(self):
        m = Mapper()
        m.connect(':controller/:action/:id')
        m.create_regs(['content'])
        route = m.matchlist[0]
        
        resultdict, route_obj = m.routematch('/content')
        assert {'action':'index', 'controller':'content','id':None} == resultdict
        assert route == route_obj
        assert None == m.routematch('/nowhere')
    
    def test_routematch_debug(self):
        m = Mapper()
        m.connect(':controller/:action/:id')
        m.debug = True
        m.create_regs(['content'])
        route = m.matchlist[0]
        
        resultdict, route_obj, debug = m.routematch('/content')
        assert {'action':'index', 'controller':'content','id':None} == resultdict
        assert route == route_obj
        resultdict, route_obj, debug = m.routematch('/nowhere')
        assert resultdict is None
        assert route_obj is None
        assert len(debug) == 1
    
    def test_match_debug(self):
        m = Mapper()
        m.connect('nowhere', 'http://nowhere.com/', _static=True)
        m.connect(':controller/:action/:id')
        m.debug = True
        m.create_regs(['content'])
        route = m.matchlist[1]
        
        resultdict, route_obj, debug = m.match('/content')
        assert {'action':'index', 'controller':'content','id':None} == resultdict
        assert route == route_obj
        resultdict, route_obj, debug = m.match('/nowhere')
        assert resultdict is None
        assert route_obj is None
        assert len(debug) == 2
    
    def test_conditions(self):
        m = Mapper()
        m.connect('home/upload', controller='content', action='upload', conditions=dict(method=['POST']))
        m.connect(':controller/:action/:id')
        m.create_regs(['content', 'blog'])
        
        con = request_config()
        con.mapper = m
        env = dict(PATH_INFO='/nowhere', HTTP_HOST='example.com', REQUEST_METHOD='GET')
        con.mapper_dict = {}
        con.environ = env
        assert None == con.mapper_dict
        
        env['PATH_INFO'] = '/content'
        con.environ = env
        assert {'action':'index','controller':'content','id':None} == con.mapper_dict
        
        env['PATH_INFO'] = '/home/upload'
        con.environ = env
        assert None == con.mapper_dict
        
        env['REQUEST_METHOD'] = 'POST'
        con.environ = env
        assert {'action':'upload','controller':'content'} == con.mapper_dict
        
    def test_subdomains(self):
        m = Mapper()
        m.sub_domains = True
        m.connect(':controller/:action/:id')
        m.create_regs(['content', 'blog'])
        
        con = request_config()
        con.mapper = m
        env = dict(PATH_INFO='/nowhere', HTTP_HOST='example.com')
        con.mapper_dict = {}
        con.environ = env
        
        self.assertEqual(None, con.mapper_dict)
        
        env['PATH_INFO'] = '/content'
        con.environ = env
        self.assertEqual({'action': 'index', 'controller': 'content', 'sub_domain': None, 'id': None},
            con.mapper_dict)
        
        env['HTTP_HOST'] = 'fred.example.com'
        con.environ = env
        self.assertEqual({'action': 'index', 'controller': 'content', 'sub_domain': 'fred', 'id': None},
            con.mapper_dict)
        
        env['HTTP_HOST'] = 'www.example.com'
        con.environ = env
        self.assertEqual({'action': 'index', 'controller': 'content', 'sub_domain': 'www', 'id': None},
            con.mapper_dict)
    
    def test_subdomains_with_conditions(self):
        m = Mapper()
        m.sub_domains = True
        m.connect(':controller/:action/:id')
        m.create_regs(['content', 'blog'])
        
        con = request_config()
        con.mapper = m
        env = dict(PATH_INFO='/nowhere', HTTP_HOST='example.com')
        con.mapper_dict = {}
        con.environ = env
        
        self.assertEqual(None, con.mapper_dict)
        
        env['PATH_INFO'] = '/content'
        con.environ = env
        self.assertEqual({'action': 'index', 'controller': 'content', 'sub_domain': None, 'id': None},
            con.mapper_dict)
        
        m.connect('', controller='users', action='home', conditions={'sub_domain':True})
        m.create_regs(['content', 'users', 'blog'])
        env['PATH_INFO'] = '/'
        con.environ = env
        assert None == con.mapper_dict
        
        env['HTTP_HOST'] = 'fred.example.com'
        con.environ = env
        print con.mapper_dict
        assert {'action': 'home', 'controller': 'users', 'sub_domain': 'fred'} == con.mapper_dict
        
        m.sub_domains_ignore = ['www']
        env['HTTP_HOST'] = 'www.example.com'
        con.environ = env
        print con.mapper_dict
        assert None == con.mapper_dict
    
    def test_subdomains_with_ignore(self):
        m = Mapper()
        m.sub_domains = True
        m.sub_domains_ignore = ['www']
        m.connect(':controller/:action/:id')
        m.create_regs(['content', 'blog'])
        
        con = request_config()
        con.mapper = m
        env = dict(PATH_INFO='/nowhere', HTTP_HOST='example.com')
        con.mapper_dict = {}
        con.environ = env
        
        self.assertEqual(None, con.mapper_dict)
        
        env['PATH_INFO'] = '/content'
        con.environ = env
        self.assertEqual({'action': 'index', 'controller': 'content', 'sub_domain': None, 'id': None},
            con.mapper_dict)
        
        env['HTTP_HOST'] = 'fred.example.com'
        con.environ = env
        self.assertEqual({'action': 'index', 'controller': 'content', 'sub_domain': 'fred', 'id': None},
            con.mapper_dict)
        
        env['HTTP_HOST'] = 'www.example.com'
        con.environ = env
        self.assertEqual({'action': 'index', 'controller': 'content', 'sub_domain': None, 'id': None},
            con.mapper_dict)
    
    def test_resource(self):
        m = Mapper()
        m.resource('person', 'people')
        m.create_regs(['people'])
        
        con = request_config()
        con.mapper = m
        def test_path(path, method):
            env = dict(HTTP_HOST='example.com', PATH_INFO=path, REQUEST_METHOD=method)
            con.mapper_dict = {}
            con.environ = env
        
        test_path('/people', 'GET')
        assert {'controller':'people', 'action':'index'} == con.mapper_dict
        
        test_path('/people', 'POST')
        assert {'controller':'people', 'action':'create'} == con.mapper_dict
        
        test_path('/people/2', 'GET')
        assert {'controller':'people', 'action':'show', 'id':'2'} == con.mapper_dict
        test_path('/people/2/edit', 'GET')
        assert {'controller':'people', 'action':'edit', 'id':'2'} == con.mapper_dict

        test_path('/people/2', 'DELETE')
        assert {'controller':'people', 'action':'delete', 'id':'2'} == con.mapper_dict

        test_path('/people/2', 'PUT')
        assert {'controller':'people', 'action':'update', 'id':'2'} == con.mapper_dict        

    def test_resource_with_nomin(self):
        m = Mapper()
        m.minimization = False
        m.resource('person', 'people')
        m.create_regs(['people'])
        
        con = request_config()
        con.mapper = m
        def test_path(path, method):
            env = dict(HTTP_HOST='example.com', PATH_INFO=path, REQUEST_METHOD=method)
            con.mapper_dict = {}
            con.environ = env
        
        test_path('/people', 'GET')
        eq_({'controller':'people', 'action':'index'}, con.mapper_dict)
        
        test_path('/people', 'POST')
        assert {'controller':'people', 'action':'create'} == con.mapper_dict
        
        test_path('/people/2', 'GET')
        assert {'controller':'people', 'action':'show', 'id':'2'} == con.mapper_dict
        test_path('/people/2/edit', 'GET')
        assert {'controller':'people', 'action':'edit', 'id':'2'} == con.mapper_dict

        test_path('/people/2', 'DELETE')
        assert {'controller':'people', 'action':'delete', 'id':'2'} == con.mapper_dict

        test_path('/people/2', 'PUT')
        assert {'controller':'people', 'action':'update', 'id':'2'} == con.mapper_dict        

    def test_resource_created_with_parent_resource(self): 
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'))
        m.create_regs(['locations'])
        
        con = request_config()
        con.mapper = m
        def test_path(path, method):
            env = dict(HTTP_HOST='example.com', PATH_INFO=path,
                       REQUEST_METHOD=method)
            con.mapper_dict = {}
            con.environ = env
        
        test_path('/regions/13/locations', 'GET')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations',
                                   'action': 'index'}
        url = url_for('region_locations', region_id=13)
        assert url == '/regions/13/locations'
        
        test_path('/regions/13/locations', 'POST')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations',
                                   'action': 'create'}
        # new
        url = url_for('region_new_location', region_id=13)
        assert url == '/regions/13/locations/new'
        # create
        url = url_for('region_locations', region_id=13)
        assert url == '/regions/13/locations'
        
        test_path('/regions/13/locations/60', 'GET')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations',
                                   'id': '60', 'action': 'show'}
        url = url_for('region_location', region_id=13, id=60)
        assert url == '/regions/13/locations/60'
        
        test_path('/regions/13/locations/60/edit', 'GET')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations',
                                   'id': '60', 'action': 'edit'}
        url = url_for('region_edit_location', region_id=13, id=60)
        assert url == '/regions/13/locations/60/edit'
        
        test_path('/regions/13/locations/60', 'DELETE')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations',
                                   'id': '60', 'action': 'delete'}
        url = url_for('region_location', region_id=13, id=60)
        assert url == '/regions/13/locations/60'
        
        test_path('/regions/13/locations/60', 'PUT')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations',
                                   'id': '60', 'action': 'update'}
        url = url_for('region_location', region_id=13, id=60)
        assert url == '/regions/13/locations/60'
    
        # Make sure ``path_prefix`` overrides work
        # empty ``path_prefix`` (though I'm not sure why someone would do this)
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='')
        url = url_for('region_locations')
        assert url == '/locations'
        # different ``path_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='areas/:area_id')
        url = url_for('region_locations', area_id=51)
        assert url == '/areas/51/locations'

        # Make sure ``name_prefix`` overrides work
        # empty ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   name_prefix='')
        url = url_for('locations', region_id=51)
        assert url == '/regions/51/locations'
        # different ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   name_prefix='area_')
        url = url_for('area_locations', region_id=51)
        assert url == '/regions/51/locations'

        # Make sure ``path_prefix`` and ``name_prefix`` overrides work together
        # empty ``path_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='',
                   name_prefix='place_')
        url = url_for('place_locations')
        assert url == '/locations'
        # empty ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='areas/:area_id',
                   name_prefix='')
        url = url_for('locations', area_id=51)
        assert url == '/areas/51/locations'
        # different ``path_prefix`` and ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='areas/:area_id',
                   name_prefix='place_')
        url = url_for('place_locations', area_id=51)
        assert url == '/areas/51/locations'

    def test_resource_created_with_parent_resource_nomin(self): 
        m = Mapper()
        m.minimization = False
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'))
        m.create_regs(['locations'])
        
        con = request_config()
        con.mapper = m
        def test_path(path, method):
            env = dict(HTTP_HOST='example.com', PATH_INFO=path,
                       REQUEST_METHOD=method)
            con.mapper_dict = {}
            con.environ = env
        
        test_path('/regions/13/locations', 'GET')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations',
                                   'action': 'index'}
        url = url_for('region_locations', region_id=13)
        assert url == '/regions/13/locations'
        
        test_path('/regions/13/locations', 'POST')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations',
                                   'action': 'create'}
        # new
        url = url_for('region_new_location', region_id=13)
        assert url == '/regions/13/locations/new'
        # create
        url = url_for('region_locations', region_id=13)
        assert url == '/regions/13/locations'
        
        test_path('/regions/13/locations/60', 'GET')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations',
                                   'id': '60', 'action': 'show'}
        url = url_for('region_location', region_id=13, id=60)
        assert url == '/regions/13/locations/60'
        
        test_path('/regions/13/locations/60/edit', 'GET')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations',
                                   'id': '60', 'action': 'edit'}
        url = url_for('region_edit_location', region_id=13, id=60)
        assert url == '/regions/13/locations/60/edit'
        
        test_path('/regions/13/locations/60', 'DELETE')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations',
                                   'id': '60', 'action': 'delete'}
        url = url_for('region_location', region_id=13, id=60)
        assert url == '/regions/13/locations/60'
        
        test_path('/regions/13/locations/60', 'PUT')
        assert con.mapper_dict == {'region_id': '13', 'controller': 'locations',
                                   'id': '60', 'action': 'update'}
        url = url_for('region_location', region_id=13, id=60)
        assert url == '/regions/13/locations/60'
    
        # Make sure ``path_prefix`` overrides work
        # empty ``path_prefix`` (though I'm not sure why someone would do this)
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='/')
        url = url_for('region_locations')
        assert url == '/locations'
        # different ``path_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='areas/:area_id')
        url = url_for('region_locations', area_id=51)
        assert url == '/areas/51/locations'

        # Make sure ``name_prefix`` overrides work
        # empty ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   name_prefix='')
        url = url_for('locations', region_id=51)
        assert url == '/regions/51/locations'
        # different ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   name_prefix='area_')
        url = url_for('area_locations', region_id=51)
        assert url == '/regions/51/locations'

        # Make sure ``path_prefix`` and ``name_prefix`` overrides work together
        # empty ``path_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='',
                   name_prefix='place_')
        url = url_for('place_locations')
        assert url == '/locations'
        # empty ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='areas/:area_id',
                   name_prefix='')
        url = url_for('locations', area_id=51)
        assert url == '/areas/51/locations'
        # different ``path_prefix`` and ``name_prefix``
        m = Mapper()
        m.resource('location', 'locations',
                   parent_resource=dict(member_name='region',
                                        collection_name='regions'),
                   path_prefix='areas/:area_id',
                   name_prefix='place_')
        url = url_for('place_locations', area_id=51)
        assert url == '/areas/51/locations'


    def test_other_special_chars(self):
        m = Mapper()
        m.connect('/:year/:(slug).:(format),:(locale)', format='html', locale='en')
        m.connect('/error/:action/:id', controller='error')
        m.create_regs(['content'])

        self.assertEqual({'year': '2007', 'slug': 'test', 'locale': 'en', 'format': 'html',
                          'controller': 'content', 'action': 'index'},
                         m.match('/2007/test'))
        self.assertEqual({'year': '2007', 'slug': 'test', 'format': 'html', 'locale': 'en',
                          'controller': 'content', 'action': 'index'},
                         m.match('/2007/test.html'))
        self.assertEqual({'year': '2007', 'slug': 'test',
                          'format': 'html', 'locale': 'en',
                          'controller': 'content', 'action': 'index'},
                         m.match('/2007/test.html,en'))
        self.assertEqual(None, m.match('/2007/test.'))
        self.assertEqual({'controller': 'error', 'action': 'img',
                          'id': 'icon-16.png'}, m.match('/error/img/icon-16.png'))
    
    def test_various_periods(self):
        m = Mapper()
        m.connect('sites/:site/pages/:page')
        m.create_regs(['content'])
        
        self.assertEqual({'action': u'index', 'controller': u'content', 
                          'site': u'python.com', 'page': u'index.html'}, 
                         m.match('/sites/python.com/pages/index.html'))
        m = Mapper()
        m.connect('sites/:site/pages/:page.:format', format='html')
        m.create_regs(['content'])
        
        self.assertEqual({'action': u'index', 'controller': u'content', 
                          'site': u'python.com', 'page': u'index', 'format': u'html'}, 
                         m.match('/sites/python.com/pages/index.html'))
        
    def test_empty_fails(self):
        m = Mapper()
        m.connect(':controller/:action/:id')
        m.connect('', controller='content', action='view', id=4)
        m.create_regs(['content'])
        
        assert {'controller':'content','action':'index','id':None} == m.match('/content')
        assert {'controller':'content','action':'view','id':'4'} == m.match('/')
        def call_func():
            m.match('')
        self.assertRaises(RouteException, call_func)
        
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
            a = m.match('/content')
            a = m.match('/content/list')
            a = m.match('/content/show/10')

            a = m.match('/admin/user')
            a = m.match('/admin/user/list')
            a = m.match('/admin/user/show/bbangert')

            a = m.match('/admin/user/show/bbangert/dude')
            a = m.match('/admin/why/show/bbangert')
            a = m.match('/content/show/10/20')
            a = m.match('/food')
        end = time.time()
        ts = time.time()
        for x in range(1,n):
            pass
        en = time.time()
        total = end-start-(en-ts)
        per_url = total / (n*10)
        print "Recognition\n"
        print "%s ms/url" % (per_url*1000)
        print "%s urls/s\n" % (1.00/per_url)
    
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