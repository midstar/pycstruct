import unittest, os, sys

test_dir = os.path.dirname(os.path.realpath(__file__))
proj_dir = os.path.dirname(test_dir)

sys.path.append(proj_dir)
import pycstruct

class TestCParser(unittest.TestCase):

    def test_parse(self):
        parser = pycstruct.CParser(os.path.join(test_dir, 'savestruct.c'))
        structs = parser._parse_xml(os.path.join(test_dir, 'savestruct.xml'))
        structdefs = parser._to_structdefs(structs, 'native')

if __name__ == '__main__':
  unittest.main()