"""
Utility functions for use in templates / controllers

*PLEASE NOTE*: Many of these functions expect an initialized RequestConfig object. This is 
expected to have been initialized for EACH REQUEST by the web framework.

"""
import os
import re
import urllib
from routes import request_config

def _screenargs(new):
    """
    Private function that takes a dict, and screens it against the current request dict
    to determine what the dict should look like that is used. This is responsible for
    the requests "memory" of the current.
    """
    conval = new.get('controller')
    if conval and conval.startswith('/'):
        new['controller'] = new['controller'][1:]
        return new
    elif conval and not new.has_key('action'):
        new['action'] = 'index'
    config = request_config()
    old = getattr(config, 'mapper_dict', {}).copy()
    for key in [key for key in new.keys() if new[key] is None]:
        del new[key]
        if old.has_key(key): del old[key]
    old.update(new)
    return old

def _url_quote(string):
    return urllib.quote_plus(str(string), '/')

def url_for(*args, **kargs):
    """
    Returns a url that has been rewritten according to the keyword args and the defined
    Routes in the mapper. 
    
    All keys given to url_for are sent to the Routes Mapper instance for generation except for::
        
        anchor          specified the anchor name to be appened to the path
        host            overrides the default (current) host if provided
        protocol        overrides the default (current) protocol if provided
        
    The URL is generated based on the rest of the keys. When generating a new URL, values
    will be used from the current request's parameters (if present). The following rules
    are used to determine when and how to keep the current requests parameters:
    
    * If the controller is present and begins with '/', no defaults are used
    * If the controller is changed, action is set to 'index' unless otherwise specified
    
    For example, if the current request yielded a dict of
    {'controller': 'blog', 'action': 'view', 'id': 2}, with the standard 
    ':controller/:action/:id' route, you'd get the following results::
    
        url_for(id=4)                    =>  '/blog/view/4',
        url_for(controller='/admin')     =>  '/admin',
        url_for(controller='admin')      =>  '/admin/index/4'
        url_for(action='edit')           =>  '/blog/post/4',
        url_for(action='list', id=None)  =>  '/blog/list'
    
    If there is a string present as the first argument, it is assumed to be a Route Name, and
    a lookup will be done on the Routes Mapper instance to see if there is a set of keyword
    defaults associated with that name. If so, the keyword args passed in will override default
    ones that were retrieved.  
    """
    anchor = kargs.get('anchor')
    host = kargs.get('host')
    protocol = kargs.get('protocol')
    for key in ['anchor', 'host', 'protocol']:
        if kargs.get(key): del kargs[key]
    config = request_config()
    newdict = None
    if len(args) > 0:
        newdict = config.mapper._routenames.get(args[0])
    if newdict:
        newargs = newdict.copy()
        newargs.update(kargs)
    else:
        newargs = _screenargs(kargs)
    url = config.mapper.generate(**newargs)
    if anchor: url += '#' + _url_quote(anchor)
    if host or protocol:
        if not host: host = config.host
        if not protocol: protocol = config.protocol
        url = protocol + '://' + host + url
    return url

def redirect_to(*args, **kargs):
    """
    Issues a redirect based on the arguments. 
    
    Redirect's *should* occur as a "302 Moved" header, however the web framework
    may utilize a different method.
    
    Three formats for the arguments are possible:
    
    Keyword Args
        Lookup the best URL using the same keyword args as the url_for function.
    String starting with protocol
        Redirect to the string exactly as is given.
    String without protocol
        Prepend the string with the current protocol and host, then redirect to
        it. The protocol and host is prepended because not all redirect functions
        can handle relative URL's.
        
    Examples::
    
        # Keyword args
        redirect_to(controller='blog', action='view')
        
        # String starting with protocol
        redirect_to('https://www.gmail.com/')
        
        # String without protocol
        redirect_to('/blog/view/4')
    
    """
    
    config = request_config()
    target = ''
    if args:
        target = args[0]
        if target.startswith('/'):
            target = config.protocol + '://' + config.host + _url_quote(target)
        elif not target.startswith('http://'):
            newdict = config.mapper._routenames.get(args[0])
            if newdict:
                newargs = newdict.copy()
                newargs.update(kargs)
                target = url_for(**newargs)
    elif kargs:
        target = url_for(**kargs)
    config.redirect(target)

def controller_scan(directory):
    """
    Scan a directory for python files and use them as controllers
    """
    def find_controllers(dirname, prefix=''):
        controllers = []
        for fname in os.listdir(dirname):
            filename = dirname + '/' + fname
            if os.path.isfile(filename) and re.match('^[^_]{1,1}.*\.py$', fname):
                controllers.append(fname[:-3])
            elif os.path.isdir(filename):
                controllers.extend(find_controllers(filename, prefix=fname+'/'))
        return controllers
    
    controllers = find_controllers(directory)
    return controllers
