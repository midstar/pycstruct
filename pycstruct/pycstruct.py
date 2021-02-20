# Copyright 2020 by Joel Midstjärna.
# All rights reserved.
# This file is part of the pycstruct python library and is
# released under the "MIT License Agreement". Please see the LICENSE
# file that should have been included as part of this package.

import struct, collections, math, sys

###############################################################################
# Global constants

# Basic Types
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
  'float64' : {'format' : 'd', 'bytes' : 8}
}

_BYTEORDER = {
  'native' : {'format' : '='},
  'little' : {'format' : '<'},
  'big'    : {'format' : '>'}
}


###############################################################################
# Internal functions

def _get_padding(alignment, current_size, next_element_size):
  """Calculate number of padding bytes required to get next element in 
     the correct alignment
  """
  if alignment == 1:
    return 0 # Always aligned

  elem_size = min(alignment, next_element_size)
  remainder = current_size % elem_size
  if remainder == 0:
    return 0
  return elem_size - remainder

def _round_pow_2(value):
  """Round value to next power of 2 value - max 16"""
  if value > 8:
    return 16
  elif value > 4:
    return 8
  elif value > 2:
    return 4
  
  return value

###############################################################################
# BaseDef Class

class BaseDef:
  """This is an abstract base class for definitions"""
  def size(self):
    raise NotImplementedError

  def serialize(self, data):
    raise NotImplementedError

  def deserialize(self, buffer):
    raise NotImplementedError

  def _largest_member(self):
    raise NotImplementedError

  def _type_name(self):
    raise NotImplementedError


###############################################################################
# BasicTypeDef Class

class BasicTypeDef(BaseDef):
  """This class represents the basic types (int, float and bool)
  """
  def __init__(self, type, byteorder):
    self.type = type
    self.byteorder = byteorder
    self.size_bytes = _TYPE[type]['bytes']
    self.format = _TYPE[type]['format']

  def serialize(self, data):
    ''' Data needs to be an integer, floating point or boolean value '''
    buffer = bytearray(self.size())
    format = _BYTEORDER[self.byteorder]['format'] + self.format
    struct.pack_into(format, buffer, 0, data)

    return buffer

  def deserialize(self, buffer):
    ''' Result is an integer, floating point or boolean value '''
    format = _BYTEORDER[self.byteorder]['format'] + self.format
    value = struct.unpack_from(format, buffer, 0)[0]

    if self.type.startswith("bool"):
      if value == 0:
        value = False
      else:
        value = True

    return value

  def size(self):
    return self.size_bytes

  def _largest_member(self):
    return self.size_bytes

  def _type_name(self):
    return self.type


###############################################################################
# StringDef Class
  
class StringDef(BaseDef):
  """This class represents UTF-8 strings
  """
  def __init__(self, length):
    self.length = length

  def serialize(self, data):
    ''' Data needs to be a string '''
    buffer = bytearray(self.size())

    if not isinstance(data, str):
      raise Exception('Not a valid string: {0}'.format(data))

    utf8_bytes = data.encode('utf-8')
    if len(utf8_bytes) > self.length:
      raise Exception('String overflow. Produced size {0} but max is {1}'.format(
        len(utf8_bytes), self.length))

    for i in range(0, len(utf8_bytes)):
      buffer[i] = utf8_bytes[i]
    return buffer

  def deserialize(self, buffer):
    ''' Result is a string '''
    # Find null termination
    index = buffer.find(0)
    if index >= 0:
      buffer = buffer[:index]

    return buffer.decode('utf-8') 

  def size(self):
    return self.length # Each element 1 byte

  def _largest_member(self):
    return 1 # 1 byte

  def _type_name(self):
    return 'utf-8'


###############################################################################
# StructDef Class

