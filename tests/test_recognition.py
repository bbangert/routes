#
#  test_recognition
#
#  Created by Ben Bangert on 2005-08-08.
#  Copyright (c) 2005 Parachute. All rights reserved.
#

import sys
import routes
from routes.base import Mapper
import unittest

class TestRecognition(unittest.TestCase):

    def test_all_static(self):
        m = Mapper()
        m.connect('hello/world/how/are/you', controller='content', action='index')
        m.create_regs([])
        
        self.assertEqual(None, m.match('/x'))
        self.assertEqual(None, m.match('/hello/world/how'))
        self.assertEqual(None, m.match('/hello/world/how/are'))
        self.assertEqual(None, m.match('/hello/world/how/are/you/today'))
        self.assertEqual({'controller':'content','action':'index'}, m.match('/hello/world/how/are/you'))
    
    def test_basic_dynamic(self):
        m = Mapper()
        m.connect('hi/:name', controller='content')
        m.create_regs([])
        
        self.assertEqual(None, m.match('/boo'))
        self.assertEqual(None, m.match('/boo/blah'))
        self.assertEqual(None, m.match('/hi'))
        self.assertEqual(None, m.match('/hi/dude/what'))
        self.assertEqual({'controller':'content','name':'dude','action':'index'}, m.match('/hi/dude'))
    
    def test_dynamic_with_default(self):
        m = Mapper()
        m.connect('hi/:action', controller='content')
        m.create_regs([])
        
        self.assertEqual(None, m.match('/boo'))
        self.assertEqual(None, m.match('/boo/blah'))
        self.assertEqual(None, m.match('/hi/dude/what'))
        self.assertEqual({'controller':'content','action':'index'}, m.match('/hi'))
        self.assertEqual({'controller':'content','action':'index'}, m.match('/hi/index'))
        self.assertEqual({'controller':'content','action':'dude'}, m.match('/hi/dude'))
    
    def test_dynamic_with_string_condition(self):
        m = Mapper()
        m.connect('hi/:name', controller='content', requirements={'name':'index'})
        m.create_regs([])
        
        self.assertEqual(None, m.match('/boo'))
        self.assertEqual(None, m.match('/boo/blah'))
        self.assertEqual(None, m.match('/hi'))
        self.assertEqual(None, m.match('/hi/dude/what'))
        self.assertEqual({'controller':'content','name':'index','action':'index'}, m.match('/hi/index'))
        self.assertEqual(None, m.match('/hi/dude'))
    
    def test_dynamic_with_regexp_condition(self):
        m = Mapper()
        m.connect('hi/:name', controller='content', requirements={'name':'[a-z]+'})
        m.create_regs([])
        
        self.assertEqual(None, m.match('/boo'))
        self.assertEqual(None, m.match('/boo/blah'))
        self.assertEqual(None, m.match('/hi'))
        self.assertEqual(None, m.match('/hi/FOXY'))
        self.assertEqual(None, m.match('/hi/138708jkhdf'))
        self.assertEqual(None, m.match('/hi/dkjfl8792343dfsf'))
        self.assertEqual(None, m.match('/hi/dude/what'))
        self.assertEqual({'controller':'content','name':'index','action':'index'}, m.match('/hi/index'))
        self.assertEqual({'controller':'content','name':'dude','action':'index'}, m.match('/hi/dude'))
    
    def test_dynamic_with_regexp_and_default(self):
        m = Mapper()
        m.connect('hi/:action', controller='content', requirements={'action':'[a-z]+'})
        m.create_regs([])
        
        self.assertEqual(None, m.match('/boo'))
        self.assertEqual(None, m.match('/boo/blah'))
        self.assertEqual(None, m.match('/hi/FOXY'))
        self.assertEqual(None, m.match('/hi/138708jkhdf'))
        self.assertEqual(None, m.match('/hi/dkjfl8792343dfsf'))
        self.assertEqual(None, m.match('/hi/dude/what'))
        self.assertEqual({'controller':'content','action':'index'}, m.match('/hi'))
        self.assertEqual({'controller':'content','action':'index'}, m.match('/hi/index'))
        self.assertEqual({'controller':'content','action':'dude'}, m.match('/hi/dude'))
    
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
        self.assertEqual({'controller':'blog','action':'view','month':None,'day':None,'year':'2004'}, m.match('/archive/2004'))
        
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

    def test_dynamic_with_regexp_gaps_controllers(self):
        m = Mapper()
        m.connect('view/:id/:controller', id=2, action='view', requirements={'id':'\d{1,2}'})
        m.create_regs(['post','blog','admin/user'])
        
        self.assertEqual(None, m.match('/'))
        self.assertEqual(None, m.match('/view'))
        self.assertEqual(None, m.match('/view/blog'))
        self.assertEqual(None, m.match('/view/3'))
        self.assertEqual(None, m.match('/view/4/honker'))
        self.assertEqual({'controller':'blog','action':'view','id':'2'}, m.match('/view/2/blog'))
    
    def test_dynamic_with_trailing_strings(self):
        m = Mapper()
        m.connect('view/:id/:controller/super', controller='blog', id=2, action='view', requirements={'id':'\d{1,2}'})
        m.create_regs(['post','blog','admin/user'])
        
        self.assertEqual(None, m.match('/'))
        self.assertEqual(None, m.match('/view'))
        self.assertEqual(None, m.match('/view/blah/blog/super'))
        self.assertEqual(None, m.match('/view/3/super'))
        self.assertEqual(None, m.match('/view/super'))
        self.assertEqual({'controller':'blog','action':'view','id':'2'}, m.match('/view/2/blog/super'))
        self.assertEqual({'controller':'admin/user','action':'view','id':'4'}, m.match('/view/4/admin/user/super'))
    
    def test_path(self):
        m = Mapper()
        m.connect('hi/*file', controller='content', action='download')
        m.create_regs([])
        
        self.assertEqual(None, m.match('/boo'))
        self.assertEqual(None, m.match('/boo/blah'))
        self.assertEqual({'controller':'content','action':'download','file':None}, m.match('/hi'))
        self.assertEqual({'controller':'content','action':'download','file':'books/learning_python.pdf'}, m.match('/hi/books/learning_python.pdf'))
        self.assertEqual({'controller':'content','action':'download','file':'dude'}, m.match('/hi/dude'))
        self.assertEqual({'controller':'content','action':'download','file':'dude/what'}, m.match('/hi/dude/what'))
    
    def test_path_with_dynamic(self):
        m = Mapper()
        m.connect(':controller/:action/*url')
        m.create_regs(['content','admin/user'])
        
        self.assertEqual(None, m.match('/'))
        self.assertEqual(None, m.match('/blog'))
        self.assertEqual({'controller':'content','action':'index','url':None}, m.match('/content'))
        self.assertEqual({'controller':'content','action':'view','url':None}, m.match('/content/view'))
        self.assertEqual({'controller':'content','action':'view','url':'blob'}, m.match('/content/view/blob'))
        self.assertEqual({'controller':'admin/user','action':'index','url':None}, m.match('/admin/user'))
        self.assertEqual({'controller':'admin/user','action':'view','url':None}, m.match('/admin/user/view'))
        self.assertEqual({'controller':'admin/user','action':'view','url':'blob/check'}, m.match('/admin/user/view/blob/check'))
    
    def test_dynamic_with_default_and_string_condition_backwards(self):
        m = Mapper()
        m.connect(':action/hi')
        m.create_regs([])
        
        self.assertEqual(None, m.match('/'))
        self.assertEqual(None, m.match('/boo'))
        self.assertEqual(None, m.match('/boo/blah'))
        self.assertEqual({'action':'index'}, m.match('/index/hi'))
        self.assertEqual({'action':'index'}, m.match('/index/hi'))
    
    def test_path_with_dyanmic_and_default(self):
        m = Mapper()
        m.connect(':controller/:action/*url', controller='content', action='view')
        m.create_regs(['content','admin/user'])
        
        self.assertEqual({'controller':'content','action':'view','url':''}, m.match('/'))
        self.assertEqual({'controller':'content','action':'view','url':None}, m.match('/content'))
        self.assertEqual({'controller':'content','action':'view','url':None}, m.match('/content/view'))
        self.assertEqual({'controller':'content','action':'goober','url':'view/here'}, m.match('/goober/view/here'))
        self.assertEqual({'controller':'admin/user','action':'view','url':None}, m.match('/admin/user'))
        self.assertEqual({'controller':'admin/user','action':'view','url':None}, m.match('/admin/user/view'))
    
    def test_path_backwards(self):
        m = Mapper()
        m.connect('*file/login', controller='content', action='download')
        m.create_regs([])
        
        self.assertEqual(None, m.match('/boo'))
        self.assertEqual(None, m.match('/boo/blah'))
        self.assertEqual({'controller':'content','action':'download','file':None}, m.match('/login'))
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
        self.assertEqual({'controller':'content','action':'check_access','url':None}, m.match('/login'))
        self.assertEqual({'controller':'content','action':'check_access','url':'books/learning_python.pdf'}, m.match('/books/learning_python.pdf/login'))
        self.assertEqual({'controller':'content','action':'check_access','url':'dude'}, m.match('/dude/login'))
        self.assertEqual({'controller':'content','action':'check_access','url':'dude/what'}, m.match('/dude/what/login'))
        
        self.assertEqual({'controller':'admin/user','action':'view','url':None}, m.match('/admin/user'))
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
    
    def test_default_route(self):
        m = Mapper()
        m.connect('',controller='content',action='index')
        m.create_regs(['content'])
        
        self.assertEqual(None, m.match('/x'))
        self.assertEqual(None, m.match('/hello/world'))
        self.assertEqual(None, m.match('/hello/world/how/are'))
        self.assertEqual(None, m.match('/hello/world/how/are/you/today'))
        
        self.assertEqual({'controller':'content','action':'index'}, m.match('/'))
    

if __name__ == '__main__':
    unittest.main()