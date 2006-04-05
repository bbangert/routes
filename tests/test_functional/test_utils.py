"""
test_utils

(c) Copyright 2005 Ben Bangert, Parachute
[See end of file]
"""

import sys, time, unittest
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
        
    def test_url_for(self):
        con = self.con
        con.mapper_dict = {}
        
        self.assertEqual('/blog', url_for(controller='blog'))
        self.assertEqual('/content', url_for())
        self.assertEqual('https://www.test.com/viewpost', url_for(controller='post', action='view', protocol='https'))
        self.assertEqual('http://www.test.org/content', url_for(host='www.test.org'))
    
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
        self.assertEqual('/category', url_for('home', action='view', section='home'))
        self.assertEqual('/content/splash', url_for('home', controller='content'))
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
        

    def test_redirect_to(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
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
        redirect_to('home', action='view', section='home')
        self.assertEqual('/category', redirect_to.result)
        redirect_to('home', controller='content')
        self.assertEqual('/content/splash', redirect_to.result)
        redirect_to('home')
        self.assertEqual('/', redirect_to.result)
    
    def test_static_route(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        self.con.environ = dict(SCRIPT_NAME='', SERVER_NAME='example.com')
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
        self.con.environ = dict(SCRIPT_NAME='/webapp', SERVER_NAME='example.com')
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
        self.con.environ = dict(SCRIPT_NAME='', SERVER_NAME='example.com')
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
        self.con.environ = dict(SCRIPT_NAME='', SERVER_NAME='example.com')
        m.connect(':controller/:action/:id')
        m.connect('home', 'http://www.groovie.org/', _static=True)
        m.connect('space', '/nasa/images', _static=True)
        m.create_regs(['content', 'blog'])
        
        self.assertEqual('http://www.google.com/search', url_for('http://www.google.com/search'))
        self.assertEqual('http://www.google.com/search?q=routes', url_for('http://www.google.com/search', q='routes'))
        self.assertEqual('/delicious.jpg', url_for('/delicious.jpg'))
        self.assertEqual('/delicious/search?v=routes', url_for('/delicious/search', v='routes'))
        self.assertEqual('/content/list/', url_for(controller='/content', action='list'))

    def test_no_named_path_with_script(self):
        m = self.con.mapper
        self.con.mapper_dict = {}
        self.con.environ = dict(SCRIPT_NAME='/webapp', SERVER_NAME='example.com')
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
        self.con.environ = dict(SCRIPT_NAME='', SERVER_NAME='example.com')

        m = Mapper()
        m.connect(':controller/:(action)-:(id).html')
        m.connect('archives', 'archives/:year/:month/:day/:slug', controller='archives', action='view',
                  _filter=article_filter)
        m.create_regs(['content','archives','admin/comments'])
        self.con.mapper = m
        
        self.assertEqual(None, url_for(controller='content', action='view'))
        self.assertEqual(None, url_for(controller='content'))
        
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