class StructDef(BaseDef):
  """This class represents a struct or a union definition

  :param default_byteorder: Byte order of each element unless explicitly set 
                            for the element. Valid values are 'native', 
                            'little' and 'big'.
  :type default_byteorder: str, optional
  :param alignment: Alignment of elements in bytes. If set to a value > 1
                    padding will be added between elements when necessary.
                    Use 4 for 32 bit architectures, 8 for 64 bit 
                    architectures unless packing is performed.
  :type alignment: str, optional
  :param union: If this is set the True, the instance will behave like
                a union instead of a struct, i.e. all elements share the
                same data (same start address). Default is False.
  :type union: boolean, optional
  """

  def __init__(self, default_byteorder = 'native', alignment = 1, union = False):
    """Constructor method"""
    if default_byteorder not in _BYTEORDER:
      raise Exception('Invalid byteorder: {0}.'.format(default_byteorder))
    self.__default_byteorder = default_byteorder
    self.__alignment = alignment
    self.__union = union
    self.__pad_count = 0
    self.__fields = collections.OrderedDict()
    self.__fields_same_level = collections.OrderedDict()

    # Add end padding of 0 size
    self.__pad_byte = BasicTypeDef('uint8', default_byteorder)
    self.__pad_end = {'type' : self.__pad_byte, 'length' : 0, 
                      'same_level' : False, 'offset' : 0}
  
  def add(self, type, name, length = 1, byteorder = '', same_level = False):
    """Add a new element in the struct/union definition. The element will be added 
       directly after the previous element if a struct or in parallel with the
       previous element if union. Padding might be added depending on the alignment
       setting.

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
          | struct     | struct size   | Embedded struct. The actual          |
          |            |               | StructDef object shall be set as     |
          |            |               | type and not 'struct' string.        |
          +------------+---------------+--------------------------------------+
          | bitfield   | bitfield size | Bitfield. The actual                 |
          |            |               | :meth:`BitfieldDef` object shall be  |
          |            |               | set as type and not 'bitfield'       |
          |            |               | string.                              |
          +------------+---------------+--------------------------------------+
          | enum       | enum size     | Enum. The actual :meth:`EnumDef`     |
          |            |               | object shall be set as type and not  |
          |            |               | 'enum' string.                       |
          +------------+---------------+--------------------------------------+
       
       :param type: Element data type. See above.
       :type type: str
       :param name: Name of element. Needs to be unique.
       :type name: str
       :param length: Number of elements. If > 1 this is an array/list of 
                      elements with equal size. Default is 1.
       :type length: int, optional
       :param byteorder: Byteorder of this element. Valid values are 'native', 
                         'little' and 'big'. If not specified the default 
                         byteorder is used.
       :type byteorder: str, optional
       :param same_level: Relevant if adding embedded bitfield. If True, the
                          serialized or deserialized dictionary keys will be
                          on the same level as the parent. Default is False.
       :type same_level: bool, optional
       
       """

    # Sanity checks
    if length < 1:
      raise Exception('Invalid length: {0}.'.format(length))
    if name in self.__fields:
      raise Exception('Field name already exist: {0}.'.format(name))
    if byteorder == "":
      byteorder = self.__default_byteorder
    elif byteorder not in _BYTEORDER:
      raise Exception('Invalid byteorder: {0}.'.format(byteorder))
    if same_level and length > 1:
      raise Exception('same_level not allowed in combination with length > 1')
    if same_level and not isinstance(type, BitfieldDef):
      raise Exception('same_level only allowed in combination with BitfieldDef')

    # Create objects when necessary
    if type == 'utf-8':
      type = StringDef(length)
      # String length is handled inside the definition
      length = 1
    elif type in _TYPE:
      type = BasicTypeDef(type, byteorder)
    elif not isinstance(type, BaseDef):
      raise Exception('Invalid type: {0}.'.format(type))

    # Remove end padding if it exists
    self.__fields.pop('__pad_end','')

    # Offset in buffer (for unions always 0)
    offset = 0

    # Check if padding between elements is required (only struct not union)
    if not self.__union:
      offset = self.size()
      padding = _get_padding(self.__alignment, self.size(), type._largest_member())
      if padding > 0:
        self.__fields['__pad_{0}'.format(self.__pad_count)] = \
          {'type' : self.__pad_byte, 'length' : padding, 'same_level' : False,
          'offset' : offset }
        offset += padding
        self.__pad_count += 1

    # Add the element
    self.__fields[name] = { 'type' : type, 'length' : length, 
                            'same_level' : same_level, 
                            'offset' : offset }

    # Check if end padding is required
    padding = _get_padding(self.__alignment, self.size(), self._largest_member())
    if padding > 0:
      offset += length * type.size()
      self.__pad_end['length'] = padding
      self.__fields['__pad_end'] = self.__pad_end
      self.__fields['__pad_end']['offset'] = offset
    
    # If same_level, store the bitfield elements
    if same_level:
      for subname in type._element_names():
        self.__fields_same_level[subname] = name

  def size(self):
    """ Get size of structure or union.

    :return: Number of bytes this structure represents alternatively largest
             of the elements (including end padding) if this is a union.
    :rtype: int
    """
    all_elem_size = 0
    largest_size = 0
    for name, field in self.__fields.items():
      elem_size = field['length'] * field['type'].size()
      if  not name.startswith('__pad') and elem_size > largest_size:
        largest_size = elem_size
      all_elem_size += elem_size
    if self.__union:
      return largest_size +  self.__pad_end['length'] # Union
    return all_elem_size # Struct

  def _largest_member(self):
    """ Used for struct/union padding

    :return: Largest member
    :rtype: int
    """
    largest = 0
    for field in self.__fields.values():
      l = field['type']._largest_member()
      if l > largest:
        largest = l
    
    return largest

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

    for name in self._element_names():
      if not name.startswith('__pad'):
        length = 1
        if name in self.__fields:
          length = self.__fields[name]['length']
        if length > 1:
          # This is a list (array)
          l = []
          for index in range(0, length):
            l.append(self._deserialize_element(name, buffer, index = index))
          result[name] = l
        else:
          result[name] = self._deserialize_element(name, buffer)

    return result

  def _deserialize_element(self, name, buffer, buffer_offset = 0, index = 0):
    """ Deserialize one element from buffer

    :param name: Name of element
    :type data: str
    :param buffer: Buffer that contains the data to deserialize data from.
    :type buffer: bytearray
    :param buffer_offset: Start address in buffer
    :type buffer: int
    :param index: If this is a list (array) which index to deserialize?
    :type buffer: int
    :return: The value of the element
    :rtype: varies
    """
    if name in self.__fields_same_level:
      # This is a bitfield on same level
      field = self.__fields[self.__fields_same_level[name]]
      bitfield = field['type']
      return bitfield._deserialize_element(name, buffer, buffer_offset + field['offset'])

    field = self.__fields[name]
    datatype = field['type']
    length = field['length']
    offset = field['offset']
    datatype_size = datatype.size()

    next_offset = buffer_offset + offset + index * datatype_size
    buffer_subset = buffer[next_offset:next_offset + datatype_size]

    try:
      value = datatype.deserialize(buffer_subset)
    except Exception as e:
      raise Exception('Unable to deserialize {} {}. Reason:\n{}'.format(
      datatype._type_name(), name, e.args[0]))
    
    return value

  def serialize(self, data):
    """ Serialize dictionary into buffer

    NOTE! If this is a union the method will try to serialize all the
    elements into the buffer (at the same position in the buffer).
    It is quite possible that the elements in the dictionary have 
    contradicting data and the buffer of the last serialized element
    will be ok while the others might be wrong. Thus you should only define
    the element that you want to serialize in the dictionary. 

    :param data: A dictionary keyed with element names. Elements can be omitted from the dictionary (defaults to value 0).
    :type data: dict
    :return: A buffer that contains data
    :rtype: bytearray
    """
    buffer = bytearray(self.size())
    for name in self._element_names():
      if name in data and not name.startswith('__pad'):
        length = 1
        if name in self.__fields:
          length = self.__fields[name]['length']
        if length > 1:
          # This is a list (array)
          if not isinstance(data[name], collections.abc.Iterable):
            raise Exception('Element: {0} shall be a list'.format(name))
          if len(data[name]) > length:
            raise Exception('List in element: {0} is larger than {1}'.format(name, length))
          index = 0
          for item in data[name]:
            self._serialize_element(name, item, buffer, index = index)
            index += 1
        else:
          self._serialize_element(name, data[name], buffer)

    return buffer
  
  def _serialize_element(self, name, value, buffer, buffer_offset = 0, index = 0):
    """ Serialize one element into the buffer

    :param name: Name of element
    :type data: str
    :param value: Value of element
    :type data: varies
    :param buffer: Buffer that contains the data to serialize data into. This is an output.
    :type buffer: bytearray
    :param buffer_offset: Start address in buffer
    :type buffer: int
    :param index: If this is a list (array) which index to deserialize?
    :type buffer: int
    """
    if name in self.__fields_same_level:
      # This is a bitfield on same level
      field = self.__fields[self.__fields_same_level[name]]
      bitfield = field['type']
      bitfield._serialize_element(name, value, buffer, buffer_offset + field['offset'])
      return # We are done

    field = self.__fields[name]
    datatype = field['type']
    length = field['length']
    offset = field['offset']
    datatype_size = datatype.size()

    next_offset = buffer_offset + offset + index * datatype_size
    try:
      buffer[next_offset:next_offset + datatype_size] = datatype.serialize(value)
    except Exception as e:
        raise Exception('Unable to serialize {} {}. Reason:\n{}'.format(
          datatype._type_name(), name, e.args[0]))


  def instance(self, buffer = None, buffer_offset = 0):
      """ Create an instance of this struct / union.

      This is an alternative of using dictionaries and the :meth:`StructDef.serialize`/
      :meth:`StructDef.deserialize` methods for representing the data.

      :param buffer: Byte buffer where data is stored. If no buffer is provided a new byte
                     buffer will be created and the instance will be 'empty'.
      :type buffer: bytearray, optional
      :param buffer_offset: Start offset in the buffer. This means that you
                            can have multiple Instances (or other data) that
                            shares the same buffer.
      :type buffer_offset: int, optional
      :return: A new Instance object
      :rtype: :meth:`Instance`
      """
      return Instance(self, buffer, buffer_offset)

  def create_empty_data(self):
    """ Create an empty dictionary with all keys

    :return: A dictionary keyed with the element names. Values are "empty" or 0.
    :rtype: dict
    """
    buffer = bytearray(self.size())
    return self.deserialize(buffer)

  def __str__(self):
    """ Create string representation

    :return: A string illustrating all members (not Bitfield fields with same_level = True)
    :rtype: string
    """
    result = []
    result.append('{:<30}{:<15}{:<10}{:<10}{:<10}{:<10}'.format(
      'Name','Type', 'Size','Length','Offset','Largest type'))
    for name, field in self.__fields.items():
      type = field['type']
      result.append('{:<30}{:<15}{:<10}{:<10}{:<10}{:<10}'.format(
        name,type._type_name(), type.size(),field['length'], 
        field['offset'],type._largest_member()))
    return '\n'.join(result)

  def _type_name(self):
    if self.__union:
      return 'union'
    return 'struct'
  
  def remove_from(self, name):

    """Remove all elements from a specific element

      This function is useful to create a sub-set of a struct.

       :param name: Name of element to remove and all after this element
       :type name: str
    """
    self._remove_from_or_to(name, to = False)

  def remove_to(self, name):

    """Remove all elements from beginning to a specific element

      This function is useful to create a sub-set of a struct.

       :param name: Name of element to remove and all before element
       :type name: str
    """
    self._remove_from_or_to(name, to = True)
    
  def _remove_from_or_to(self, name, to = True):
    if name not in self.__fields:
      raise Exception('Element {} does not exist'.format(name))

    keys = list(self.__fields)
    if to == False:
      keys.reverse()
    for key in keys:
      del self.__fields[key]
      if key == name:
        break # Done
    
    if (len(self.__fields) > 0):
      # Update offset of all elements
      keys = list(self.__fields)
      adjust_offset = self.__fields[keys[0]]['offset']
      for _, field in self.__fields.items():
        field['offset'] -= adjust_offset

  def _element_names(self):
    """ Get a list of all element names (in correct order)

    Note that this method also include elements of bitfields with same_level = True

    :return: A list of all elements
    :rtype: list
    """
    result = []
    for name, field in self.__fields.items():
      if field['same_level']:
        for subname, parent_name in self.__fields_same_level.items():
          if name == parent_name:
            result.append(subname)
      else:
        result.append(name)
    return result

  def _element_type(self, name):
    """ Returns the type of element. 

    Note that elements of bitfields with same_level = True will be returned as None.

    :return: Type of element or None
    :rtype: pycstruct class
    """
    if name in self.__fields:
      return self.__fields[name]['type']
    return None

  def _element_offset(self, name):
    """ Returns the offset of the element. 

    :return: Offset of element
    :rtype: int
    """
    if name in self.__fields:
      return self.__fields[name]['offset']
    raise Exception('Invalid element {}'.format(name))

  def _element_length(self, name):
    """ Returns the length of the element. 

    :return: Length of element
    :rtype: int
    """
    if name in self.__fields:
      return self.__fields[name]['length']
    return 1

