Examples
========

Simple Example
--------------

Following C has a structure (person) with a set of elements
that are written to a binary file.

.. literalinclude:: simple_example.c
   :language: c

To read the binary file using pycstruct following code 
required.

.. literalinclude:: simple_example_read.py
   :language: python

The produced output will be::

    {'name': 'Foo Bar', 'is_male': True, 'nbr_of_children': 2, 
     'age': 42, 'child_ages': [7, 9, 0, 0, 0, 0, 0, 0, 0, 0], 
     'height': 1.75}

To write a binary file from python using the same structure
using pycstruct following code is required.

.. literalinclude:: simple_example_write.py
   :language: python