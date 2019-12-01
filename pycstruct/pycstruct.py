import struct, collections

_TYPE = {
  'int8'    : {'format' : 'b', 'bytes' : 1},
  'uint8'   : {'format' : 'B', 'bytes' : 1},
  'bool8'   : {'format' : 'B', 'bytes' : 1},
  'int16'   : {'format' : 'h', 'bytes' : 2},
  'bool16'  : {'format' : 'H', 'bytes' : 2},
  'uint16'  : {'format' : 'H', 'bytes' : 2},
  'float16' : {'format' : 'e', 'bytes' : 2},
  'int32'   : {'format' : 'i', 'bytes' : 4},
  'uint32'  : {'format' : 'I', 'bytes' : 4},
  'bool32'  : {'format' : 'I', 'bytes' : 4},
  'float32' : {'format' : 'f', 'bytes' : 4},
  'int64'   : {'format' : 'q', 'bytes' : 8},
  'uint64'  : {'format' : 'Q', 'bytes' : 8},
  'bool64'  : {'format' : 'Q', 'bytes' : 8},
  'float64' : {'format' : 'd', 'bytes' : 8},
  'utf-8'   : {'format' : 'B', 'bytes' : 1},
}

_BYTEORDER = {
  'native' : {'format' : '='},
  'little' : {'format' : '<'},
  'big'    : {'format' : '>'}
}

class StructDef:
  def __init__(self, default_byteorder = 'native'):
    self.__fields = collections.OrderedDict()
    if default_byteorder not in _BYTEORDER:
      raise Exception('Invalid byteorder: {0}.'.format(default_byteorder))
    self.__default_byteorder = default_byteorder
  
  def add(self, type, name, length = 1, byteorder = ''):
    if length < 1:
      raise Exception('Invalid length: {0}.'.format(length))
    if byteorder == "":
      byteorder = self.__default_byteorder
    elif byteorder not in _BYTEORDER:
      raise Exception('Invalid byteorder: {0}.'.format(byteorder))
    if name in self.__fields:
      raise Exception('Field name already exist: {0}.'.format(name))

    self.__fields[name] = {'type' : type, 'length' : length, 'byteorder' : byteorder}

  def size(self):
    ''' Returns size of structure in bytes '''
    size = 0
    for field in self.__fields.values():
      size += field['length'] * _TYPE[field['type']]['bytes']
    return size

  def deserialize(self, buffer):
    result = {}
    if len(buffer) != self.size():
      raise Exception("Invalid buffer size: {0}. Expected: {1}".format(len(buffer),self.size()))
    offset = 0
    for name, field in self.__fields.items():
      typeinfo = _TYPE[field['type']]
      length = field['length']
      if field['type'] == 'utf-8':
        utf8_bytes = buffer[offset:offset + length]
        # Find null termination
        index = utf8_bytes.find(0)
        if index >= 0:
          utf8_bytes = utf8_bytes[:index]
        result[name] = utf8_bytes.decode('utf-8') 
      else: 
        values = []
        format = _BYTEORDER[field['byteorder']]['format'] + typeinfo['format']
        for i in range(0, length):
          values.append(struct.unpack_from(format, buffer, offset + i*typeinfo['bytes'] )[0])
        if length == 1:
          result[name] = values[0]
        else:
          result[name] = values
      offset += typeinfo['bytes'] * length
    return result

  def serialize(self, data):
    buffer = bytearray(self.size())
    offset = 0
    for name, field in self.__fields.items():
      typeinfo = _TYPE[field['type']]
      length = field['length']
      format = _BYTEORDER[field['byteorder']]['format'] + typeinfo['format']
      if name in data:
        value = data[name]
        if field['type'] == 'utf-8':
          if not isinstance(value, str):
            raise Exception('Key: {0} shall be a string'.format(name))
          utf8_bytes = value.encode('utf-8')
          if len(utf8_bytes) > length:
            raise Exception('String in key: {0} is larger than {1}'.format(name, length))
          for i in range(0, len(utf8_bytes)):
            buffer[i+offset] = utf8_bytes[i]
        elif length > 1:
          if not isinstance(value, collections.Iterable):
            raise Exception('Key: {0} shall be a list'.format(name))
          if len(value) > length:
            raise Exception('List in key: {0} is larger than {1}'.format(name, length))
          for i in range(0, len(value)):
            struct.pack_into(format, buffer, offset + i*typeinfo['bytes'], value[i])
        else:
          struct.pack_into(format, buffer, offset, value)

      offset += typeinfo['bytes'] * length
    return buffer

  def create_empty_data(self):
    buffer = bytearray(self.size())
    return self.deserialize(buffer)

