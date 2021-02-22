"""pycstruct cparser

Copyright 2021 by Joel Midstjärna.
All rights reserved.
This file is part of the pycstruct python library and is
released under the "MIT License Agreement". Please see the LICENSE
file that should have been included as part of this package.
"""

import xml.etree.ElementTree as ET

import hashlib
import logging
import math
import os
import shutil
import subprocess
import tempfile

from pycstruct.pycstruct import StructDef, BitfieldDef, EnumDef

###############################################################################
# Global constants

logger = logging.getLogger("pycstruct")

###############################################################################
# Internal functions


def _run_castxml(
    input_files, xml_filename, castxml_cmd="castxml", castxml_extra_args=None
):
    """Run castcml as a 'shell command'"""
    if shutil.which(castxml_cmd) is None:
        raise Exception(
            'Executable "{}" not found.\n'.format(castxml_cmd)
            + "External software castxml is not installed.\n"
            + "You need to install it and put it in your PATH."
        )
    if castxml_extra_args is None:
        castxml_extra_args = []
    args = [castxml_cmd]
    args += castxml_extra_args
    args += input_files
    args.append("--castxml-gccxml")
    args.append("-o")
    args.append(xml_filename)

    try:
        output = subprocess.check_output(args, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as exception:
        raise Exception(
            "Unable to run:\n"
            + "{}\n\n".format(" ".join(args))
            + "Output:\n"
            + exception.output.decode()
        ) from exception

    if not os.path.isfile(xml_filename):
        raise Exception(
            "castxml did not report any error but "
            + "{} was never produced.\n\n".format(xml_filename)
            + "castxml output was:\n{}".format(output.decode())
        )


def _get_hash(list_of_strings):
    """ Get a reproducible short name of a list of strings """
    long_string = "".join(list_of_strings)
    sha256 = hashlib.sha256(long_string.encode())
    hexdigest = sha256.hexdigest()
    return hexdigest[:10]


def _listify(list_or_str):
    """ If list_or_str is a string it will be put in a list """
    if isinstance(list_or_str, str):
        list_or_str = [list_or_str]
    return list_or_str


###############################################################################
# CastXMLParser class (internal)


class _CastXmlParser:
    """Parses XML:s produced by CastXML and creates a new dictionary where
    each key represent a type name of a defined type (struct, bitstruct,
    enum, union etc.). The value represents the metadata about the type,
    such as members etc.
    """

    # pylint: disable=too-few-public-methods, broad-except

    def __init__(self, xml_filename):
        self._xml_filename = xml_filename
        self._anonymous_count = 0
        self._embedded_bf_count = 0
        self._embedded_bf = []
        self.root = None

    def parse(self):
        """Parse the XML file provided in the constructor"""
        # pylint: disable=too-many-branches, too-many-locals
        self.root = ET.parse(self._xml_filename).getroot()

        supported_types = {}

        # Parse enums
        xml_enums = self.root.findall("Enumeration")
        for xml_enum in xml_enums:
            typeid = xml_enum.attrib["id"]
            supported_types[typeid] = self._parse_enum(xml_enum)

        # Parse unions
        xml_unions = self.root.findall("Union")
        for xml_union in xml_unions:
            typeid = xml_union.attrib["id"]
            supported_types[typeid] = self._parse_union(xml_union)

        # Parse structs and bitfields:
        xml_structs_and_bitfields = self.root.findall("Struct")
        for xml_struct_or_bitfield in xml_structs_and_bitfields:
            typeid = xml_struct_or_bitfield.attrib["id"]
            if self._is_bitfield(xml_struct_or_bitfield):
                supported_types[typeid] = self._parse_bitfield(xml_struct_or_bitfield)
            else:
                supported_types[typeid] = self._parse_struct(xml_struct_or_bitfield)

        # Add all embedded bitfields in supported_types
        for bitfield in self._embedded_bf:
            supported_types[bitfield["name"]] = bitfield

        # Change mapping from id to name
        type_meta = {}
        for _, datatype in supported_types.items():
            name = datatype["name"]
            if name in type_meta:
                # Name is not unique, make it unique
                for i in range(1, 1000):
                    new_name = name + str(i)
                    if new_name not in type_meta:
                        name = new_name
                        break
            datatype["name"] = name  # Change old name to new
            type_meta[name] = datatype

        # Secure all references points to names instead of id's
        for _, datatype in type_meta.items():
            for member in datatype["members"]:
                if "reference" in member:
                    typeid = member["reference"]
                    name = supported_types[typeid]["name"]
                    member["reference"] = name

        return type_meta

    def _is_bitfield(self, xml_struct_or_bitfield):
        """Returns true if this is a "true" bitfield, i.e. the
        struct only contains bitfield members"""
        for field in self._get_fields(xml_struct_or_bitfield):
            if "bits" not in field.attrib:
                # Only bitfield fields has the bits attribute set
                return False
        return True

    def _get_fields(self, xml_item):
        fields = []
        for member_id in self._get_attrib(xml_item, "members", "").split():
            xml_member = self._get_elem_with_id(member_id)
            if xml_member.tag != "Field":
                continue  # Probably just a struct/union definition
            fields.append(xml_member)
        return fields

    def _parse_enum(self, xml_enum):
        enum = {}
        enum["type"] = "enum"
        self._set_common_meta(xml_enum, enum)
        enum["members"] = []
        has_negative = False
        for xml_member in xml_enum.findall("EnumValue"):
            member = {}
            member["name"] = xml_member.attrib["name"]
            member["value"] = int(xml_member.attrib["init"])
            if member["value"] < 0:
                has_negative = True
            enum["members"].append(member)
        if has_negative:
            enum["signed"] = True
        else:
            enum["signed"] = False
        return enum

    def _parse_union(self, xml_union):
        union = {}
        union["type"] = "union"
        self._set_common_meta(xml_union, union)
        self._set_struct_union_members(xml_union, union)
        return union

    def _parse_struct(self, xml_struct):
        struct = {}
        struct["type"] = "struct"
        self._set_common_meta(xml_struct, struct)
        self._set_struct_union_members(xml_struct, struct)
        return struct

    def _parse_bitfield_members(self, xml_bitfield_members):
        result = []
        for field in xml_bitfield_members:
            member = {}
            member["name"] = field.attrib["name"]
            member["bits"] = int(field.attrib["bits"])
            member["signed"] = True

            # Figure out if it is signed
            type_elem = self._get_basic_type_element(field.attrib["type"])
            if type_elem.tag == "FundamentalType":
                # Figure out sign
                if "unsigned" in type_elem.attrib["name"]:
                    member["signed"] = False
            else:
                logger.warning(
                    "Unable to parse sign of bitfield member %s. Will be signed.",
                    member["name"],
                )

            result.append(member)
        return result

    def _parse_bitfield(self, xml_bitfield):
        bitfield = {}
        bitfield["type"] = "bitfield"
        self._set_common_meta(xml_bitfield, bitfield)
        bitfield["members"] = self._parse_bitfield_members(
            self._get_fields(xml_bitfield)
        )

        return bitfield

    def _set_common_meta(self, xml_input, dict_output):
        """ Set common metadata available for all types """
        typeid = xml_input.attrib["id"]
        name = self._get_attrib(xml_input, "name", "")
        if name == "":
            # Does not have a name - check for TypeDef
            name = self._get_typedef_name(typeid)
        dict_output["name"] = name
        dict_output["size"] = int(int(self._get_attrib(xml_input, "size", "0")) / 8)
        dict_output["align"] = int(int(self._get_attrib(xml_input, "align", "8")) / 8)
        dict_output["supported"] = True

    def _set_struct_union_members(self, xml_input, dict_output):
        """ Set members - common for struct and unions """
        dict_output["members"] = []
        fields = self._get_fields(xml_input)
        while len(fields) > 0:
            field = fields.pop(0)
            member = {}
            if "bits" in field.attrib:
                # This is a bitfield, we need to create our
                # own bitfield definition for this field and
                # all bitfield members directly after this
                # member
                bf_fields = []
                nbr_bits = 0
                fields.insert(0, field)
                while len(fields) > 0 and "bits" in fields[0].attrib:
                    bf_field = fields.pop(0)
                    nbr_bits += int(self._get_attrib(bf_field, "bits", "0"))
                    bf_fields.append(bf_field)
                bitfield = {}
                bitfield["type"] = "bitfield"
                bitfield["name"] = "auto_bitfield_{0}".format(self._embedded_bf_count)
                self._embedded_bf_count += 1
                # WARNING! The size is compiler specific and not covered
                # by the C standard. We guess:
                bitfield["size"] = int(math.ceil(nbr_bits / 8.0))
                bitfield["align"] = dict_output["align"]  # Same as parent
                bitfield["supported"] = True
                bitfield["members"] = self._parse_bitfield_members(bf_fields)
                self._embedded_bf.append(bitfield)

                member["name"] = "__{0}".format(bitfield["name"])
                member["type"] = "bitfield"
                member["length"] = 1
                member["reference"] = bitfield["name"]
                member["same_level"] = True
            else:
                member["name"] = field.attrib["name"]
                try:
                    member_type = self._get_type(field.attrib["type"])
                    member["type"] = member_type["type_name"]
                    member["length"] = member_type["length"]
                    if "reference" in member_type:
                        member["reference"] = member_type["reference"]
                except Exception as exception:
                    logger.warning(
                        """%s has a member %s could not be handled:
 - %s
 - Composite type will be ignored.""",
                        dict_output["name"],
                        member["name"],
                        str(exception.args[0]),
                    )
                    dict_output["supported"] = False
                    break
            dict_output["members"].append(member)

    def _get_attrib(self, elem, attrib, default):
        # pylint: disable=no-self-use
        if attrib in elem.attrib:
            return elem.attrib[attrib]
        return default

    def _get_elem_with_id(self, typeid):
        elem = self.root.find("*[@id='{0}']".format(typeid))
        if elem is None:
            raise Exception(
                "No XML element with id attribute {} identified".format(typeid)
            )
        return elem

    def _get_elem_with_attrib(self, tag, attrib, value):
        elem = self.root.find("{}[@{}='{}']".format(tag, attrib, value))
        if elem is None:
            raise Exception(
                "No {} XML element with {} attribute {} identified".format(
                    tag, attrib, value
                )
            )
        return elem

    def _get_typedef_name(self, type_id):
        """ Find out the typedef name of a type which do not have a name """

        # First check if there is a connected ElaboratedType element
        try:
            type_id = self._get_elem_with_attrib(
                "ElaboratedType", "type", type_id
            ).attrib["id"]
        except Exception:
            pass

        # Now find the TypeDef element connected to the type or ElaboratedType element
        name = ""
        try:
            name = self._get_elem_with_attrib("Typedef", "type", type_id).attrib["name"]
        except Exception:
            name = "anonymous_{}".format(self._anonymous_count)
            self._anonymous_count += 1
        return name

    def _fundamental_type_to_pycstruct_type(self, elem, length):
        """ Map the fundamental type to pycstruct type """
        # pylint: disable=no-self-use
        typename = elem.attrib["name"]
        typesize = elem.attrib["size"]
        pycstruct_type_name = "int"
        if "float" in typename or "double" in typename:
            pycstruct_type_name = "float"
        elif length > 1 and "char" in typename:
            if "unsigned" in typename:
                # unsigned char of length > 1 are considered uint8 array
                pycstruct_type_name = "uint"
            elif "signed" in typename:
                # signed char of length > 1 are considered int8 array
                pycstruct_type_name = "int"
            else:
                # char of length > 1 are considered UTF-8 data (string)
                pycstruct_type_name = "utf-"
        elif "unsigned" in typename:
            pycstruct_type_name = "uint"
        else:
            pycstruct_type_name = "int"

        return "{0}{1}".format(pycstruct_type_name, typesize)

    def _get_basic_type_element(self, type_id):
        """ Finds the basic type element possible hidden behind TypeDef's or ElaboratedType's """
        elem = self._get_elem_with_id(type_id)
        while elem.tag == "Typedef" or elem.tag == "ElaboratedType":
            elem = self._get_elem_with_id(elem.attrib["type"])
        return elem

    def _get_type(self, type_id):
        elem = self._get_basic_type_element(type_id)

        member_type = {}
        member_type["length"] = 1

        if elem.tag == "ArrayType":
            member_type["length"] = (
                int(elem.attrib["max"]) - int(elem.attrib["min"]) + 1
            )
            elem = self._get_basic_type_element(elem.attrib["type"])
            if elem.tag == "ArrayType":
                raise Exception("Nested arrays (matrixes) are not supported.")

        if elem.tag == "CvQualifiedType":  # volatile
            elem = self._get_basic_type_element(elem.attrib["type"])

        if elem.tag == "FundamentalType":
            member_type["type_name"] = self._fundamental_type_to_pycstruct_type(
                elem, member_type["length"]
            )
        elif elem.tag == "PointerType":
            member_type["type_name"] = "uint{0}".format(elem.attrib["size"])
        elif elem.tag == "Struct":
            member_type["type_name"] = "struct"
            member_type["reference"] = elem.attrib["id"]
        elif elem.tag == "Union":
            member_type["type_name"] = "union"
            member_type["reference"] = elem.attrib["id"]
        elif elem.tag == "Enumeration":
            member_type["type_name"] = "enum"
            member_type["reference"] = elem.attrib["id"]
        else:
            raise Exception("Member type {0} is not supported.".format(elem.tag))

        return member_type


###############################################################################
# _TypeMetaParser class (internal)


class _TypeMetaParser:
    """This class takes a dictionary with metadata about the types and
    generate pycstruct instances.
    """

    # pylint: disable=too-few-public-methods, broad-except

    def __init__(self, type_meta, byteorder):
        self._type_meta = type_meta
        self._instances = {}
        self._byteorder = byteorder

    def parse(self):
        """Parse the type_meta file provided in the constructor"""
        for name, datatype in self._type_meta.items():
            if datatype["supported"]:
                try:
                    self._to_instance(name)
                except Exception as exception:
                    logger.warning(
                        """Unable to convert %s, type %s, to pycstruct defintion:
  - %s
  - Type will be ignored.""",
                        name,
                        datatype["type"],
                        str(exception.args[0]),
                    )
                    datatype["supported"] = False
        return self._instances

    def _to_instance(self, name):
        """Create a pycstruct instance of type with name. Will recursively
        create instances of referenced types.

        Returns the instance.
        """
        # pylint: disable=too-many-branches
        if name in self._instances:
            return self._instances[name]  # Parsed before

        meta = self._type_meta[name]

        if not meta["supported"]:
            return None  # Not supported

        instance = None

        # Structs or union
        if meta["type"] == "struct" or meta["type"] == "union":
            is_union = meta["type"] == "union"
            instance = StructDef(self._byteorder, meta["align"], union=is_union)
            for member in meta["members"]:
                if "reference" in member:
                    other_instance = self._to_instance(member["reference"])
                    if other_instance is None:
                        raise Exception(
                            "Member {} is of type {} {} that is not supported".format(
                                member["name"], member["type"], member["reference"]
                            )
                        )
                    same_level = False
                    if ("same_level" in member) and member["same_level"]:
                        same_level = True
                    instance.add(
                        other_instance,
                        member["name"],
                        member["length"],
                        same_level=same_level,
                    )
                else:
                    instance.add(member["type"], member["name"], member["length"])

        # Enum
        elif meta["type"] == "enum":
            instance = EnumDef(self._byteorder, meta["size"], meta["signed"])
            for member in meta["members"]:
                instance.add(member["name"], member["value"])

        # Bitfield
        elif meta["type"] == "bitfield":
            instance = BitfieldDef(self._byteorder, meta["size"])
            for member in meta["members"]:
                instance.add(member["name"], member["bits"], member["signed"])

        # Not supported
        else:
            logger.warning(
                "Unable to create instance for %s (type %s). Not supported.",
                meta["name"],
                meta["type"],
            )
            meta["supported"] = False
            return None

        # Sanity check size:
        if meta["size"] != instance.size():
            logger.warning(
                "%s size, %s, does match indicated size %s",
                meta["name"],
                instance.size(),
                meta["size"],
            )

        self._instances[name] = instance
        return instance


###############################################################################
# Public functions


def parse_file(
    input_files,
    byteorder="native",
    castxml_cmd="castxml",
    castxml_extra_args=None,
    cache_path="",
    use_cached=False,
):
    """Parse one or more C source files (C or C++) and generate pycstruct
    instances as a result.

    The result is a dictionary where the keys are the names of the
    struct, unions etc. typedef'ed names are also supported.

    The values of the resulting dictionary are the actual pycstruct
    instance connected to the name.

    This function requires that the external tool
    `castxml <https://github.com/CastXML/CastXML>`_ is installed.

    Alignment will automatically be detected and configured for the pycstruct
    instances.

    Note that following pycstruct types will be used for char arrays:

    - 'unsigned char []' = uint8 array
    - 'signed char []' = int8 array
    - 'char []' = utf-8 data (string)

    :param input_files: Source file name or a list of file names.
    :type input_files: str or list
    :param byteorder: Byteorder of all elements Valid values are 'native',
                      'little' and 'big'. If not specified the 'native'
                      byteorder is used.
    :type byteorder: str, optional
    :param castxml_cmd: Path to the castxml binary. If not specified
                        castxml must be within the PATH.
    :type castxml_cmd: str, optional
    :param castxml_extra_args: Extra arguments to provide to castxml.
                               For example definitions etc. Check
                               castxml documentation for which
                               arguments that are supported.
    :type castxml_extra_args: list, optional
    :param cache_path: Path where to store temporary files. If not
                       provided, the default system temporary
                       directory is used.
    :type cache_path: str, optional
    :param use_cached: If this is True, use previously cached
                       output from castxml to avoid re-running
                       castxml (since it could be time consuming).
                       Default is False.
    :type use_cached: boolean, optional
    :return: A dictionary keyed on names of the structs, unions
             etc. The values are the actual pycstruct instances.
    :rtype: dict
    """
    # pylint: disable=too-many-arguments

    input_files = _listify(input_files)
    xml_filename = _get_hash(input_files) + ".xml"

    if castxml_extra_args is None:
        castxml_extra_args = []

    if cache_path == "":
        # Use temporary path to store xml
        cache_path = tempfile.gettempdir()

    xml_path = os.path.join(cache_path, xml_filename)

    # Generate XML
    if not use_cached or not os.path.isfile(xml_path):
        _run_castxml(input_files, xml_path, castxml_cmd, castxml_extra_args)

    # Parse XML
    castxml_parser = _CastXmlParser(xml_path)
    type_meta = castxml_parser.parse()

    # Generate pycstruct instances
    type_meta_parser = _TypeMetaParser(type_meta, byteorder)
    pycstruct_instances = type_meta_parser.parse()

    return pycstruct_instances


def parse_str(
    c_str,
    byteorder="native",
    castxml_cmd="castxml",
    castxml_extra_args=None,
    cache_path="",
    use_cached=False,
):
    """Parse a string containing C source code, such as struct or
    union defintions. Any valid C code is supported.

    The result is a dictionary where the keys are the names of the
    struct, unions etc. typedef'ed names are also supported.

    The values of the resulting dictionary are the actual pycstruct
    instance connected to the name.

    This function requires that the external tool
    `castxml <https://github.com/CastXML/CastXML>`_ is installed.

    Alignment will automatically be detected and configured for the pycstruct
    instances.

    Note that following pycstruct types will be used for char arrays:

    - 'unsigned char []' = uint8 array
    - 'signed char []' = int8 array
    - 'char []' = utf-8 data (string)

    :param c_str: A string of C source code.
    :type c_str: str
    :param byteorder: Byteorder of all elements Valid values are 'native',
                      'little' and 'big'. If not specified the 'native'
                      byteorder is used.
    :type byteorder: str, optional
    :param castxml_cmd: Path to the castxml binary. If not specified
                        castxml must be within the PATH.
    :type castxml_cmd: str, optional
    :param castxml_extra_args: Extra arguments to provide to castxml.
                               For example definitions etc. Check
                               castxml documentation for which
                               arguments that are supported.
    :type castxml_extra_args: list, optional
    :param cache_path: Path where to store temporary files. If not
                       provided, the default system temporary
                       directory is used.
    :type cache_path: str, optional
    :param use_cached: If this is True, use previously cached
                       output from castxml to avoid re-running
                       castxml (since it could be time consuming).
                       Default is False.
    :type use_cached: boolean, optional
    :return: A dictionary keyed on names of the structs, unions
             etc. The values are the actual pycstruct instances.
    :rtype: dict
    """
    # pylint: disable=too-many-arguments

    if castxml_extra_args is None:
        castxml_extra_args = []

    if cache_path == "":
        # Use temporary path to store xml
        cache_path = tempfile.gettempdir()

    c_filename = _get_hash([c_str]) + ".c"
    c_path = os.path.join(cache_path, c_filename)

    with open(c_path, "w") as file:
        file.write(c_str)

    return parse_file(
        c_path, byteorder, castxml_cmd, castxml_extra_args, cache_path, use_cached
    )
