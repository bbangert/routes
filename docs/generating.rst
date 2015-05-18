Generation
==========

To generate URLs, use the ``url`` or ``url_for`` object provided by your
framework.  ``url`` is an instance of Routes ``URLGenerator``, while
``url_for`` is the older ``routes.url_for()`` function.  ``url_for`` is being
phased out, so new applications should use ``url``.

To generate a named route, specify the route name as a positional argument::

    url("home")   =>  "/"

If the route contains path variables, you must specify values for them using
keyword arguments::

    url("blog", year=2008, month=10, day=2)

Non-string values are automatically converted to strings using ``str()``.
(This may break with Unicode values containing non-ASCII characters.)

However, if the route defines an extra variable with the same name as a path
variable, the extra variable is used as the default if that keyword is not
specified.  Example::

    m.connect("archives", "/archives/{id}",
        controller="archives", action="view", id=1)
    url("archives", id=123)  =>  "/archives/123"
    url("archives")  =>  "/archives/1"

(The extra variable is *not* used for matching unless minimization is enabled.)

Any keyword args that do not correspond to path variables will be put in the
query string.  Append a "_" if the variable name collides with a Python
keyword::

    map.connect("archive", "/archive/{year}")
    url("archive", year=2009, font=large)  =>  "/archive/2009?font=large"
    url("archive", year=2009, print_=1)  =>  "/archive/2009?print=1"

If the application is mounted at a subdirectory of the URL space,
all generated URLs will have the application prefix.  The application prefix is
the "SCRIPT_NAME" variable in the request's WSGI environment.

If the positional argument corresponds to no named route, it is assumed to be a
literal URL.  The application's mount point is prefixed to it, and keyword args
are converted to query parameters::

    url("/search", q="My question")  =>  "/search?q=My+question"

If there is no positional argument, Routes will use the keyword args to choose
a route.  The first route that has all path variables specified by keyword args
and the fewest number of extra variables not overridden by keyword args will be
chosen.  This was common in older versions of Routes but can cause application
bugs if an unexpected route is chosen, so using route names is much preferable
because that guarantees only the named route will be chosen.  The most common
use for unnamed generation is when you have a seldom-used controller with a lot
of ad hoc methods; e.g., ``url(controller="admin", action="session")``.

An exception is raised if no route corresponds to the arguments.  The exception
is ``routes.util.GenerationException``.  (Prior to Routes 1.9, ``None`` was
returned instead.  It was changed to an exception to prevent invalid blank URLs
from being insered into templates.)  

You'll also get this exception if Python produces a Unicode URL (which could
happen if the route path or a variable value is Unicode).  Routes generates
only ``str`` URLs.

The following keyword args are special:

    anchor

        Specifies the URL anchor (the part to the right of "#"). ::

            url("home", "summary")  =>  "/#summary"

    host

        Make the URL fully qualified and override the host (domain).

    protocol

        Make the URL fully qualified and override the protocol (e.g., "ftp").

    qualified

        Make the URL fully qualified (i.e., add "protocol://host:port" prefix).

    sub_domain

        See "Generating URLs with subdomains" below.

The syntax in this section is the same for both ``url`` and ``url_for``.

*New in Routes 1.10: ``url`` and the ``URLGenerator`` class behind it.*

Generating routes based on the current URL
------------------------------------------

``url.current()`` returns the URL of the current request, without the query
string.  This is called "route memory", and works only if the RoutesMiddleware
is in the middleware stack.  Keyword arguments override path variables or are
put on the query string.

``url_for`` combines the behavior of ``url`` and ``url_current``.  This is
deprecated because nameless routes and route memory have the same syntax, which
can lead to the wrong route being chosen in some cases.

Here's an example of route memory::

    m.connect("/archives/{year}/{month}/{day}", year=2004)

    # Current URL is "/archives/2005/10/4".
    # Routing variables are {"controller": "archives", "action": "view",
      "year": "2005", "month": "10", "day": "4"}

    url.current(day=6)    =>  "/archives/2005/10/6"
    url.current(month=4)  =>  "/archives/2005/4/4"
    url.current()         =>  "/archives/2005/10/4"

Route memory can be disabled globally with ``map.explicit = True``.

Generation-only routes (aka. static routes)
-------------------------------------------

A static route is used only for generation -- not matching -- and it must be
named.  To define a static route, use the argument ``_static=True``.  

This example provides a convenient way to link to a search::

    map.connect("google", "http://google.com/", _static=True)
    url("google", q="search term")  =>  "http://google.com/?q=search+term")

This example generates a URL to a static image in a Pylons public directory.
Pylons serves the public directory in a way that bypasses Routes, so there's no
reason to match URLs under it. ::

    map.connect("attachment", "/images/attachments/{category}/{id}.jpg",
        _static=True)
    url("attachment", category="dogs", id="Mastiff") =>
        "/images/attachments/dogs/Mastiff.jpg"

Starting in Routes 1.10, static routes are exactly the same as regular routes
except they're not added to the internal match table.  In previous versions of
Routes they could not contain path variables and they had to point to external
URLs.

Filter functions
----------------

A filter function modifies how a named route is generated.  Don't confuse it
with a function condition, which is used in matching.  A filter function is its
opposite counterpart.

One use case is when you have a ``story`` object with attributes for year,
month, and day.  You don't want to hardcode these attributes in every ``url``
call because the interface may change someday.  Instead you pass the story as a
pseudo-argument, and the filter produces the actual generation args.  Here's an
example::

    class Story(object):
        def __init__(self, year, month, day):
            self.year = year
            self.month = month
            self.day = day

        @staticmethod
        def expand(kw):
            try:
                story = kw["story"]
            except KeyError:
                pass   # Don't modify dict if ``story`` key not present.
            else:
                # Set the actual generation args from the story.
                kw["year"] = story.year
                kw["month"] = story.month
                kw["day"] = story.day
            return kw

    m.connect("archives", "/archives/{year}/{month}/{day}",
        controller="archives", action="view", _filter=Story.expand)

    my_story = Story(2009, 1, 2)
    url("archives", story=my_story)  =>  "/archives/2009/1/2"

The ``_filter`` argument can be any function that takes a dict and returns a
dict.  In the example we've used a static method of the ``Story`` class to keep
everything story-related together, but you may prefer to use a standalone
function to keep Routes-related code away from your model.

Generating URLs with subdomains
-------------------------------

If subdomain support is enabled and the ``sub_domain`` arg is passed to
``url_for``, Routes ensures the generated route points to that subdomain. ::

    # Enable subdomain support.
    map.sub_domains = True
    
    # Ignore the www subdomain.
    map.sub_domains_ignore = "www"

    map.connect("/users/{action}")

    # Add a subdomain.
    url_for(action="update", sub_domain="fred")  =>  "http://fred.example.com/users/update"

    # Delete a subdomain.  Assume current URL is fred.example.com.
    url_for(action="new", sub_domain=None)  =>  "http://example.com/users/new"
