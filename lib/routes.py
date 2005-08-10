#
#  routes
#
#  Created by Ben Bangert on 2005-08-08.
#  Copyright (c) 2005 Parachute. All rights reserved.
#

import re, time
from urllib import quote_plus

def quote(string):
    return quote_plus(string, '/')


if not "frozenset" in dir(__builtins__): from sets import ImmutableSet as frozenset

class Route(object):
    def __init__(self, routepath, **kargs):
        reserved_keys = ['requirements']
        
        # Build 3 lists, our route list, the default keys, and the route keys
        routelist = routepath.split('/')
        defaultkeys = frozenset([key for key in kargs.keys() if key not in reserved_keys])
        routekeys = frozenset([key[1:] for key in routelist if (key.startswith(':') or key.startswith('*')) and key not in reserved_keys])
        
        # Save the maximum keys we could utilize
        self.maxkeys = defaultkeys | routekeys
        
        # Save our routelist
        self.routelist = routelist[:]
        
        # Build a req list with all the regexp requirements for our args
        self.reqs = kargs.has_key('requirements') and kargs['requirements']
        if not self.reqs: self.reqs = {}
        
        # Put together our list of defaults, stringify non-None values
        # and add in our action/id default if they use it and didn't specify it
        defaults = {}
        for key in defaultkeys:
            if kargs[key] != None:
                defaults[key] = str(kargs[key])
            else:
                defaults[key] = None
        if 'action' in routekeys and not defaults.has_key('action'):
            defaults['action'] = 'index'
        if 'id' in routekeys and not defaults.has_key('id'):
            defaults['id'] = None
        
        # We walk our route backwards, anytime we can leave off a key due to it
        # having a default, or being None, we know its not needed. As soon as we
        # add something though, the rest is needed no matter what.
        minkeys = []
        backcheck = routelist[:]
        gaps = False
        backcheck.reverse()
        self.routebackwards = backcheck[:]
        for part in backcheck:
            if not part.startswith(':'):
                gaps = True
                continue
            key = part[1:]
            if defaults.has_key(key) and not gaps:
                continue
            minkeys.append(key)
            gaps = True
        self.minkeys = frozenset(minkeys)

        # Our hardcoded args exist as defaults, but have no place in the route to
        # specify them. Thus for the route to be generated, the args passed in must
        # match these ones for the URL to be usable.
        hardcoded = []
        for key in self.maxkeys:
            if key not in routekeys and kargs[key] is not None:
                hardcoded.append(key)
        self.defaults = defaults
        self.hardcoded = frozenset(hardcoded)
    
    def makeregexp(self, clist):
        # Build our regexp to match this expression
        default = '[^/]+'
        reg = ''
        for part in self.routelist:
            if not part:
                continue
            if part.startswith(':'):
                var = part[1:]
                partreg = ''
                if self.reqs.has_key(var):
                    partreg += '(?P<' + var + '>' + self.reqs[var] + ')'
                elif var == 'controller':
                    partreg += '(?P<' + var + '>' + '|'.join(clist) + ')'
                else:
                    partreg += '(?P<' + var + '>' + default + ')'
                if self.defaults.has_key(var):
                    reg += '(/' + partreg + '){0,1}'
                else:
                    reg += '/' + partreg
            elif part.startswith('*'):
                var = part[1:]
                reg += '(/' + '(?P<' + var + '>.*))*'
            else:
                reg += '/' + part
        if not reg: reg = '/'
        reg = '^' + reg + '$'
        self.regexp = reg
        self.regmatch = re.compile(reg)
    
    def match(self, url):
        m = self.regmatch.match(url)
        if m:
            matchdict = m.groupdict()
            result = {}
            extras = frozenset(self.defaults.keys()) - frozenset(matchdict.keys())
            for key in self.reqs.keys():
                if key not in matchdict.keys():
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
        # Verify that our args pass any regexp requirements
        for key in self.reqs.keys():
            if kargs.has_key(key):
                if self.defaults.has_key(key) and self.defaults[key] is None and kargs[key] is None:
                    continue
                if not re.compile('^' + self.reqs[key] + '$').match(kargs[key]):
                    raise Exception, "Route doesn't match reqs"

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
                    raise Exception, "Route causes gaps"
                val = quote(str(val))
                urllist.append(val)
                if kargs.has_key(arg): del kargs[arg]
                gaps = True
            elif part.startswith('*'):
                arg = part[1:]
                if kargs.has_key(arg) and kargs[arg] is not None:
                    val = quote(str(kargs[arg]))
                    urllist.append(val)
                    gaps = True
            else:
                gaps = True
                urllist.append(part)
        urllist.reverse()
        url = '/' + '/'.join(urllist)
        extras = frozenset(kargs.keys()) - self.maxkeys
        #if extras:
            #url += '?'
            #url += '&'.join([str(key)+'='+str(kargs[key]) for key in extras])
        return url
    

