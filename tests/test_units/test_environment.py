import unittest
import routes

class TestEnvironment(unittest.TestCase):
    def setUp(self):
        m = routes.Mapper(explicit=False)
        m.minimization = True
        m.connect('archive/:year/:month/:day', controller='blog', action='view', month=None, day=None,
                  requirements={'month':'\d{1,2}','day':'\d{1,2}'})
        m.connect('viewpost/:id', controller='post', action='view')
        m.connect(':controller/:action/:id')
        m.create_regs(['content', 'blog'])
        con = routes.request_config()
        con.mapper = m
        self.con = con
    
    def test_env_set(self):
        env = dict(PATH_INFO='/content', HTTP_HOST='somewhere.com')
        con = self.con
        con.mapper_dict = {}
        assert con.mapper_dict == {}
        delattr(con, 'mapper_dict')
        
        assert not hasattr(con, 'mapper_dict')
        con.mapper_dict = {}
        
        con.environ = env
        assert con.mapper.environ == env
        assert con.protocol == 'http'
        assert con.host == 'somewhere.com'
        assert 'controller' in con.mapper_dict
        assert con.mapper_dict['controller'] == 'content'

if __name__ == '__main__':
    unittest.main()
