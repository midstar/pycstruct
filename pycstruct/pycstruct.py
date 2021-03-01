"""pycstruct definitions

Copyright 2021 by Joel Midstjärna.
All rights reserved.
This file is part of the pycstruct python library and is
released under the "MIT License Agreement". Please see the LICENSE
file that should have been included as part of this package.
"""

# pylint: disable=too-many-lines, protected-access

import collections
import math
import struct
import sys

###############################################################################
# Global constants

# Basic Types
_TYPE = {
    "int8": {"format": "b", "bytes": 1, "dtype": "i1"},
    "uint8": {"format": "B", "bytes": 1, "dtype": "u1"},
    "bool8": {"format": "B", "bytes": 1, "dtype": "b1"},
    "int16": {"format": "h", "bytes": 2, "dtype": "i2"},
    "uint16": {"format": "H", "bytes": 2, "dtype": "u2"},
    "bool16": {"format": "H", "bytes": 2},
    "float16": {"format": "e", "bytes": 2, "dtype": "f2"},
    "int32": {"format": "i", "bytes": 4, "dtype": "i4"},
    "uint32": {"format": "I", "bytes": 4, "dtype": "u4"},
    "bool32": {"format": "I", "bytes": 4},
    "float32": {"format": "f", "bytes": 4, "dtype": "f4"},
    "int64": {"format": "q", "bytes": 8, "dtype": "i8"},
    "uint64": {"format": "Q", "bytes": 8, "dtype": "u8"},
    "bool64": {"format": "Q", "bytes": 8},
    "float64": {"format": "d", "bytes": 8, "dtype": "f8"},
}

_BYTEORDER = {
    "native": {"format": "="},
    "little": {"format": "<"},
    "big": {"format": ">"},
}


###############################################################################
# Internal functions


def _get_padding(alignment, current_size, next_element_size):
    """Calculate number of padding bytes required to get next element in
    the correct alignment
    """
    if alignment == 1:
        return 0  # Always aligned

    elem_size = min(alignment, next_element_size)
    remainder = current_size % elem_size
    if remainder == 0:
        return 0
    return elem_size - remainder


def _round_pow_2(value):
    """Round value to next power of 2 value - max 16"""
    if value > 8:
        return 16
    if value > 4:
        return 8
    if value > 2:
        return 4

    return value


###############################################################################
# _BaseDef Class


class _BaseDef:
    """This is an abstract base class for definitions"""

    def size(self):
        """Returns size in bytes"""
        raise NotImplementedError

    def serialize(self, data):
        """Serialize dictionary. Returns bytearray"""
        raise NotImplementedError

    def deserialize(self, buffer):
        """Deserialize buffer. Returns dictionary"""
        raise NotImplementedError

    def _largest_member(self):
        raise NotImplementedError

    def _type_name(self):
        raise NotImplementedError

    def dtype(self):
        """Returns the numpy dtype of this definition"""
        raise Exception("dtype not implemented for %s" % type(self))


###############################################################################
# BasicTypeDef Class


class BasicTypeDef(_BaseDef):
    """This class represents the basic types (int, float and bool)"""

    def __init__(self, datatype, byteorder):
        self.type = datatype
        self.byteorder = byteorder
        self.size_bytes = _TYPE[datatype]["bytes"]
        self.format = _TYPE[datatype]["format"]

    def serialize(self, data):
        """ Data needs to be an integer, floating point or boolean value """
        buffer = bytearray(self.size())
        dataformat = _BYTEORDER[self.byteorder]["format"] + self.format
        struct.pack_into(dataformat, buffer, 0, data)

        return buffer

    def deserialize(self, buffer):
        """ Result is an integer, floating point or boolean value """
        dataformat = _BYTEORDER[self.byteorder]["format"] + self.format
        value = struct.unpack_from(dataformat, buffer, 0)[0]

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

    def dtype(self):
        dtype = _TYPE[self.type].get("dtype")
        if dtype is None:
            raise NotImplementedError(
                'Basic type "%s" is not implemented as dtype' % self.type
            )
        byteorder = _BYTEORDER[self.byteorder]["format"]
        return byteorder + dtype


###############################################################################
# StringDef Class


