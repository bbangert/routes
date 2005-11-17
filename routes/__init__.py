"""
Provides common classes and functions most users will want access to.

"""

import threadinglocal, sys

if sys.version < '2.4':
  class _RequestConfig(object):
      __shared_state = threadinglocal.local()
      def __getattr__(self, name):
          return self.__shared_state.__getattr__(name)

      def __setattr__(self, name, value):
          return self.__shared_state.__setattr__(name, value)
else:
  class _RequestConfig(object):
      __shared_state = threadinglocal.local()
      def __getattr__(self, name):
          return self.__shared_state.__getattribute__(name)

      def __setattr__(self, name, value):
          return self.__shared_state.__setattr__(name, value)
  
def request_config():
    """
    Returns the Routes RequestConfig object.
    
    This object is a thread-local singleton that should be initialized by
    the web framework that is utilizing Routes.
    
    To get the Routes RequestConfig:
    
    >>> from routes import *
    >>> config = routes.request_config()
    
    The following attributes must be set on the config object every request:
    
    mapper
        mapper should be a Mapper instance thats ready for use
    host
        host is the hostname of the webapp
    protocol
        protocol is the protocol of the current request
    mapper_dict
        mapper_dict should be the dict returned by mapper.match()
    redirect
        redirect should be a function that issues a redirect, 
        and takes a url as the sole argument
    prefix (optional)
        Set if the application is moved under a URL prefix. Prefix
        will be stripped before matching, and prepended on generation
    environ (optional)
        Set to the WSGI environ for automatic prefix support if the
        webapp is underneath a 'SCRIPT_NAME'
    
    """
    return _RequestConfig()
    
from base import Mapper
from util import url_for, redirect_to
__all__=['Mapper', 'url_for', 'redirect_to', 'request_config']