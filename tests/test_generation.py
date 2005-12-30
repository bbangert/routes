"""
test_generation

(c) Copyright 2005 Ben Bangert, Parachute
[See end of file]
"""

import sys, time, unittest
from routes import *

class TestGeneration(unittest.TestCase):
    
    def test_all_static_no_reqs(self):
        m = Mapper()
        m.connect('hello/world')
        
        self.assertEqual('/hello/world', m.generate())
    
    def test_basic_dynamic(self):
        m = Mapper()
        m.connect('hi/:fred')
        
        self.assertEqual('/hi/index', m.generate(fred='index'))
        self.assertEqual('/hi/show', m.generate(fred='show'))
        self.assertEqual('/hi/list+people', m.generate(fred='list people'))
        self.assertEqual(None, m.generate())
    
    def test_dynamic_with_default(self):
        m = Mapper()
        m.connect('hi/:action')
        
        self.assertEqual('/hi', m.generate(action='index'))
        self.assertEqual('/hi/show', m.generate(action='show'))
        self.assertEqual('/hi/list+people', m.generate(action='list people'))
        self.assertEqual('/hi', m.generate())
    
    def test_dynamic_with_false_equivs(self):
        m = Mapper()
        m.connect(':controller/:action/:id')
        
        self.assertEqual('/blog/view/0', m.generate(controller="blog", action="view", id="0"))
        self.assertEqual('/blog/view/0', m.generate(controller="blog", action="view", id=0))
        self.assertEqual('/blog/view/False', m.generate(controller="blog", action="view", id=False))
        self.assertEqual('/blog/view/False', m.generate(controller="blog", action="view", id='False'))
        self.assertEqual('/blog/view', m.generate(controller="blog", action="view", id=None))
        self.assertEqual('/blog/view', m.generate(controller="blog", action="view", id='None'))
    
    def test_dynamic_with_regexp_condition(self):
        m = Mapper()
        m.connect('hi/:name', requirements = {'name':'[a-z]+'})
        
        self.assertEqual('/hi/index', m.generate(name='index'))
        self.assertEqual(None, m.generate(name='fox5'))
        self.assertEqual(None, m.generate(name='something_is_up'))
        self.assertEqual('/hi/abunchofcharacter', m.generate(name='abunchofcharacter'))
        self.assertEqual(None, m.generate())
    
    def test_dynamic_with_default_and_regexp_condition(self):
        m = Mapper()
        m.connect('hi/:action', requirements = {'action':'[a-z]+'})
        
        self.assertEqual('/hi', m.generate(action='index'))
        self.assertEqual(None, m.generate(action='fox5'))
        self.assertEqual(None, m.generate(action='something_is_up'))
        self.assertEqual(None, m.generate(action='list people'))
        self.assertEqual('/hi/abunchofcharacter', m.generate(action='abunchofcharacter'))
        self.assertEqual('/hi', m.generate())
    
    def test_path(self):
        m = Mapper()
        m.connect('hi/*file')
        
        self.assertEqual('/hi', m.generate(file=None))
        self.assertEqual('/hi/books/learning_python.pdf', m.generate(file='books/learning_python.pdf'))
        self.assertEqual('/hi/books/development%26whatever/learning_python.pdf', m.generate(file='books/development&whatever/learning_python.pdf'))
    
    def test_path_backwards(self):
        m = Mapper()
        m.connect('*file/hi')

        self.assertEqual('/hi', m.generate(file=None))
        self.assertEqual('/books/learning_python.pdf/hi', m.generate(file='books/learning_python.pdf'))
        self.assertEqual('/books/development%26whatever/learning_python.pdf/hi', m.generate(file='books/development&whatever/learning_python.pdf'))
    
    def test_controller(self):
        m = Mapper()
        m.connect('hi/:controller')
        
        self.assertEqual('/hi/content', m.generate(controller='content'))
        self.assertEqual('/hi/admin/user', m.generate(controller='admin/user'))
    
    def test_standard_route(self):
        m = Mapper()
        m.connect(':controller/:action/:id')
        
        self.assertEqual('/content', m.generate(controller='content', action='index'))
        self.assertEqual('/content/list', m.generate(controller='content', action='list'))
        self.assertEqual('/content/show/10', m.generate(controller='content', action='show', id ='10'))
        
        self.assertEqual('/admin/user', m.generate(controller='admin/user', action='index'))
        self.assertEqual('/admin/user/list', m.generate(controller='admin/user', action='list'))
        self.assertEqual('/admin/user/show/10', m.generate(controller='admin/user', action='show', id='10'))
    
    def test_multiroute(self):
        m = Mapper()
        m.connect('archive/:year/:month/:day', controller='blog', action='view', month=None, day=None,
                            requirements={'month':'\d{1,2}','day':'\d{1,2}'})
        m.connect('viewpost/:id', controller='post', action='view')
        m.connect(':controller/:action/:id')
        
        self.assertEqual('/blog/view?year=2004&month=blah', m.generate(controller='blog', action='view', year=2004, month='blah'))
        self.assertEqual('/archive/2004/11', m.generate(controller='blog', action='view', year=2004, month=11))
        self.assertEqual('/archive/2004/11', m.generate(controller='blog', action='view', year=2004, month='11'))
        self.assertEqual('/archive/2004', m.generate(controller='blog', action='view', year=2004))
        self.assertEqual('/viewpost/3', m.generate(controller='post', action='view', id=3))
        
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
        
        
        self.assertEqual('/pages/the/idiot/has/spoken', m.generate(controller='articles', action='view_page',
                            name='the/idiot/has/spoken'))
        self.assertEqual('/', m.generate(controller='articles', action='index'))
        self.assertEqual('/xml/articlerss/4/feed.xml', m.generate(controller='xml', action='articlerss', id=4))
        self.assertEqual('/xml/rss/feed.xml', m.generate(controller='xml', action='rss'))
        self.assertEqual('/admin/comments/article/4/view/2', m.generate(controller='admin/comments', action='view', article_id=4, id=2))
        self.assertEqual('/admin', m.generate(controller='admin/general'))
        self.assertEqual('/admin/comments/article/4/index', m.generate(controller='admin/comments', article_id=4))
        self.assertEqual('/admin/comments/article/4', m.generate(controller='admin/comments', action=None, article_id=4))
        self.assertEqual('/articles/2004/2/20/page/1', m.generate(controller='articles', action='find_by_date', 
                    year=2004, month=2, day=20, page=1))
        self.assertEqual('/articles/category', m.generate(controller='articles', action='category'))
        self.assertEqual('/xml/index/feed.xml', m.generate(controller='xml'))
        self.assertEqual('/xml/articlerss/feed.xml', m.generate(controller='xml', action='articlerss'))
        
        self.assertEqual(None, m.generate(controller='admin/comments', id=2))
        self.assertEqual(None, m.generate(controller='articles', action='find_by_date', year=2004))
    
    def test_no_extras(self):
        m = Mapper()
        m.connect(':controller/:action/:id')
        m.connect('archive/:year/:month/:day', controller='blog', action='view', month=None, day=None)
        
        self.assertEqual('/archive/2004', m.generate(controller='blog', action='view', year=2004))
        
    def test_the_smallest_route(self):
        m = Mapper()
        m.connect('', controller='page', action='view', title='HomePage')
        m.connect('pages/:title', controller='page', action='view')
        
        self.assertEqual('/', m.generate(controller='page', action='view', title='HomePage'))
        self.assertEqual('/pages/joe', m.generate(controller='page', action='view', title='joe'))
        
    def test_extras(self):
        m = Mapper()
        m.connect('viewpost/:id', controller='post', action='view')
        m.connect(':controller/:action/:id')
        
        self.assertEqual('/blog?extra=3', m.generate(controller='blog', action='index', extra=3))
        self.assertEqual('/viewpost/2?extra=3', m.generate(controller='post', action='view', id=2, extra=3))
    
    def test_static(self):
        m = Mapper()
        m.connect('hello/world',known='known_value',controller='content',action='index')
        
        self.assertEqual('/hello/world', m.generate(controller='content',action= 'index',known ='known_value'))
        self.assertEqual('/hello/world?extra=hi', m.generate(controller='content',action='index',known='known_value',extra='hi'))
        
        self.assertEqual(None, m.generate(known='foo'))
    
    def test_dynamic(self):
        m = Mapper()
        m.connect('hello/:name', controller='content', action='show_person')
        
        self.assertEqual('/hello/rails', m.generate(controller='content', action='show_person',name='rails'))
        self.assertEqual('/hello/Alfred+Hitchcock', m.generate(controller='content', action='show_person',name='Alfred Hitchcock'))
        
        self.assertEqual(None, m.generate(controller='content', action='show_dude', name='rails'))
        self.assertEqual(None, m.generate(controller='content', action='show_person'))
        self.assertEqual(None, m.generate(controller='admin/user', action='show_person', name='rails'))
    
    def test_typical(self):
        m = Mapper()
        m.connect(':controller/:action/:id', action = 'index', id = None)
        
        self.assertEqual('/content', m.generate(controller='content', action='index'))
        self.assertEqual('/content/list', m.generate(controller='content', action='list'))
        self.assertEqual('/content/show/10', m.generate(controller='content', action='show', id=10))
        
        self.assertEqual('/admin/user', m.generate(controller='admin/user', action='index'))
        self.assertEqual('/admin/user', m.generate(controller='admin/user'))
        self.assertEqual('/admin/user/show/10', m.generate(controller='admin/user', action='show', id=10))
        
        self.assertEqual('/content', m.generate(controller='content'))
    
    def test_route_with_fixnum_default(self):
        m = Mapper()
        m.connect('page/:id', controller='content', action='show_page', id =1)
        m.connect(':controller/:action/:id')
        
        self.assertEqual('/page', m.generate(controller='content', action='show_page'))
        self.assertEqual('/page', m.generate(controller='content', action='show_page', id=1))
        self.assertEqual('/page', m.generate(controller='content', action='show_page', id='1'))
        self.assertEqual('/page/10', m.generate(controller='content', action='show_page', id=10))
        
        self.assertEqual('/blog/show/4', m.generate(controller='blog', action='show', id=4))
        self.assertEqual('/page', m.generate(controller='content', action='show_page'))
        self.assertEqual('/page/4', m.generate(controller='content', action='show_page',id=4))
        self.assertEqual('/content/show', m.generate(controller='content', action='show'))
    
    def test_uppercase_recognition(self):
        m = Mapper()
        m.connect(':controller/:action/:id')

        self.assertEqual('/Content', m.generate(controller='Content', action='index'))
        self.assertEqual('/Content/list', m.generate(controller='Content', action='list'))
        self.assertEqual('/Content/show/10', m.generate(controller='Content', action='show', id='10'))

        self.assertEqual('/Admin/NewsFeed', m.generate(controller='Admin/NewsFeed', action='index'))
    
    def test_backwards(self):
        m = Mapper()
        m.connect('page/:id/:action', controller='pages', action='show')
        m.connect(':controller/:action/:id')

        self.assertEqual('/page/20', m.generate(controller='pages', action='show', id=20))
        self.assertEqual('/pages/boo', m.generate(controller='pages', action='boo'))
    
    def test_both_requirement_and_optional(self):
        m = Mapper()
        m.connect('test/:year', controller='post', action='show', year=None, requirements = {'year':'\d{4}'})

        self.assertEqual('/test', m.generate(controller='post', action='show'))
        self.assertEqual('/test', m.generate(controller='post', action='show', year=None))
    
    def test_set_to_nil_forgets(self):
        m = Mapper()
        m.connect('pages/:year/:month/:day', controller='content', action='list_pages', month=None, day=None)
        m.connect(':controller/:action/:id')

        self.assertEqual('/pages/2005', m.generate(controller='content', action='list_pages', year=2005))
        self.assertEqual('/pages/2005/6', m.generate(controller='content', action='list_pages', year=2005, month=6))
        self.assertEqual('/pages/2005/6/12', m.generate(controller='content', action='list_pages', year=2005, month=6, day=12))
    
    def test_url_with_no_action_specified(self):
        m = Mapper()
        m.connect('', controller='content')
        m.connect(':controller/:action/:id')

        self.assertEqual('/', m.generate(controller='content', action='index'))
        self.assertEqual('/', m.generate(controller='content'))
    
    def test_url_with_prefix(self):
        m = Mapper()
        m.prefix = '/blog'
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        self.assertEqual('/blog/content/view', m.generate(controller='content', action='view'))
        self.assertEqual('/blog/content', m.generate(controller='content'))
        self.assertEqual('/blog/admin/comments', m.generate(controller='admin/comments'))

    def test_url_with_prefix_deeper(self):
        m = Mapper()
        m.prefix = '/blog/phil'
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        self.assertEqual('/blog/phil/content/view', m.generate(controller='content', action='view'))
        self.assertEqual('/blog/phil/content', m.generate(controller='content'))
        self.assertEqual('/blog/phil/admin/comments', m.generate(controller='admin/comments'))

    def test_url_with_environ_empty(self):
        m = Mapper()
        m.environ = dict(SCRIPT_NAME='')
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        self.assertEqual('/content/view', m.generate(controller='content', action='view'))
        self.assertEqual('/content', m.generate(controller='content'))
        self.assertEqual('/admin/comments', m.generate(controller='admin/comments'))

    def test_url_with_environ(self):
        m = Mapper()
        m.environ = dict(SCRIPT_NAME='/blog')
        m.connect(':controller/:action/:id')
        m.create_regs(['content','blog','admin/comments'])

        self.assertEqual('/blog/content/view', m.generate(controller='content', action='view'))
        self.assertEqual('/blog/content', m.generate(controller='content'))
        self.assertEqual('/blog/admin/comments', m.generate(controller='admin/comments'))


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