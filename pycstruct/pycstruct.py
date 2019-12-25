import struct, collections

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
    self.__fields = collections.OrderedDict()
    if default_byteorder not in _BYTEORDER:
      raise Exception('Invalid byteorder: {0}.'.format(default_byteorder))
    self.__default_byteorder = default_byteorder
  
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

