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

Embedded Struct Example
------------------------

A struct can also include another struct. 

Following C structure:

.. code-block:: c

    struct car_s 
    {
        unsigned short year;
        char model[50];
        char registration_number[10];
    };

    struct garage_s 
    {
        struct car_s cars[20];
        unsigned char nbr_registered_parkings;
    };

    struct house_s {
        unsigned char nbr_of_levels;
        struct garage_s garage;
    };

Is defined as following:

.. code-block:: python

    car = pycstruct.StructDef()
    car.add('uint16', 'year')
    car.add('utf-8', 'model', length=50)
    car.add('utf-8', 'registration_number', length=10)

    garage = pycstruct.StructDef()
    garage.add(car, 'cars', length=20)
    garage.add('uint8', 'nbr_registered_parkings')

    house = pycstruct.StructDef()
    house.add('uint8', 'nbr_of_levels')
    house.add(garage, 'garage')

To print the model number of the first car:

.. code-block:: python

    my_house = house.deserialize(databuffer)
    print(my_house['garage']['cars'][0]['model'])