###############################################################################
# BitfieldDef Class

class BitfieldDef(BaseDef):
  """This class represents a bit field definition

  The size of the bit field is 1, 2, 3, .., 8 bytes depending on the number of
  elements added to the bit field. You can also force the bitfield size by
  setting the size argument. When forcing the size larger bitfields than
  8 bytes are allowed.

  :param byteorder: Byte order of the bitfield. Valid values are 'native', 
                    'little' and 'big'.
  :type byteorder: str, optional
  :param size: Force bitfield to be a certain size. By default it will expand
               when new elements are added.
  :type size: int, optional
  """

  def __init__(self, byteorder = 'native', size = -1):
    if byteorder not in _BYTEORDER:
      raise Exception('Invalid byteorder: {0}.'.format(byteorder))
    if byteorder == 'native':
      byteorder = sys.byteorder
    self.__byteorder = byteorder
    self.__size = size
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
      # Check for same bitfield name
      if name in self.__fields:
        raise Exception('Field with name {0} already exists.'.format(name))
    
      # Check that new size is not too large
      assigned_bits = self.assigned_bits()
      total_nbr_of_bits = assigned_bits + nbr_of_bits
      if total_nbr_of_bits > self._max_bits():
        raise Exception('Maximum number of bits ({}) exceeded: {}.'.format(
          self._max_bits(), total_nbr_of_bits))

      self.__fields[name] = {'nbr_of_bits' : nbr_of_bits, 'signed' : signed, 
                             'offset' : assigned_bits}

  def deserialize(self, buffer):
    """ Deserialize buffer into dictionary

    :param buffer: Buffer that contains the data to deserialize (1 - 8 bytes)
    :type buffer: bytearray
    :param buffer_offset: Start address in buffer
    :type buffer: int
    :return: A dictionary keyed with the element names
    :rtype: dict
    """
    result = {}
    if len(buffer) < self.size():
      raise Exception("Invalid buffer size: {0}. Expected at least: {1}".format(
                      len(buffer), self.size()))

    for name in self._element_names():
      result[name] = self._deserialize_element(name, buffer)

    return result

  def _deserialize_element(self, name, buffer, buffer_offset = 0):
      """ Deserialize one element from buffer

      :param name: Name of element
      :type data: str
      :param buffer: Buffer that contains the data to deserialize data from (1 - 8 bytes).
      :type buffer: bytearray
      :param buffer_offset: Start address in buffer
      :type buffer: int
      :return: The value of the element
      :rtype: int
      """
      full_value = int.from_bytes(buffer[buffer_offset:buffer_offset + self.size()], 
                                  self.__byteorder, signed=False)
      field = self.__fields[name]
      return self._get_subvalue(full_value, field['nbr_of_bits'], field['offset'], field['signed'])

  def serialize(self, data):
    """ Serialize dictionary into buffer

    :param data: A dictionary keyed with element names. Elements can be omitted from the dictionary (defaults to value 0).
    :type data: dict
    :return: A buffer that contains data
    :rtype: bytearray
    """
    buffer = bytearray(self.size())
    for name in self._element_names():
      if name in data:
        self._serialize_element(name, data[name], buffer)

    return buffer

  def _serialize_element(self, name, value, buffer, buffer_offset = 0):
      """ Serialize one element into the buffer

      :param name: Name of element
      :type data: str
      :param value: Value of element
      :type data: int
      :param buffer: Buffer that contains the data to serialize data into (1 - 8 bytes). This is an output.
      :type buffer: bytearray
      :param buffer_offset: Start address in buffer
      :type buffer: int
      """
      full_value = int.from_bytes(buffer[buffer_offset:buffer_offset + self.size()], 
                                  self.__byteorder, signed=False)
      field = self.__fields[name]
      value = self._set_subvalue(full_value, value, field['nbr_of_bits'], 
                                 field['offset'], field['signed'])
      buffer[buffer_offset:buffer_offset + self.size()] = value.to_bytes(
        self.size(), self.__byteorder, signed=False)

  def instance(self, buffer = None, buffer_offset = 0):
      """ Create an instance of this bitfield.

      This is an alternative of using dictionaries and the :meth:`BitfieldDef.serialize`/
      :meth:`BitfieldDef.deserialize` methods for representing the data.

      :param buffer: Byte buffer where data is stored. If no buffer is provided a new byte
                     buffer will be created and the instance will be 'empty'.
      :type buffer: bytearray, optional
      :param buffer_offset: Start offset in the buffer. This means that you
                            can have multiple Instances (or other data) that
                            shares the same buffer.
      :type buffer_offset: int, optional
      :return: A new Instance object
      :rtype: :meth:`Instance`
      """
      return Instance(self, buffer, buffer_offset)

  def assigned_bits(self):
    """ Get size of bitfield in bits excluding padding bits

    :return: Number of bits this bitfield represents excluding padding bits
    :rtype: int
    """
    total_nbr_of_bits = 0
    for _, field in self.__fields.items():
      total_nbr_of_bits += field['nbr_of_bits']

    return total_nbr_of_bits

  def size(self):
    """ Get size of bitfield in bytes

    :return: Number of bytes this bitfield represents
    :rtype: int
    """
    if self.__size >= 0:
      return self.__size # Force size

    return int(math.ceil(self.assigned_bits()/8.0))

  def _max_bits(self):
    if self.__size >= 0:
      return self.__size * 8 # Force size
    return 64    

  def _largest_member(self):
    """ Used for struct padding

    :return: Closest power of 2 value of size
    :rtype: int
    """
    return _round_pow_2(self.size())
  
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

  def create_empty_data(self):
    """ Create an empty dictionary with all keys

    :return: A dictionary keyed with the element names. Values are "empty" or 0.
    :rtype: dict
    """
    buffer = bytearray(self.size())
    return self.deserialize(buffer)

  def _type_name(self):
    return 'bitfield'

  def __str__(self):
    """ Create string representation

    :return: A string illustrating all members
    :rtype: string
    """
    result = []
    result.append('{:<30}{:<10}{:<10}{:<10}'.format(
      'Name','Bits', 'Offset', 'Signed'))
    for name, field in self.__fields.items():
      signed = '-'
      if field['signed']:
        signed = 'x'
      result.append('{:<30}{:<10}{:<10}{:<10}'.format(
        name,field['nbr_of_bits'], field['offset'], signed))
    return '\n'.join(result)
  
  def _element_names(self):
    """ Get a list of all element names (in correct order)

    :return: A list of all elements
    :rtype: list
    """
    result = []
    for name in self.__fields.keys():
      result.append(name)
    return result


