"""Route and Mapper core classes"""

import re
import sys
import urllib
from util import _url_quote as url_quote
from util import controller_scan, RouteException
from routes import request_config

if sys.version < '2.4':
    from sets import ImmutableSet as frozenset

import threadinglocal

def strip_slashes(name):
    """Remove slashes from the beginning and end of a part/URL."""
    if name.startswith('/'):
        name = name[1:]
    if name.endswith('/'):
        name = name[:-1]
    return name

class Route(object):
    """The Route object holds a route recognition and generation routine.
    
    See Route.__init__ docs for usage.
    """
    
    def __init__(self, routepath, **kargs):
        """Initialize a route, with a given routepath for matching/generation
        
        The set of keyword args will be used as defaults.
        
        Usage::
        
            >>> from routes.base import Route
            >>> newroute = Route(':controller/:action/:id')
            >>> newroute.defaults
            {'action': 'index', 'id': None}
            >>> newroute = Route('date/:year/:month/:day', controller="blog", 
            ...     action="view")
            >>> newroute = Route('archives/:page', controller="blog", 
            ...     action="by_page", requirements = { 'page':'\d{1,2}' })
            >>> newroute.reqs
            {'page': '\\\d{1,2}'}
        
        .. Note:: 
            Route is generally not called directly, a Mapper instance connect 
            method should be used to add routes.
        """
        
        self.routepath = routepath
        self.sub_domains = False
        self.prior = None
        self.encoding = kargs.pop('_encoding', 'utf-8')
        self.decode_errors = 'replace'
        
        # Don't bother forming stuff we don't need if its a static route
        self.static = kargs.get('_static', False)
        self.filter = kargs.pop('_filter', None)
        self.absolute = kargs.pop('_absolute', False)
        
        # Pull out the member/collection name if present, this applies only to
        # map.resource
        self.member_name = kargs.pop('_member_name', None)
        self.collection_name = kargs.pop('_collection_name', None)
        self.parent_resource = kargs.pop('_parent_resource', None)
        
        # Pull out route conditions
        self.conditions = kargs.pop('conditions', None)
        
        # Determine if explicit behavior should be used
        self.explicit = kargs.pop('_explicit', False)
        
        # reserved keys that don't count
        reserved_keys = ['requirements']
        
        # special chars to indicate a natural split in the URL
        self.done_chars = ('/', ',', ';', '.', '#')
        
        # Strip preceding '/' if present
        if routepath.startswith('/'):
            routepath = routepath[1:]
        
        # Build our routelist, and the keys used in the route
        self.routelist = routelist = self._pathkeys(routepath)
        routekeys = frozenset([key['name'] for key in routelist \
                               if isinstance(key, dict)])
        
        # Build a req list with all the regexp requirements for our args
        self.reqs = kargs.get('requirements', {})
        self.req_regs = {}
        for key, val in self.reqs.iteritems():
            self.req_regs[key] = re.compile('^' + val + '$')
        # Update our defaults and set new default keys if needed. defaults
        # needs to be saved
        (self.defaults, defaultkeys) = self._defaults(routekeys, 
                                                      reserved_keys, kargs)
        # Save the maximum keys we could utilize
        self.maxkeys = defaultkeys | routekeys
        
        # Populate our minimum keys, and save a copy of our backward keys for
        # quicker generation later
        (self.minkeys, self.routebackwards) = self._minkeys(routelist[:])
        
        # Populate our hardcoded keys, these are ones that are set and don't 
        # exist in the route
        self.hardcoded = frozenset([key for key in self.maxkeys \
            if key not in routekeys and self.defaults[key] is not None])
    
    def make_unicode(self, s):
        """Transform the given argument into a unicode string."""
        if isinstance(s, unicode):
            return s
        elif isinstance(s, str):
            return s.decode(self.encoding)
        else:
            return unicode(s)
    
    def _pathkeys(self, routepath):
        """Utility function to walk the route, and pull out the valid 
        dynamic/wildcard keys."""
        collecting = False
        current = ''
        done_on = ''
        var_type = ''
        just_started = False
        routelist = []
        for char in routepath:
            if char in [':', '*'] and not collecting:
                just_started = True
                collecting = True
                var_type = char
                if len(current) > 0:
                    routelist.append(current)
                    current = ''
            elif collecting and just_started:
                just_started = False
                if char == '(':
                    done_on = ')'
                else:
                    current = char
                    done_on = self.done_chars + ('-',)
            elif collecting and char not in done_on:
                current += char
            elif collecting:
                collecting = False
                routelist.append(dict(type=var_type, name=current))
                if char in self.done_chars:
                    routelist.append(char)
                done_on = var_type = current = ''
            else:
                current += char
        if collecting:
            routelist.append(dict(type=var_type, name=current))
        elif current:
            routelist.append(current)
        return routelist

    def _minkeys(self, routelist):
        """Utility function to walk the route backwards
        
        Will also determine the minimum keys we can handle to generate a 
        working route.
        
        routelist is a list of the '/' split route path
        defaults is a dict of all the defaults provided for the route
        """
        minkeys = []
        backcheck = routelist[:]
        gaps = False
        backcheck.reverse()
        for part in backcheck:
            if not isinstance(part, dict) and part not in self.done_chars:
                gaps = True
                continue
            elif not isinstance(part, dict):
                continue
            key = part['name']
            if self.defaults.has_key(key) and not gaps:
                continue
            minkeys.append(key)
            gaps = True
        return  (frozenset(minkeys), backcheck)
    
    def _defaults(self, routekeys, reserved_keys, kargs):
        """Creates default set with values stringified
        
        Put together our list of defaults, stringify non-None values
        and add in our action/id default if they use it and didn't specify it
        
        defaultkeys is a list of the currently assumed default keys
        routekeys is a list of the keys found in the route path
        reserved_keys is a list of keys that are not
        
        """
        defaults = {}
        # Add in a controller/action default if they don't exist
        if 'controller' not in routekeys and 'controller' not in kargs \
           and not self.explicit:
            kargs['controller'] = 'content'
        if 'action' not in routekeys and 'action' not in kargs \
           and not self.explicit:
            kargs['action'] = 'index'
        defaultkeys = frozenset([key for key in kargs.keys() \
                                 if key not in reserved_keys])
        for key in defaultkeys:
            if kargs[key] is not None:
                defaults[key] = self.make_unicode(kargs[key])
            else:
                defaults[key] = None
        if 'action' in routekeys and not defaults.has_key('action') \
           and not self.explicit:
            defaults['action'] = 'index'
        if 'id' in routekeys and not defaults.has_key('id') \
           and not self.explicit:
            defaults['id'] = None
        newdefaultkeys = frozenset([key for key in defaults.keys() \
                                    if key not in reserved_keys])
        
        return (defaults, newdefaultkeys)
        
    def makeregexp(self, clist):
        """Create a regular expression for matching purposes
        
        Note: This MUST be called before match can function properly.
        
        clist should be a list of valid controller strings that can be 
        matched, for this reason makeregexp should be called by the web 
        framework after it knows all available controllers that can be 
        utilized.
        """        
        (reg, noreqs, allblank) = self.buildnextreg(self.routelist, clist)
        
        if not reg:
            reg = '/'
        reg = reg + '(/)?' + '$'
        if not reg.startswith('/'):
            reg = '/' + reg
        reg = '^' + reg
        
        self.regexp = reg
        self.regmatch = re.compile(reg)
    
    def buildnextreg(self, path, clist):
        """Recursively build our regexp given a path, and a controller list.
        
        Returns the regular expression string, and two booleans that can be
        ignored as they're only used internally by buildnextreg.
        """
        if path:
            part = path[0]
        else:
            part = ''
        reg = ''
        
        # noreqs will remember whether the remainder has either a string 
        # match, or a non-defaulted regexp match on a key, allblank remembers
        # if the rest could possible be completely empty
        (rest, noreqs, allblank) = ('', True, True)
        if len(path[1:]) > 0:
            self.prior = part
            (rest, noreqs, allblank) = self.buildnextreg(path[1:], clist)
        
        if isinstance(part, dict) and part['type'] == ':':
            var = part['name']
            partreg = ''
            
            # First we plug in the proper part matcher
            if self.reqs.has_key(var):
                partreg = '(?P<' + var + '>' + self.reqs[var] + ')'
            elif var == 'controller':
                partreg = '(?P<' + var + '>' + '|'.join(map(re.escape, clist))
                partreg += ')'
            elif self.prior in ['/', '#']:
                partreg = '(?P<' + var + '>[^' + self.prior + ']+?)'
            else:
                if not rest:
                    partreg = '(?P<' + var + '>[^%s]+?)' % '/'
                else:
                    end = ''.join(self.done_chars)
                    rem = rest
                    if rem[0] == '\\' and len(rem) > 1:
                        rem = rem[1]
                    elif rem.startswith('(\\') and len(rem) > 2:
                        rem = rem[2]
                    else:
                        rem = end
                    rem = frozenset(rem) | frozenset(['/'])
                    partreg = '(?P<' + var + '>[^%s]+?)' % ''.join(rem)
            
            if self.reqs.has_key(var):
                noreqs = False
            if not self.defaults.has_key(var): 
                allblank = False
                noreqs = False
            
            # Now we determine if its optional, or required. This changes 
            # depending on what is in the rest of the match. If noreqs is 
            # true, then its possible the entire thing is optional as there's
            # no reqs or string matches.
            if noreqs:
                # The rest is optional, but now we have an optional with a 
                # regexp. Wrap to ensure that if we match anything, we match
                # our regexp first. It's still possible we could be completely
                # blank as we have a default
                if self.reqs.has_key(var) and self.defaults.has_key(var):
                    reg = '(' + partreg + rest + ')?'
                
                # Or we have a regexp match with no default, so now being 
                # completely blank form here on out isn't possible
                elif self.reqs.has_key(var):
                    allblank = False
                    reg = partreg + rest
                
                # If the character before this is a special char, it has to be
                # followed by this
                elif self.defaults.has_key(var) and \
                     self.prior in (',', ';', '.'):
                    reg = partreg + rest
                
                # Or we have a default with no regexp, don't touch the allblank
                elif self.defaults.has_key(var):
                    reg = partreg + '?' + rest
                
                # Or we have a key with no default, and no reqs. Not possible
                # to be all blank from here
                else:
                    allblank = False
                    reg = partreg + rest
            # In this case, we have something dangling that might need to be
            # matched
            else:
                # If they can all be blank, and we have a default here, we know
                # its safe to make everything from here optional. Since 
                # something else in the chain does have req's though, we have
                # to make the partreg here required to continue matching
                if allblank and self.defaults.has_key(var):
                    reg = '(' + partreg + rest + ')?'
                    
                # Same as before, but they can't all be blank, so we have to 
                # require it all to ensure our matches line up right
                else:
                    reg = partreg + rest
        elif isinstance(part, dict) and part['type'] == '*':
            var = part['name']
            if noreqs:
                if self.defaults.has_key(var):
                    reg = '(?P<' + var + '>.*)' + rest
                else:
                    reg = '(?P<' + var + '>.*)' + rest
                    allblank = False
                    noreqs = False
            else:
                if allblank and self.defaults.has_key(var):
                    reg = '(?P<' + var + '>.*)' + rest
                elif self.defaults.has_key(var):
                    reg = '(?P<' + var + '>.*)' + rest
                else:
                    allblank = False
                    noreqs = False
                    reg = '(?P<' + var + '>.*)' + rest
        elif part and part[-1] in self.done_chars:
            if allblank:
                reg = re.escape(part[:-1]) + '(' + re.escape(part[-1]) + rest
                reg += ')?'
            else:
                allblank = False
                reg = re.escape(part) + rest
        
        # We have a normal string here, this is a req, and it prevents us from 
        # being all blank
        else:
            noreqs = False
            allblank = False
            reg = re.escape(part) + rest
        
        return (reg, noreqs, allblank)
    
    def match(self, url, environ=None, sub_domains=False, 
              sub_domains_ignore=None, domain_match=''):
        """Match a url to our regexp. 
        
        While the regexp might match, this operation isn't
        guaranteed as there's other factors that can cause a match to fail 
        even though the regexp succeeds (Default that was relied on wasn't 
        given, requirement regexp doesn't pass, etc.).
        
        Therefore the calling function shouldn't assume this will return a
        valid dict, the other possible return is False if a match doesn't work
        out.
        """
        # Static routes don't match, they generate only
        if self.static:
            return False
        
        if url.endswith('/') and len(url) > 1:
            url = url[:-1]
        match = self.regmatch.match(url)
        
        if not match:
            return False
            
        if not environ:
            environ = {}
        
        sub_domain = None
        
        if environ.get('HTTP_HOST') and sub_domains:
            host = environ['HTTP_HOST'].split(':')[0]
            sub_match = re.compile('^(.+?)\.%s$' % domain_match)
            subdomain = re.sub(sub_match, r'\1', host)
            if subdomain not in sub_domains_ignore and host != subdomain:
                sub_domain = subdomain
        
        if self.conditions:
            if self.conditions.has_key('method') and \
                environ.get('REQUEST_METHOD') not in self.conditions['method']:
                return False
            
            # Check sub-domains?
            use_sd = self.conditions.get('sub_domain')
            if use_sd and not sub_domain:
                return False
            if isinstance(use_sd, list) and sub_domain not in use_sd:
                return False
        
        matchdict = match.groupdict()
        result = {}
        extras = frozenset(self.defaults.keys()) - frozenset(matchdict.keys())
        for key, val in matchdict.iteritems():
            if key != 'path_info' and self.encoding:
                # change back into python unicode objects from the URL 
                # representation
                try:
                    val = val and val.decode(self.encoding, self.decode_errors)
                except UnicodeDecodeError:
                    return False
            
            if not val and self.defaults.has_key(key) and self.defaults[key]:
                result[key] = self.defaults[key]
            else:
                result[key] = val
        for key in extras:
            result[key] = self.defaults[key]
        
        # Add the sub-domain if there is one
        if sub_domains:
            result['sub_domain'] = sub_domain
        
        # If there's a function, call it with environ and expire if it
        # returns False
        if self.conditions and self.conditions.has_key('function') and \
            not self.conditions['function'](environ, result):
            return False
        
        return result
    
    def generate(self, _ignore_req_list=False, _append_slash=False, **kargs):
        """Generate a URL from ourself given a set of keyword arguments
        
        Toss an exception if this
        set of keywords would cause a gap in the url.
        
        """
        # Verify that our args pass any regexp requirements
        if not _ignore_req_list:
            for key in self.reqs.keys():
                val = kargs.get(key)
                if val and not self.req_regs[key].match(self.make_unicode(val)):
                    return False
        
        # Verify that if we have a method arg, its in the method accept list. 
        # Also, method will be changed to _method for route generation
        meth = kargs.get('method')
        if meth:
            if self.conditions and 'method' in self.conditions \
                and meth.upper() not in self.conditions['method']:
                return False
            kargs.pop('method')
        
        routelist = self.routebackwards
        urllist = []
        gaps = False
        for part in routelist:
            if isinstance(part, dict) and part['type'] == ':':
                arg = part['name']
                
                # For efficiency, check these just once
                has_arg = kargs.has_key(arg)
                has_default = self.defaults.has_key(arg)
                
                # Determine if we can leave this part off
                # First check if the default exists and wasn't provided in the 
                # call (also no gaps)
                if has_default and not has_arg and not gaps:
                    continue
                    
                # Now check to see if there's a default and it matches the 
                # incoming call arg
                if (has_default and has_arg) and self.make_unicode(kargs[arg]) == \
                    self.make_unicode(self.defaults[arg]) and not gaps: 
                    continue
                
                # We need to pull the value to append, if the arg is None and 
                # we have a default, use that
                if has_arg and kargs[arg] is None and has_default and not gaps:
                    continue
                
                # Otherwise if we do have an arg, use that
                elif has_arg:
                    val = kargs[arg]
                
                elif has_default and self.defaults[arg] is not None:
                    val = self.defaults[arg]
                
                # No arg at all? This won't work
                else:
                    return False
                
                urllist.append(url_quote(val, self.encoding))
                if has_arg:
                    del kargs[arg]
                gaps = True
            elif isinstance(part, dict) and part['type'] == '*':
                arg = part['name']
                kar = kargs.get(arg)
                if kar is not None:
                    urllist.append(url_quote(kar, self.encoding))
                    gaps = True
            elif part and part[-1] in self.done_chars:
                if not gaps and part in self.done_chars:
                    continue
                elif not gaps:
                    urllist.append(part[:-1])
                    gaps = True
                else:
                    gaps = True
                    urllist.append(part)
            else:
                gaps = True
                urllist.append(part)
        urllist.reverse()
        url = ''.join(urllist)
        if not url.startswith('/'):
            url = '/' + url
        extras = frozenset(kargs.keys()) - self.maxkeys
        if extras:
            if _append_slash and not url.endswith('/'):
                url += '/'
            url += '?'
            fragments = []
            # don't assume the 'extras' set preserves order: iterate
            # through the ordered kargs instead
            for key in kargs:
                if key not in extras:
                    continue
                if key == 'action' or key == 'controller':
                    continue
                val = kargs[key]
                if isinstance(val, (tuple, list)):
                    for value in val:
                        fragments.append((key, value))
                else:
                    fragments.append((key, val))
                
            url += urllib.urlencode(fragments)
        elif _append_slash and not url.endswith('/'):
            url += '/'
        return url
    

