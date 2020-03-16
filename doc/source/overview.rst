Overview
========

Background
----------

Typically python applications don't care about memory layout of the used varables 
or objects. This is generally not a problem when parsing text based data such as
JSON, XML data. However, when parsing binary data the Python language and standard
library has limited support for this. 

The pycstruct library solves this problem by allowing the user to define the memory
layout of an "object". Once the memory layout has been defined data can serialized
or deserialized into/from simple python dictionaries.

Why and when does the memory layout matter?
-------------------------------------------

Strict memory layout is required when reading and writing binary data, such as:

* Binary file formats 
* Binary network data

Structs
-------

Memory layout of an object is defined using the :py:meth:`StructDef` 
object. For example:

.. code-block:: python

    myStruct = pycstruct.StructDef()
    myStruct.add('int8', 'mySmallInteger')
    myStruct.add('uint32', 'myUnsignedInteger')
    myStruct.add('float32', 'myFloatingPointNumber')

The above example corresponds to following layout:

+---------------+-----------------------+---------------------------+
| Size in bytes | Type                  | Name                      |
+===============+=======================+===========================+
| 1             | Signed integer        | mySmallInteger            |
+---------------+-----------------------+---------------------------+
| 4             | Unsigned integer      | myUnsignedInteger         |
+---------------+-----------------------+---------------------------+
| 4             | Floating point number | myFloatingPointNumber     |
+---------------+-----------------------+---------------------------+

Now, when the layout has been defined, you can write binary data using 
ordinary python dictionaries.

.. code-block:: python

    myDict = {}
    myDict['mySmallInteger'] = -4
    myDict['myUnsignedInteger'] = 12345
    myDict['myFloatingPointNumber'] = 3.1415

    myByteArray = myStruct.serialize(myDict)

myByteArray is now a byte array that can for example can be written to
a file or transmittet over a network.

The reverse process looks like this (assuming data is stored in the
file myDataFile.dat):

.. code-block:: python

    with open('myDataFile.dat', 'rb') as f:
        inbytes = f.read()

    myDict2 = myStruct.deserialize(inbytes)

myDict2 will now be a dictionary with the fields mySmallInteger, 
myUnsignedInteger and myFloatingPointNumber.

Arrays
------

Arrays are added like this:

.. code-block:: python

    myStruct = pycstruct.StructDef()
    myStruct.add('int32', 'myArray', length=100)

Now myArray will be an array with 100 elements. 

.. code-block:: python

    myDict = {}
    myDict['myArray'] = [32, 11]

    myByteArray = myStruct.serialize(myDict)

Note that you don't have to provide all elements of the array in the 
dictionary. Elements not defined will be set to 0 during serialization.

Strings
-------

Strings are always encoded as UTF-8. UTF-8 is backwards compatible with
ASCII, thus ASCII strings are also supported.

.. code-block:: python

    myStruct = pycstruct.StructDef()
    myStruct.add('utf-8', 'myString', length=50)

Now myString will be a string of 50 bytes. Note that:

* Non-ASCII characters are larger than one byte. Thus the number of characters
  might not be equal to the specified length (which is in bytes not characters)
* The last byte is used as null-termination and should not be used for characters
  data.

To write a string:

.. code-block:: python

    myDict = {}
    myDict['myString'] = "this is a string"

    myByteArray = myStruct.serialize(myDict)

If you need another encoding that UTF-8 or ASCII it is recommended that you
define your element as an array of uint8. Then you can decode/encode the array
to any format you wan't.

Embedding Structs
-----------------

Embedding structs in other structs is simple:

.. code-block:: python

    myChildStruct = pycstruct.StructDef()
    myChildStruct.add('int8', 'myChildInteger')

    myParentStruct = pycstruct.StructDef()
    myParentStruct.add('int8', 'myParentInteger')
    myParentStruct.add(myChildStruct, 'myChild')

Now myParentStruct includes myChildStruct.

.. code-block:: python

    myChildDict = {}
    myChildDict['myChildInteger'] = 7

    myParentDict['myParentInteger'] = 45
    myParentDict['myChild'] = myChildDict

    myByteArray = myStruct.serialize(myParentDict)

Note that you can also make an array of child structs by setting the length
argument when adding the element.

Bitfields
---------

The struct definition requires that the size of each member is 1, 2, 4 or 8 
bytes. :py:meth:`BitfieldDef` allows you to define members that have any 
size between 1 to 64 bits.

.. code-block:: python

    myBitfield = pycstruct.BitfieldDef()

    myBitfield.add("myBit",1)
    myBitfield.add("myTwoBits",2)
    myBitfield.add("myFourSignedBits",4 ,signed=True)

The above bitfield will allocate one byte with following layout:

+-------------+------------------+---------------+-------------+
| BIT index 7 | BIT index 6 - 3  | BIT index 2-1 | BIT index 0 |
+=============+==================+===============+=============+
| Unused      | MyFourSignedBits | myTwoBits     | myBit       | 
+-------------+------------------+---------------+-------------+

To add myBitfield to a struct def:

.. code-block:: python

    myStruct = pycstruct.StructDef()
    myStruct.add(myBitfield, 'myBitfieldChild')

To access myBitfield

.. code-block:: python

    myBitfieldDict = {}
    myBitfieldDict['myBit'] = 0
    myBitfieldDict['myTwoBit'] = 3
    myBitfieldDict['myFourSignedBits'] = -1

    myDict = {}
    myDict['myBitfieldChild'] = myBitfieldDict

    myByteArray = myStruct.serialize(myDict)

Enum
----

:py:meth:`EnumDef` allows your to define a signed integer of size 1, 2, 3, ... 
or 8 bytes with a defined set of values (constants):

.. code-block:: python

    myEnum = pycstruct.EnumDef()

    myEnum.add('myConstantM3',-3)
    myEnum.add('myConstant0',0)
    myEnum.add('myConstant5',5)
    myEnum.add('myConstant44',44)

To add an enum to a struct:

.. code-block:: python

    myStruct = pycstruct.StructDef()
    myStruct.add(myEnum, 'myEnumChild')

The constants are accessed as strings:

.. code-block:: python

    myDict = {}
    myDict['myEnumChild'] = 'myConstant5'

    myByteArray = myStruct.serialize(myDict)

Setting myEnumChild to a value not defined in the EnumDef will result
in an exception.

Byte order
----------

Structs, bitfields and enums are by default read and written in the 
native byte order. However, you can always override the default 
byteorder by providing the byteorder argument. 

.. code-block:: python

    myStruct = pycstruct.StructDef(default_byteorder = 'big')
    myStruct.add('int16', 'willBeBigEndian')
    myStruct.add('int32', 'willBeBigEndianAlso')
    myStruct.add('int32', 'willBeLittleEndian', byteorder = 'little')

    myBitfield = pycstruct.BitfieldDef(byteorder = 'little')

    myEnum = pycstruct.EnumDef(byteorder = 'big')



