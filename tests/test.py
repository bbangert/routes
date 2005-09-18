import unittest, sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from test_generation import TestGeneration
from test_recognition import TestRecognition
from test_utils import TestUtils

if __name__ == '__main__':
    suite = [unittest.makeSuite(TestGeneration)]
    suite.append(unittest.makeSuite(TestRecognition))
    suite.append(unittest.makeSuite(TestUtils))
    for testsuite in suite:
        unittest.TextTestRunner(verbosity=1).run(testsuite)