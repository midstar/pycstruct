pycstruct
=========

pycstruct is a python library for converting binary data to and from ordinary
python dictionaries.

Data is defined similar to what is done in C language structs.

Typical usage of this library is read/write binary files or binary data
transmitted over a network.

It supports all traditional data types (integer, unsigned integer, boolean and
float) between 1 to 8 bytes large, arrays (lists), strings (UTF-8), bitfields
and enums.

Structs can be embedded inside other structs.

Individual elements can be stored / read in any byte order.

pycstruct also supports parsing of existing C language source code to
automatically generate the pycstruct definitions / instances.

.. toctree::
   :maxdepth: 2

   installation.rst
   overview.rst
   examples/examples.rst
   faq.rst
   reference.rst



Indices and tables
==================

* :ref:`genindex`
* :ref:`search`

