============================
Unicode, Redirects, and More
============================

Unicode
=======

Routes assumes UTF-8 encoding on incoming URLs, and ``url`` and ``url_for``
also generate UTF-8.  You can change the encoding with the ``map.charset``
attribute::

   map.charset = "latin-1"

New in Routes 1.10: several bugfixes.

Redirect Routes
===============

Redirect routes allow you to specify redirects in the route map, similar to
RewriteRule in an Apache configuration.  This avoids the need to define dummy
controller actions just to handle redirects.  It's especially useful when the
URL structure changes and you want to redirect legacy URLs to their new
equivalents.  The redirection is done by the Routes middleware, and the WSGI
application is not called.

``map.redirect`` takes two positional arguments:  the route path and the
destination URL.  Redirect routes do not have a name.  Both paths can contain
variables, and the route path can take inline requirements.  Keyword arguments
are the same as ``map.connect``, both in regards to extra variables and to route
options. ::

    map.redirect("/legacyapp/archives/{url:.*}", "/archives/{url}")

    map.redirect("/legacyapp/archives/{url:.*}", "/archives/{url}")

By default a "302 Found" HTTP status is issued.  You can override this with the
``_redirect_code`` keyword argument.  The value must be an entire status
string. ::

    map.redirect("/home/index", "/", _redirect_code="301 Moved Permanently")

*New in Routes 1.10.*

Printing
========

Mappers now have a formatted string representation.  In your python shell,
simply print your application's mapper::

    >>> map.collection("entries", "entry")
    >>> print map
    Route name   Methods Path                        Controller action
    entries      GET     /entries{.format}           entry      index
    create_entry POST    /entries{.format}           entry      create
    new_entry    GET     /entries/new{.format}       entry      new
    entry        GET     /entries/{id}{.format}      entry      show
    update_entry PUT     /entries/{id}{.format}      entry      update
    delete_entry DELETE  /entries/{id}{.format}      entry      delete
    edit_entry   GET     /entries/{id}/edit{.format} entry      edit

*New in Routes 1.12.*

*Controller/action fields new in Routes 2.1*


Introspection
=============

The mapper attribute ``.matchlist`` contains the list of routes to be matched
against incoming URLs.  You can iterate this list to see what routes are
defined.  This can be useful when debugging route configurations.


Other
=====

If your application is behind an HTTP proxy such a load balancer on another
host, the WSGI environment will refer to the internal server rather than to the
proxy, which will mess up generated URLs.  Use the ProxyMiddleware in
PasteDeploy to fix the WSGI environment to what it would have been without the
proxy.

To debug routes, turn on debug logging for the "routes.middleware" logger.
(See Python's ``logging`` module to set up your logging configuration.)

Backward compatibility
======================

The following syntaxes are allowed for compatibility with previous versions
of Routes.  They may be removed in the future.

Omitting the name arg
---------------------

In the tutorial we said that nameless routes can be defined by passing ``None``
as the first argument.  You can also omit the first argument entirely::

    map.connect(None, "/{controller}/{action}")
    map.connect("/{controller}/{action}")

The syntax with ``None`` is preferred to be forward-compatible with future
versions of Routes.  It avoids the path argument changing position between
the first and second arguments, which is unpythonic.

:varname
--------

Path variables were defined in the format ``:varname`` and ``:(varname)``
prior to Routes 1.9.  The form with parentheses was called "grouping", used
to delimit the variable name from a following letter or number.  Thus the old
syntax "/:controller/:(id)abc" corresponds to the new syntax
"/{controller}/{id}abc".

The older wildcard syntax is ``*varname`` or ``*(varname)``::

    # OK because the following component is static.
    map.connect("/static/*filename/download")

    # Deprecated syntax.  WRONG because the wildcard will eat the rest of the
    # URL, leaving nothing for the following variable, which will cause the
    # match to fail.
    map.connect("/static/*filename/:action")


Minimization
------------

Minimization was a misfeature which was intended to save typing, but which
often resulted in the wrong route being chosen.  Old applications that still
depend on it must now enable it by putting ``map.minimization = True`` in
their route definitions.

Without minimization, the URL must contain values for all path variables in
the route::

    map.connect("basic", "/{controller}/{action}",
        controller="mycontroller", action="myaction", weather="sunny")

This route matches any two-component URL, for instance "/help/about".  The
resulting routing variables would be::

    {"controller": "help", "action": "about", "weather": "sunny"}

The path variables are taken from the URL, and any extra variables are added as
constants.  The extra variables for "controller" and "action" are *never used*
in matching, but are available as default values for generation::

    url("basic", controller="help") => "/help/about?weather=sunny"

With minimization, the same route path would also match shorter URLs such as
"/help", "/foo", and "/".  Missing values on the right of the URL would be
taken from the extra variables.  This was intended to lessen the number of
routes you had to write.  In practice it led to obscure application bugs
because sometimes an unexpected route would be matched.  Thus Routes 1.9
introduced non-minimization and recommended "map.minimization = False" for
all new applications.

A corollary problem was generating the wrong route.  Routes 1.9 tightened up
the rule for generating named routes.  If a route name is specified in
``url()`` or ``url_for()``, *only* that named route will be chosen.  In
previous versions, it might choose another route based on the keyword args.

Implicit defaults and route memory
----------------------------------

Implicit defaults worked with minimization to provide automatic default values
for the "action" and "id" variables.  If a route was defined as
``map.connect("/{controller}/{action}/{id}") and the URL "/archives"`` was
requested, Routes would implicitly add ``action="index", id=None`` to the
routing variables.

To enable implicit defaults, set ``map.minimization = True; map.explicit =
False``.  You can also enable implicit defaults on a per-route basis by setting
``map.explicit = True`` and defining each route with a keyword argument ``explicit=False``.

Previous versions also had implicit default values for "controller",
"action", and "id".  These are now disabled by default, but can be enabled via
``map.explicit = True``.  This also enables route memory

url_for()
---------

``url_for`` was a route generation function which was replaced by the ``url``
object.  Usage is the same except that ``url_for`` uses route memory in some
cases and ``url`` never does.  Route memory is where variables from the current
URL (the current request) are injected into the generated URL.  To use route
memory with ``url``, call ``url.current()`` passing the variables you want to
override.  Any other variables needed by the route will be taken from the
current routing variables.

In other words, ``url_for`` combines ``url`` and ``url.current()`` into one
function.  The location of ``url_for`` is also different.  ``url_for`` is
properly imported from ``routes``::

    from routes import url_for

``url_for`` was traditionally imported into WebHelpers, and it's still used in
some tests and in ``webhelpers.paginate``.  Many old Pylons applications
contain ``h.url_for()`` based on its traditional importation to helpers.py.
However, its use in new applications is discouraged both because of its
ambiguous syntax and because its implementation depends on an ugly singleton.

The ``url`` object is created by the RoutesMiddleware and inserted into the
WSGI environment.  Pylons makes it available as ``pylons.url``, and in
templates as ``url``.

redirect_to()
-------------

This combined ``url_for`` with a redirect.  Instead, please use your
framework's redirect mechanism with a ``url`` call.  For instance in Pylons::

    from pylons.controllers.util import redirect
    redirect(url("login"))
