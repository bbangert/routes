Setting up routes
=================

It is assumed that you are using a framework that has preconfigured Routes for
you.  In Pylons, you define your routes in the ``make_map`` function in your
*myapp/config/routing.py* module.  Here is a typical configuration:

.. code-block:: python
    :linenos:

    from routes import Mapper
    map = Mapper()
    map.connect(None, "/error/{action}/{id}", controller="error")
    map.connect("home", "/", controller="main", action="index")
    # ADD CUSTOM ROUTES HERE
    map.connect(None, "/{controller}/{action}")
    map.connect(None, "/{controller}/{action}/{id}")

Lines 1 and 2 create a mapper.

Line 3 matches any three-component route that starts with "/error", and sets
the "controller" variable to a constant, so that a URL
"/error/images/arrow.jpg" would produce::

    {"controller": "error", "action": "images", "id": "arrow.jpg"}

Line 4 matches the single URL "/", and sets both the controller and action to
constants.  It also has a route name "home", which can be used in generation.
(The other routes have ``None`` instead of a name, so they don't have names.
It's recommended to name all routes that may be used in generation, but it's
not necessary to name other routes.)

Line 6 matches any two-component URL, and line 7 matches any 3-component URL.
These are used as catchall routes if we're too lazy to define a separate route
for every action.  If you *have* defined a route for every action, you can
delete these two routes.

Note that a URL "/error/images/arrow.jpg" could match both line 3 and line 7.
The mapper resolves this by trying routes in the order defined, so this URL
would match line 3.

If no routes match the URL, the mapper returns a "match failed" condition,
which is seen in Pylons as HTTP 404 "Not Found".

Here are some more examples of valid routes::

    m.connect("/feeds/{category}/atom.xml", controller="feeds", action="atom")
    m.connect("history", "/archives/by_eon/{century}", controller="archives",
              action="aggregate")
    m.connect("article", "/article/{section}/{slug}/{page}.html",
              controller="article", action="view")

Extra variables may be any Python type, not just strings.  However, if the
route is used in generation, ``str()`` will  be called on the value unless
the generation call specifies an overriding value.

Other argument syntaxes are allowed for compatibility with earlier versions of
Routes.  These are described in the ``Backward Compatibility`` section.

Route paths should always begin with a slash ("/").  Earlier versions of 
Routes allowed slashless paths, but their behavior now is undefined.


Requirements
------------

It's possible to restrict a path variable to a regular expression; e.g., to
match only a numeric component or a restricted choice of words.  There are two
syntaxes for this: inline and the ``requirements`` argument.  An inline
requirement looks like this::

    map.connect(R"/blog/{id:\d+}")
    map.connect(R"/download/{platform:windows|mac}/{filename}")

