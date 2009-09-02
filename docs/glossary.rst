.. _glossary:

Glossary
========



.. glossary::

    component
        A part of a URL delimited by slashes.  The URL "/help/about" contains
        two components: "help" and "about".
    
    generation
        The act of creating a URL based on a route name and/or variable values.
        This is the opposite of matching.  Finding a route by name is called
        *named generation*.  Finding a route without specifying a name is
        called *nameless generation*.

    mapper
        A container for routes.  There is normally one mapper per application,
        although nested subapplications might have their own mappers.  A
        mapper knows how to match routes and generate them.

    matching
        The act of matching a given URL against a list  of routes, and
        returning the routing variables.  See the *route* entry for an example.

    minimization
        A deprecated feature which allowed short URLs to match long paths.
        Details are in the ``Backward Compatibility`` section in the manual. 

    route
        A rule mapping a URL pattern to a dict of routing  variables.   For
        instance, if the pattern is "/{controller}/{action}" and the requested
        URL is "/help/about", the resulting dict would be::

            {"controller": "help", "action": "about"}

        Routes does not know what these variables mean; it simply returns them
        to the application.  Pylons would look for a ``controllers/help.py``
        module containing a ``HelpController`` class, and call its ``about``
        method.  Other frameworks may do something different.

        A route may have a name, used to identify the route.

    route path
        The URL pattern in a route.

    routing variables
        A dict of key-value pairs returned by matching.  Variables defined in
        the route path are called *path variables*; their values will be taken
        from the URL.  Variables defined outside the route path are called
        *default variables*; their values are not affected by the URL. 
        
        The WSGI.org environment key for routing variables is
        "wsgiorg.routing_args".  This manual does not use that term because it
        can be confused with function arguments.
        
