.. _limitations:

Limitations
===========

Matrixes not supported
----------------------

pycstruct supports arrays but not matrixes

.. code-block:: c

    struct a_struct {
      int this_is_supported[4];
      int this_is_not_supported[4][5];
    };

It is possible to emulate a matrix by defining sub-structs.

.. code-block:: c

    struct substruct {
        int array[5]
    };

    struct a_struct {
      struct substruct workaround[4];
    };


Padding of bitfields
--------------------

How bitfields are stored in memory is not defined by the C standard.
pycstruct c parser tries to keep consecutive defined bitfields together, 
however gcc (for example) will split bitfields when alignment is needed.

Following example will be a problem:

.. code-block:: c

    struct a_struct {
      char m1;       // = 8 bits
      int bf1 : 2;   // = 2 bits
      int bf2 : 23;  // = 23 bits
    };

pycstruct c parser will layout the struct like this using 32 bit alignment:

+---------------+-----------------------+---------------------------+
| Size in bytes | Type                  | Name                      |
+===============+=======================+===========================+
| 1             | Unsigned integer      | m1                        |
+---------------+-----------------------+---------------------------+
| 1             | Unsigned integer      | __pad_0[0]                |
+---------------+-----------------------+---------------------------+
| 1             | Unsigned integer      | __pad_0[1]                |
+---------------+-----------------------+---------------------------+
| 1             | Unsigned integer      | __pad_0[2]                |
+---------------+-----------------------+---------------------------+
| 4             | Bitfield              | bf1 + bf2                 |
+---------------+-----------------------+---------------------------+

gcc will layout the struct like this using 32 bit alignment:

+---------------+-----------------------+---------------------------+
| Size in bytes | Type                  | Name                      |
+===============+=======================+===========================+
| 1             | Unsigned integer      | m1                        |
+---------------+-----------------------+---------------------------+
| 1             | Bitfield              | bf1                       |
+---------------+-----------------------+---------------------------+
| 1             | Unsigned integer      | __pad_0[0]                |
+---------------+-----------------------+---------------------------+
| 1             | Unsigned integer      | __pad_0[1]                |
+---------------+-----------------------+---------------------------+
| 3             | Bitfield              | bf2                       |
+---------------+-----------------------+---------------------------+

One workaround is to pack the struct using compiler directives.

Another workaround is to manually add padding bytes in the struct
in-between the bitfield definitions.
