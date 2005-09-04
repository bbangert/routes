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
    return _RequestConfig()
