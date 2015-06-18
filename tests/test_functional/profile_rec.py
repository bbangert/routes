try:
    import profile
    import pstats
except ImportError:
    pass
import tempfile
import os
import time
from routes import Mapper

def get_mapper():
    m = Mapper()
    m.connect('', controller='articles', action='index')
    m.connect('admin', controller='admin/general', action='index')

    m.connect('admin/comments/article/:article_id/:action/:id',
              controller = 'admin/comments', action = None, id=None)
    m.connect('admin/trackback/article/:article_id/:action/:id',
              controller='admin/trackback', action=None, id=None)
    m.connect('admin/content/:action/:id', controller='admin/content')

    m.connect('xml/:action/feed.xml', controller='xml')
    m.connect('xml/articlerss/:id/feed.xml', controller='xml',
              action='articlerss')
    m.connect('index.rdf', controller='xml', action='rss')

    m.connect('articles', controller='articles', action='index')
    m.connect('articles/page/:page', controller='articles',
              action='index', requirements = {'page':'\d+'})

    m.connect(
        'articles/:year/:month/:day/page/:page',
        controller='articles', action='find_by_date', month = None,
        day = None,
        requirements = {'year':'\d{4}', 'month':'\d{1,2}','day':'\d{1,2}'})

    m.connect('articles/category/:id', controller='articles', action='category')
    m.connect('pages/*name', controller='articles', action='view_page')
    m.create_regs(['content','admin/why', 'admin/user'])
    return m

def bench_rec(mapper, n):
    ts = time.time()
    for x in range(1,n):
        pass
    en = time.time()

    match = mapper.match

    # hits
    start = time.time()
    for x in range(1,n):
        match('/admin')
        match('/xml/1/feed.xml')
        match('/index.rdf')
    end = time.time()
    total = end-start-(en-ts)
    per_url = total / (n*10)
    print("Hit recognition\n")
    print("%s ms/url" % (per_url*1000))
    print("%s urls/s\n" % (1.00/per_url))

    # misses
    start = time.time()
    for x in range(1,n):
        match('/content')
        match('/content/list')
        match('/content/show/10')
    end = time.time()
    total = end-start-(en-ts)
    per_url = total / (n*10)
    print("Miss recognition\n")
    print("%s ms/url" % (per_url*1000))
    print("%s urls/s\n" % (1.00/per_url))
        
def do_profile(cmd, globals, locals, sort_order, callers):
    fd, fn = tempfile.mkstemp()
    try:
        if hasattr(profile, 'runctx'):
            profile.runctx(cmd, globals, locals, fn)
        else:
            raise NotImplementedError(
                'No profiling support under Python 2.3')
        stats = pstats.Stats(fn)
        stats.strip_dirs()
        # calls,time,cumulative and cumulative,calls,time are useful
        stats.sort_stats(*sort_order or ('cumulative', 'calls', 'time'))
        if callers:
            stats.print_callers()
        else:
            stats.print_stats()
    finally:
        os.remove(fn)

def main(n=300):
    mapper = get_mapper()
    do_profile('bench_rec(mapper, %s)' % n, globals(), locals(),
               ('time', 'cumulative', 'calls'), None)

if __name__ == '__main__':
    main()
    
