"""pycstruct instance

Copyright 2021 by Joel Midstjärna.
All rights reserved.
This file is part of the pycstruct python library and is
released under the "MIT License Agreement". Please see the LICENSE
file that should have been included as part of this package.
"""

import pycstruct.pycstruct


class Instance:
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

    def __init__(self, datatype, buffer=None, buffer_offset=0):
        if not isinstance(datatype, (pycstruct.StructDef, pycstruct.BitfieldDef)):
            raise Exception("top_class needs to be of type StructDef or BitfieldDef")

        if buffer is None:
            buffer = bytearray(datatype.size())

        # All private fields needs to be defined here to avoid
        # recursive calls to __setattr__ and __getattr__
        super().__setattr__("_Instance__type", datatype)
        super().__setattr__("_Instance__buffer", buffer)
        super().__setattr__("_Instance__buffer_offset", buffer_offset)
        super().__setattr__("_Instance__attributes", datatype._element_names())
        super().__setattr__("_Instance__subinstances", {})

        if isinstance(datatype, pycstruct.StructDef):
            # Create "sub-instances" for nested structs/bitfields and lists
            for attribute in self.__attributes:
                length = datatype._element_length(attribute)
                if length > 1:
                    # This is a list
                    self.__subinstances[attribute] = _InstanceList(
                        datatype, attribute, self.__buffer, buffer_offset
                    )
                else:
                    subtype = datatype._element_type(attribute)
                    if isinstance(
                        subtype, (pycstruct.StructDef, pycstruct.BitfieldDef)
                    ):
                        self.__subinstances[attribute] = Instance(
                            subtype,
                            self.__buffer,
                            buffer_offset + datatype._element_offset(attribute),
                        )

    def __getattr__(self, item):
        if item in self.__subinstances:
            return self.__subinstances[item]
        if item in self.__attributes:
            return self.__type._deserialize_element(
                item, self.__buffer, self.__buffer_offset
            )
        raise AttributeError("Instance has no element {}".format(item))

    def __setattr__(self, item, value):
        if item in self.__subinstances:
            raise AttributeError("You are not allowed to modify {}".format(item))
        if item in self.__attributes:
            self.__type._serialize_element(
                item, value, self.__buffer, self.__buffer_offset
            )
        else:
            raise AttributeError("Instance has no element {}".format(item))

    def __bytes__(self):
        return bytes(self.__buffer)

    def __str__(self, prefix=""):
        result = []
        for attribute in self.__attributes:
            if attribute in self.__subinstances:
                if isinstance(self.__subinstances[attribute], _InstanceList):
                    result.append(
                        self.__subinstances[attribute].__str__(
                            "{}{} : ".format(prefix, attribute)
                        )
                    )
                else:
                    result.append(
                        self.__subinstances[attribute].__str__(
                            "{}{}.".format(prefix, attribute)
                        )
                    )
            else:
                result.append(
                    "{}{} : {}".format(prefix, attribute, self.__getattr__(attribute))
                )
        return "\n".join(result)


class _InstanceList:
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

        if isinstance(self.__type, (pycstruct.StructDef, pycstruct.BitfieldDef)):
            element_offset = parenttype._element_offset(name)
            for i in range(0, self.__length):
                self.__subinstances.append(
                    Instance(
                        self.__type,
                        buffer,
                        buffer_offset + element_offset + i * self.__type.size(),
                    )
                )

    def __check_key(self, key):
        if not isinstance(key, int):
            raise KeyError("Invalid index: {} - needs to be an integer".format(key))
        if key < 0 or key >= self.__length:
            raise KeyError(
                "Invalid index: {} - supported 0 - {}".format(key, self.__length)
            )

    def __getitem__(self, key):
        self.__check_key(key)
        if len(self.__subinstances) == 0:
            return self.__parenttype._deserialize_element(
                self.__name, self.__buffer, self.__buffer_offset, key
            )
        return self.__subinstances[key]

    def __setitem__(self, key, value):
        self.__check_key(key)
        if len(self.__subinstances) == 0:
            self.__parenttype._serialize_element(
                self.__name, value, self.__buffer, self.__buffer_offset, key
            )
        else:
            raise AttributeError(
                "You are not allowed to replace object. Use object properties."
            )

    def __len__(self):
        return self.__length

    def __bytes__(self):
        return bytes(self.__buffer)

    def __str__(self, prefix=""):
        elements = []

        if len(self.__subinstances) == 0:
            for i in range(0, self.__length):
                elements.append(str(self.__getitem__(i)))
            elements_str = ", ".join(elements)
        else:
            indent = " " * len(prefix)
            for i in range(0, self.__length):
                elements.append(self.__getitem__(i).__str__(indent))
            elements_str = "\n" + ("\n" + indent + ",\n").join(elements) + "\n" + indent

        return "{}[{}]".format(prefix, elements_str)
