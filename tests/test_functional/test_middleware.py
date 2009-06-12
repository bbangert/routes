from routes import Mapper
from routes.middleware import RoutesMiddleware
from webtest import TestApp
from nose.tools import eq_

def simple_app(environ, start_response):
    route_dict = environ['wsgiorg.routing_args'][1]
    start_response('200 OK', [('Content-type', 'text/plain')])
    items = route_dict.items()
    items.sort()
    return ['The matchdict items are %s and environ is %s' % (items, environ)]

def test_basic():
    map = Mapper()
    map.connect(':controller/:action/:id')
    map.create_regs(['content'])
    app = TestApp(RoutesMiddleware(simple_app, map))
    res = app.get('/')
    assert 'matchdict items are []' in res
    
    res = app.get('/content')
    assert "matchdict items are [('action', 'index'), ('controller', u'content'), ('id', None)]" in res
    
def test_path_info():
    map = Mapper()
    map.connect('myapp/*path_info', controller='myapp')
    map.connect('project/*path_info', controller='myapp')
    map.create_regs(['content', 'myapp'])
    
    app = TestApp(RoutesMiddleware(simple_app, map))
    res = app.get('/')
    assert 'matchdict items are []' in res
    
    res = app.get('/myapp/some/other/url')
    print res
    assert "matchdict items are [('action', u'index'), ('controller', u'myapp'), ('path_info', 'some/other/url')]" in res
    assert "'SCRIPT_NAME': '/myapp'" in res
    assert "'PATH_INFO': '/some/other/url'" in res
    
    res = app.get('/project/pylonshq/browser/pylons/templates/default_project/+package+/pylonshq/browser/pylons/templates/default_project/+package+/controllers')
    print res
    assert "'SCRIPT_NAME': '/project'" in res
    assert "'PATH_INFO': '/pylonshq/browser/pylons/templates/default_project/+package+/pylonshq/browser/pylons/templates/default_project/+package+/controllers'" in res    

def test_redirect_middleware():
    map = Mapper()
    map.connect('myapp/*path_info', controller='myapp')
    map.redirect("faq/{section}", "/static/faq/{section}.html")
    map.redirect("home/index", "/", _redirect_code='301 Moved Permanently')
    map.create_regs(['content', 'myapp'])
    
    app = TestApp(RoutesMiddleware(simple_app, map))
    res = app.get('/')
    assert 'matchdict items are []' in res
    
    res = app.get('/faq/home')
    eq_('302 Found', res.status)
    eq_(res.headers['Location'], '/static/faq/home.html')
    
    res = app.get('/myapp/some/other/url')
    print res
    assert "matchdict items are [('action', u'index'), ('controller', u'myapp'), ('path_info', 'some/other/url')]" in res
    assert "'SCRIPT_NAME': '/myapp'" in res
    assert "'PATH_INFO': '/some/other/url'" in res
    
    res = app.get('/home/index')
    assert '301 Moved Permanently' in res.status
    eq_(res.headers['Location'], '/')

def test_method_conversion():
    map = Mapper()
    map.connect('content/:type', conditions=dict(method='DELETE'))
    map.connect(':controller/:action/:id')
    map.create_regs(['content'])
    app = TestApp(RoutesMiddleware(simple_app, map))
    res = app.get('/')
    assert 'matchdict items are []' in res
    
    res = app.get('/content')
    assert "matchdict items are [('action', 'index'), ('controller', u'content'), ('id', None)]" in res
    
    res = app.get('/content/hopper', params={'_method':'DELETE'})
    assert "matchdict items are [('action', u'index'), ('controller', u'content'), ('type', u'hopper')]" in res
    
    res = app.post('/content/grind', 
                   params={'_method':'DELETE', 'name':'smoth'},
                   headers={'Content-Type': 'application/x-www-form-urlencoded'})
    assert "matchdict items are [('action', u'index'), ('controller', u'content'), ('type', u'grind')]" in res
    assert "'REQUEST_METHOD': 'POST'" in res

    #res = app.post('/content/grind',
    #               upload_files=[('fileupload', 'hello.txt', 'Hello World')],
    #               params={'_method':'DELETE', 'name':'smoth'})
    #assert "matchdict items are [('action', u'index'), ('controller', u'content'), ('type', u'grind')]" in res
    #assert "'REQUEST_METHOD': 'POST'" in res
