#
#  test_recognition
#
#  Created by Ben Bangert on 2005-08-08.
#  Copyright (c) 2005 Parachute. All rights reserved.
#

import sys
import routes
from routes import Mapper
import unittest

class TestRecognition(unittest.TestCase):

    def test_all_static(self):
        m = Mapper()
        m.connect('/hello/world/how/are/you', controller='content', action='index')
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
        self.assertEqual({'controller':'content','name':'dude'}, m.match('/hi/dude'))
    
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
        self.assertEqual({'controller':'content','name':'index'}, m.match('/hi/index'))
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
        self.assertEqual({'controller':'content','name':'index'}, m.match('/hi/index'))
        self.assertEqual({'controller':'content','name':'dude'}, m.match('/hi/dude'))
    
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