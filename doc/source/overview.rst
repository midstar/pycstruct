Overview
========

Background
----------

Typically python applications don't care about memory layout of the used variables 
or objects. This is generally not a problem when parsing text based data such as
JSON, XML data. However, when parsing binary data the Python language and standard
library has limited support for this. 

The pycstruct library solves this problem by allowing the user to define the memory
layout of an "object". Once the memory layout has been defined data can serialized
or deserialized into/from simple python dictionaries or specific instance objects.

Why and when does the memory layout matter?
-------------------------------------------

Strict memory layout is required when reading and writing binary data, such as:

* Binary file formats 
* Binary network data

Structs
-------

Memory layout of an object is defined using the :py:meth:`pycstruct.StructDef` 
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
a file or transmitted over a network.

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
    myStruct.add('int32', 'myArray', shape=100)

Now myArray will be an array with 100 elements. 

.. code-block:: python

    myDict = {}
    myDict['myArray'] = [32, 11]

    myByteArray = myStruct.serialize(myDict)

Note that you don't have to provide all elements of the array in the 
dictionary. Elements not defined will be set to 0 during serialization.

Ndim arrays
-----------

The shape can be a tuple for multi dimensional arrays.
The last element of the tuple is the fastest dimension.

.. code-block:: python

    myStruct = pycstruct.StructDef()
    myStruct.add('int32', 'myNdimArray', shape=(100, 50, 2))

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
to any format you want.

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

Unions
------

Unions are defined using the :py:meth:`pycstruct.StructDef` class, but the
union argument in the construct shall be set to True.

When deserializing a binary for a union, pycstruct tries to generate 
a dictionary for each member. If any of the members fails due to formatting
errors these members will be ignored.

When serializing a dictionary into a binary pycstruct will just pick the
first member it finds in the dictionary. Therefore you should only 
define the member that you which to serialize in your dictionary.

Bitfields
---------

The struct definition requires that the size of each member is 1, 2, 4 or 8 
bytes. :py:meth:`pycstruct.BitfieldDef` allows you to define members that have any 
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

:py:meth:`pycstruct.EnumDef` allows your to define a signed integer of size 1, 2, 3, ... 
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

Alignment and padding
---------------------

Compilers usually add padding in-between elements in structs to secure
individual elements are put on addresses that can be accessed 
efficiently. Also, padding is added in the end of the structs when
required so that an array of the struct can be made without "memory gaps".

Padding depends on the alignment of the CPU architecture (typically 32
or 64 bits on modern architectures), the size of individual items in
the struct and the position of the items in the struct.

The padding behavior can be removed by most compilers, usually adding
a compiler flag or directive such as:

.. code-block:: c

    #pragma pack(1)

pycstruct is by default not adding any padding, i.e. the structs are 
packed. However by providing the alignment argument padding will be
added automatically.

.. code-block:: python

    noPadding_Default          = pycstruct.StructDef(alignment = 1)
    paddedFor16BitArchitecture = pycstruct.StructDef(alignment = 2)
    paddedFor32BitArchitecture = pycstruct.StructDef(alignment = 4)
    paddedFor64BitArchitecture = pycstruct.StructDef(alignment = 8)

Lets add padding to the first example in this overview:

.. code-block:: python

    myStruct = pycstruct.StructDef(alignment = 8)
    myStruct.add('int8', 'mySmallInteger')
    myStruct.add('uint32', 'myUnsignedInteger')
    myStruct.add('float32', 'myFloatingPointNumber')

The above example will now have following layout:

+---------------+-----------------------+---------------------------+
| Size in bytes | Type                  | Name                      |
+===============+=======================+===========================+
| 1             | Signed integer        | mySmallInteger            |
+---------------+-----------------------+---------------------------+
| 1             | Unsigned integer      | __pad_0[0]                |
+---------------+-----------------------+---------------------------+
| 1             | Unsigned integer      | __pad_0[1]                |
+---------------+-----------------------+---------------------------+
| 1             | Unsigned integer      | __pad_0[2]                |
+---------------+-----------------------+---------------------------+
| 4             | Unsigned integer      | myUnsignedInteger         |
+---------------+-----------------------+---------------------------+
| 4             | Floating point number | myFloatingPointNumber     |
+---------------+-----------------------+---------------------------+

Note that when parsing source code, pycstruct has some 
limitations regarding padding of bitfields. See :ref:`limitations`.

Parsing source code
-------------------

Instead of manually creating the definitions as described above,
C source code files can be parsed and the definitions will be 
generated automatically with :func:`pycstruct.parse_file`.

It is also possible to write the source code into a string and
parse it with :func:`pycstruct.parse_str`. 

Internally pycstruct use the external tool 
`castxml <https://github.com/CastXML/CastXML>`_ which needs to
be installed and put in the current path.

Instance objects
----------------

Most examples in this section are using dictionaries. An alternative
of using dictionaries to represent the object is to use 
:py:meth:`pycstruct.Instance` objects. 

Instance objects has following advantages over dictionaries:

- Data is only serialized/deserialized when accessed
- Data is validated for each element/attribute access. I.e. you will
  get an exception if you try to set an element/attribute to a value
  that is not supported by the definition.
- Data is accessed by attribute name instead of key indexing

Instance objects are created from the :py:meth:`pycstruct.StructDef`
or :py:meth:`pycstruct.BitfieldDef` object.

.. code-block:: python

    myStruct = pycstruct.StructDef()
    #.... Add some elements to myStruct here
    instanceOfMyStruct = myStruct.instance()

    myBitfield = pycstruct.BitfieldDef()
    #.... Add some elements to myBitfield here
    instanceOfMyBitfield = myBitfield.instance()


Deserialize with numpy
----------------------

The structure definitions can be used together with
`numpy <https://numpy.org/>`_, with some restrictions.

This provides an easy way to describe complex numpy dtype,
especially compound dtypes.

There is some restructions:

- bitfields and enums are not supported
- strings are not decoded (that's still bytes)

This can be used for use cases requiring very fast processing,
or smart indexing.

The structure definitions provides a method `dtype` which
can be read by numpy.

.. code-block:: python

    import pycstruct
    import numpy

    # Define a RGBA color
    color_t = pycstruct.StructDef()
    color_t.add("uint8", "r")
    color_t.add("uint8", "g")
    color_t.add("uint8", "b")
    color_t.add("uint8", "a")

    # Define a vector of RGBA
    colorarray_t = pycstruct.StructDef()
    colorarray_t.add(color_t, "vector", shape=200)

    # Dummy data
    raw = b"\x20\x30\x40\xFF" * 200

    # Deserialize the raw bytes
    colorarray = numpy.frombuffer(raw, dtype=colorarray_t.dtype(), count=1)
    # numpy.frombuffer deserialize arrays. In this case there is
    # a single element of colorarray_t, which can be unstacked
    colorarray = colorarray[0]

    # Elements can be accessed by names
    # Here we can access to the whole red components is a single request
    red_component = colorarray["vector"]["r"]
    assert red_component.dtype == numpy.uint8
    assert red_component.shape == (200, )

Numpy also provides record array which can be used like the
instance objects.

.. code-block:: python

    colorarray = numpy.frombuffer(raw, dtype=colorarray_t.dtype())[0]

    # Create a record array
    colorarray = numpy.rec.array(colorarray)

    # Elements can be accessed by attributes
    assert colorarray.vector.r.dtype == numpy.uint8
    assert colorarray.vector.r.shape == (200, )
