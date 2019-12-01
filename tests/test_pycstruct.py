import unittest
import sys
from pycstruct import pycstruct

class TestPyCStruct(unittest.TestCase):
  def test_all(self):
    m = pycstruct.StructDef('little')
    m.add('uint32', 'header')
    m.add('uint32', 'length')
    m.add('int32',  'signedInt')
    m.add('uint32', 'unsignedInt')
    m.add('uint32', 'array', 10)
    m.add('utf-8', 'utf8', 100)
    m.add('utf-8', 'utf8_no_term', 4)
    m.add('utf-8', 'utf8_specials', 40)

    print("In Size: " + str(m.size()))
    f = open("tests/struct.dat","rb")
    result = m.deserialize(f.read())
    print("Out Size: " + str(len(result)))
    for name, value in result.items():
      print("{0} = {1}".format(name,value))

    b = m.serialize(result)
    result2 = m.deserialize(b)
    print("\n\nNew result:")
    for name, value in result2.items():
      print("{0} = {1}".format(name,value))

    empty = m.create_empty_data()
    print("\n\nEmpty result:")
    for name, value in empty.items():
      print("{0} = {1}".format(name,value))

if __name__ == '__main__':
    unittest.main()