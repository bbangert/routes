#
#  base
#
#  Created by Ben Bangert on 2005-08-08.
#  Copyright (c) 2005 Parachute. All rights reserved.
#

import re, time, sys
from urllib import quote_plus

def quote(string):
    return quote_plus(str(string), '/')

if sys.version < '2.4':
    from sets import ImmutableSet as frozenset

class Route(object):
    """
    The Route object holds a route recognition and generation routine.
    
    See __init__ docs for usage.
    """
    
    def __init__(self, routepath, **kargs):
        """
        Initialize a route, with a given routepath for matching/generation, and a set of keyword
        args that setup defaults.
        
        Usage:
        newroute = Route(':controller/:action/:id')
        newroute = Route('date/:year/:month/:day', controller="blog", action="view")
        newroute = Route('archives/:page', controller="blog", action="by_page",
                         requirements = { 'page':'\d{1,2}' })

        Note: Route is generally not called directly, a Mapper instance connect method should
        be used to add routes.
        """
        # reserved keys that don't count
        reserved_keys = ['requirements']
        
        # Build our routelist, and the keys used in the route
        self.routelist = routelist = routepath.split('/')
        routekeys = frozenset([key[1:] for key in routelist if (key.startswith(':') or key.startswith('*')) and key not in reserved_keys])
        
        
        # Build a req list with all the regexp requirements for our args
        self.reqs = kargs.get('requirements', {})
        self.req_regs = {}
        for key,val in self.reqs.iteritems():
            self.req_regs[key] = re.compile('^' + val + '$')
        # Update our defaults and set new default keys if needed. defaults needs to be saved
        (self.defaults, defaultkeys) = self._defaults(routekeys, reserved_keys, kargs)
        # Save the maximum keys we could utilize
        self.maxkeys = defaultkeys | routekeys
        # Populate our minimum keys, and save a copy of our backward keys for quicker generation later
        (self.minkeys, self.routebackwards) = self._minkeys(routelist[:])
        # Populate our hardcoded keys, these are ones that are set and don't exist in the route
        self.hardcoded = frozenset([key for key in self.maxkeys if key not in routekeys and self.defaults[key] is not None])
        
    def _minkeys(self, routelist):
        """
        Utility function to walk the route backwards, and determine the minimum
        keys we can handle to generate a working route.
        
        routelist is a list of the '/' split route path
        defaults is a dict of all the defaults provided for the route
        """
        minkeys = []
        backcheck = routelist[:]
        gaps = False
        backcheck.reverse()
        for part in backcheck:
            if not part.startswith(':'):
                gaps = True
                continue
            key = part[1:]
            if self.defaults.has_key(key) and not gaps:
                continue
            minkeys.append(key)
            gaps = True
        return  (frozenset(minkeys), backcheck)
    
    def _defaults(self, routekeys, reserved_keys, kargs):
        """
        Put together our list of defaults, stringify non-None values
        and add in our action/id default if they use it and didn't specify it
        
        defaultkeys is a list of the currently assumed default keys
        routekeys is a list of the keys found in the route path
        reserved_keys is a list of keys that are not 
        """
        defaults = {}
        # Add in a controller/action default if they don't exist
        if 'controller' not in routekeys and not kargs.has_key('controller'):
            kargs['controller'] = 'content'
        if 'action' not in routekeys and not kargs.has_key('action'):
            kargs['action'] = 'index'
        defaultkeys = frozenset([key for key in kargs.keys() if key not in reserved_keys])
        for key in defaultkeys:
            if kargs[key] != None:
                defaults[key] = str(kargs[key])
            else:
                defaults[key] = None
        if 'action' in routekeys and not defaults.has_key('action'):
            defaults['action'] = 'index'
        elif not defaults.has_key('action') and 'controller' in maxkeys:
            defaults['action'] = 'index'
        if 'id' in routekeys and not defaults.has_key('id'):
            defaults['id'] = None
        newdefaultkeys = frozenset([key for key in defaults.keys() if key not in reserved_keys])
        return (defaults, newdefaultkeys)
        
    def makeregexp(self, clist):
        """
        Create a regular expression for matching purposes, this MUST be called before match
        can function properly.
        
        clist should be a list of valid controller strings that can be matched, for this reason
        makeregexp should be called by the web framework after it knows all available controllers
        that can be utilized
        """
        
        (reg, noreqs, allblank) = self.buildnextreg(self.routelist, clist)
        
        if not reg: reg = '/'
        reg = '^' + reg + '$'
        
        self.regexp = reg
        self.regmatch = re.compile(reg)
    
    def buildnextreg(self, path, clist):
        """
        Recursively build our regexp given a path, and a controller list.
        
        Returns the regular expression string, and two booleans that can be ignored as
        they're only used internally by buildnextreg
        """
        part = path[0]
        reg = ''
        
        # noreqs will remember whether the remainder has either a string match, or a non-defaulted
        # regexp match on a key, allblank remembers if the rest could possible be completely empty
        (rest, noreqs, allblank) = ('', True, True)
        if len(path[1:]) > 0:
            (rest, noreqs, allblank) = self.buildnextreg(path[1:], clist)
            
        if part.startswith(':'):
            var = part[1:]
            partreg = ''
            
            # First we plug in the proper part matcher
            if self.reqs.has_key(var):
                partreg = '(?P<' + var + '>' + self.reqs[var] + ')'
            elif var == 'controller':
                partreg = '(?P<' + var + '>' + '|'.join(clist) + ')'
            else:
                partreg = '(?P<' + var + '>[^/]+)'
            
            if self.reqs.has_key(var): noreqs = False
            
            # Now we determine if its optional, or required. This changes depending on what is in
            # the rest of the match. If noreqs is true, then its possible the entire thing is optional
            # as there's no reqs or string matches.
            if noreqs:
                # The rest is optional, but now we have an optional with a regexp. Wrap to ensure that if we match
                # anything, we match our regexp first. It's still possible we could be completely blank as we have
                # a default
                if self.reqs.has_key(var) and self.defaults.has_key(var):
                    reg = '(/' + partreg + rest + ')?'
                
                # Or we have a regexp match with no default, so now being completely blank form here on out isn't
                # possible
                elif self.reqs.has_key(var):
                    allblank = False
                    reg = '/' + partreg + rest
                
                # Or we have a default with no regexp, don't touch the allblank
                elif self.defaults.has_key(var):
                    reg = '(/' + partreg + ')?' + rest
                
                # Or we have a key with no default, and no reqs. Not possible to be all blank from here
                else:
                    allblank = False
                    reg = '/' + partreg + rest
            # In this case, we have something dangling that might need to be matched
            else:
                # If they can all be blank, and we have a default here, we know its
                # safe to make everything from here optional. Since something else in
                # the chain does have req's though, we have to make the partreg here
                # required to continue matching
                if allblank and self.defaults.has_key(var):
                    reg = '(/' + partreg + rest + ')?'
                    
                # Same as before, but they can't all be blank, so we have to require it all to ensure
                # our matches line up right
                else:
                    reg = '/' + partreg + rest
        elif part.startswith('*'):
            var = part[1:]
            if noreqs:
                if self.defaults.has_key(var):
                    reg = '(/' + '(?P<' + var + '>.*))*' + rest
                else:
                    reg = '/' + '(?P<' + var + '>.*)' + rest
                    allblank = False
                    noreqs = False
            else:
                if allblank and self.defaults.has_key(var):
                    reg = '(/' + '(?P<' + var + '>.*))*' + rest
                elif self.defaults.has_key(var):
                    reg = '(/' + '(?P<' + var + '>.*))*' + rest
                else:
                    allblank = False
                    noreqs = False
                    reg = '/' + '(?P<' + var + '>.*)' + rest
        # We have a normal string here, this is a req, and it prevents us from being all blank
        else:
            noreqs = False
            allblank = False
            reg = '/' + part + rest
        
        return (reg, noreqs, allblank)
    
    def match(self, url):
        """
        Match a url to our regexp. While the regexp might match, this operation isn't
        guaranteed as there's other factors that can cause a match to fail even though
        the regexp succeeds (Default that was relied on wasn't given, requirement regexp
        doesn't pass, etc.).
        
        Therefore the calling function shouldn't assume this will return a valid dict, the
        other possible return is False if a match doesn't work out.
        """
        
        m = self.regmatch.match(url)
        if m:
            matchdict = m.groupdict()
            result = {}
            extras = frozenset(self.defaults.keys()) - frozenset(matchdict.keys())
            for key in self.reqs.keys():
                if key not in matchdict.keys() or matchdict[key] is None:
                    try:
                        result[key] = self.defaults[key]
                    except:
                        return False
                else:
                    value = matchdict[key] or (self.defaults.has_key(key) and self.defaults[key]) or ''
                    if not re.compile('^' + self.reqs[key] + '$').match(value):
                        return False
            for key,val in matchdict.iteritems():
                if not val and self.defaults.has_key(key) and self.defaults[key]:
                    result[key] = self.defaults[key]
                else:
                    result[key] = val
            for key in extras:
                result[key] = self.defaults[key]
            return result
        else:
            return False
    
    def generate(self,**kargs):
        """
        Generate a URL from ourself given a set of keyword arguments, toss an exception if this
        set of keywords would cause a gap in the url.
        """
        
        # Verify that our args pass any regexp requirements
        for key in self.reqs.keys():
            val = kargs.get(key)
            if val and not self.req_regs[key].match(str(kargs[key])):
                return False

        routelist = self.routebackwards
        urllist = []
        gaps = False
        for part in routelist:
            if part.startswith(':'):
                arg = part[1:]
                if self.defaults.has_key(arg) and kargs.has_key(arg) and str(kargs[arg]) == self.defaults[arg] and not gaps:
                    continue
                if self.defaults.has_key(arg) and not kargs.has_key(arg) and not gaps:
                    continue
                val = kargs.has_key(arg) and kargs[arg]
                if not val:
                    val = self.defaults.has_key(arg) and self.defaults[arg]
                if (not val or val is None) and not gaps:
                    continue
                if val is None:
                    return False
                val = quote(val)
                urllist.append(val)
                if kargs.has_key(arg): del kargs[arg]
                gaps = True
            elif part.startswith('*'):
                arg = part[1:]
                if kargs.has_key(arg) and kargs[arg] is not None:
                    val = quote(kargs[arg])
                    urllist.append(val)
                    gaps = True
            else:
                gaps = True
                urllist.append(part)
        urllist.reverse()
        url = '/' + '/'.join(urllist)
        extras = frozenset(kargs.keys()) - self.maxkeys
        if extras:
            url += '?'
            url += '&'.join([quote(key)+'='+quote(kargs[key]) for key in extras if key != 'action' or key != 'controller'])
        return url
    

