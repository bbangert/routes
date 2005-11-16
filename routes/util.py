"""
util - Utility functions for use in templates / controllers

(c) Copyright 2005 Ben Bangert, Parachute
[See end of file]


PLEASE NOTE: Many of these functions expect an initialized RequestConfig object. This is 
expected to have been initialized for EACH REQUEST by the web framework
like so:
import routes
config = routes.request_config()
config.mapper = mapper       # mapper should be a Mapper instance thats ready for use
config.host = host           # host is the hostname of the webapp
config.protocol = protocol   # protocol is the protocol of the current request
config.mapper_dict = mapdi   # mapdi should be the dict returned by mapper.match()
config.redirect = redir_func # redir_func should be a function that issues a redirect, and
#       takes a url as the sole argument
config.prefix                # Set if the application is moved under a URL prefix. Prefix
# will be stripped before matching, and prepended on generation
config.environ               # Set to the WSGI environ for automatic prefix support if the
# webapp is underneath a 'SCRIPT_NAME'

"""
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
    old = config.mapper_dict.copy()
    for key in [key for key in new.keys() if new[key] is None]:
        del new[key]
        if old.has_key(key): del old[key]
    old.update(new)
    return old

def url_quote(string):
    return urllib.quote_plus(str(string), '/')

def url_for(*args, **kargs):
    """
    Returns a url that has been rewritten according to the keyword args and the defined
    Routes in the mapper. All keys given to url_for are sent to the Routes Mapper instance
    for generation except for:
    anchor   - specified the anchor name to be appened to the path
    host     - overrides the default (current) host if provided
    protocol - overrides the default (current) protocol if provided
        
    The URL is generated based on the rest of the keys. When generating a new URL, values
    will be used from the current request's parameters (if present). The following rules
    are used to determine when and how to keep the current requests parameters:
    * If the controller is present and begins with '/', no defaults are used
    * If the controller is changed, action is set to 'index' unless otherwise specified
    
    For example, if the current request yielded a dict of
    {'controller': 'blog', 'action': 'view', 'id': 2}, with the standard 
    ':controller/:action/:id' route, you'd get the following results:
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
    if anchor: url += '#' + url_quote(anchor)
    if host or protocol:
        if not host: host = config.host
        if not protocol: protocol = config.protocol
        url = protocol + '://' + host + url
    return url

def redirect_to(*args, **kargs):
    """
    Redirects based on the arguments. This can be one of three formats:
    - (Keyword Args) Lookup the best URL using the same keyword args
    as url_for and redirect to it
    - (String starting with protocol) Redirect to the string exactly as is
    - (String without protocol) Prepend the string with the current protocol
    and host, then redirect to it.
    Redirect's *should* occur as a "302 Moved" header, however the web framework
    may utilize a different method.
    """
    
    config = request_config()
    target = ''
    if args:
        target = args[0]
        if target.startswith('/'):
            target = config.protocol + '://' + config.host + url_quote(target)
        elif not target.startswith('http://'):
            newdict = config.mapper._routenames.get(args[0])
            if newdict:
                newargs = newdict.copy()
                newargs.update(kargs)
                target = url_for(**newargs)
    elif kargs:
        target = url_for(**kargs)
    config.redirect(target)


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