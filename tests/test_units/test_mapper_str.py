import unittest
from routes import Mapper

class TestMapperStr(unittest.TestCase):
    def test_str(self):
        m = Mapper()
        m.connect('/{controller}/{action}')
        m.connect('entries', '/entries', controller='entry', action='index')
        m.connect('entry', '/entries/{id}', controller='entry', action='show')

        expected = """\
Route name Methods Path
                   /{controller}/{action}
entries            /entries
entry              /entries/{id}"""
        
        for expected_line, actual_line in zip(expected.splitlines(), str(m).splitlines()):
            assert expected_line == actual_line.rstrip()
