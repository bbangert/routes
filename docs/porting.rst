Porting Routes to a WSGI Web Framework
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

RoutesMiddleware
----------------

An application can create a raw mapper object and call its ``.match`` and
``.generate`` methods.  However, WSGI applications probably want to use
the ``RoutesMiddleware`` as Pylons does::

    # In myapp/config/middleware.py
    from routes.middleware import RoutesMiddleware
    app = RoutesMiddleware(app, map)     # ``map`` is a routes.Mapper.

The middleware matches the requested URL and sets the following WSGI
variables::

        environ['wsgiorg.routing_args'] = ((url, match))
        environ['routes.route'] = route
        environ['routes.url'] = url

where ``match`` is the routing variables dict, ``route`` is the matched route,
and ``url`` is a ``URLGenerator`` object.  In Pylons, ``match`` is used by the
dispatcher, and ``url`` is accessible as ``pylons.url``.

The middleware handles redirect routes itself, issuing the appropriate
redirect.  The application is not called in this case.

To debug routes, turn on debug logging for the "routes.middleware" logger.

See the Routes source code for other features which may have been added.

URL Resolution
--------------

When the URL is looked up, it should be matched against the Mapper. When
matching an incoming URL, it is assumed that the URL path is the only string
being matched. All query args should be stripped before matching::

    m.connect('/articles/{year}/{month}', controller='blog', action='view', year=None)

    m.match('/articles/2003/10')
    # {'controller':'blog', 'action':'view', 'year':'2003', 'month':'10'}

Matching a URL will return a dict of the match results, if you'd like to
differentiate between where the argument came from you can use routematch which
will return the Route object that has all these details::

    m.connect('/articles/{year}/{month}', controller='blog', action='view', year=None)

    result = m.routematch('/articles/2003/10')
    # result is a tuple of the match dict and the Route object

    # result[0] - {'controller':'blog', 'action':'view', 'year':'2003', 'month':'10'}
    # result[1] - Route object
    # result[1].defaults - {'controller':'blog', 'action':'view', 'year':None}
    # result[1].hardcoded - ['controller', 'action']

Your integration code is then expected to dispatch to a controller and action
in the dict. How it does this is entirely up to the framework integrator. Your
integration should also typically provide the web developer a mechanism to
access the additional dict values.  

Request Configuration
---------------------

If you intend to support ``url_for()`` and ``redirect_to()``, they depend on a
singleton object which requires additional configuration.  You're better off
not supporting them at all because they will be deprecated soon.  
``URLGenerator`` is the forward-compatible successor to ``url_for()``.
``redirect_to()`` is better done in the web framework`as in
``pylons.controllers.util.redirect_to()``.

``url_for()`` and ``redirect_to()`` need information on the current request,
and since they can be called from anywhere they don't have direct access to the
WSGI environment.  To remedy this, Routes provides a thread-safe singleton class
called "request_config", which holds the request information for the current
thread. You should update this after matching the incoming URL but before
executing any code that might call the two functions.  Here is an example::

    from routes import request_config

    config = request_config()

    config.mapper = m                  # Your mapper object
    config.mapper_dict = result        # The dict from m.match for this URL request
    config.host = hostname             # The server hostname
    config.protocol = port             # Protocol used, http, https, etc.
    config.redirect = redir_func       # A redirect function used by your framework, that is
                                       # expected to take as the first non-keyword arg a single
                                       # full or relative URL

See the docstring for ``request_config`` in routes/__init__.py to make sure
you've initialized everything necessary.
