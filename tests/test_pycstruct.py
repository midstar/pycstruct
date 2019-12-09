import unittest, os, sys

test_dir = os.path.dirname(os.path.realpath(__file__))
proj_dir = os.path.dirname(test_dir)

sys.path.append(proj_dir)
from pycstruct import pycstruct

class TestPyCStruct(unittest.TestCase):

  def test_invalid_creation(self):
    # Invalid byteorder on creation
    self.assertRaises(Exception, pycstruct.StructDef, "invalid")

  def test_invalid_add(self):

    m = pycstruct.StructDef()

    # Invalid type
    self.assertRaises(Exception, m.add, "invalid", "aname")

    # Invalid length
    self.assertRaises(Exception, m.add, "int8", "aname", 0)

    # Invalid byteorder in member
    self.assertRaises(Exception, m.add, "int8", "aname", 1, "invalid")

    # Duplicaded member
    m.add("int8", "name1")
    self.assertRaises(Exception, m.add, "uint8", "name1")


  def test_invalid_deserialize(self):

    m = pycstruct.StructDef()
    m.add("int8", "name1")

    buffer = bytearray(m.size() + 1)
    self.assertRaises(Exception, m.deserialize, buffer)

  def test_invalid_serialize(self):

    m = pycstruct.StructDef()
    m.add("utf-8", "astring", length=5)

    data = {}
    data["astring"] = 5 # no valid string
    self.assertRaises(Exception, m.serialize, data)

    data["astring"] = "too long string"
    self.assertRaises(Exception, m.serialize, data)

    m.add("int32", "alist", length=5)
    data["astring"] = "valid"
    data["alist"] = 3 # no valid list
    self.assertRaises(Exception, m.serialize, data)

    data["alist"] = [1,2,3,4,5,6,7] # to long
    self.assertRaises(Exception, m.serialize, data)

  def test_empty_data(self):
    m = self.create_struct("native")
    data = m.create_empty_data()
    

  def test_deserialize_serialize_little(self):
    self.deserialize_serialize('little')

  def test_deserialize_serialize_big(self):
    self.deserialize_serialize('big')

  def create_struct(self, byteorder):
    m = pycstruct.StructDef(byteorder)

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

    m.add('int32', 'int32_array', length = 5)

    m.add('utf-8', 'utf8_ascii', 100)
    m.add('utf-8', 'utf8_nonascii', 80)
    m.add('utf-8', 'utf8_no_term', 4)

    return m

  def deserialize_serialize(self, byteorder):

    #############################################
    # Define PyCStruct
    m = self.create_struct(byteorder)

    #############################################
    # Load pre-stored binary data and deserialize

    f = open(os.path.join(test_dir, "struct_{0}.dat".format(byteorder)),"rb")
    inbytes = f.read()
    result = m.deserialize(inbytes)
    f.close()
    
    #for name, value in result.items():
    #  print("{0} = {1}".format(name,value))


    #############################################
    # Check expected values

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

    for i in range(0,5):
      self.assertEqual(result['int32_array'][i], i)

    self.assertEqual(result['utf8_ascii'],   'This is a normal ASCII string!')
    self.assertEqual(result['utf8_nonascii'],'This string has special characters ÅÄÖü')
    self.assertEqual(result['utf8_no_term'], 'ABCD')

    #############################################
    # Serialize result into new byte array

    outbytes = m.serialize(result)

    #############################################
    # Check that generated bytes match read ones

    self.assertEqual(len(inbytes), len(outbytes))
    for i in range(0, len(inbytes)):
      self.assertEqual(int(inbytes[i]), int(outbytes[i]), msg='Index {0}'.format(i))

if __name__ == '__main__':
  unittest.main()