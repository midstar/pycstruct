import struct, collections, math

_TYPE = {
  'int8'    : {'format' : 'b', 'bytes' : 1},
  'uint8'   : {'format' : 'B', 'bytes' : 1},
  'bool8'   : {'format' : 'B', 'bytes' : 1},
  'int16'   : {'format' : 'h', 'bytes' : 2},
  'uint16'  : {'format' : 'H', 'bytes' : 2},
  'bool16'  : {'format' : 'H', 'bytes' : 2},
  'float16' : {'format' : 'e', 'bytes' : 2},
  'int32'   : {'format' : 'i', 'bytes' : 4},
  'uint32'  : {'format' : 'I', 'bytes' : 4},
  'bool32'  : {'format' : 'I', 'bytes' : 4},
  'float32' : {'format' : 'f', 'bytes' : 4},
  'int64'   : {'format' : 'q', 'bytes' : 8},
  'uint64'  : {'format' : 'Q', 'bytes' : 8},
  'bool64'  : {'format' : 'Q', 'bytes' : 8},
  'float64' : {'format' : 'd', 'bytes' : 8},
  'utf-8'   : {'format' : 'B', 'bytes' : 1}
}

_BYTEORDER = {
  'native' : {'format' : '='},
  'little' : {'format' : '<'},
  'big'    : {'format' : '>'}
}

