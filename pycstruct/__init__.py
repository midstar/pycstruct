"""pycstruct library

pycstruct is a python library for converting binary data to and from ordinary
python dictionaries or specific instance objects.

Data is defined similar to what is done in C language structs, unions,
bitfields and enums.

Typical usage of this library is read/write binary files or binary data
transmitted over a network.

For more information see:

https://github.com/midstar/pycstruct
"""

from pycstruct.pycstruct import StructDef
from pycstruct.pycstruct import BitfieldDef
from pycstruct.pycstruct import EnumDef
from pycstruct.pycstruct import ArrayDef

from pycstruct.instance import Instance

from pycstruct.cparser import parse_file
from pycstruct.cparser import parse_str
