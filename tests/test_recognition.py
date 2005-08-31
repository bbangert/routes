"""
test_recognition

(c) Copyright 2005 Ben Bangert, Parachute
[See end of file]
"""

import sys, time, unittest
import routes
from routes.base import Mapper

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
    
    def test_basic_dynamic_backwards(self):
        m = Mapper()
        m.connect(':name/hi')
        m.create_regs([])

        self.assertEqual(None, m.match('/'))
        self.assertEqual(None, m.match('/hi'))
        self.assertEqual(None, m.match('/boo'))
        self.assertEqual(None, m.match('/boo/blah'))
        self.assertEqual(None, m.match('/shop/wallmart/hi'))
        self.assertEqual({'name':'fred', 'action':'index', 'controller':'content'}, m.match('/fred/hi'))
        self.assertEqual({'name':'index', 'action':'index', 'controller':'content'}, m.match('/index/hi'))
    
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
    
    def test_dynamic_with_default_backwards(self):
        m = Mapper()
        m.connect(':action/hi', controller='content')
        m.create_regs([])

        self.assertEqual(None, m.match('/'))
        self.assertEqual(None, m.match('/boo'))
        self.assertEqual(None, m.match('/boo/blah'))
        self.assertEqual(None, m.match('/hi'))
        self.assertEqual({'controller':'content','action':'index'}, m.match('/index/hi'))
        self.assertEqual({'controller':'content','action':'dude'}, m.match('/dude/hi'))
    
    def test_dynamic_with_string_condition(self):
        m = Mapper()
        m.connect(':name/hi', controller='content', requirements={'name':'index'})
        m.create_regs([])
        
        self.assertEqual(None, m.match('/boo'))
        self.assertEqual(None, m.match('/boo/blah'))
        self.assertEqual(None, m.match('/hi'))
        self.assertEqual(None, m.match('/dude/what/hi'))
        self.assertEqual({'controller':'content','name':'index','action':'index'}, m.match('/index/hi'))
        self.assertEqual(None, m.match('/dude/hi'))
    
    def test_dynamic_with_string_condition_backwards(self):
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
    
    def test_dynamic_with_default_and_string_condition_backwards(self):
        m = Mapper()
        m.connect(':action/hi')
        m.create_regs([])

        self.assertEqual(None, m.match('/'))
        self.assertEqual(None, m.match('/boo'))
        self.assertEqual(None, m.match('/boo/blah'))
        self.assertEqual(None, m.match('/hi'))
        self.assertEqual({'action':'index', 'controller':'content'}, m.match('/index/hi'))

    def test_dynamic_and_controller_with_string_and_default_backwards(self):
        m = Mapper()
        m.connect(':controller/:action/hi', controller='content')
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
        self.assertEqual(None, m.match('/view/ha/super'))
        self.assertEqual(None, m.match('/view/super'))
        self.assertEqual(None, m.match('/view/4/super'))
        self.assertEqual({'controller':'blog','action':'view','id':'2'}, m.match('/view/2/blog/super'))
        self.assertEqual({'controller':'admin/user','action':'view','id':'4'}, m.match('/view/4/admin/user/super'))
    
    def test_path(self):
        m = Mapper()
        m.connect('hi/*file', controller='content', action='download')
        m.create_regs([])
        
        self.assertEqual(None, m.match('/boo'))
        self.assertEqual(None, m.match('/boo/blah'))
        self.assertEqual(None, m.match('/hi'))
        self.assertEqual({'controller':'content','action':'download','file':'books/learning_python.pdf'}, m.match('/hi/books/learning_python.pdf'))
        self.assertEqual({'controller':'content','action':'download','file':'dude'}, m.match('/hi/dude'))
        self.assertEqual({'controller':'content','action':'download','file':'dude/what'}, m.match('/hi/dude/what'))
    
    def test_path_with_dynamic(self):
        m = Mapper()
        m.connect(':controller/:action/*url')
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
        m = Mapper()
        m.connect(':controller/:action/*url', controller='content', action='view', url=None)
        m.create_regs(['content','admin/user'])
        
        self.assertEqual({'controller':'content','action':'view','url':''}, m.match('/'))
        self.assertEqual({'controller':'content','action':'view','url':None}, m.match('/content'))
        self.assertEqual({'controller':'content','action':'view','url':None}, m.match('/content/view'))
        self.assertEqual({'controller':'content','action':'goober','url':'view/here'}, m.match('/goober/view/here'))
        self.assertEqual({'controller':'admin/user','action':'view','url':None}, m.match('/admin/user'))
        self.assertEqual({'controller':'admin/user','action':'view','url':None}, m.match('/admin/user/view'))
    
    def test_path_with_dynamic_and_default_backwards(self):
        m = Mapper()
        m.connect('*file/login', controller='content', action='download', file=None)
        m.create_regs([])

        self.assertEqual(None, m.match('/boo'))
        self.assertEqual(None, m.match('/boo/blah'))
        self.assertEqual({'controller':'content','action':'download','file':None}, m.match('/login'))
        self.assertEqual({'controller':'content','action':'download','file':'books/learning_python.pdf'}, m.match('/books/learning_python.pdf/login'))
        self.assertEqual({'controller':'content','action':'download','file':'dude'}, m.match('/dude/login'))
        self.assertEqual({'controller':'content','action':'download','file':'dude/what'}, m.match('/dude/what/login'))
        
    def test_path_backwards(self):
        m = Mapper()
        m.connect('*file/login', controller='content', action='download')
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