class StructDef:
  """This class represents a struct definition



  :param default_byteorder: Byte order of each element unless explicilty set 
                            for the element. Valid values are 'native', 
                            'little' and 'big'.
  :type default_byteorder: str, optional
  """

  def __init__(self, default_byteorder = 'native'):
    """Constructor method"""
    if default_byteorder not in _BYTEORDER:
      raise Exception('Invalid byteorder: {0}.'.format(default_byteorder))
    self.__default_byteorder = default_byteorder
    self.__fields = collections.OrderedDict()
  
  def add(self, type, name, length = 1, byteorder = ''):
    """Add a new element in the struct definition. The element will be added 
       directly after the previous element. Padding is never added.

       - Supported data types:

          +------------+---------------+--------------------------------------+
          | Name       | Size in bytes | Comment                              |
          +============+===============+======================================+
          | int8       | 1             | Integer                              |
          +------------+---------------+--------------------------------------+
          | uint8      | 1             | Unsigned integer                     |
          +------------+---------------+--------------------------------------+
          | bool8      | 1             | True (<>0) or False (0)              |
          +------------+---------------+--------------------------------------+
          | int16      | 2             | Integer                              |
          +------------+---------------+--------------------------------------+
          | uint16     | 2             | Unsigned integer                     |
          +------------+---------------+--------------------------------------+
          | bool16     | 2             | True (<>0) or False (0)              |
          +------------+---------------+--------------------------------------+
          | float16    | 2             | Floating point number                |
          +------------+---------------+--------------------------------------+
          | int32      | 4             | Integer                              |
          +------------+---------------+--------------------------------------+
          | uint32     | 4             | Unsigned integer                     |
          +------------+---------------+--------------------------------------+
          | bool32     | 4             | True (<>0) or False (0)              |
          +------------+---------------+--------------------------------------+
          | float32    | 4             | Floating point number                |
          +------------+---------------+--------------------------------------+
          | int64      | 8             | Integer                              |
          +------------+---------------+--------------------------------------+
          | uint64     | 8             | Unsigned integer                     |
          +------------+---------------+--------------------------------------+
          | bool64     | 8             | True (<>0) or False (0)              |
          +------------+---------------+--------------------------------------+
          | float64    | 8             | Floating point number                |
          +------------+---------------+--------------------------------------+
          | utf-8      | 1             | UTF-8/ASCII string. Use length       |
          |            |               | parameter to set the length of the   |
          |            |               | string including null termination    |
          +------------+---------------+--------------------------------------+
          | struct     | struct size   | Embedded struct. The actual struct   |
          |            |               | definition shall be set as type and  |
          |            |               | not 'struct' string.                 |
          +------------+---------------+--------------------------------------+
       
       :param type: Element data type. See above.
       :type type: str
       :param name: Name of element. Needs to be unique.
       :type name: str
       :param length: Number of elements. If > 1 this is an array/list of elements with equal size. Default is 1.
       :type length: int, optional
       :param byteorder: Byteorder of this element. Valid values are 'native', 
                         'little' and 'big'. If not specified the default byteorder is used.
       :type byteorder: str, optional"""
    if length < 1:
      raise Exception('Invalid length: {0}.'.format(length))
    if name in self.__fields:
      raise Exception('Field name already exist: {0}.'.format(name))
    if byteorder == "":
      byteorder = self.__default_byteorder
    elif byteorder not in _BYTEORDER:
      raise Exception('Invalid byteorder: {0}.'.format(byteorder))
    if type not in _TYPE and not isinstance(type, StructDef):
      raise Exception('Invalid type: {0}.'.format(type))

    self.__fields[name] = {'type' : type, 'length' : length, 'byteorder' : byteorder}

  def size(self):
    """ Get size of structure

    :return: Number of bytes this structure represents
    :rtype: int
    """
    size = 0
    for field in self.__fields.values():
      nbr_bytes = 0
      if isinstance(field['type'], StructDef):
        nbr_bytes = field['type'].size()
      else:
        nbr_bytes =  _TYPE[field['type']]['bytes']
      size += field['length'] * nbr_bytes
    return size

  def deserialize(self, buffer):
    """ Deserialize buffer into dictionary

    :param buffer: Buffer that contains the data to deserialize
    :type buffer: bytearray
    :return: A dictionary keyed with the element names
    :rtype: dict
    """
    result = {}
    if len(buffer) != self.size():
      raise Exception("Invalid buffer size: {0}. Expected: {1}".format(len(buffer),self.size()))
    offset = 0
    for name, field in self.__fields.items():
      datatype = field['type']
      length = field['length']
      datatype_size = 0
      typeinfo = 0
      if isinstance(datatype, StructDef):
        datatype_size = datatype.size()
      else:
        typeinfo = _TYPE[datatype]
        datatype_size = typeinfo['bytes']

      if datatype == 'utf-8':
        utf8_bytes = buffer[offset:offset + length]
        # Find null termination
        index = utf8_bytes.find(0)
        if index >= 0:
          utf8_bytes = utf8_bytes[:index]
        result[name] = utf8_bytes.decode('utf-8') 
      else: 
        values = []
        if isinstance(datatype, StructDef):
          for i in range(0, length):
            next_offset = offset + i*datatype_size
            buffer_subset = buffer[next_offset:next_offset + datatype_size]
            value = datatype.deserialize(buffer_subset)
            values.append(value)
        else:
          format = _BYTEORDER[field['byteorder']]['format'] + typeinfo['format']
          for i in range(0, length):
            value = struct.unpack_from(format, buffer, offset + i*datatype_size)[0]
            if field['type'].startswith("bool"):
              if value == 0:
                value = False
              else:
                value = True
            values.append(value)
        if length == 1:
          result[name] = values[0]
        else:
          result[name] = values

      offset += datatype_size * length
    return result

  def serialize(self, data):
    """ Serialize dictionary into buffer

    :param data: A dictionary keyed with element names. Elements can be omitted from the dictionary (defaults to value 0).
    :type data: dict
    :return: A buffer that contains data
    :rtype: bytearray
    """
    buffer = bytearray(self.size())
    offset = 0
    for name, field in self.__fields.items():
      datatype = field['type']
      length = field['length']
      datatype_size = 0
      typeinfo = 0
      if isinstance(datatype, StructDef):
        datatype_size = datatype.size()
      else:
        typeinfo = _TYPE[datatype]
        datatype_size = typeinfo['bytes']

      if name in data:
        value = data[name]
        if datatype == 'utf-8':
          if not isinstance(value, str):
            raise Exception('Key: {0} shall be a string'.format(name))
          utf8_bytes = value.encode('utf-8')
          if len(utf8_bytes) > length:
            raise Exception('String in key: {0} is larger than {1}'.format(name, length))
          for i in range(0, len(utf8_bytes)):
            buffer[i+offset] = utf8_bytes[i]
        else:
          value_list = []
          if length > 1:
            if not isinstance(value, collections.Iterable):
              raise Exception('Key: {0} shall be a list'.format(name))
            if len(value) > length:
              raise Exception('List in key: {0} is larger than {1}'.format(name, length))
            value_list = value
          else:
            value_list.append(value) # Make list of single value
          if isinstance(datatype, StructDef):
            for i in range(0, len(value_list)):
              next_offset = offset + i*datatype_size
              buffer[next_offset:next_offset + datatype_size] = datatype.serialize(value_list[i])
          else:
            format = _BYTEORDER[field['byteorder']]['format'] + typeinfo['format']
            for i in range(0, len(value_list)):
              struct.pack_into(format, buffer, offset + i * datatype_size, value_list[i])

      offset += datatype_size * length
    return buffer

  def create_empty_data(self):
    """ Create an empty dictionary with all keys

    :return: A dictionary keyed with the element names. Values are "empty" or 0.
    :rtype: dict
    """
    buffer = bytearray(self.size())
    return self.deserialize(buffer)

