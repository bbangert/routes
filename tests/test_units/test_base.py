import unittest
from routes.base import Route

class TestBase(unittest.TestCase):
    def test_route(self):
        route = Route(':controller/:action/:id')
        assert not route.static
 
if __name__ == '__main__':
    unittest.main()