This matches "/blog/123" but not "/blog/12A".  The equivalent ``requirements``
syntax is::

    map.connect("/blog/{id}", requirements={"id": R"\d+"}
    map.connect("/download/{platform}/{filename}",
        requirements={"platform": R"windows|mac"})

Note the use of raw string syntax (``R""``) for regexes which might contain
backslashes.  Without the R you'd have to double every backslash.

Another example::

    m.connect("/archives/{year}/{month}/{day}", controller="archives",
              action="view", year=2004,
              requirements=dict(year=R"\d{2,4}", month=R"\d{1,2}"))

The inline syntax was added in Routes (XXX 1.10?? not in changelog).  Previous
versions had only the ``requirements`` argument.  Two advantages of the
``requirements`` argument are that if you have several variables with identical
requirements, you can set one variable or even the entire argument to a
global::

    NUMERIC = R"\d+"
    map.connect(..., requirements={"id": NUMERIC})

    ARTICLE_REQS = {"year": R"\d\d\d\d", "month": R"\d\d", "day": R"\d\d"}
    map.connect(..., requirements=ARTICLE_REQS)

Because the argument ``requirements`` is reserved, you can't define a routing
variable by that name.

Magic path_info
---------------

If the "path_info" variable is used at the end of the URL, Routes moves
everything preceding it into the "SCRIPT_NAME" environment variable.  This is
useful when delegating to another WSGI application that does its own routing:
the subapplication will route on the remainder of the URL rather than the
entire URL.  You still
need the ":.*" requirement to capture the following URL components into the
variable.  ::

    map.connect(None, "/cards/{path_info:.*}",
        controller="main", action="cards")
    # Incoming URL "/cards/diamonds/4.png"
    => {"controller": "main", action: "cards", "path_info": "/diamonds/4.png"}
    # Second WSGI application sees: 
    # SCRIPT_NAME="/cards"   PATH_INFO="/diamonds/4.png"

This route does not match "/cards" because it requires a following slash.
Add another route to get around this::

    map.connect("cards", "/cards", controller="main", action="cards",
        path_info="/")

.. tip::

    You may think you can combine the two with the following route::

        map.connect("cards", "/cards{path_info:.*}",
            controller="main", action="cards")

    There are two problems with this, however. One, it would also match
    "/cardshark".  Two, Routes 1.10 has a bug: it forgets to take
    the suffix off the SCRIPT_NAME.

A future version of Routes may delegate directly to WSGI applications, but for
now this must be done in the framework.  In Pylons, you can do this in a
controller action as follows::

    from paste.fileapp import DirectoryApp
    def cards(self, environ, start_response):
        app = DirectoryApp("/cards-directory")
        return app(environ, start_response)

Or create a fake controller module with a ``__controller__`` variable set to
the WSGI application::

    from paste.fileapp import DirectoryApp
    __controller__ = DirectoryApp("/cards-directory")

Conditions
----------

Conditions impose additional constraints on what kinds of requests can match.
The ``conditions`` argument is a dict with up to three keys:

    method

        A list of uppercase HTTP methods.  The request must be one of the
        listed methods.

    sub_domain

        Can be a list of subdomains, ``True``, ``False``, or ``None``.  If a
        list, the request must be for one of the specified subdomains.  If
        ``True``, the request must contain a subdomain but it can be anything.
        If ``False`` or ``None``, do not match if there's a subdomain.

        *New in Routes 1.10: ``False`` and ``None`` values.*

    function

        A function that evaluates the request.  Its signature must be
        ``func(environ, match_dict) => bool``.  It should return true if the
        match is successful or false otherwise.  The first arg is the WSGI
        environment; the second is the routing variables that would be
        returned if the match succeeds.  The function can modify ``match_dict``
        in place to affect which variables are returned.  This allows a wide
        range of transformations.

Examples::

    # Match only if the HTTP method is "GET" or "HEAD".
    m.connect("/user/list", controller="user", action="list",
              conditions=dict(method=["GET", "HEAD"]))

    # A sub-domain should be present.
    m.connect("/", controller="user", action="home",
              conditions=dict(sub_domain=True))

    # Sub-domain should be either "fred" or "george".
    m.connect("/", controller="user", action="home",
              conditions=dict(sub_domain=["fred", "george"]))

    # Put the referrer into the resulting match dictionary.
    # This function always returns true, so it never prevents the match
    # from succeeding.
    def referals(environ, result):
        result["referer"] = environ.get("HTTP_REFERER")
        return True
    m.connect("/{controller}/{action}/{id}", 
        conditions=dict(function=referals))

Wildcard routes
---------------

By default, path variables do not match a slash.  This ensures that each
variable will match exactly one component.  You can use requirements to
override this::

    map.connect("/static/{filename:.*?}")

This matches "/static/foo.jpg", "/static/bar/foo.jpg", etc.  

Beware that careless regexes may eat the entire rest of the URL and cause
components to the right of it not to match::

    # OK because the following component is static and the regex has a "?".
    map.connect("/static/{filename:.*?}/download")

The lesson is to always test wildcard patterns.

Format extensions
-----------------

A path component of ``{.format}`` will match an optional format extension (e.g.
".html" or ".json"), setting the format variable to the part after the "."
(e.g. "html" or "json") if there is one, or to ``None`` otherwise.  For example::

    map.connect('/entries/{id}{.format}')
    
will match "/entries/1" and "/entries/1.mp3".  You can use requirements to
limit which extensions will match, for example::

    map.connect('/entries/{id:\d+}{.format:json}')

will match "/entries/1" and "/entries/1.json" but not "/entries/1.mp3".

As with wildcard routes, it's important to understand and test this.  Without
the ``\d+`` requirement on the ``id`` variable above, "/entries/1.mp3" would match
successfully, with the ``id`` variable capturing "1.mp3".

*New in Routes 1.12.*

Submappers
----------

A submapper lets you add several similar routes 
without having to repeat identical keyword arguments.  There are two syntaxes,
one using a Python ``with`` block, and the other avoiding it. ::

    # Using 'with'
    with map.submapper(controller="home") as m:
        m.connect("home", "/", action="splash")
        m.connect("index", "/index", action="index")

    # Not using 'with'
    m = map.submapper(controller="home")
    m.connect("home", "/", action="splash")
    m.connect("index", "/index", action="index")

    # Both of these syntaxes create the following routes::
    # "/"      => {"controller": "home", action="splash"}
    # "/index" => {"controller": "home", action="index"}

You can also specify a common path prefix for your routes::

    with map.submapper(path_prefix="/admin", controller="admin") as m:
        m.connect("admin_users", "/users", action="users")
        m.connect("admin_databases", "/databases", action="databases")

    # /admin/users     => {"controller": "admin", "action": "users"}
    # /admin/databases => {"controller": "admin", "action": "databases"}

All arguments to ``.submapper`` must be keyword arguments.

The submapper is *not* a complete mapper.  It's just a temporary object
with a ``.connect`` method that adds routes to the mapper it was spawned 
from.

*New in Routes 1.11.*

Submapper helpers
-----------------

Submappers contain a number of helpers that further simplify routing
configuration.  This::

    with map.submapper(controller="home") as m:
        m.connect("home", "/", action="splash")
        m.connect("index", "/index", action="index")
        
can be written::

    with map.submapper(controller="home", path_prefix="/") as m:
        m.action("home", action="splash")
        m.link("index")

The ``action`` helper generates a route for one or more HTTP methods ('GET' is
assumed) at the submapper's path ('/' in the example above).  The ``link``
helper generates a route at a relative path.

There are specific helpers corresponding to the standard ``index``, ``new``,
``create``, ``show``, ``edit``, ``update`` and ``delete`` actions.
You can use these directly::

    with map.submapper(controller="entries", path_prefix="/entries") as entries:
        entries.index()
        with entries.submapper(path_prefix="/{id}") as entry:
            entry.show()

or indirectly::

    with map.submapper(controller="entries", path_prefix="/entries",
                       actions=["index"]) as entries:
        entries.submapper(path_prefix="/{id}", actions=["show"])

Collection/member submappers nested in this way are common enough that there is
helper for this too::

    map.collection(collection_name="entries", member_name="entry",
                   controller="entries",
                   collection_actions=["index"], member_actions["show"])

This returns a submapper instance to which further routes may be added; it has
a ``member`` property (a nested submapper) to which which member-specific routes
can be added.  When ``collection_actions`` or ``member_actions`` are omitted,
the full set of actions is generated (see the example under "Printing" below).

See "RESTful services" below for ``map.resource``, a precursor to
``map.collection`` that does not use submappers.

*New in Routes 1.12.*

Adding routes from a nested application
---------------------------------------

*New in Routes 1.11.*  Sometimes in nested applications, the child application
gives the parent a list of routes to add to its mapper.  These can be added
with the ``.extend`` method, optionally providing a path prefix::

    from routes.route import Route
    routes = [
        Route("index", "/index.html", controller="home", action="index"),
        ]

    map.extend(routes)
    # /index.html => {"controller": "home", "action": "index"}

    map.extend(routes, "/subapp")
    # /subapp/index.html => {"controller": "home", "action": "index"}

This does not exactly add the route objects to the mapper.  It creates
identical new route objects and adds those to the mapper.
    
*New in Routes 1.11.*
