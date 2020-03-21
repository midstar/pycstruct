import unittest, os, sys

test_dir = os.path.dirname(os.path.realpath(__file__))
proj_dir = os.path.dirname(test_dir)

sys.path.append(proj_dir)
import pycstruct

class TestPyCStruct(unittest.TestCase):

  def test_invalid_baseclass(self):

    b = pycstruct.BaseDef()

    self.assertRaises(NotImplementedError, b.size)
    self.assertRaises(NotImplementedError, b.serialize, 0)
    self.assertRaises(NotImplementedError, b.deserialize, 0)

  def test_invalid_creation(self):
    # Invalid byteorder on creation
    self.assertRaises(Exception, pycstruct.StructDef, 'invalid')

  def test_invalid_add(self):

    m = pycstruct.StructDef()

    # Invalid type
    self.assertRaises(Exception, m.add, 'invalid', 'aname')

    # Invalid length
    self.assertRaises(Exception, m.add, 'int8', 'aname', 0)

    # Invalid byteorder in member
    self.assertRaises(Exception, m.add, 'int8', 'aname', 1, 'invalid')

    # Duplicaded member
    m.add('int8', 'name1')
    self.assertRaises(Exception, m.add, 'uint8', 'name1')


  def test_invalid_deserialize(self):

    m = pycstruct.StructDef()
    m.add('int8', 'name1')

    buffer = bytearray(m.size() + 1)
    self.assertRaises(Exception, m.deserialize, buffer)

  def test_invalid_serialize(self):

    m = pycstruct.StructDef()
    m.add('utf-8', 'astring', length=5)

    data = {}
    data['astring'] = 5 # no valid string
    self.assertRaises(Exception, m.serialize, data)

    data['astring'] = 'too long string'
    self.assertRaises(Exception, m.serialize, data)

    m.add('int32', 'alist', length=5)
    data['astring'] = 'valid'
    data['alist'] = 3 # no valid list
    self.assertRaises(Exception, m.serialize, data)

    data['alist'] = [1,2,3,4,5,6,7] # to long
    self.assertRaises(Exception, m.serialize, data)

  def test_empty_data(self):
    m = self.create_struct('native', 1)
    data = m.create_empty_data()
    # Check a few of the fields
    self.assertTrue('int8_low' in data)
    self.assertTrue('utf8_nonascii' in data)
    

  def test_deserialize_serialize_little(self):
    self.deserialize_serialize('little', 1, 'struct_little.dat')

  def test_deserialize_serialize_little_nopack(self):
    self.deserialize_serialize('little', 8, 'struct_little_nopack.dat')

  def test_deserialize_serialize_big(self):
    self.deserialize_serialize('big', 1, 'struct_big.dat')

  def test_deserialize_serialize_big_nopack(self):
    self.deserialize_serialize('big', 8, 'struct_big_nopack.dat')

  def create_struct(self, byteorder, alignment):
    m = pycstruct.StructDef(byteorder, alignment)

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

  def deserialize_serialize(self, byteorder, alignment, filename):

    #############################################
    # Define PyCStruct
    m = self.create_struct(byteorder, alignment)

    #############################################
    # Load pre-stored binary data and deserialize

    f = open(os.path.join(test_dir, filename),'rb')
    inbytes = f.read()
    result = m.deserialize(inbytes)
    f.close()
    
    #for name, value in result.items():
    #  print('{0} = {1}'.format(name,value))


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

  def test_embedded_struct(self):
    car_type = pycstruct.EnumDef()
    car_type.add('Sedan', 0)
    car_type.add('Station_Wagon', 5)
    car_type.add('Bus', 7)
    car_type.add('Pickup', 12)
    car_type.add('_padding_', 0xFFFFFFF) # To ensure 4 bytes

    car_properties = pycstruct.BitfieldDef()
    car_properties.add('class', 3)
    car_properties.add('registered', 1)
    car_properties.add('over_3500_kg', 1)


    car = pycstruct.StructDef()
    car.add('uint16', 'year')
    car.add('utf-8', 'model', length=50)
    car.add('utf-8', 'registration_number', length=10)
    car.add(car_properties, 'properties')
    car.add(car_type, 'type')

    garage = pycstruct.StructDef()
    garage.add(car, 'cars', length=20)
    garage.add('uint8', 'nbr_registered_parkings')

    house = pycstruct.StructDef()
    house.add('uint8', 'nbr_of_levels')
    house.add(garage, 'garage')

    #############################################
    # Load pre-stored binary data and deserialize

    f = open(os.path.join(test_dir, 'embedded_struct.dat'),'rb')
    inbytes = f.read()
    result = house.deserialize(inbytes)
    f.close()



    #############################################
    # Check expected values

    self.assertEqual(result['nbr_of_levels'], 5)
    self.assertEqual(result['garage']['nbr_registered_parkings'], 3)
    self.assertEqual(result['garage']['cars'][0]['year'], 2011)
    self.assertEqual(result['garage']['cars'][0]['properties']['class'], 0)
    self.assertEqual(result['garage']['cars'][0]['properties']['registered'], 1)
    self.assertEqual(result['garage']['cars'][0]['properties']['over_3500_kg'], 0)
    self.assertEqual(result['garage']['cars'][0]['type'], 'Sedan')
    self.assertEqual(result['garage']['cars'][0]['registration_number'], 'AHF432')
    self.assertEqual(result['garage']['cars'][0]['model'], 'Nissan Micra')
    self.assertEqual(result['garage']['cars'][1]['year'], 2005)
    self.assertEqual(result['garage']['cars'][1]['properties']['class'], 1)
    self.assertEqual(result['garage']['cars'][1]['properties']['registered'], 1)
    self.assertEqual(result['garage']['cars'][1]['properties']['over_3500_kg'], 1)
    self.assertEqual(result['garage']['cars'][1]['type'], 'Bus')
    self.assertEqual(result['garage']['cars'][1]['registration_number'], 'CCO544')
    self.assertEqual(result['garage']['cars'][1]['model'], 'Ford Focus')
    self.assertEqual(result['garage']['cars'][2]['year'], 1998)
    self.assertEqual(result['garage']['cars'][2]['properties']['class'], 3)
    self.assertEqual(result['garage']['cars'][2]['properties']['registered'], 0)
    self.assertEqual(result['garage']['cars'][2]['properties']['over_3500_kg'], 0)
    self.assertEqual(result['garage']['cars'][2]['type'], 'Pickup')
    self.assertEqual(result['garage']['cars'][2]['registration_number'], 'HHT434')
    self.assertEqual(result['garage']['cars'][2]['model'], 'Volkswagen Golf')

    #############################################
    # Serialize result into new byte array

    outbytes = house.serialize(result)

    #############################################
    # Check that generated bytes match read ones

    self.assertEqual(len(inbytes), len(outbytes))
    for i in range(0, len(inbytes)):
      self.assertEqual(int(inbytes[i]), int(outbytes[i]), msg='Index {0}'.format(i))


  def test_bitfield_invalid_creation(self):
    # Invalid byteorder on creation
    self.assertRaises(Exception, pycstruct.BitfieldDef, 'invalid')

  def test_bitfield_add(self):
    bitfield = pycstruct.BitfieldDef()

    self.assertEqual(bitfield.assigned_bits(), 0)
    self.assertEqual(bitfield.size(), 0)

    bitfield.add("one_bit")
    self.assertEqual(bitfield.assigned_bits(), 1)
    bitfield.add("two_bits", 2)
    bitfield.add("three_bits", 3)
    bitfield.add("two_bits_signed", 2, signed=True)
    self.assertEqual(bitfield.assigned_bits(), 8)
    self.assertEqual(bitfield.size(), 1)

    bitfield.add("one_more_bit")
    self.assertEqual(bitfield.assigned_bits(), 9)
    self.assertEqual(bitfield.size(), 2)
    bitfield.add("seven_bits", 7)
    self.assertEqual(bitfield.assigned_bits(), 16)
    self.assertEqual(bitfield.size(), 2)

    bitfield.add("three_bits_signed", 3, signed=True)
    self.assertEqual(bitfield.assigned_bits(), 19)
    self.assertEqual(bitfield.size(), 3)

    bitfield.add("32_bits", 32)
    self.assertEqual(bitfield.assigned_bits(), 51)
    self.assertEqual(bitfield.size(), 7)

    bitfield.add("13_signed_bits", 13, signed=True)
    self.assertEqual(bitfield.assigned_bits(), 64)
    self.assertEqual(bitfield.size(), 8)

    # Should overflow
    self.assertRaises(Exception, bitfield.add, 'this_wont_fit_in_64_bits')


    # Same bit field name again - forbidden
    self.assertRaises(Exception, bitfield.add, 'three_bits')

  def create_bitfield(self, byteorder):
    b = pycstruct.BitfieldDef(byteorder)

    b.add("onebit",1 ,signed=False)
    b.add("twobits",2 ,signed=False)
    b.add("threebits",3 ,signed=False)
    b.add("fourbits",4 ,signed=False)
    b.add("fivesignedbits",5 ,signed=True)
    b.add("eightbits",8 ,signed=False)
    b.add("eightsignedbits",8 ,signed=True)
    b.add("onesignedbit",1 ,signed=True)
    b.add("foursignedbits",4 ,signed=True)
    b.add("sixteensignedbits",16 ,signed=True)
    b.add("fivebits",5 ,signed=False)

    return b

  def deserialize_serialize_bitfield(self, byteorder):

    #############################################
    # Define Bitfield
    b = self.create_bitfield(byteorder)

    #############################################
    # Load pre-stored binary data and deserialize

    f = open(os.path.join(test_dir, 'bitfield_{0}.dat'.format(byteorder)),'rb')
    inbytes = f.read()
    result = b.deserialize(inbytes)
    f.close()

    #############################################
    # Check expected values
    self.assertEqual(result['onebit'], 1)
    self.assertEqual(result['twobits'], 3)
    self.assertEqual(result['threebits'], 1)
    self.assertEqual(result['fourbits'], 3)
    self.assertEqual(result['fivesignedbits'], -2)
    self.assertEqual(result['eightbits'], 255)
    self.assertEqual(result['eightsignedbits'], -128)
    self.assertEqual(result['onesignedbit'], -1)
    self.assertEqual(result['foursignedbits'], 5)
    self.assertEqual(result['sixteensignedbits'], -12345)
    self.assertEqual(result['fivebits'], 16)

    #############################################
    # Serialize result into new byte array

    outbytes = b.serialize(result)

    #############################################
    # Check that generated bytes match read ones

    self.assertEqual(len(inbytes), len(outbytes))
    for i in range(0, len(inbytes)):
      self.assertEqual(int(inbytes[i]), int(outbytes[i]), msg='Index {0}'.format(i))

  def test_bitfield_deserialize_serialize_little(self):
    self.deserialize_serialize_bitfield('little')

  def test_bitfield_deserialize_serialize_big(self):
    self.deserialize_serialize_bitfield('big')

  def test_bitfield_invalid_deserialize(self):

    b = pycstruct.BitfieldDef()
    b.add('afield')

    buffer = bytearray(b.size() + 1)
    self.assertRaises(Exception, b.deserialize, buffer)

  def test_bitfield_getsubvalue(self):
    bitstruct = pycstruct.BitfieldDef()
    value = int('0101110001010011', 2)

    # Unsigned tests
    self.assertEqual(bitstruct._get_subvalue(value, nbr_of_bits = 1, start_bit = 0, signed = False), 1)
    self.assertEqual(bitstruct._get_subvalue(value, nbr_of_bits = 4, start_bit = 0, signed = False), 3)
    self.assertEqual(bitstruct._get_subvalue(value, nbr_of_bits = 16, start_bit = 0, signed = False), 23635)
    self.assertEqual(bitstruct._get_subvalue(value, nbr_of_bits = 15, start_bit = 0, signed = False), 23635)
    self.assertEqual(bitstruct._get_subvalue(value, nbr_of_bits = 14, start_bit = 2, signed = False), 5908)
    self.assertEqual(bitstruct._get_subvalue(value, nbr_of_bits = 3, start_bit = 4, signed = False), 5)

    # Signed tests
    self.assertEqual(bitstruct._get_subvalue(value, nbr_of_bits = 1, start_bit = 0, signed = True), -1)
    self.assertEqual(bitstruct._get_subvalue(value, nbr_of_bits = 4, start_bit = 0, signed = True), 3)
    self.assertEqual(bitstruct._get_subvalue(value, nbr_of_bits = 16, start_bit = 0, signed = True), 23635)
    self.assertEqual(bitstruct._get_subvalue(value, nbr_of_bits = 15, start_bit = 0, signed = True), -9133)
    self.assertEqual(bitstruct._get_subvalue(value, nbr_of_bits = 14, start_bit = 2, signed = True), 5908)
    self.assertEqual(bitstruct._get_subvalue(value, nbr_of_bits = 3, start_bit = 4, signed = True), -3)


  def test_bitfield_setsubvalue(self):
    bitstruct = pycstruct.BitfieldDef()
    

    # Unsigned tests
    self.assertEqual(bin(bitstruct._set_subvalue(0, 1, nbr_of_bits = 1, start_bit = 0, signed = False)), '0b1')
    self.assertEqual(bin(bitstruct._set_subvalue(0, 1, nbr_of_bits = 1, start_bit = 2, signed = False)), '0b100')
    self.assertEqual(bin(bitstruct._set_subvalue(0, 5, nbr_of_bits = 3, start_bit = 5, signed = False)), '0b10100000')

    value = int('010100001111', 2)
    self.assertEqual(bin(bitstruct._set_subvalue(value, 15, nbr_of_bits = 4, start_bit = 4, signed = False)), '0b10111111111')

    # Signed tests
    value = 0
    self.assertEqual(bin(bitstruct._set_subvalue(0, -1, nbr_of_bits = 1, start_bit = 0, signed = True)), '0b1')
    self.assertEqual(bin(bitstruct._set_subvalue(0, -1, nbr_of_bits = 1, start_bit = 2, signed = True)), '0b100')
    self.assertEqual(bin(bitstruct._set_subvalue(0, -5, nbr_of_bits = 4, start_bit = 5, signed = True)), '0b101100000')
    self.assertEqual(bin(bitstruct._set_subvalue(0,  5, nbr_of_bits = 4, start_bit = 5, signed = True)), '0b10100000')

    # Invalid values
    self.assertRaises(Exception, bitstruct._set_subvalue, 0, -1, 1, 0, False)
    self.assertRaises(Exception, bitstruct._set_subvalue, 0, 2, 1, 0, False)
    self.assertRaises(Exception, bitstruct._set_subvalue, 0, 8, 3, 0, False)
    self.assertRaises(Exception, bitstruct._set_subvalue, 0, -2, 1, 0, True)
    self.assertRaises(Exception, bitstruct._set_subvalue, 0, 2, 1, 0, True)
    self.assertRaises(Exception, bitstruct._set_subvalue, 0, 7, 3, 0, True)


  def test_enum_invalid_creation(self):
    # Invalid byteorder on creation
    self.assertRaises(Exception, pycstruct.EnumDef, 'invalid')


  def test_enum_add(self):
    e = pycstruct.EnumDef()

    self.assertEqual(e.size(), 1)

    e.add("first")
    self.assertEqual(e.get_value("first"), 0)
    self.assertEqual(e.get_name(0), "first")
    self.assertEqual(e.size(), 1)

    e.add("second", 1)
    self.assertEqual(e.get_value("second"), 1)
    self.assertEqual(e.get_name(1), "second")
    self.assertEqual(e.size(), 1)

    e.add("fitbyte", 127)
    self.assertEqual(e.get_value("fitbyte"), 127)
    self.assertEqual(e.get_name(127), "fitbyte")
    self.assertEqual(e.size(), 1)

    e.add("third")
    self.assertEqual(e.get_value("third"), 2)
    self.assertEqual(e.get_name(2), "third")
    self.assertEqual(e.size(), 1)

    e.add("dont_fit_byte", 128)
    self.assertEqual(e.size(), 2)

    # Duplicate
    self.assertRaises(Exception, e.add, "second")

    # > 64 bits
    self.assertRaises(Exception, e.add, "too_big", 12345678901234561234567)

    # Get invalid value
    self.assertRaises(Exception, e.get_value, 33)

    # Get invalid name
    self.assertRaises(Exception, e.get_name, "invalid")

  def test_enum_serialize_deserialize(self):
    e = pycstruct.EnumDef()
    e.add("zero", 0)
    e.add("one", 1)
    e.add("two", 2)
    e.add("three", 2)

    value = "two"
    buf = e.serialize(value)
    self.assertEqual(len(buf), 1)
    self.assertEqual(buf[0], 2)

    big = pycstruct.EnumDef('big')
    big.add("twofiftysix", 256)
    value = "twofiftysix"
    buf = big.serialize(value)
    self.assertEqual(len(buf), 2)
    self.assertEqual(buf[0], 1)
    self.assertEqual(buf[1], 0)
    outval = big.deserialize(buf)
    self.assertEqual(outval, "twofiftysix")

    little = pycstruct.EnumDef('little')
    little.add("twofiftysix", 256)
    value = "twofiftysix"
    buf = little.serialize(value)
    self.assertEqual(len(buf), 2)
    self.assertEqual(buf[0], 0)
    self.assertEqual(buf[1], 1)
    outval = little.deserialize(buf)
    self.assertEqual(outval, "twofiftysix")

  def test_enum_invalid_deserialize(self):

    e = pycstruct.EnumDef()
    e.add('zero')

    buffer = bytearray(e.size() + 1)
    self.assertRaises(Exception, e.deserialize, buffer)

  def test_get_padding(self):
    padding = pycstruct.pycstruct._get_padding

    # Alignment 1
    self.assertEqual(padding(1, 5, 4), 0)

    # Alignment 2
    self.assertEqual(padding(2, 0, 1), 0)
    self.assertEqual(padding(2, 0, 2), 0)
    self.assertEqual(padding(2, 0, 4), 0)
    self.assertEqual(padding(2, 0, 8), 0)
    self.assertEqual(padding(2, 1, 1), 0)
    self.assertEqual(padding(2, 1, 2), 1)
    self.assertEqual(padding(2, 1, 4), 1)
    self.assertEqual(padding(2, 1, 8), 1)
    self.assertEqual(padding(2, 2, 1), 0)
    self.assertEqual(padding(2, 2, 2), 0)
    self.assertEqual(padding(2, 2, 4), 0)
    self.assertEqual(padding(2, 2, 8), 0)
    self.assertEqual(padding(2, 3, 1), 0)
    self.assertEqual(padding(2, 3, 2), 1)
    self.assertEqual(padding(2, 3, 4), 1)
    self.assertEqual(padding(2, 3, 8), 1)

    # Alignment 4
    self.assertEqual(padding(4, 0, 1), 0)
    self.assertEqual(padding(4, 0, 2), 0)
    self.assertEqual(padding(4, 0, 4), 0)
    self.assertEqual(padding(4, 0, 8), 0)
    self.assertEqual(padding(4, 1, 1), 0)
    self.assertEqual(padding(4, 1, 2), 1)
    self.assertEqual(padding(4, 1, 4), 3)
    self.assertEqual(padding(4, 1, 8), 3)
    self.assertEqual(padding(4, 2, 1), 0)
    self.assertEqual(padding(4, 2, 2), 0)
    self.assertEqual(padding(4, 2, 4), 2)
    self.assertEqual(padding(4, 2, 8), 2)
    self.assertEqual(padding(4, 3, 1), 0)
    self.assertEqual(padding(4, 3, 2), 1)
    self.assertEqual(padding(4, 3, 4), 1)
    self.assertEqual(padding(4, 3, 8), 1)
    self.assertEqual(padding(4, 4, 1), 0)
    self.assertEqual(padding(4, 4, 2), 0)
    self.assertEqual(padding(4, 4, 4), 0)
    self.assertEqual(padding(4, 4, 8), 0)
    self.assertEqual(padding(4, 5, 1), 0)
    self.assertEqual(padding(4, 5, 2), 1)
    self.assertEqual(padding(4, 5, 4), 3)
    self.assertEqual(padding(4, 5, 8), 3)

    # Alignment 8
    self.assertEqual(padding(8, 0, 1), 0)
    self.assertEqual(padding(8, 0, 2), 0)
    self.assertEqual(padding(8, 0, 4), 0)
    self.assertEqual(padding(8, 0, 8), 0)
    self.assertEqual(padding(8, 1, 1), 0)
    self.assertEqual(padding(8, 1, 2), 1)
    self.assertEqual(padding(8, 1, 4), 3)
    self.assertEqual(padding(8, 1, 8), 7)
    self.assertEqual(padding(8, 2, 1), 0)
    self.assertEqual(padding(8, 2, 2), 0)
    self.assertEqual(padding(8, 2, 4), 2)
    self.assertEqual(padding(8, 2, 8), 6)
    self.assertEqual(padding(8, 3, 1), 0)
    self.assertEqual(padding(8, 3, 2), 1)
    self.assertEqual(padding(8, 3, 4), 1)
    self.assertEqual(padding(8, 3, 8), 5)
    self.assertEqual(padding(8, 4, 1), 0)
    self.assertEqual(padding(8, 4, 2), 0)
    self.assertEqual(padding(8, 4, 4), 0)
    self.assertEqual(padding(8, 4, 8), 4)
    self.assertEqual(padding(8, 5, 1), 0)
    self.assertEqual(padding(8, 5, 2), 1)
    self.assertEqual(padding(8, 5, 4), 3)
    self.assertEqual(padding(8, 5, 8), 3)
    self.assertEqual(padding(8, 7, 8), 1)
    self.assertEqual(padding(8, 8, 8), 0)
    self.assertEqual(padding(8, 9, 8), 7)
    
if __name__ == '__main__':
  unittest.main()