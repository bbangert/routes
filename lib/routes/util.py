"""
util
(c) Copyright 2005 Ben Bangert, Parachute
[See end of file]


PLEASE NOTE: Many of these functions expect a initialized Config object. This is 
             expected to have been initialized for EACH REQUEST by the web framework
             like so:
import routes.base
config = base.Config()
config.mapper = mapper       # mapper should be a Mapper instance thats ready for use
config.host = host           # host is the hostname of the webapp
config.protocol = protocol   # protocol is the protocol of the current request
config.mapper_dict = mapdi   # mapdi should be the dict returned by mapper.match()
config.redirect = redir_func # redir_func should be a function that issues a redirect, and
                             #       takes a url as the sole argument

"""
import urllib
import base

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
    config = base.Config()
    old = config.mapper_dict.copy()
    todel = []
    for key, val in new.iteritems():
        if val is None: todel.append(key)
    for key in todel:
        del new[key]
        if old.has_key(key): del old[key]
    old.update(new)
    return old

def url_quote(string):
    return urllib.quote_plus(str(string), '/')

def url_for(anchor = None, host = None, protocol = None, **kargs):
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
    """
    
    config = base.Config()
    newargs = _screenargs(kargs)
    url = config.mapper.generate(**newargs)
    if anchor: url += '#' + url_quote(anchor)
    if host or protocol:
        if not host: host = config.host
        if not protocol: protocol = config.protocol
        url = protocol + '://' + host + url
    return url

def redirect_to(*args, **kargs):
    config = base.Config()
    target = ''
    if args:
        target = args[0]
        if not target.startswith('ht'):
            target = config.protocol + '://' + config.host + target
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