class Mapper(object):
    """
    Mapper handles URL generation and URL recognition in a web application.
    
    Mapper is built handling dictionary's. It is assumed that the web application will handle
    the dictionary returned by URL recognition to dispatch appropriately.
    
    URL generation is done by passing keyword parameters into the generate function, a URL is then
    returned.
    """
    
    def __init__(self):
        """
        Create a new Mapper instance
        """
        self.matchlist = []
        self.maxkeys = {}
        self.minkeys = {}
        self.urlcache = None
        self._created_regs = False
        self._created_gens = False
    
    def connect(self, *args, **kargs):
        """
        Create and connect a new Route to the Mapper. 
        Usage:
        
        m = Mapper()
        m.connect(':controller/:action/:id')
        m.connect('date/:year/:month/:day', controller="blog", action="view")
        m.connect('archives/:page', controller="blog", action="by_page",
                  requirements = { 'page':'\d{1,2}' })
        """
        route = Route(*args, **kargs)
        self.matchlist.append(route)
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
        """
        Create the generation hashes for route lookups
        """
        
        # Use keys temporailly to assemble the list to avoid excessive
        # list iteration testing with "in"
        controllerlist = {}
        actionlist = {}
        
        # Assemble all the hardcoded/defaulted actions/controllers used
        for route in self.matchlist:
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
        gens = {} # Our generated two-deep hash
        for route in self.matchlist:
            clist = controllerlist
            alist = actionlist
            if 'controller' in route.hardcoded:
                clist = [route.defaults['controller']]
            if 'action' in route.hardcoded:
                alist = [str(route.defaults['action'])]
            for controller in clist:
                if not gens.has_key(controller):
                    gens[controller] = {}
                for action in alist:
                    actiondict = gens[controller]
                    if not actiondict.has_key(action):
                        actiondict[action] = ([], {})
                    actiondict[action][0].append(route)
        self._gendict = gens
        self._created_gens = True
        
    def create_regs(self, clist):
        """
        Iterate through all connected Routes with our controller list (clist), and
        generate regexp's for every route.
        """
        for key,val in self.maxkeys.iteritems():
            for route in val:
                route.makeregexp(clist)
        self._created_regs = True
    
    def match(self, url):
        """
        Match a URL against against one of the routes contained.
        
        Will return None if no valid match is found.
        
        resultdict = m.match('/joe/sixpack')
        """
        if not self._created_regs:
            raise Exception, "Must created regexps first"
            
        for route in self.matchlist:
            match = route.match(url)
            if match: return match
        return None
    
    def generate(self, controller='content', action='index', **kargs):
        """
        Generate a route from a set of keywords and return the url text, or None if no
        URL could be generated.
        
        m.generate(controller='content',action='view',id=10)
        """
        
        # Generate ourself if we haven't already
        if not self._created_gens:
            self._create_gens()

        kargs['controller'] = controller
        kargs['action'] = action
        
        # Check the url cache to see if it exists, use it if it does
        if self.urlcache is not None:
            try:
                return self.urlcache[str(kargs)]
            except:
                pass
        
        if self._gendict.has_key(controller):
            actionlist = self._gendict[controller]
        else:
            actionlist = self._gendict.get('*')
        if not actionlist: return None
        if actionlist.has_key(action):
            (keylist, sortcache) = actionlist[action]
        else:
            (keylist, sortcache) = actionlist.get('*', (None, None))
        if not keylist: return None
        
        keys = frozenset(kargs.keys())
        cacheset = False
        cachekey = str(keys)
        cachelist = sortcache.get(cachekey)
        if cachelist:
            keylist = cachelist
        else:
            cacheset = True
            newlist = []
            for route in keylist:
                if len(route.minkeys-keys) == 0:
                    newlist.append(route)
            keylist = newlist

            def keysort(a, b):
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
                
                # Neither matches exactly, return the one with the most in common
                if cmp(lendiffa,lendiffb) != 0:
                    return cmp(lendiffa,lendiffb)
                
                # Neither matches exactly, but if they both have just as much in common
                if len(keys&b) == len(keys&a):
                    return cmp(len(a),len(b))     # Then we return the shortest of the two
                
                # Otherwise, we return the one that has the most in common
                else:
                    return cmp(len(keys&b), len(keys&a))
            
            keylist.sort(keysort)
            if cacheset:
                sortcache[cachekey] = keylist
        
        for route in keylist:
            fail = False
            for key in route.hardcoded:
                if not kargs.has_key(key):
                    continue
                if kargs[key] != route.defaults[key]:
                    fail = True
                    break
            if fail: continue
            path = route.generate(**kargs)
            if path:
                if self.urlcache is not None:
                    self.urlcache[str(kargs)] = path
                return path
            else:
                continue
        return None
    

