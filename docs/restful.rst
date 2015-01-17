RESTful services
================

Routes makes it easy to configure RESTful web services.  ``map.resource``
creates a set of add/modify/delete routes conforming to the Atom publishing
protocol.

A resource route addresses *members* in a *collection*, and the collection
itself.  Normally a collection is a plural word, and a member is the
corresponding singular word.  For instance, consider a collection of messages::

    map.resource("message", "messages")

    # The above command sets up several routes as if you had typed the
    # following commands:
    map.connect("messages", "/messages",
        controller="messages", action="create",
        conditions=dict(method=["POST"]))
    map.connect("messages", "/messages",
        controller="messages", action="index",
        conditions=dict(method=["GET"]))
    map.connect("formatted_messages", "/messages.{format}",
        controller="messages", action="index",
        conditions=dict(method=["GET"]))
    map.connect("new_message", "/messages/new",
        controller="messages", action="new",
        conditions=dict(method=["GET"]))
    map.connect("formatted_new_message", "/messages/new.{format}",
        controller="messages", action="new",
        conditions=dict(method=["GET"]))
    map.connect("/messages/{id}",
        controller="messages", action="update",
        conditions=dict(method=["PUT"]))
    map.connect("/messages/{id}",
        controller="messages", action="delete",
        conditions=dict(method=["DELETE"]))
    map.connect("edit_message", "/messages/{id}/edit",
        controller="messages", action="edit",
        conditions=dict(method=["GET"]))
    map.connect("formatted_edit_message", "/messages/{id}.{format}/edit",
        controller="messages", action="edit",
        conditions=dict(method=["GET"]))
    map.connect("message", "/messages/{id}",
        controller="messages", action="show",
        conditions=dict(method=["GET"]))
    map.connect("formatted_message", "/messages/{id}.{format}",
        controller="messages", action="show",
        conditions=dict(method=["GET"]))

This establishes the following convention::

    GET    /messages        => messages.index()    => url("messages")
    POST   /messages        => messages.create()   => url("messages")
    GET    /messages/new    => messages.new()      => url("new_message")
    PUT    /messages/1      => messages.update(id) => url("message", id=1)
    DELETE /messages/1      => messages.delete(id) => url("message", id=1)
    GET    /messages/1      => messages.show(id)   => url("message", id=1)
    GET    /messages/1/edit => messages.edit(id)   => url("edit_message", id=1)

.. note::

    Due to how Routes matches a list of URL's, it has no inherent knowledge of
    a route being a **resource**. As such, if a route fails to match due to
    the method requirements not being met, a 404 will return just like any
    other failure to match a route.

Thus, you GET the collection to see an index of links to members ("index"
method).  You GET a member to see it ("show").  You GET "COLLECTION/new" to
obtain a new message form ("new"), which you POST to the collection ("create").
You GET "MEMBER/edit" to obtain an edit for ("edit"), which you PUT to the
member ("update").  You DELETE the member to delete it.  Note that there are
only four route names because multiple actions are doubled up on the same URLs.

This URL structure may look strange if you're not used to the Atom protocol.
REST is a vague term, and some people think it means proper URL syntax (every
component contains the one on its right), others think it means not putting IDs
in query parameters, and others think it means using HTTP methods beyond GET
and POST.  ``map.resource`` does all three, but it may be overkill for
applications that don't need Atom compliance or prefer to stick with GET and
POST.  ``map.resource`` has the advantage that many automated tools and
non-browser agents will be able to list and modify your resources without any
programming on your part.  But you don't have to use it if you prefer a simpler
add/modify/delete structure.

HTML forms can produce only GET and POST requests.  As a workaround, if a POST
request contains a ``_method`` parameter, the Routes middleware changes the
HTTP method to whatever the parameter specifies, as if it had been requested
that way in the first place.  This convention is becoming increasingly common
in other frameworks.  If you're using WebHelpers, the The WebHelpers ``form``
function has a ``method`` argument which automatically sets the HTTP method and
"_method" parameter.