class StringDef(_BaseDef):
    """This class represents UTF-8 strings"""

    def __init__(self, length):
        self.length = length

    def serialize(self, data):
        """ Data needs to be a string """
        buffer = bytearray(self.size())

        if not isinstance(data, str):
            raise Exception("Not a valid string: {0}".format(data))

        utf8_bytes = data.encode("utf-8")
        if len(utf8_bytes) > self.length:
            raise Exception(
                "String overflow. Produced size {0} but max is {1}".format(
                    len(utf8_bytes), self.length
                )
            )

        for i, value in enumerate(utf8_bytes):
            buffer[i] = value
        return buffer

    def deserialize(self, buffer):
        """ Result is a string """
        # Find null termination
        index = buffer.find(0)
        if index >= 0:
            buffer = buffer[:index]

        return buffer.decode("utf-8")

    def size(self):
        return self.length  # Each element 1 byte

    def _largest_member(self):
        return 1  # 1 byte

    def _type_name(self):
        return "utf-8"

    def dtype(self):
        return ("S", self.length)


###############################################################################
# StructDef Class


class StructDef(_BaseDef):
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

    # pylint: disable=too-many-instance-attributes, too-many-arguments

    def __init__(self, default_byteorder="native", alignment=1, union=False):
        """Constructor method"""
        if default_byteorder not in _BYTEORDER:
            raise Exception("Invalid byteorder: {0}.".format(default_byteorder))
        self.__default_byteorder = default_byteorder
        self.__alignment = alignment
        self.__union = union
        self.__pad_count = 0
        self.__fields = collections.OrderedDict()
        self.__fields_same_level = collections.OrderedDict()
        self.__dtype = None

        # Add end padding of 0 size
        self.__pad_byte = BasicTypeDef("uint8", default_byteorder)
        self.__pad_end = {
            "type": self.__pad_byte,
            "length": 0,
            "same_level": False,
            "offset": 0,
        }

    def add(self, datatype, name, length=1, byteorder="", same_level=False):
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

        :param datatype: Element data type. See above.
        :type datatype: str
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
        # pylint: disable=too-many-branches
        # Sanity checks
        if length < 1:
            raise Exception("Invalid length: {0}.".format(length))
        if name in self.__fields:
            raise Exception("Field name already exist: {0}.".format(name))
        if byteorder == "":
            byteorder = self.__default_byteorder
        elif byteorder not in _BYTEORDER:
            raise Exception("Invalid byteorder: {0}.".format(byteorder))
        if same_level and length > 1:
            raise Exception("same_level not allowed in combination with length > 1")
        if same_level and not isinstance(datatype, BitfieldDef):
            raise Exception("same_level only allowed in combination with BitfieldDef")

        # Invalidate the dtype cache
        self.__dtype = None

        # Create objects when necessary
        if datatype == "utf-8":
            datatype = StringDef(length)
            # String length is handled inside the definition
            length = 1
        elif datatype in _TYPE:
            datatype = BasicTypeDef(datatype, byteorder)
        elif not isinstance(datatype, _BaseDef):
            raise Exception("Invalid datatype: {0}.".format(datatype))

        # Remove end padding if it exists
        self.__fields.pop("__pad_end", "")

        # Offset in buffer (for unions always 0)
        offset = 0

        # Check if padding between elements is required (only struct not union)
        if not self.__union:
            offset = self.size()
            padding = _get_padding(
                self.__alignment, self.size(), datatype._largest_member()
            )
            if padding > 0:
                self.__fields["__pad_{0}".format(self.__pad_count)] = {
                    "type": self.__pad_byte,
                    "length": padding,
                    "same_level": False,
                    "offset": offset,
                }
                offset += padding
                self.__pad_count += 1

        # Add the element
        self.__fields[name] = {
            "type": datatype,
            "length": length,
            "same_level": same_level,
            "offset": offset,
        }

        # Check if end padding is required
        padding = _get_padding(self.__alignment, self.size(), self._largest_member())
        if padding > 0:
            offset += length * datatype.size()
            self.__pad_end["length"] = padding
            self.__fields["__pad_end"] = self.__pad_end
            self.__fields["__pad_end"]["offset"] = offset

        # If same_level, store the bitfield elements
        if same_level:
            for subname in datatype._element_names():
                self.__fields_same_level[subname] = name

    def size(self):
        """Get size of structure or union.

        :return: Number of bytes this structure represents alternatively largest
                 of the elements (including end padding) if this is a union.
        :rtype: int
        """
        all_elem_size = 0
        largest_size = 0
        for name, field in self.__fields.items():
            elem_size = field["length"] * field["type"].size()
            if not name.startswith("__pad") and elem_size > largest_size:
                largest_size = elem_size
            all_elem_size += elem_size
        if self.__union:
            return largest_size + self.__pad_end["length"]  # Union
        return all_elem_size  # Struct

    def _largest_member(self):
        """Used for struct/union padding

        :return: Largest member
        :rtype: int
        """
        largest = 0
        for field in self.__fields.values():
            current_largest = field["type"]._largest_member()
            if current_largest > largest:
                largest = current_largest

        return largest

    def deserialize(self, buffer):
        """Deserialize buffer into dictionary

        :param buffer: Buffer that contains the data to deserialize
        :type buffer: bytearray
        :return: A dictionary keyed with the element names
        :rtype: dict
        """
        result = {}

        if len(buffer) != self.size():
            raise Exception(
                "Invalid buffer size: {0}. Expected: {1}".format(
                    len(buffer), self.size()
                )
            )

        for name in self._element_names():
            if not name.startswith("__pad"):
                length = 1
                if name in self.__fields:
                    length = self.__fields[name]["length"]
                if length > 1:
                    # This is a list (array)
                    result[name] = []
                    for index in range(0, length):
                        result[name].append(
                            self._deserialize_element(name, buffer, index=index)
                        )
                else:
                    result[name] = self._deserialize_element(name, buffer)

        return result

    def _deserialize_element(self, name, buffer, buffer_offset=0, index=0):
        """Deserialize one element from buffer

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
            bitfield = field["type"]
            return bitfield._deserialize_element(
                name, buffer, buffer_offset + field["offset"]
            )

        field = self.__fields[name]
        datatype = field["type"]
        offset = field["offset"]
        datatype_size = datatype.size()

        next_offset = buffer_offset + offset + index * datatype_size
        buffer_subset = buffer[next_offset : next_offset + datatype_size]

        try:
            value = datatype.deserialize(buffer_subset)
        except Exception as exception:
            raise Exception(
                "Unable to deserialize {} {}. Reason:\n{}".format(
                    datatype._type_name(), name, exception.args[0]
                )
            ) from exception

        return value

    def serialize(self, data):
        """Serialize dictionary into buffer

        NOTE! If this is a union the method will try to serialize all the
        elements into the buffer (at the same position in the buffer).
        It is quite possible that the elements in the dictionary have
        contradicting data and the buffer of the last serialized element
        will be ok while the others might be wrong. Thus you should only define
        the element that you want to serialize in the dictionary.

        :param data: A dictionary keyed with element names. Elements can be
                     omitted from the dictionary (defaults to value 0).
        :type data: dict
        :return: A buffer that contains data
        :rtype: bytearray
        """
        buffer = bytearray(self.size())
        for name in self._element_names():
            if name in data and not name.startswith("__pad"):
                length = 1
                if name in self.__fields:
                    length = self.__fields[name]["length"]
                if length > 1:
                    # This is a list (array)
                    if not isinstance(data[name], collections.abc.Iterable):
                        raise Exception("Element: {0} shall be a list".format(name))
                    if len(data[name]) > length:
                        raise Exception(
                            "List in element: {0} is larger than {1}".format(
                                name, length
                            )
                        )
                    index = 0
                    for item in data[name]:
                        self._serialize_element(name, item, buffer, index=index)
                        index += 1
                else:
                    self._serialize_element(name, data[name], buffer)

        return buffer

    def _serialize_element(self, name, value, buffer, buffer_offset=0, index=0):
        """Serialize one element into the buffer

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
            bitfield = field["type"]
            bitfield._serialize_element(
                name, value, buffer, buffer_offset + field["offset"]
            )
            return  # We are done

        field = self.__fields[name]
        datatype = field["type"]
        offset = field["offset"]
        datatype_size = datatype.size()

        next_offset = buffer_offset + offset + index * datatype_size
        try:
            buffer[next_offset : next_offset + datatype_size] = datatype.serialize(
                value
            )
        except Exception as exception:
            raise Exception(
                "Unable to serialize {} {}. Reason:\n{}".format(
                    datatype._type_name(), name, exception.args[0]
                )
            ) from exception

    def instance(self, buffer=None, buffer_offset=0):
        """Create an instance of this struct / union.

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
        # I know. This is cyclic import of Instance, since instance depends
        # on classes within this file. However, it should not be any problem
        # since this file will be full imported once this method is called.
        # pylint: disable=cyclic-import, import-outside-toplevel
        from pycstruct.instance import Instance

        return Instance(self, buffer, buffer_offset)

    def create_empty_data(self):
        """Create an empty dictionary with all keys

        :return: A dictionary keyed with the element names. Values are "empty" or 0.
        :rtype: dict
        """
        buffer = bytearray(self.size())
        return self.deserialize(buffer)

    def __str__(self):
        """Create string representation

        :return: A string illustrating all members (not Bitfield fields with same_level = True)
        :rtype: string
        """
        result = []
        result.append(
            "{:<30}{:<15}{:<10}{:<10}{:<10}{:<10}".format(
                "Name", "Type", "Size", "Length", "Offset", "Largest type"
            )
        )
        for name, field in self.__fields.items():
            datatype = field["type"]
            result.append(
                "{:<30}{:<15}{:<10}{:<10}{:<10}{:<10}".format(
                    name,
                    datatype._type_name(),
                    datatype.size(),
                    field["length"],
                    field["offset"],
                    datatype._largest_member(),
                )
            )
        return "\n".join(result)

    def _type_name(self):
        if self.__union:
            return "union"
        return "struct"

    def remove_from(self, name):

        """Remove all elements from a specific element

        This function is useful to create a sub-set of a struct.

         :param name: Name of element to remove and all after this element
         :type name: str
        """
        self._remove_from_or_to(name, to_criteria=False)

    def remove_to(self, name):

        """Remove all elements from beginning to a specific element

        This function is useful to create a sub-set of a struct.

         :param name: Name of element to remove and all before element
         :type name: str
        """
        self._remove_from_or_to(name, to_criteria=True)

    def _remove_from_or_to(self, name, to_criteria=True):
        if name not in self.__fields:
            raise Exception("Element {} does not exist".format(name))

        # Invalidate the dtype cache
        self.__dtype = None

        keys = list(self.__fields)
        if not to_criteria:
            keys.reverse()
        for key in keys:
            del self.__fields[key]
            if key == name:
                break  # Done

        if len(self.__fields) > 0:
            # Update offset of all elements
            keys = list(self.__fields)
            adjust_offset = self.__fields[keys[0]]["offset"]
            for _, field in self.__fields.items():
                field["offset"] -= adjust_offset

    def _element_names(self):
        """Get a list of all element names (in correct order)

        Note that this method also include elements of bitfields with same_level = True

        :return: A list of all elements
        :rtype: list
        """
        result = []
        for name, field in self.__fields.items():
            if field["same_level"]:
                for subname, parent_name in self.__fields_same_level.items():
                    if name == parent_name:
                        result.append(subname)
            else:
                result.append(name)
        return result

    def _element_type(self, name):
        """Returns the type of element.

        Note that elements of bitfields with same_level = True will be returned as None.

        :return: Type of element or None
        :rtype: pycstruct class
        """
        if name in self.__fields:
            return self.__fields[name]["type"]
        return None

    def _element_offset(self, name):
        """Returns the offset of the element.

        :return: Offset of element
        :rtype: int
        """
        if name in self.__fields:
            return self.__fields[name]["offset"]
        raise Exception("Invalid element {}".format(name))

    def _element_length(self, name):
        """Returns the length of the element.

        :return: Length of element
        :rtype: int
        """
        if name in self.__fields:
            return self.__fields[name]["length"]
        return 1

    def dtype(self):
        """Returns the dtype of this structure as defined by numpy.

        This allows to use the pycstruct modelization together with numpy
        to read C structures from buffers.

        .. code-block:: python

            color_t = StructDef()
            color_t.add("uint8", "r")
            color_t.add("uint8", "g")
            color_t.add("uint8", "b")
            color_t.add("uint8", "a")
            raw = b"\x01\x02\x03\x00"
            color = numpy.frombuffer(raw, dtype=color_t.dtype())

        :return: a python dict representing a numpy dtype
        :rtype: dict
        """
        if self.__dtype is not None:
            return self.__dtype

        names = []
        formats = []
        offsets = []

        for name in self._element_names():
            if name.startswith("__pad"):
                continue
            if name not in self.__fields:
                continue
            length = self.__fields[name]["length"]
            offset = self.__fields[name]["offset"]
            datatype = self.__fields[name]["type"]
            if length > 1:
                dtype = (datatype.dtype(), length)
            else:
                dtype = datatype.dtype()
            names.append(name)
            formats.append(dtype)
            offsets.append(offset)

        dtype_def = {
            "names": names,
            "formats": formats,
            "offsets": offsets,
            "itemsize": self.size(),
        }
        self.__dtype = dtype_def
        return dtype_def


###############################################################################
# BitfieldDef Class


class BitfieldDef(_BaseDef):
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

    def __init__(self, byteorder="native", size=-1):
        if byteorder not in _BYTEORDER:
            raise Exception("Invalid byteorder: {0}.".format(byteorder))
        if byteorder == "native":
            byteorder = sys.byteorder
        self.__byteorder = byteorder
        self.__size = size
        self.__fields = collections.OrderedDict()

    def add(self, name, nbr_of_bits=1, signed=False):
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
            raise Exception("Field with name {0} already exists.".format(name))

        # Check that new size is not too large
        assigned_bits = self.assigned_bits()
        total_nbr_of_bits = assigned_bits + nbr_of_bits
        if total_nbr_of_bits > self._max_bits():
            raise Exception(
                "Maximum number of bits ({}) exceeded: {}.".format(
                    self._max_bits(), total_nbr_of_bits
                )
            )

        self.__fields[name] = {
            "nbr_of_bits": nbr_of_bits,
            "signed": signed,
            "offset": assigned_bits,
        }

    def deserialize(self, buffer):
        """Deserialize buffer into dictionary

        :param buffer: Buffer that contains the data to deserialize (1 - 8 bytes)
        :type buffer: bytearray
        :param buffer_offset: Start address in buffer
        :type buffer: int
        :return: A dictionary keyed with the element names
        :rtype: dict
        """
        result = {}
        if len(buffer) < self.size():
            raise Exception(
                "Invalid buffer size: {0}. Expected at least: {1}".format(
                    len(buffer), self.size()
                )
            )

        for name in self._element_names():
            result[name] = self._deserialize_element(name, buffer)

        return result

    def _deserialize_element(self, name, buffer, buffer_offset=0):
        """Deserialize one element from buffer

        :param name: Name of element
        :type data: str
        :param buffer: Buffer that contains the data to deserialize data from (1 - 8 bytes).
        :type buffer: bytearray
        :param buffer_offset: Start address in buffer
        :type buffer: int
        :return: The value of the element
        :rtype: int
        """
        full_value = int.from_bytes(
            buffer[buffer_offset : buffer_offset + self.size()],
            self.__byteorder,
            signed=False,
        )
        field = self.__fields[name]
        return self._get_subvalue(
            full_value, field["nbr_of_bits"], field["offset"], field["signed"]
        )

    def serialize(self, data):
        """Serialize dictionary into buffer

        :param data: A dictionary keyed with element names. Elements can be
                     omitted from the dictionary (defaults to value 0).
        :type data: dict
        :return: A buffer that contains data
        :rtype: bytearray
        """
        buffer = bytearray(self.size())
        for name in self._element_names():
            if name in data:
                self._serialize_element(name, data[name], buffer)

        return buffer

    def _serialize_element(self, name, value, buffer, buffer_offset=0):
        """Serialize one element into the buffer

        :param name: Name of element
        :type data: str
        :param value: Value of element
        :type data: int
        :param buffer: Buffer that contains the data to serialize data into
                       (1 - 8 bytes). This is an output.
        :type buffer: bytearray
        :param buffer_offset: Start address in buffer
        :type buffer: int
        """
        full_value = int.from_bytes(
            buffer[buffer_offset : buffer_offset + self.size()],
            self.__byteorder,
            signed=False,
        )
        field = self.__fields[name]
        value = self._set_subvalue(
            full_value, value, field["nbr_of_bits"], field["offset"], field["signed"]
        )
        buffer[buffer_offset : buffer_offset + self.size()] = value.to_bytes(
            self.size(), self.__byteorder, signed=False
        )

    def instance(self, buffer=None, buffer_offset=0):
        """Create an instance of this bitfield.

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
        # I know. This is cyclic import of Instance, since instance depends
        # on classes within this file. However, it should not be any problem
        # since this file will be full imported once this method is called.
        # pylint: disable=cyclic-import, import-outside-toplevel
        from pycstruct.instance import Instance

        return Instance(self, buffer, buffer_offset)

    def assigned_bits(self):
        """Get size of bitfield in bits excluding padding bits

        :return: Number of bits this bitfield represents excluding padding bits
        :rtype: int
        """
        total_nbr_of_bits = 0
        for _, field in self.__fields.items():
            total_nbr_of_bits += field["nbr_of_bits"]

        return total_nbr_of_bits

    def size(self):
        """Get size of bitfield in bytes

        :return: Number of bytes this bitfield represents
        :rtype: int
        """
        if self.__size >= 0:
            return self.__size  # Force size

        return int(math.ceil(self.assigned_bits() / 8.0))

    def _max_bits(self):
        if self.__size >= 0:
            return self.__size * 8  # Force size
        return 64

    def _largest_member(self):
        """Used for struct padding

        :return: Closest power of 2 value of size
        :rtype: int
        """
        return _round_pow_2(self.size())

    def _get_subvalue(self, value, nbr_of_bits, start_bit, signed):
        """Get subvalue of value
        :return: The subvalue
        :rtype: int
        """
        # pylint: disable=no-self-use
        shifted_value = value >> start_bit
        mask = 0xFFFFFFFFFFFFFFFF >> (64 - nbr_of_bits)
        non_signed_value = shifted_value & mask
        if not signed:
            return non_signed_value
        sign_bit = 0x1 << (nbr_of_bits - 1)
        if non_signed_value & sign_bit == 0:
            # Value is positive
            return non_signed_value
        # Convert to negative value using Two's complement
        signed_value = -1 * ((~non_signed_value & mask) + 1)
        return signed_value

    def _set_subvalue(self, value, subvalue, nbr_of_bits, start_bit, signed):
        """Set subvalue of value
        :return: New value where subvalue is included
        :rtype: int
        """
        # pylint: disable=too-many-arguments,no-self-use
        # Validate size according to nbr_of_bits
        max_value = 2 ** nbr_of_bits - 1
        min_value = 0
        if signed:
            max_value = 2 ** (nbr_of_bits - 1) - 1
            min_value = -1 * (2 ** (nbr_of_bits - 1))

        signed_str = "Unsigned"
        if signed:
            signed_str = "Signed"

        if subvalue > max_value:
            raise Exception(
                "{0} value {1} is too large to fit in {2} bits. Max value is {3}.".format(
                    signed_str, subvalue, nbr_of_bits, max_value
                )
            )
        if subvalue < min_value:
            raise Exception(
                "{0} value {1} is too small to fit in {2} bits. Min value is {3}.".format(
                    signed_str, subvalue, nbr_of_bits, min_value
                )
            )

        if signed and subvalue < 0:
            # Convert from negative value using Two's complement
            sign_bit = 0x1 << (nbr_of_bits - 1)
            subvalue = sign_bit | ~(-1 * subvalue - 1)

        mask = 0xFFFFFFFFFFFFFFFF >> (64 - nbr_of_bits)

        shifted_subvalue = (subvalue & mask) << start_bit

        return value | shifted_subvalue

    def create_empty_data(self):
        """Create an empty dictionary with all keys

        :return: A dictionary keyed with the element names. Values are "empty" or 0.
        :rtype: dict
        """
        buffer = bytearray(self.size())
        return self.deserialize(buffer)

    def _type_name(self):
        return "bitfield"

    def __str__(self):
        """Create string representation

        :return: A string illustrating all members
        :rtype: string
        """
        result = []
        result.append(
            "{:<30}{:<10}{:<10}{:<10}".format("Name", "Bits", "Offset", "Signed")
        )
        for name, field in self.__fields.items():
            signed = "-"
            if field["signed"]:
                signed = "x"
            result.append(
                "{:<30}{:<10}{:<10}{:<10}".format(
                    name, field["nbr_of_bits"], field["offset"], signed
                )
            )
        return "\n".join(result)

    def _element_names(self):
        """Get a list of all element names (in correct order)

        :return: A list of all elements
        :rtype: list
        """
        result = []
        for name in self.__fields.keys():
            result.append(name)
        return result


