import unittest
from test_generation import TestGeneration
from test_recognition import TestRecognition

if __name__ == '__main__':
    suite = unittest.makeSuite(TestGeneration)
    suite2 = unittest.makeSuite(TestRecognition)
    unittest.TextTestRunner(verbosity=2).run(suite)
    unittest.TextTestRunner(verbosity=2).run(suite2)