class BitfieldDef:
  """This class represents a bit field definition

  The size of the bit field is 1, 2, 4 or 8 bytes depending on the number of
  elements added to the bit field. If a lager size is required than what
  is required by the elements you have to add additional, "dummy", elements.

  :param byteorder: Byte order of the bitfield. Valid values are 'native', 
                    'little' and 'big'.
  :type byteorder: str, optional
  """

  def __init__(self, byteorder = 'native'):
    if byteorder not in _BYTEORDER:
      raise Exception('Invalid byteorder: {0}.'.format(byteorder))
    self._byteorder = byteorder
    self._type = 'uint8' # Might be expanded when elements are added
    self.__fields = collections.OrderedDict()

  def add(self, name, nbr_of_bits = 1, signed = False):
      """Add a new element in the bitfield definition. The element will be added 
       directly after the previous element. 

       The size of the bitfield will expand when required, but adding more than
       in total 64 bits (8 bytes) will generate an exception.
       
       :param name: Name of element. Needs to be unique.
       :type name: str
       :param nbr_of_bits: Number of bits this element represents. Default is 1.
       :type nbr_of_bits: int, optional
       :param signed: Should the bit field be signed or not. Default is False.
       :type signed: bool, optional"""
      # Calculate number of bits
      total_nbr_of_bits = nbr_of_bits
      for name, field in self.__fields.items():
        total_nbr_of_bits += field['nbr_of_bits']
    
      # Set the new type
      if total_nbr_of_bits <= 8:
        self._type = 'uint8'
      elif total_nbr_of_bits <= 16:
        self._type = 'uint16'
      elif total_nbr_of_bits <= 32:
        self._type = 'uint32'
      elif total_nbr_of_bits <= 64:
        self._type = 'uint64'
      else:
        raise Exception('Maximum number of bits (64) exceeded: {0}.'.format(total_nbr_of_bits))

      self.__fields[name] = {'nbr_of_bits' : nbr_of_bits, 'signed' : signed}

  def deserialize(self, buffer):
    """ Deserialize buffer into dictionary

    :param buffer: Buffer that contains the data to deserialize
    :type buffer: bytearray
    :return: A dictionary keyed with the element names
    :rtype: dict
    """
    result = {}
    if len(buffer) != self.size():
      raise Exception("Invalid buffer size: {0}. Expected: {1}".format(len(buffer),self.size()))
    typeinfo = _TYPE[self._type]
    format = _BYTEORDER[self._byteorder]['format'] + typeinfo['format']
    value = struct.unpack(format, buffer)

    start_bit = 0
    for name, field in self.__fields.items():
      result[name] = self._get_subvalue(value, field['nbr_of_bits'], start_bit, field['signed'])
      start_bit += field['nbr_of_bits']

    return result

  def size(self):
    """ Get size of bitfield

    :return: Number of bytes this bitfield represents
    :rtype: int
    """
    return _TYPE[self._type]['bytes']
  
  def _get_subvalue(self, value, nbr_of_bits, start_bit, signed):
    """ Get subvalue of value
    :return: The subvalue
    :rtype: int
    """
    shifted_value = value >> start_bit
    mask = 0xFFFFFFFFFFFFFFFF >> (64 - nbr_of_bits)
    non_signed_value = shifted_value & mask
    if (signed == False):
      return non_signed_value
    sign_bit = 0x1 << (nbr_of_bits - 1)
    if non_signed_value & sign_bit == 0:
      # Value is positive
      return non_signed_value
    # Convert to negative value using Two's complement
    signed_value = -1 * ((~non_signed_value & mask) + 1) 
    return signed_value
  
  def _set_subvalue(self, value, subvalue, nbr_of_bits, start_bit, signed):
    """ Set subvalue of value
    :return: New value where subvalue is included
    :rtype: int
    """

    # Validate size according to nbr_of_bits
    max = 2**nbr_of_bits - 1
    min = 0
    if signed:
      max = 2**(nbr_of_bits-1) - 1
      min = -1 * (2**(nbr_of_bits-1))
    
    signed_str = 'Unsigned'
    if signed:
      signed_str = 'Signed'

    if subvalue > max:
      raise Exception('{0} value {1} is too large to fit in {2} bits. Max value is {3}.'.format(signed_str, subvalue,nbr_of_bits, max))
    if subvalue < min:
      raise Exception('{0} value {1} is too small to fit in {2} bits. Min value is {3}.'.format(signed_str, subvalue,nbr_of_bits, max))

    if signed and subvalue < 0:
      # Convert from negative value using Two's complement
      sign_bit = 0x1 << (nbr_of_bits - 1)
      subvalue = sign_bit | ~(-1 * subvalue - 1)

    mask = 0xFFFFFFFFFFFFFFFF >> (64 - nbr_of_bits)

    shifted_subvalue = (subvalue & mask) << start_bit

    return value | shifted_subvalue