if __name__ == '__main__':
    pass
else:
    m = Mapper()
    m.connect('date/:year/:month/:day', controller = 'blog', action = 'by_date', month = None, day = None)
    m.connect(':controller/:action/:id', id = None)
    url = '/date/2004/20/4'
    c = Mapper()
    c.connect(':controller/:action/:id')
    
    m = Mapper()
    m.connect('page/:id/:action', controller='pages', action='show')
    m.connect(':controller/:action/:id')

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
        if withcache:
            m.urlcache = {}
        m._create_gens()
        n = 5000
        start = time.time()
        for x in range(1,n):
            m.generate(controller='articles', action='index', page=4)
            m.generate(controller='admin/general', action='index')
            m.generate(controller='admin/comments', action='show', article_id=2)
            
            m.generate(controller='articles', action='find_by_date', year=2004, page=1)
            m.generate(controller='articles', action='category', id=4)
            m.generate(controller='xml', action='articlerss', id=2)
        end = time.time()
        ts = time.time()
        for x in range(1,n*6):
            pass
        en = time.time()
        total = end-start-(en-ts)
        per_url = total / (n*6)
        print "Generation (%s URLs)" % (n*6)
        print "%s ms/url" % (per_url*1000)
        print "%s urls/s\n" % (1.00/per_url)
    
    def bench_rec():
        n = 1000
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
        m.create_regs(['content','admin/why', 'admin/user'])
        start = time.time()
        for x in range(1,n):
            a = m.match('/content')
            a = m.match('/content/list')
            a = m.match('/content/show/10')
            
            a = m.match('/admin/user')
            a = m.match('/admin/user/list')
            a = m.match('/admin/user/show/bbangert')
            
            a = m.match('/admin/user/show/bbangert/dude')
            a = m.match('/admin/why/show/bbangert')
            a = m.match('/content/show/10/20')
            a = m.match('/food')
        end = time.time()
        ts = time.time()
        for x in range(1,n):
            pass
        en = time.time()
        total = end-start-(en-ts)
        per_url = total / (n*10)
        print "Recognition\n"
        print "%s ms/url" % (per_url*1000)
        print "%s urls/s\n" % (1.00/per_url)
    

