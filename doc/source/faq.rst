Frequently Asked Questions
==========================

How to disable printouts from pycstruct
---------------------------------------

pycstruct utilizes the standard logging module for printing out warnings.
To disable logging from the pycstruct module add following to your 
application

.. code-block:: python

    import logging
    logging.getLogger('pycstruct').setLevel(logging.CRITICAL)