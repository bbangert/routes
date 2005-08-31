import unittest, sys
sys.path.append('./tests')
sys.path.append('./lib')

from test_generation import TestGeneration
from test_recognition import TestRecognition
from test_utils import TestUtils

if __name__ == '__main__':
    suite = [unittest.makeSuite(TestGeneration)]
    suite.append(unittest.makeSuite(TestRecognition))
    suite.append(unittest.makeSuite(TestUtils))
    for testsuite in suite:
        unittest.TextTestRunner(verbosity=1).run(testsuite)