###############################################################################
# EnumDef Class


class EnumDef(BaseDef):
  """This class represents an enum definition

  The size of the enum is 1, 2, 3, .., 8 bytes depending on the value of the
  largest enum constant. You can also force the enum size by setting 
  the size argument.

  :param byteorder: Byte order of the enum. Valid values are 'native', 
                    'little' and 'big'.
  :type byteorder: str, optional
  :param size: Force enum to be a certain size. By default it will expand
               when new elements are added.
  :type size: int, optional
  :param signed: True if enum is signed (may contain negative values)
  :type signed: bool, optional
  """

  def __init__(self, byteorder = 'native', size = -1, signed = False):
    if byteorder not in _BYTEORDER:
      raise Exception('Invalid byteorder: {0}.'.format(byteorder))
    if byteorder == 'native':
      byteorder = sys.byteorder
    self.__byteorder = byteorder
    self.__size = size
    self.__signed = signed
    self.__constants = collections.OrderedDict()

  def add(self, name, value=None):
      """Add a new constant in the enum definition. Multiple constant might
       be assigned to the same value.

       The size of the enum will expand when required, but adding a value
       requiring a size larger than 64 bits will generate an exception.
       
       :param name: Name of constant. Needs to be unique.
       :type name: str
       :param value: Value of the constant. Automatically assigned to next
                     available value (0, 1, 2, ...) if not provided.
       :type value: int, optional"""
      # Check for same bitfield name
      if name in self.__constants:
        raise Exception('Constant with name {0} already exists.'.format(name))

      # Automatically assigned to next available value
      index = 0
      while value == None:
        try: 
          self.get_name(index)
          index += 1
        except:
          value = index  

      # Secure that no negative number are added to signed enum
      if not self.__signed and value < 0:
        raise Exception('Negative value, {0}, not supported in unsigned enums.'.format(value))
    
      # Check that new size is not too large
      if self._bit_length(value) > self._max_bits():
        raise Exception('Maximum number of bits ({}) exceeded: {}.'.format(
          self._max_bits(), self._bit_length(value)))

      self.__constants[name] = value

  def deserialize(self, buffer):
    """ Deserialize buffer into a string (constant name)

    If no constant name is defined for the value following name will be returned::

         __VALUE__<value>
    
    Where <value> is the integer stored in the buffer.

    :param buffer: Buffer that contains the data to deserialize (1 - 8 bytes)
    :type buffer: bytearray
    :return: The constant name (string) 
    :rtype: str
    """
    if len(buffer) != self.size():
      raise Exception("Invalid buffer size: {0}. Expected: {1}".format(len(buffer),self.size()))

    value = int.from_bytes(buffer, self.__byteorder, signed = self.__signed)

    name = ''
    try: 
      name = self.get_name(value)
    except:
      # No constant name exist, generate a new
      name = '__VALUE__{}'.format(value)
    return name

  def serialize(self, data):
    """ Serialize string (constant name) into buffer

    :param data: A string representing the constant name.
    :type data: str
    :return: A buffer that contains data
    :rtype: bytearray
    """
    value = self.get_value(data)

    return value.to_bytes(self.size(), self.__byteorder, signed = self.__signed)

  def size(self):
    """ Get size of enum in bytes

    :return: Number of bytes this enum represents
    :rtype: int
    """
    if self.__size >= 0:
      return self.__size # Force size

    max_length = 1 # To avoid 0 size
    for _, value in self.__constants.items():
      bit_length = self._bit_length(value)
      if bit_length > max_length:
        max_length = bit_length

    return int(math.ceil( max_length / 8.0 ))

  def _max_bits(self):
    if self.__size >= 0:
      return self.__size * 8 # Force size
    return 64    

  def _largest_member(self):
    """ Used for struct padding

    :return: Closest power of 2 value of size
    :rtype: int
    """
    return _round_pow_2(self.size())

  def get_name(self, value):
    """ Get the name representation of the value

    :return: The constant name
    :rtype: str
    """
    for constant, v in self.__constants.items():
      if value == v:
        return constant
    raise Exception("Value {0} is not a valid value for this enum.".format(value))

  def get_value(self, name):
    """ Get the value representation of the name

    :return: The value
    :rtype: int
    """
    if name not in self.__constants:
      raise Exception("{0} is not a valid name in this enum".format(name))
    return self.__constants[name]

  def _type_name(self):
    return 'enum'

  def _bit_length(self, value):
    """ Get number of bits a value represents.

    Works for negative values based on two's complement,
    which is not considered in the python built in 
    bit_length method.

    If enum is signed the extra sign bit is included
    in the returned result.
    """
    if value < 0:
      value += 1 # Two's complement reverse
    bit_length = value.bit_length()
    if self.__signed:
      bit_length += 1
    return bit_length

  def __str__(self):
    """ Create string representation

    :return: A string illustrating all constants
    :rtype: string
    """
    result = []
    result.append('{:<30}{:<10}'.format(
      'Name','Value'))
    for name, value in self.__constants.items():
      result.append('{:<30}{:<10}'.format(
        name,value))
    return '\n'.join(result)



