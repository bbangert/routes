"""Routes WSGI Middleware"""
import re
import urllib

try:
    from paste.wsgiwrappers import WSGIRequest
except:
    pass

from routes.base import request_config

class RoutesMiddleware(object):
    def __init__(self, wsgi_app, mapper, use_method_override=True, 
                 path_info=True):
        """Create a Route middleware object
        
        Using the use_method_override keyword will require Paste to be 
        installed, and your application should use Paste's WSGIRequest object
        as it will properly handle POST issues with wsgi.input should Routes
        check it.
        
        If path_info is True, then should a route var contain path_info, the
        SCRIPT_NAME and PATH_INFO will be altered accordingly. This should be
        used with routes like:
        
        .. code-block:: Python
        
            map.connect('blog/*path_info', controller='blog', path_info='')
        """
        self.app = wsgi_app
        self.mapper = mapper
        self.use_method_override = use_method_override
        self.path_info = path_info
    
    def __call__(self, environ, start_response):
        config = request_config()
        config.mapper = self.mapper
        
        old_method = None
        if self.use_method_override:
            req = WSGIRequest(environ)
            if '_method' in environ.get('QUERY_STRING', '') and '_method' in req.GET:
                old_method = environ['REQUEST_METHOD']
                environ['REQUEST_METHOD'] = req.GET['_method']
            elif environ['REQUEST_METHOD'] == 'POST' and '_method' in req.POST:
                old_method = environ['REQUEST_METHOD']
                environ['REQUEST_METHOD'] = req.POST['_method']
        
        config.environ = environ
        match = config.mapper_dict
        
        if old_method:
            environ['REQUEST_METHOD'] = old_method
        
        if not match:
            match = {}
        
        for k,v in match.iteritems():
            if v:
                match[k] = urllib.unquote_plus(v)
        
        environ['wsgiorg.routing_args'] = ((), match)

        # If the route included a path_info attribute and it should be used to
        # alter the environ, we'll pull it out
        if self.path_info and match.get('path_info'):
            oldpath = environ['PATH_INFO']
            newpath = match.get('path_info') or ''
            environ['PATH_INFO'] = newpath
            if not environ['PATH_INFO'].startswith('/'):
                environ['PATH_INFO'] = '/' + environ['PATH_INFO']
            environ['SCRIPT_NAME'] += re.sub(r'^(.*?)/' + newpath + '$', r'\1', oldpath)
            if environ['SCRIPT_NAME'].endswith('/'):
                environ['SCRIPT_NAME'] = environ['SCRIPT_NAME'][:-1]
            
        return self.app(environ, start_response)
    