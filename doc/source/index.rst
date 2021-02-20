pycstruct
=========

pycstruct is a python library for converting binary data to and from ordinary
python dictionaries or specific instance objects.

Data is defined similar to what is done in C language structs, unions,
bitfields and enums.

Typical usage of this library is read/write binary files or binary data
transmitted over a network.

Following complex C types are supported:

- Structs
- Unions
- Bitfields
- Enums

These types may consist of any traditional data types (integer, unsigned integer, 
boolean and float) between 1 to 8 bytes large, arrays (lists), and strings (ASCII/UTF-8).

Structs, unions, bitfields and enums can be embedded inside other structs/unions
in any level. 

Individual elements can be stored / read in any byte order and alignment.

pycstruct also supports parsing of existing C language source code to
automatically generate the pycstruct definitions / instances.

.. toctree::
   :maxdepth: 2

   installation.rst
   overview.rst
   examples/examples.rst
   faq.rst
   limitations.rst
   reference.rst



Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