class Mapper(object):
    """Mapper handles URL generation and URL recognition in a web application.
    
    Mapper is built handling dictionary's. It is assumed that the web application will handle
    the dictionary returned by URL recognition to dispatch appropriately.
    
    URL generation is done by passing keyword parameters into the generate function, a URL is then
    returned.
    """
    def __init__(self, controller_scan=controller_scan, directory=None, 
                 always_scan=False, register=True, explicit=False):
        """Create a new Mapper instance
        
        All keyword arguments are optional.
        
        ``controller_scan``
            Function reference that will be used to return a list of valid 
            controllers used during URL matching. If ``directory`` keyword arg
            is present, it will be passed into the function during its call. 
            This option defaults to a function that will scan a directory for
            controllers.
        
        ``directory``
            Passed into controller_scan for the directory to scan. It should be
            an absolute path if using the default ``controller_scan`` function.
        
        ``always_scan``
            Whether or not the ``controller_scan`` function should be run 
            during every URL match. This is typically a good idea during 
            development so the server won't need to be restarted anytime a 
            controller is added.
        
        ``register``
            Boolean used to determine if the Mapper should use 
            ``request_config`` to register itself as the mapper. Since it's 
            done on a thread-local basis, this is typically best used during 
            testing though it won't hurt in other cases.
        
        ``explicit``
            Boolean used to determine if routes should be connected with 
            implicit defaults of::
                
                {'controller':'content','action':'index','id':None}
            
            When set to True, these defaults will not be added to route
            connections and ``url_for`` will not use Route memory.
        
        Additional attributes that may be set after mapper initialization (ie,
        map.ATTRIBUTE = 'something'):
        
        ``encoding``
            Used to indicate alternative encoding/decoding systems to use with
            both incoming URL's, and during Route generation when passed a 
            Unicode string. Defaults to 'utf-8'.
        
        ``decode_errors``
            How to handle errors in the encoding, generally ignoring any chars 
            that don't convert should be sufficient. Defaults to 'ignore'.
        
        ``hardcode_names``
            Whether or not Named Routes result in the default options for the 
            route being used *or* if they actually force url generation to use
            the route. Defaults to False.
        """
        self.matchlist = []
        self.maxkeys = {}
        self.minkeys = {}
        self.urlcache = {}
        self._created_regs = False
        self._created_gens = False
        self.prefix = None
        self.req_data = threadinglocal.local()
        self.directory = directory
        self.always_scan = always_scan
        self.controller_scan = controller_scan
        self._regprefix = None
        self._routenames = {}
        self.debug = False
        self.append_slash = False
        self.sub_domains = False
        self.sub_domains_ignore = []
        self.domain_match = '[^\.\/]+?\.[^\.\/]+'
        self.explicit = explicit
        self.encoding = 'utf-8'
        self.decode_errors = 'ignore'
        self.hardcode_names = False
        if register:
            config = request_config()
            config.mapper = self
    
    def _envget(self):
        return getattr(self.req_data, 'environ', None)
    def _envset(self, env):
        self.req_data.environ = env
    def _envdel(self):
        del self.req_data.environ
    environ = property(_envget, _envset, _envdel)

    def connect(self, *args, **kargs):
        """Create and connect a new Route to the Mapper.
        
        Usage:
        
        .. code-block:: Python
        
            m = Mapper()
            m.connect(':controller/:action/:id')
            m.connect('date/:year/:month/:day', controller="blog", action="view")
            m.connect('archives/:page', controller="blog", action="by_page",
            requirements = { 'page':'\d{1,2}' })
            m.connect('category_list', 'archives/category/:section', controller='blog', action='category',
            section='home', type='list')
            m.connect('home', '', controller='blog', action='view', section='home')
        
        """
        routename = None
        if len(args) > 1:
            routename = args[0]
            args = args[1:]
        if '_explicit' not in kargs:
            kargs['_explicit'] = self.explicit
        route = Route(*args, **kargs)
        
        # Apply encoding and errors if its not the defaults and the route 
        # didn't have one passed in.
        if (self.encoding != 'utf-8' or self.decode_errors != 'ignore') and \
           '_encoding' not in kargs:
            route.encoding = self.encoding
            route.decode_errors = self.decode_errors
        
        self.matchlist.append(route)
        if routename:
            self._routenames[routename] = route
        if route.static:
            return
        exists = False
        for key in self.maxkeys:
            if key == route.maxkeys:
                self.maxkeys[key].append(route)
                exists = True
                break
        if not exists:
            self.maxkeys[route.maxkeys] = [route]
        self._created_gens = False
    
    def _create_gens(self):
        """Create the generation hashes for route lookups"""
        # Use keys temporailly to assemble the list to avoid excessive
        # list iteration testing with "in"
        controllerlist = {}
        actionlist = {}
        
        # Assemble all the hardcoded/defaulted actions/controllers used
        for route in self.matchlist:
            if route.static:
                continue
            if route.defaults.has_key('controller'):
                controllerlist[route.defaults['controller']] = True
            if route.defaults.has_key('action'):
                actionlist[route.defaults['action']] = True
        
        # Setup the lists of all controllers/actions we'll add each route
        # to. We include the '*' in the case that a generate contains a
        # controller/action that has no hardcodes
        controllerlist = controllerlist.keys() + ['*']
        actionlist = actionlist.keys() + ['*']
        
        # Go through our list again, assemble the controllers/actions we'll
        # add each route to. If its hardcoded, we only add it to that dict key.
        # Otherwise we add it to every hardcode since it can be changed.
        gendict = {} # Our generated two-deep hash
        for route in self.matchlist:
            if route.static:
                continue
            clist = controllerlist
            alist = actionlist
            if 'controller' in route.hardcoded:
                clist = [route.defaults['controller']]
            if 'action' in route.hardcoded:
                alist = [unicode(route.defaults['action'])]
            for controller in clist:
                for action in alist:
                    actiondict = gendict.setdefault(controller, {})
                    actiondict.setdefault(action, ([], {}))[0].append(route)
        self._gendict = gendict
        self._created_gens = True
    
    def create_regs(self, clist=None):
        """Creates regular expressions for all connected routes"""
        if clist is None:
            if self.directory:
                clist = self.controller_scan(self.directory)
            else:
                clist = self.controller_scan()
            
        for key, val in self.maxkeys.iteritems():
            for route in val:
                route.makeregexp(clist)
        
        
        # Create our regexp to strip the prefix
        if self.prefix:
            self._regprefix = re.compile(self.prefix + '(.*)')
        self._created_regs = True
    
    def _match(self, url):
        """Internal Route matcher
        
        Matches a URL against a route, and returns a tuple of the match dict
        and the route object if a match is successfull, otherwise it returns 
        empty.
        
        For internal use only.
        """
        if not self._created_regs and self.controller_scan:
            self.create_regs()
        elif not self._created_regs:
            raise RouteException("You must generate the regular expressions before matching.")
        
        if self.always_scan:
            self.create_regs()
        
        matchlog = []
        if self.prefix:
            if re.match(self._regprefix, url):
                url = re.sub(self._regprefix, r'\1', url)
                if not url:
                    url = '/'
            else:
                return (None, None, matchlog)
        for route in self.matchlist:
            if route.static:
                if self.debug:
                    matchlog.append(dict(route=route, static=True))
                continue
            match = route.match(url, self.environ, self.sub_domains, 
                self.sub_domains_ignore, self.domain_match)
            if self.debug:
                matchlog.append(dict(route=route, regexp=bool(match)))
            if match:
                return (match, route, matchlog)
        return (None, None, matchlog)
        
    def match(self, url):
        """Match a URL against against one of the routes contained.
        
        Will return None if no valid match is found.
        
        .. code-block:: Python
            
            resultdict = m.match('/joe/sixpack')
        
        """
        if not url:
            raise RouteException('No URL provided, the minimum URL necessary'
                                 ' to match is "/".')
        
        result = self._match(url)
        if self.debug:
            return result[0], result[1], result[2]
        if result[0]:
            return result[0]
        return None
        
    def routematch(self, url):
        """Match a URL against against one of the routes contained.
        
        Will return None if no valid match is found, otherwise a
        result dict and a route object is returned.
        
        .. code-block:: Python
        
            resultdict, route_obj = m.match('/joe/sixpack')
        
        """
        result = self._match(url)
        if self.debug:
            return result[0], result[1], result[2]
        if result[0]:
            return result[0], result[1]
        return None
        
    
    def generate(self, *args, **kargs):
        """Generate a route from a set of keywords
        
        Returns the url text, or None if no URL could be generated.
        
        .. code-block:: Python
            
            m.generate(controller='content',action='view',id=10)
        
        """
        # Generate ourself if we haven't already
        if not self._created_gens:
            self._create_gens()
        
        if self.append_slash:
            kargs['_append_slash'] = True
                
        if not self.explicit:
            if 'controller' not in kargs:
                kargs['controller'] = 'content'
            if 'action' not in kargs:
                kargs['action'] = 'index'
        
        controller = kargs.get('controller', None)
        action = kargs.get('action', None)

        # If the URL didn't depend on the SCRIPT_NAME, we'll cache it
        # keyed by just by kargs; otherwise we need to cache it with
        # both SCRIPT_NAME and kargs:
        cache_key = unicode(args).encode('utf8') + unicode(kargs).encode('utf8')
        if self.environ:
            cache_key_script_name = '%s:%s' % (
                self.environ.get('SCRIPT_NAME', ''), cache_key)
        else:
            cache_key_script_name = cache_key
        
        # Check the url cache to see if it exists, use it if it does
        for key in [cache_key, cache_key_script_name]:
            if key in self.urlcache:
                return self.urlcache[key]
        
        actionlist = self._gendict.get(controller) or self._gendict.get('*')
        if not actionlist:
            return None
        (keylist, sortcache) = actionlist.get(action) or \
                               actionlist.get('*', (None, None))
        if not keylist:
            return None
        
        keys = frozenset(kargs.keys())
        cacheset = False
        cachekey = unicode(keys)
        cachelist = sortcache.get(cachekey)
        if args:
            keylist = args
        elif cachelist:
            keylist = cachelist
        else:
            cacheset = True
            newlist = []
            for route in keylist:
                if len(route.minkeys-keys) == 0:
                    newlist.append(route)
            keylist = newlist
            
            def keysort(a, b):
                """Sorts two sets of sets, to order them ideally for
                matching."""
                am = a.minkeys
                a = a.maxkeys
                b = b.maxkeys
                
                lendiffa = len(keys^a)
                lendiffb = len(keys^b)
                # If they both match, don't switch them
                if lendiffa == 0 and lendiffb == 0:
                    return 0
                
                # First, if a matches exactly, use it
                if lendiffa == 0:
                    return -1
                
                # Or b matches exactly, use it
                if lendiffb == 0:
                    return 1
                
                # Neither matches exactly, return the one with the most in 
                # common
                if cmp(lendiffa, lendiffb) != 0:
                    return cmp(lendiffa, lendiffb)
                
                # Neither matches exactly, but if they both have just as much 
                # in common
                if len(keys&b) == len(keys&a):
                    # Then we return the shortest of the two
                    return cmp(len(a), len(b))
                
                # Otherwise, we return the one that has the most in common
                else:
                    return cmp(len(keys&b), len(keys&a))
            
            keylist.sort(keysort)
            if cacheset:
                sortcache[cachekey] = keylist
        
        for route in keylist:
            fail = False
            for key in route.hardcoded:
                kval = kargs.get(key)
                if not kval:
                    continue
                if kval != route.defaults[key]:
                    fail = True
                    break
            if fail:
                continue
            path = route.generate(**kargs)
            if path:
                if self.prefix:
                    path = self.prefix + path
                if self.environ and self.environ.get('SCRIPT_NAME', '') != '' \
                    and not route.absolute:
                    path = self.environ['SCRIPT_NAME'] + path
                    key = cache_key_script_name
                else:
                    key = cache_key
                if self.urlcache is not None:
                    self.urlcache[key] = str(path)
                return str(path)
            else:
                continue
        return None
    
    def resource(self, member_name, collection_name, **kwargs):
        """Generate routes for a controller resource
        
        The member_name name should be the appropriate singular version of the
        resource given your locale and used with members of the collection.
        The collection_name name will be used to refer to the resource 
        collection methods and should be a plural version of the member_name
        argument. By default, the member_name name will also be assumed to map
        to a controller you create.
        
        The concept of a web resource maps somewhat directly to 'CRUD' 
        operations. The overlying things to keep in mind is that mapping a
        resource is about handling creating, viewing, and editing that
        resource.
        
        All keyword arguments are optional.
        
        ``controller``
            If specified in the keyword args, the controller will be the actual
            controller used, but the rest of the naming conventions used for
            the route names and URL paths are unchanged.
        
        ``collection``
            Additional action mappings used to manipulate/view the entire set of
            resources provided by the controller.
            
            Example::
                
                map.resource('message', 'messages', collection={'rss':'GET'})
                # GET /message/rss (maps to the rss action)
                # also adds named route "rss_message"
        
        ``member``
            Additional action mappings used to access an individual 'member'
            of this controllers resources.
            
            Example::
                
                map.resource('message', 'messages', member={'mark':'POST'})
                # POST /message/1/mark (maps to the mark action)
                # also adds named route "mark_message"
        
        ``new``
            Action mappings that involve dealing with a new member in the
            controller resources.
            
            Example::
                
                map.resource('message', 'messages', new={'preview':'POST'})
                # POST /message/new/preview (maps to the preview action)
                # also adds a url named "preview_new_message"
        
        ``path_prefix``
            Prepends the URL path for the Route with the path_prefix given.
            This is most useful for cases where you want to mix resources
            or relations between resources.
        
        ``name_prefix``
            Perpends the route names that are generated with the name_prefix
            given. Combined with the path_prefix option, it's easy to
            generate route names and paths that represent resources that are
            in relations.
            
            Example::
                
                map.resource('message', 'messages', controller='categories', 
                    path_prefix='/category/:category_id', 
                    name_prefix="category_")
                # GET /category/7/message/1
                # has named route "category_message"
                
        ``parent_resource`` 
            A ``dict`` containing information about the parent resource, for 
            creating a nested resource. It should contain the ``member_name`` 
            and ``collection_name`` of the parent resource. This ``dict`` will 
            be available via the associated ``Route`` object which can be 
            accessed during a request via ``request.environ['routes.route']`` 
 
            If ``parent_resource`` is supplied and ``path_prefix`` isn't, 
            ``path_prefix`` will be generated from ``parent_resource`` as  
            "<parent collection name>/:<parent member name>_id". 

            If ``parent_resource`` is supplied and ``name_prefix`` isn't, 
            ``name_prefix`` will be generated from ``parent_resource`` as  
            "<parent member name>_". 
 
            Example:: 
 
                >>> from routes.util import url_for 
                >>> m = Mapper() 
                >>> m.resource('location', 'locations', 
                ...            parent_resource=dict(member_name='region', 
                ...                                 collection_name='regions')) 
                >>> # path_prefix is "regions/:region_id" 
                >>> # name prefix is "region_"  
                >>> url_for('region_locations', region_id=13) 
                '/regions/13/locations'
                >>> url_for('region_new_location', region_id=13) 
                '/regions/13/locations/new'
                >>> url_for('region_location', region_id=13, id=60) 
                '/regions/13/locations/60'
                >>> url_for('region_edit_location', region_id=13, id=60) 
                '/regions/13/locations/60/edit'

            Overriding generated ``path_prefix``::

                >>> m = Mapper()
                >>> m.resource('location', 'locations',
                ...            parent_resource=dict(member_name='region',
                ...                                 collection_name='regions'),
                ...            path_prefix='areas/:area_id')
                >>> # name prefix is "region_"
                >>> url_for('region_locations', area_id=51)
                '/areas/51/locations'

            Overriding generated ``name_prefix``::

                >>> m = Mapper()
                >>> m.resource('location', 'locations',
                ...            parent_resource=dict(member_name='region',
                ...                                 collection_name='regions'),
                ...            name_prefix='')
                >>> # path_prefix is "regions/:region_id" 
                >>> url_for('locations', region_id=51)
                '/regions/51/locations'

        """
        collection = kwargs.pop('collection', {})
        member = kwargs.pop('member', {})
        new = kwargs.pop('new', {})
        path_prefix = kwargs.pop('path_prefix', None)
        name_prefix = kwargs.pop('name_prefix', None)
        parent_resource = kwargs.pop('parent_resource', None)
        
        # Generate ``path_prefix`` if ``path_prefix`` wasn't specified and 
        # ``parent_resource`` was. Likewise for ``name_prefix``. Make sure
        # that ``path_prefix`` and ``name_prefix`` *always* take precedence if
        # they are specified--in particular, we need to be careful when they
        # are explicitly set to "".
        if parent_resource is not None: 
            if path_prefix is None: 
                path_prefix = '%s/:%s_id' % (parent_resource['collection_name'], 
                                             parent_resource['member_name']) 
            if name_prefix is None:
                name_prefix = '%s_' % parent_resource['member_name']
        else:
            if path_prefix is None: path_prefix = ''
            if name_prefix is None: name_prefix = ''
        
        # Ensure the edit and new actions are in and GET
        member['edit'] = 'GET'
        new.update({'new': 'GET'})
        
        # Make new dict's based off the old, except the old values become keys,
        # and the old keys become items in a list as the value
        def swap(dct, newdct):
            """Swap the keys and values in the dict, and uppercase the values
            from the dict during the swap."""
            for key, val in dct.iteritems():
                newdct.setdefault(val.upper(), []).append(key)
            return newdct
        collection_methods = swap(collection, {})
        member_methods = swap(member, {})
        new_methods = swap(new, {})
        
        # Insert create, update, and destroy methods
        collection_methods.setdefault('POST', []).insert(0, 'create')
        member_methods.setdefault('PUT', []).insert(0, 'update')
        member_methods.setdefault('DELETE', []).insert(0, 'delete')
        
        # If there's a path prefix option, use it with the controller
        controller = strip_slashes(collection_name)
        path_prefix = strip_slashes(path_prefix)
        if path_prefix:
            path = path_prefix + '/' + controller
        else:
            path = controller
        collection_path = path
        new_path = path + "/new"
        member_path = path + "/:(id)"
        
        options = { 
            'controller': kwargs.get('controller', controller),
            '_member_name': member_name,
            '_collection_name': collection_name,
            '_parent_resource': parent_resource,
        }
        
        def requirements_for(meth):
            """Returns a new dict to be used for all route creation as the
            route options"""
            opts = options.copy()
            if method != 'any': 
                opts['conditions'] = {'method':[meth.upper()]}
            return opts
        
        # Add the routes for handling collection methods
        for method, lst in collection_methods.iteritems():
            primary = (method != 'GET' and lst.pop(0)) or None
            route_options = requirements_for(method)
            for action in lst:
                route_options['action'] = action
                route_name = "%s%s_%s" % (name_prefix, action, collection_name)
                self.connect(route_name, "%s/%s" % (collection_path, action),
                                                    **route_options)
                self.connect("formatted_" + route_name, "%s/%s.:(format)" % \
                             (collection_path, action), **route_options)
            if primary:
                route_options['action'] = primary
                self.connect(collection_path, **route_options)
                self.connect("%s.:(format)" % collection_path, **route_options)
        
        # Specifically add in the built-in 'index' collection method and its 
        # formatted version
        self.connect(name_prefix + collection_name, collection_path, 
                     action='index', conditions={'method':['GET']}, **options)
        self.connect("formatted_" + name_prefix + collection_name, 
            collection_path + ".:(format)", action='index', 
            conditions={'method':['GET']}, **options)
        
        # Add the routes that deal with new resource methods
        for method, lst in new_methods.iteritems():
            route_options = requirements_for(method)
            for action in lst:
                path = (action == 'new' and new_path) or "%s/%s" % (new_path, 
                                                                    action)
                name = "new_" + member_name
                if action != 'new':
                    name = action + "_" + name
                route_options['action'] = action
                self.connect(name_prefix + name, path, **route_options)
                path = (action == 'new' and new_path + '.:(format)') or \
                    "%s/%s.:(format)" % (new_path, action)
                self.connect("formatted_" + name_prefix + name, path, 
                             **route_options)
        
        requirements_regexp = '[\w\-_\s]+'

        # Add the routes that deal with member methods of a resource
        for method, lst in member_methods.iteritems():
            route_options = requirements_for(method)
            route_options['requirements'] = {'id':requirements_regexp}
            if method not in ['POST', 'GET', 'any']:
                primary = lst.pop(0)
            else:
                primary = None
            for action in lst:
                route_options['action'] = action
                self.connect("%s%s_%s" % (name_prefix, action, member_name),
                    "%s/%s" % (member_path, action), **route_options)
                self.connect("formatted_%s%s_%s" % (name_prefix, action, 
                                                    member_name),
                    "%s/%s.:(format)" % (member_path, action), **route_options)
            if primary:
                route_options['action'] = primary
                self.connect(member_path, **route_options)
        
        # Specifically add the member 'show' method
        route_options = requirements_for('GET')
        route_options['action'] = 'show'
        route_options['requirements'] = {'id':requirements_regexp}
        self.connect(name_prefix + member_name, member_path, **route_options)
        self.connect("formatted_" + name_prefix + member_name, 
                     member_path + ".:(format)", **route_options)
    
