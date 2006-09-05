"""Utility functions for use in templates / controllers

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
    if config.mapper.sub_domains:
        subdomain = old.pop('sub_domain', None)
        host = config.environ['HTTP_HOST'].split(':')[0]
        sub_match = re.compile('^.+?\.(%s)$' % config.mapper.domain_match)
        domain = re.sub(sub_match, r'\1', host)
        if subdomain and not host.startswith(subdomain) and \
            subdomain not in config.mapper.sub_domains_ignore:
            old['_host'] = subdomain + '.' + domain
        elif (subdomain in config.mapper.sub_domains_ignore or subdomain is None) and domain != host:
            old['_host'] = domain
        elif subdomain and not host.startswith(subdomain):
            old['_host'] = subdomain + '.' + domain
    return old

def _url_quote(string):
    return urllib.quote_plus(str(string), '/')

def url_for(*args, **kargs):
    """Generates a URL 
    
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
    
    **Static and Named Routes**
    
    If there is a string present as the first argument, a lookup is done against the named
    routes table to see if there's any matching routes. The keyword defaults used with static
    routes will be sent in as GET query arg's if a route matches.
    
    If no route by that name is found, the string is assumed to be a raw URL. Should the raw
    URL begin with ``/`` then appropriate SCRIPT_NAME data will be added if present, otherwise
    the string will be used as the url with keyword args becoming GET query args.
    
    """
    anchor = kargs.get('anchor')
    host = kargs.get('host')
    protocol = kargs.get('protocol')
    
    # Remove special words from kargs, convert placeholders
    for key in ['anchor', 'host', 'protocol']:
        if kargs.get(key): del kargs[key]
        if kargs.has_key(key+'_'):
            kargs[key] = kargs[key+'_']
            del kargs[key+'_']
    config = request_config()
    route = None
    static = False
    url = ''
    if len(args) > 0:
        route = config.mapper._routenames.get(args[0])
        
        if route and route.defaults.has_key('_static'):
            static = True
            url = route.routepath
        
        # No named route found, assume the argument is a relative path
        if not route:
            static = True
            url = args[0]
        
        if url.startswith('/') and hasattr(config, 'environ') \
                and config.environ.get('SCRIPT_NAME'):
            url = config.environ.get('SCRIPT_NAME') + url
        
        if static:
            if kargs:
                url += '?'
                url += urllib.urlencode(kargs)
    if not static:
        if route:
            newargs = route.defaults.copy()
            newargs.update(kargs)
            
            # If this route has a filter, apply it
            if route.filter:
                newargs = route.filter(newargs)
        else:
            newargs = _screenargs(kargs)
        anchor = newargs.pop('_anchor', None) or anchor
        host = newargs.pop('_host', None) or host
        protocol = newargs.pop('_protocol', None) or protocol
        url = config.mapper.generate(**newargs)
        if config.mapper.append_slash and not url.endswith('/'):
            url += '/'
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
    
    All arguments are passed to url_for to retrieve the appropriate URL, then the
    resulting URL it sent to the redirect function as the URL.
    
    """
    target = url_for(*args, **kargs)
    config = request_config()
    config.redirect(target)

def controller_scan(directory=None):
    """
    Scan a directory for python files and use them as controllers
    """
    if directory is None:
        return []
    
    def find_controllers(dirname, prefix=''):
        controllers = []
        for fname in os.listdir(dirname):
            filename = os.path.join(dirname, fname)
            if os.path.isfile(filename) and re.match('^[^_]{1,1}.*\.py$', fname):
                controllers.append(prefix + fname[:-3])
            elif os.path.isdir(filename):
                controllers.extend(find_controllers(filename, prefix=prefix+fname+'/'))
        return controllers
    def longest_first(a, b):
        return cmp(len(b), len(a))
    controllers = find_controllers(directory)
    controllers.sort(longest_first)
    return controllers

class RouteException(Exception):
    pass