class Mapper(object):
    def __init__(self):
        self.matchlist = []
        self.maxkeys = {}
        self.minkeys = {}
        self.cachematch = {}
        self.created_regs = False
        self.cacheurls = {}
    
    def connect(self, *args, **kargs):
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
    
    def create_regs(self, clist):
        for key,val in self.maxkeys.iteritems():
            for route in val:
                route.makeregexp(clist)
        self.created_regs = True
    
    def match(self, url):
        if not self.created_regs:
            raise Exception, "Must created regexps first"
            
        for route in self.matchlist:
            match = route.match(url)
            if match: return match
        return None
    
    def generate(self, **kargs):
        try:
            return self.cacheurls[str(kargs)]
        except:
            pass
        # If they used action with 'index', thats the default, so we'll pretend
        # it isn't here for proper result ordering
        actionDef = False
        if kargs.has_key('action') and kargs['action'] == 'index':
            del kargs['action']
            actionDef = True
        keys = frozenset(kargs.keys())
        
        # This keysort is probably expensive, so we'll cache the results
        try:
            keylist = self.cachematch[keys]
        except:
            keylist = self.maxkeys.keys()
            def keysort(a, b):
                # First, if a matches exactly, use it
                if len(keys^a) == 0:
                    return -1
                    
                # Or b matches exactly, use it
                if len(keys^b) == 0:
                    return 1
                    
                # Neither matches exactly, but if they both have just as much in common
                if len(keys&b) == len(keys&a):
                    return cmp(len(a),len(b))     # Then we return the shortest of the two
                
                # Otherwise, we return the one that has the most in common
                else:
                    return cmp(len(keys&b), len(keys&a))
            keylist.sort(keysort)
            self.cachematch[keys] = keylist
        
        # Restore the action arg, to ensure its called as 'index'
        if actionDef:
            kargs['action'] = 'index'
            keys = frozenset(kargs.keys())
            
        #print keylist
        for routelist in keylist:
            for route in self.maxkeys[routelist]:
                if len(route.minkeys-keys) != 0: continue
                fail = False
                for key in route.hardcoded:
                    if not kargs.has_key(key):
                        continue
                    if kargs[key] != route.defaults[key]:
                        fail = True
                        break
                if fail: continue
                if len(route.minkeys-keys) == 0:
                    try:
                        path = route.generate(**kargs)
                        self.cacheurls[str(kargs)] = path
                        return path
                    except:
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

    def bench_gen():
        n = 1000
        start = time.time()
        for x in range(1,n):
            c.generate(controller='content', action='index')
            c.generate(controller='content', action='list')
            c.generate(controller='content', action='show', id='10')
            
            c.generate(controller='admin/user', action='index')
            c.generate(controller='admin/user', action='list')
            c.generate(controller='admin/user', action='show', id='10')
        end = time.time()
        ts = time.time()
        for x in range(1,n*3):
            pass
        en = time.time()
        total = end-start-(en-ts)
        per_url = total / (n*6)
        print "Generation\n"
        print "%s ms/url" % (per_url*1000)
        print "%s urls/s\n" % (1.00/per_url)
    
    def bench_rec():
        n = 1000
        c = Mapper()
        c.connect(':controller/:action/:id')
        c.create_regs(['content','admin/user'])
        start = time.time()
        for x in range(1,n):
            a = c.match('/content')
            a = c.match('/content/list')
            a = c.match('/content/show/10')
            
            a = c.match('/admin/user')
            a = c.match('/admin/user/list')
            a = c.match('/admin/user/show/bbangert')
            
            a = c.match('/admin/user/show/bbangert/dude')
            a = c.match('/admin/why/show/bbangert')
            a = c.match('/content/show/10/20')
            a = c.match('/food')
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
    

