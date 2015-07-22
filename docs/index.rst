====================
Routes Documentation
====================

Routes is a Python re-implementation of the Rails routes system for mapping URLs to application actions, and conversely to generate URLs. Routes makes it easy to create pretty and concise URLs that are RESTful with little effort.

Routes allows conditional matching based on domain, cookies, HTTP method, or a custom function. Sub-domain support is built in. Routes comes with an extensive unit test suite.

Current features:

* Sophisticated route lookup and URL generation
* Named routes
* Redirect routes
* Wildcard paths before and after static parts
* Sub-domain support built-in
* Conditional matching based on domain, cookies, HTTP method (RESTful), and more
* Easily extensible utilizing custom condition functions and route generation
  functions
* Extensive unit tests

Installing
==========

Routes can be easily installed with pip or easy_install::

   $ easy_install routes

Example
=======

.. code-block:: python

   # Setup a mapper
   from routes import Mapper
   map = Mapper()
   map.connect(None, "/error/{action}/{id}", controller="error")
   map.connect("home", "/", controller="main", action="index")

   # Match a URL, returns a dict or None if no match
   result = map.match('/error/myapp/4')
   # result == {'controller': 'error', 'action': 'myapp', 'id': '4'}

Source
======

The `routes source can be found on GitHub <http://github.com/bbangert/routes>`_.

Bugs/Support
============

Bug's can be reported on the `github issue tracker
<https://github.com/bbangert/routes/issues>`_. Note that routes is in maintenance
mode so bug reports are unlikely to be worked on, pull requests will be applied
if submitted with tests.

Documentation
=============

.. toctree::
   :maxdepth: 2

   introduction
   setting_up
   generating
   restful
   uni_redirect_rest
   changes
   todo

.. toctree::
   :maxdepth: 1

   glossary
   porting


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`glossary`

Module Listing
--------------

.. toctree::
    :maxdepth: 2

    modules/index
