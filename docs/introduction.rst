Introduction
============

Routes tackles an interesting problem that comes up frequently in web
development, *how do you map URLs to your application's actions*? That is, how
do you say that *this* should be accessed as "/blog/2008/01/08", and "/login"
should do *that*? Many web frameworks have a fixed dispatching system; e.g., 
"/A/B/C" means to read file "C" in directory "B", or to call method "C" of
class "B" in module "A.B". These work fine until you need to refactor your code
and realize that moving a method changes its public URL and invalidates users'
bookmarks.  Likewise, if you want to reorganize your URLs and make a section
into a subsection, you have to change your carefully-tested logic code.

Routes takes a different approach. You determine your URL hierarchy and 
actions separately, and then link them together in whichever ways you decide.
If you change your mind about a particular URL, just change one line in your
route map and never touch your action logic. You can even have multiple URLs
pointing to the same action; e.g., to support legacy bookmarks.  Routes was
originally inspired by the dispatcher in Ruby on Rails but has since diverged.

Routes is the primary dispatching system in the Pylons web framework, and an
optional choice in CherryPy. It can be added to any
framework without much fuss, and used for an entire site or a URL subtree.
It can also forward subtrees to other dispatching systems, which is how
TurboGears 2 is implemented on top of Pylons.

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

Buzzword compliance:  REST, DRY.

If you're new to Routes or have not read the Routes 1.11 manual before, we
recommend reading the `Glossary <glossary.html>`_ before continuing.

This manual is written from the user's perspective: how to use Routes in a
framework that already supports it. The `Porting <porting.html>`_ 
manual describes how to add Routes support to a new framework.