###############################################################################
# Instance Class

class Instance():
  """This class represents an Instance of either a :meth:`StructDef` or
  a :meth:`BitfieldDef`. The instance object contains a bytearray
  buffer where 'raw data' is stored.
  
  The Instance object has following advantages over using dictionary 
  objects:

  - Data is only serialized/deserialized when accessed
  - Data is validated for each element/attribute access. I.e. you will
    get an exception if you try to set an element/attribute to a value
    that is not supported by the definition.
  - Data is accessed by attribute name instead of key indexing


  :param type: The :meth:`StructDef` class or :meth:`BitfieldDef` class
               that we would like to create an instance of.
  :type type: :meth:`StructDef` or :meth:`BitfieldDef`
  :param buffer: Byte buffer where data is stored. If no buffer is 
                 provided a new byte buffer will be created and the 
                 instance will be 'empty'.
  :type buffer: bytearray, optional
  :param buffer_offset: Start offset in the buffer. This means that you
                        can have multiple Instances (or other data) that
                        shares the same buffer.
  :type buffer_offset: int, optional
  """

  def __init__(self, type, buffer = None, buffer_offset = 0):
    if not isinstance(type, StructDef) and not isinstance(type, BitfieldDef):
      raise Exception('top_class needs to be of type StructDef or BitfieldDef')

    if buffer == None:
      buffer = bytearray(type.size())

    # All private fields needs to be defined here to avoid
    # recursive calls to __setattr__ and __getattr__ 
    super().__setattr__('_Instance__type', type)
    super().__setattr__('_Instance__buffer', buffer)
    super().__setattr__('_Instance__buffer_offset', buffer_offset)
    super().__setattr__('_Instance__attributes', type._element_names())
    super().__setattr__('_Instance__subinstances', {})

    if isinstance(type, StructDef):
      # Create "sub-instances" for nested structs/bitfields and lists
      for attribute in self.__attributes:
        length = type._element_length(attribute)
        if length > 1:
          # This is a list
          self.__subinstances[attribute] = _InstanceList(type, attribute, 
                   self.__buffer, buffer_offset)
        else:
          subtype = type._element_type(attribute)
          if isinstance(subtype, StructDef) or isinstance(subtype, BitfieldDef):
            self.__subinstances[attribute] = Instance(subtype, self.__buffer, 
                          buffer_offset + type._element_offset(attribute))

  def __getattr__(self, item):
    if item in self.__subinstances:
      return self.__subinstances[item]
    elif item in self.__attributes:
      return self.__type._deserialize_element(item, self.__buffer, 
                                      self.__buffer_offset)
    else:
      raise AttributeError('Instance has no element {}'.format(item))

  def __setattr__(self, item, value):
    if item in self.__subinstances:
      raise AttributeError('You are not allowed to modify {}'.format(item))
    elif item in self.__attributes:
      self.__type._serialize_element(item, value, self.__buffer, 
                                      self.__buffer_offset)
    else:
      raise AttributeError('Instance has no element {}'.format(item))

  def __bytes__(self):
    return bytes(self.__buffer)
  
  def __str__(self, prefix = ''):
    result = []
    for attribute in self.__attributes:
      if attribute in self.__subinstances:
        if isinstance(self.__subinstances[attribute], _InstanceList):
          result.append(self.__subinstances[attribute].__str__('{}{} : '.format(prefix,attribute)))
        else:
          result.append(self.__subinstances[attribute].__str__('{}{}.'.format(prefix,attribute)))
      else:
        result.append('{}{} : {}'.format(prefix, attribute, self.__getattr__(attribute)))
    return '\n'.join(result)

