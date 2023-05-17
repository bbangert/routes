"""Test non-minimization recognition"""
from six.moves import urllib

from routes import url_for
from routes.mapper import Mapper


def test_basic():
    m = Mapper(explicit=False)
    m.minimization = False
    m.connect('/:controller/:action/:id')
    m.create_regs(['content'])

    # Recognize
    assert m.match('/content') is None
    assert m.match('/content/index') is None
    assert m.match('/content/index/') is None
    assert m.match('/content/index/4') == {'controller':'content','action':'index','id':'4'}
    assert m.match('/content/view/4.html') == {'controller':'content','action':'view','id':'4.html'}

    # Generate
    assert m.generate(controller='content') is None
    assert m.generate(controller='content', id=4) == '/content/index/4'
    assert m.generate(controller='content', action='view', id=3) == '/content/view/3'

def test_full():
    m = Mapper(explicit=False)
    m.minimization = False
    m.connect('/:controller/:action/', id=None)
    m.connect('/:controller/:action/:id')
    m.create_regs(['content'])

    # Recognize
    assert m.match('/content') is None
    assert m.match('/content/index') is None
    assert m.match('/content/index/') == {'controller':'content','action':'index','id':None}
    assert m.match('/content/index/4') == {'controller':'content','action':'index','id':'4'}
    assert m.match('/content/view/4.html') == {'controller':'content','action':'view','id':'4.html'}

    # Generate
    assert m.generate(controller='content') is None

    # Looks odd, but only controller/action are set with non-explicit, so we
    # do need the id to match
    assert m.generate(controller='content', id=None) == '/content/index/'
    assert m.generate(controller='content', id=4) == '/content/index/4'
    assert m.generate(controller='content', action='view', id=3) == '/content/view/3'

def test_action_required():
    m = Mapper()
    m.minimization = False
    m.explicit = True
    m.connect('/:controller/index', action='index')
    m.create_regs(['content'])

    assert m.generate(controller='content') is None
    assert m.generate(controller='content', action='fred') is None
    assert m.generate(controller='content', action='index') == '/content/index'

def test_query_params():
    m = Mapper()
    m.minimization = False
    m.explicit = True
    m.connect('/:controller/index', action='index')
    m.create_regs(['content'])

    assert m.generate(controller='content') is None
    assert m.generate(controller='content', action='index', test='sample') == '/content/index?test=sample'


def test_syntax():
    m = Mapper(explicit=False)
    m.minimization = False
    m.connect('/{controller}/{action}/{id}')
    m.create_regs(['content'])

    # Recognize
    assert m.match('/content') is None
    assert m.match('/content/index') is None
    assert m.match('/content/index/') is None
    assert m.match('/content/index/4') == {'controller':'content','action':'index','id':'4'}

    # Generate
    assert m.generate(controller='content') is None
    assert m.generate(controller='content', id=4) == '/content/index/4'
    assert m.generate(controller='content', action='view', id=3) == '/content/view/3'

def test_regexp_syntax():
    m = Mapper(explicit=False)
    m.minimization = False
    m.connect('/{controller}/{action}/{id:\d\d}')
    m.create_regs(['content'])

    # Recognize
    assert m.match('/content') is None
    assert m.match('/content/index') is None
    assert m.match('/content/index/') is None
    assert m.match('/content/index/3') is None
    assert m.match('/content/index/44') == {'controller':'content','action':'index','id':'44'}

    # Generate
    assert m.generate(controller='content') is None
    assert m.generate(controller='content', id=4) is None
    assert m.generate(controller='content', id=43) == '/content/index/43'
    assert m.generate(controller='content', action='view', id=31) == '/content/view/31'

def test_unicode():
    hoge = u'\u30c6\u30b9\u30c8' # the word test in Japanese
    hoge_enc = urllib.parse.quote(hoge.encode('utf-8'))
    m = Mapper()
    m.minimization = False
    m.connect(':hoge')
    assert m.generate(hoge=hoge) == "/%s" % hoge_enc
    assert isinstance(m.generate(hoge=hoge), str)

def test_unicode_static():
    hoge = u'\u30c6\u30b9\u30c8' # the word test in Japanese
    hoge_enc = urllib.parse.quote(hoge.encode('utf-8'))
    m = Mapper()
    m.minimization = False
    m.connect('google-jp', 'http://www.google.co.jp/search', _static=True)
    m.create_regs(['messages'])
    assert url_for('google-jp', q=hoge) == "http://www.google.co.jp/search?q=" + hoge_enc
    assert isinstance(url_for('google-jp', q=hoge), str)

def test_other_special_chars():
    m = Mapper()
    m.minimization = False
    m.connect('/:year/:(slug).:(format),:(locale)', locale='en', format='html')
    m.create_regs(['content'])

    assert m.generate(year=2007, slug='test', format='xml', locale='ja') == '/2007/test.xml,ja'
    assert m.generate(year=2007, format='html') is None
