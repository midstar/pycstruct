import unittest, os, sys

test_dir = os.path.dirname(os.path.realpath(__file__))
proj_dir = os.path.dirname(test_dir)

sys.path.append(proj_dir)
import pycstruct

class TestCParser(unittest.TestCase):

    def test_parse(self):
        test = pycstruct.CParser(os.path.join(test_dir, 'savestruct.c'), os.path.join(test_dir, 'savestruct.xml'))

if __name__ == '__main__':
  unittest.main()