class _InstanceList():
  """This class represents a list within an Instance. Note that this
  is a private class and shall not be created manually. It is created
  as a support class of Instance class.

  It overrides __setitem__, __getitem__ so that it is possible to use
  indexing with [].

  :param parenttype: The StructDef class which contains the list element.
  :type parenttype: StructDef
  :param name: Name of the element in parenttype that contains the list
               we would like to represent.
  :type name: str
  :param buffer: Byte buffer where data is stored
  :type buffer: bytearray
  :param buffer_offset: Start offset in the buffer. Note that this should
                        be the offset to where parenttype starts, not the
                        actual list element (name)
  :type buffer_offset: int
  """

  def __init__(self, parenttype, name, buffer, buffer_offset):

    self.__parenttype = parenttype
    self.__name = name
    self.__type = parenttype._element_type(name)
    self.__length = parenttype._element_length(name)
    self.__buffer = buffer
    self.__buffer_offset = buffer_offset
    self.__subinstances = []

    if isinstance(self.__type, StructDef) or isinstance(self.__type, BitfieldDef):
      element_offset = parenttype._element_offset(name)
      for i in range(0, self.__length):
        self.__subinstances.append(Instance(self.__type, buffer, 
                          buffer_offset + element_offset + i * self.__type.size()))
  
  def __check_key(self, key):
    if not isinstance(key, int):
      raise KeyError('Invalid index: {} - needs to be an integer'.format(key))
    if key < 0 or key >= self.__length:
      raise KeyError('Invalid index: {} - supported 0 - {}'.format(key, self.__length))

  def __getitem__(self, key):
    self.__check_key(key)
    if len(self.__subinstances) == 0:
      return self.__parenttype._deserialize_element(self.__name, self.__buffer, 
                                      self.__buffer_offset, key)
    else:
      return self.__subinstances[key]

  def __setitem__(self, key, value):
    self.__check_key(key)
    if len(self.__subinstances) == 0:
      self.__parenttype._serialize_element(self.__name, value, self.__buffer, 
                                      self.__buffer_offset, key)
    else:
      raise AttributeError('You are not allowed to replace object. Use object properties.')

  def __len__(self):
    return self.__length

  def __bytes__(self):
    return bytes(self.__buffer)  

  def __str__(self, prefix = ''):
    elements = []

    if len(self.__subinstances) == 0:
      for i in range(0, self.__length):
        elements.append(str(self.__getitem__(i)))
      elements_str = ', '.join(elements)
    else:
      indent = ' ' * len(prefix)
      for i in range(0, self.__length):
        elements.append(self.__getitem__(i).__str__(indent))
      elements_str = '\n' + ('\n' + indent + ',\n').join(elements) + '\n' + indent

    return '{}[{}]'.format(prefix, elements_str)  
