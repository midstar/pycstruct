import unittest
import sys
from pycstruct import pycstruct

class TestPyCStruct(unittest.TestCase):
  def test_serialize_deserialize(self):
    m = pycstruct.StructDef('little')

    m.add('int8', 'int8_low')
    m.add('int8', 'int8_high')
    m.add('uint8','uint8_low')
    m.add('uint8','uint8_high')
    m.add('bool8','bool8_false')
    m.add('bool8','bool8_true')
    
    m.add('int16', 'int16_low')
    m.add('int16', 'int16_high')
    m.add('uint16','uint16_low')
    m.add('uint16','uint16_high')
    m.add('bool16','bool16_false')
    m.add('bool16','bool16_true')
    
    m.add('int32',  'int32_low')
    m.add('int32',  'int32_high')
    m.add('uint32', 'uint32_low')
    m.add('uint32', 'uint32_high')
    m.add('bool32', 'bool32_false')
    m.add('bool32', 'bool32_true')
    m.add('float32','float32_low')
    m.add('float32','float32_high')
    
    m.add('int64',  'int64_low')
    m.add('int64',  'int64_high')
    m.add('uint64', 'uint64_low')
    m.add('uint64', 'uint64_high')
    m.add('bool64', 'bool64_false')
    m.add('bool64', 'bool64_true')
    m.add('float64','float64_low')
    m.add('float64','float64_high')

    m.add('utf-8', 'utf8_ascii', 100)
    m.add('utf-8', 'utf8_nonascii', 80)
    m.add('utf-8', 'utf8_no_term', 4)

    f = open("tests/struct.dat","rb")
    result = m.deserialize(f.read())
    f.close()
    
    #for name, value in result.items():
    #  print("{0} = {1}".format(name,value))

    self.assertEqual(result['int8_low'],   -128)
    self.assertEqual(result['int8_high'],   127)
    self.assertEqual(result['uint8_low'],   0)
    self.assertEqual(result['uint8_high'],  255)
    self.assertEqual(result['bool8_false'], False)
    self.assertEqual(result['bool8_true'],  True)

    self.assertEqual(result['int16_low'],   -32768)
    self.assertEqual(result['int16_high'],   32767)
    self.assertEqual(result['uint16_low'],   0)
    self.assertEqual(result['uint16_high'],  65535)
    self.assertEqual(result['bool16_false'], False)
    self.assertEqual(result['bool16_true'],  True)

    self.assertEqual(result['int32_low'],   -2147483648)
    self.assertEqual(result['int32_high'],   2147483647)
    self.assertEqual(result['uint32_low'],   0)
    self.assertEqual(result['uint32_high'],  4294967295)
    self.assertEqual(result['bool32_false'], False)
    self.assertEqual(result['bool32_true'],  True)
    self.assertEqual(round(result['float32_low'], 5), 1.23456)
    self.assertEqual(round(result['float32_high'], 1), 12345.6)

    self.assertEqual(result['int64_low'],   -9223372036854775808)
    self.assertEqual(result['int64_high'],   9223372036854775807)
    self.assertEqual(result['uint64_low'],   0)
    self.assertEqual(result['uint64_high'],  18446744073709551615)
    self.assertEqual(result['bool64_false'], False)
    self.assertEqual(result['bool64_true'],  True)
    self.assertEqual(round(result['float64_low'], 8), 1.23456789)
    self.assertEqual(round(result['float64_high'], 1), 12345678.9)

  '''
  def test_all(self):
    m = pycstruct.StructDef('little')
    m.add('uint64', 'header')
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
'''
if __name__ == '__main__':
    unittest.main()