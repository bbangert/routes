import unittest
from routes import request_config, _RequestConfig
from routes.base import Route

class TestBase(unittest.TestCase):
    def test_route(self):
        route = Route(None, ':controller/:action/:id')
        assert not route.static
    
    def test_request_config(self):
        orig_config = request_config()
        class Obby(object): pass
        myobj = Obby()
        class MyCallable(object):
            def __init__(self):
                class Obby(object): pass
                self.obj = myobj
            
            def __call__(self):
                return self.obj
        
        mycall = MyCallable()
        if hasattr(orig_config, 'using_request_local'):
            orig_config.request_local = mycall 
            config = request_config()
        assert id(myobj) == id(config)
        old_config = request_config(original=True)
        assert issubclass(old_config.__class__, _RequestConfig) is True
        del orig_config.request_local
 
if __name__ == '__main__':
    unittest.main()
