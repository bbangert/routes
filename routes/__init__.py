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
        
        def __delattr__(self, name):
            self.__shared_state.__delattr__(name)
else:
    class _RequestConfig(object):
        __shared_state = threadinglocal.local()
        def __getattr__(self, name):
            return self.__shared_state.__getattribute__(name)

        def __setattr__(self, name, value):
            return self.__shared_state.__setattr__(name, value)
        
        def __delattr__(self, name):
            self.__shared_state.__delattr__(name)
  
def request_config(original=False):
    """
    Returns the Routes RequestConfig object.
    
    The Routes RequestConfig object is a thread-local singleton that should be initialized by
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
    
    **Using your own requst local**
    
    If you have your own request local object that you'd like to use instead of the default
    thread local provided by Routes, you can configure Routes to use it::
        
        from routes import request_config()
        config = request_config()
        if hasattr(config, 'using_request_local'):
            config.request_local = YourLocalCallable
            config = request_config()
    
    Once you have configured request_config, its advisable you retrieve it again to get the
    object you wanted. The variable you assign to request_local is assumed to be a callable
    that will get the local config object you wish.
    
    This example tests for the presence of the 'using_request_local' attribute which will be
    present if you haven't assigned it yet. This way you can avoid repeat assignments of the
    request specific callable.
    
    Should you want the original object, perhaps to change the callable its using or stop
    this behavior, call request_config(original=True).
    """
    obj = _RequestConfig()
    if hasattr(obj, 'request_local') and original is False:
        return getattr(obj, 'request_local')()
    else:
        obj.using_request_local = False
    return _RequestConfig()
    
from base import Mapper
from util import url_for, redirect_to
__all__=['Mapper', 'url_for', 'redirect_to', 'request_config']