Several routes are paired with an identical route containing the ``format``
variable.  The intention is to allow users to obtain different formats by means
of filename suffixes; e.g., "/messages/1.xml".  This produces a routing
variable "xml", which in Pylons will be passed to the controller action if it
defines a formal argument for it.  In generation you can pass the ``format``
argument to produce a URL with that suffix::

    url("message", id=1, format="xml")  =>  "/messages/1.xml"

Routes does not recognize any particular formats or know which ones are valid
for your application.  It merely passes the ``format`` attribute through if it
appears.

New in Routes 1.7.3: changed URL suffix from ";edit" to "/edit".  Semicolons
are not allowed in the path portion of a URL except to delimit path parameters,
which nobody uses.

Resource options
----------------

The ``map.resource`` method recognizes a number of keyword args which modifies
its behavior:

controller

    Use the specified controller rather than deducing it from the collection
    name.

collection

    Additional URLs to allow for the collection.  Example::

        map.resource("message", "messages", collection={"rss": "GET"})
        # "GET /message/rss"  =>  ``Messages.rss()``.
        # Defines a named route "rss_messages".

member

    Additional URLs to allow for a member.  Example::

        map.resource('message', 'messages', member={'mark':'POST'})
        # "POST /message/1/mark"  =>  ``Messages.mark(1)``
        # also adds named route "mark_message"

    This can be used to display a delete confirmation form::

        map.resource("message", "messages", member={"ask_delete": "GET"}
        # "GET /message/1/ask_delete"   =>   ``Messages.ask_delete(1)``.
        # Also adds a named route "ask_delete_message".

new

    Additional URLs to allow for new-member functionality. ::

        map.resource("message", "messages", new={"preview": "POST"})
        # "POST /messages/new/preview"

path_prefix

    Prepend the specified prefix to all URL patterns.  The prefix may include
    path variables.  This is mainly used to nest resources within resources.

name_prefix

    Prefix the specified string to all route names.  This is most often
    combined with ``path_prefix`` to nest resources::

        map.resource("message", "messages", controller="categories",
            path_prefix="/category/{category_id}",
            name_prefix="category_")
        # GET /category/7/message/1
        # Adds named route "category_message"

parent_resource

        A dict containing information about the parent resource, for creating a
        nested resource. It should contain the member_name and collection_name
        of the parent resource. This dict will be available via the associated
        Route object which can be accessed during a request via
        ``request.environ["routes.route"]``.

        If parent_resource is supplied and path_prefix isn't, path_prefix will
        be generated from parent_resource as "<parent collection name>/:<parent
        member name>_id".

        If parent_resource is supplied and name_prefix isn't, name_prefix will
        be generated from parent_resource as "<parent member name>_".

        Example::

            >>> m = Mapper()
            >>> m.resource('location', 'locations',
            ...            parent_resource=dict(member_name='region',
            ...                                 collection_name='regions'))
            >>> # path_prefix is "regions/:region_id"
            >>> # name prefix is "region_"
            >>> url('region_locations', region_id=13)
            '/regions/13/locations'
            >>> url('region_new_location', region_id=13)
            '/regions/13/locations/new'
            >>> url('region_location', region_id=13, id=60)
            '/regions/13/locations/60'
            >>> url('region_edit_location', region_id=13, id=60)
            '/regions/13/locations/60/edit'

            Overriding generated path_prefix:

            >>> m = Mapper()
            >>> m.resource('location', 'locations',
            ...            parent_resource=dict(member_name='region',
            ...                                 collection_name='regions'),
            ...            path_prefix='areas/:area_id')
            >>> # name prefix is "region_"
            >>> url('region_locations', area_id=51)
            '/areas/51/locations'

            Overriding generated name_prefix:

            >>> m = Mapper()
            >>> m.resource('location', 'locations',
            ...            parent_resource=dict(member_name='region',
            ...                                 collection_name='regions'),
            ...            name_prefix='')
            >>> # path_prefix is "regions/:region_id"
            >>> url('locations', region_id=51)
            '/regions/51/locations'