###############################################################################
# EnumDef Class


class EnumDef(_BaseDef):
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

    def __init__(self, byteorder="native", size=-1, signed=False):
        if byteorder not in _BYTEORDER:
            raise Exception("Invalid byteorder: {0}.".format(byteorder))
        if byteorder == "native":
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
        # pylint: disable=bare-except
        # Check for same bitfield name
        if name in self.__constants:
            raise Exception("Constant with name {0} already exists.".format(name))

        # Automatically assigned to next available value
        index = 0
        while value is None:
            try:
                self.get_name(index)
                index += 1
            except:
                value = index

        # Secure that no negative number are added to signed enum
        if not self.__signed and value < 0:
            raise Exception(
                "Negative value, {0}, not supported in unsigned enums.".format(value)
            )

        # Check that new size is not too large
        if self._bit_length(value) > self._max_bits():
            raise Exception(
                "Maximum number of bits ({}) exceeded: {}.".format(
                    self._max_bits(), self._bit_length(value)
                )
            )

        self.__constants[name] = value

    def deserialize(self, buffer):
        """Deserialize buffer into a string (constant name)

        If no constant name is defined for the value following name will be returned::

             __VALUE__<value>

        Where <value> is the integer stored in the buffer.

        :param buffer: Buffer that contains the data to deserialize (1 - 8 bytes)
        :type buffer: bytearray
        :return: The constant name (string)
        :rtype: str
        """
        # pylint: disable=bare-except
        if len(buffer) != self.size():
            raise Exception(
                "Invalid buffer size: {0}. Expected: {1}".format(
                    len(buffer), self.size()
                )
            )

        value = int.from_bytes(buffer, self.__byteorder, signed=self.__signed)

        name = ""
        try:
            name = self.get_name(value)
        except:
            # No constant name exist, generate a new
            name = "__VALUE__{}".format(value)
        return name

    def serialize(self, data):
        """Serialize string (constant name) into buffer

        :param data: A string representing the constant name.
        :type data: str
        :return: A buffer that contains data
        :rtype: bytearray
        """
        value = self.get_value(data)

        return value.to_bytes(self.size(), self.__byteorder, signed=self.__signed)

    def size(self):
        """Get size of enum in bytes

        :return: Number of bytes this enum represents
        :rtype: int
        """
        if self.__size >= 0:
            return self.__size  # Force size

        max_length = 1  # To avoid 0 size
        for _, value in self.__constants.items():
            bit_length = self._bit_length(value)
            if bit_length > max_length:
                max_length = bit_length

        return int(math.ceil(max_length / 8.0))

    def _max_bits(self):
        if self.__size >= 0:
            return self.__size * 8  # Force size
        return 64

    def _largest_member(self):
        """Used for struct padding

        :return: Closest power of 2 value of size
        :rtype: int
        """
        return _round_pow_2(self.size())

    def get_name(self, value):
        """Get the name representation of the value

        :return: The constant name
        :rtype: str
        """
        for constant, item_value in self.__constants.items():
            if value == item_value:
                return constant
        raise Exception("Value {0} is not a valid value for this enum.".format(value))

    def get_value(self, name):
        """Get the value representation of the name

        :return: The value
        :rtype: int
        """
        if name not in self.__constants:
            raise Exception("{0} is not a valid name in this enum".format(name))
        return self.__constants[name]

    def _type_name(self):
        return "enum"

    def _bit_length(self, value):
        """Get number of bits a value represents.

        Works for negative values based on two's complement,
        which is not considered in the python built in
        bit_length method.

        If enum is signed the extra sign bit is included
        in the returned result.
        """
        if value < 0:
            value += 1  # Two's complement reverse
        bit_length = value.bit_length()
        if self.__signed:
            bit_length += 1
        return bit_length

    def __str__(self):
        """Create string representation

        :return: A string illustrating all constants
        :rtype: string
        """
        result = []
        result.append("{:<30}{:<10}".format("Name", "Value"))
        for name, value in self.__constants.items():
            result.append("{:<30}{:<10}".format(name, value))
        return "\n".join(result)
