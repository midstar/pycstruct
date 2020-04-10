import xml.etree.ElementTree as ET
import os, logging, pycstruct, subprocess, shutil, hashlib, tempfile
import json # TODO Remove this later

###############################################################################
# Global constants

logger = logging.getLogger('pycstruct')

###############################################################################
# Internal functions

def _run_castxml(input_files, xml_filename, castxml_cmd = 'castxml', 
                 castxml_extra_args = []):
    if shutil.which(castxml_cmd) == None:
        raise Exception('Executable "{}" not found.\n'.format(castxml_cmd) +
                        'External software castxml is not installed.\n' +
                        'You need to install it and put it in your PATH.')
    args = [castxml_cmd]
    args += castxml_extra_args
    args += input_files
    args.append('--castxml-output=1')
    args.append('-o')
    args.append(xml_filename)

    try:
        output = subprocess.check_output(args, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        raise Exception('Unable to run:\n' +
                        '{}\n\n'.format(' '.join(args)) +
                        'Output:\n' +
                        e.output.decode())

    if not os.path.isfile(xml_filename):
        raise Exception('castxml did not report any error but ' + 
                        '{} was never produced.\n\n'.format(xml_filename) +
                        'castxml output was:\n{}'.format(output.decode()))

def _get_hash(list_of_strings):
    ''' Get a reproducible short name of a list of strings '''
    long_string = ''.join(list_of_strings)
    sha256 = hashlib.sha256(long_string.encode())
    hexdigest = sha256.hexdigest()
    return hexdigest[:10]

def _listify(list_or_str):
    ''' If list_or_str is a string it will be put in a list '''
    if isinstance(list_or_str, str):
        list_or_str = [list_or_str]
    return list_or_str


###############################################################################
# CastXMLParser class (internal)

class _CastXmlParser():
    ''' Parses XML:s produced by CastXML and creates a new dictionary where
        each key represent a type name of a supported pycstruct data type
        and the value is the actual pycstruct instance.
    '''

    def __init__(self, xml_filename):
        self._xml_filename = xml_filename
        self._anonymous_count = 0

    def parse(self, byteorder = 'native'):

        self.root = ET.parse(self._xml_filename).getroot()

        composite_types = self._parse_composite_types()
        return self._to_structdefs(composite_types, byteorder)

    def _parse_composite_types(self):
        # Create a new dict with metadata about struct, bitstructs and unions
        composite_types = {} # Keyed on id
        for xml_item in self.root:
            if xml_item.tag == 'Union':
                is_union = True
            elif xml_item.tag == 'Struct':
                is_union = False
            else:
                continue # No composite type

            id = xml_item.attrib['id']
            name = xml_item.attrib['name']
            if name == '':
                # Does not have a name - check for TypeDef
                name = self._get_typedef_name(id)
            composite_type = {}
            composite_type['is_union'] = is_union
            composite_type['name'] = name
            composite_type['size'] = int(int(self._get_attrib(xml_item, 'size', '0'))/8)
            composite_type['align'] = int(int(self._get_attrib(xml_item, 'align', '8'))/8)
            composite_type['members_ids'] = self._get_attrib(xml_item, 'members', '').split()
            composite_type['members'] = []
            composite_type['supported'] = True
            composite_type['structdef'] = None
            composite_types[id] = composite_type

        # Figure out the member names and types of each composite type
        for id, composite_type in composite_types.items():
            for member_id in composite_type['members_ids']:
                xml_member = self._get_elem_with_id(member_id)
                if xml_member.tag != 'Field':
                    continue # Probably just a struct/union definition
                member = {}
                member['name'] = xml_member.attrib['name']
                try:
                    member_type = self._get_type(xml_member.attrib['type'], composite_types)
                    member['type'] = member_type['type_name']
                    member['length'] = member_type['length']
                    member['reference'] = member_type['reference']
                except Exception as e:
                    logger.warning('{0} has a member {1} could not be handled:\n  - {2}\n  - Composite type will be ignored.'.format(
                        composite_type['name'], member['name'], e.args[0]))
                    composite_type['supported'] = False
                    break        
                composite_type['members'].append(member)

        return composite_types

    def _to_structdefs(self, structs, byteorder):
        result = {}
        for _, struct in structs.items():
            if struct['supported']:
                try:
                    result[struct['name']] = self._to_structdef(struct, structs, byteorder)
                except Exception as e:
                    logger.warning('Unable to convert struct {0} to pycstruct defintion:\n  - {1}\n  - Struct will be ignored.'.format(
                        struct['name'], e.args[0]))
                    struct['supported'] = False                   
        return result

    def _to_structdef(self, struct, structs, byteorder):
        if struct['structdef'] != None:
            return struct['structdef'] # Parsed before

        structdef = pycstruct.StructDef(byteorder, struct['align'], union = struct['is_union'])
        for member in struct['members']:
            if member['type'] == 'struct' or member['type'] == 'union':
                other_struct = structs[member['reference']]
                if other_struct['supported'] == False:
                    raise Exception('Member {0} is of type {1} {2} that is not supported'.format(
                        member['name'], member['type'], other_struct['name']))
                other_structdef = self._to_structdef(other_struct, structs, byteorder)
                structdef.add(other_structdef,member['name'], member['length'])
            else: 
                structdef.add(member['type'],member['name'], member['length'])

        # Sanity check size:
        if struct['size'] != structdef.size():
            logger.warning('{0} StructDef size, {1}, does match indicated size {2}'.format(
                struct['name'], structdef.size(), struct['size']))

        struct['structdef'] = structdef
        return structdef       

    def _get_attrib(self, elem, attrib, default):
        if attrib in elem.attrib:
            return elem.attrib[attrib]
        else:
            return default     

    def _get_elem_with_id(self, id):
        elem = self.root.find("*[@id='{0}']".format(id))
        if elem == None:
            raise Exception('No XML element with id attribute {2} identified'.format(id))
        return elem

    def _get_elem_with_attrib(self, tag, attrib, value):
        elem = self.root.find("{0}[@{1}='{2}']".format(tag, attrib, value))
        if elem == None:
            raise Exception('No {0} XML element with {1} attribute {2} identified'.format(tag, attrib, value))
        return elem

    def _get_typedef_name(self, type_id):
        ''' Find out the typedef name of a type which do not have a name '''

        # First check if there is a connected ElaboratedType element
        try:
            type_id = self._get_elem_with_attrib('ElaboratedType', 'type', type_id).attrib['id']
        except:
            pass

        # Now find the TypeDef element connected to the type or ElaboratedType element
        name = ''
        try:
            name = self._get_elem_with_attrib('Typedef', 'type', type_id).attrib['name']
        except:
            name = 'anonymous_{}'.format(self._anonymous_count)
            self._anonymous_count
        return name


    def _fundamental_type_to_pcstruct_type(self, elem, length):
        ''' Map the fundamental type to pycstruct type '''
        typename = elem.attrib['name']
        typesize = elem.attrib['size']
        pycstruct_type_name = 'int'
        if 'float' in typename or 'double' in typename:
            pycstruct_type_name = 'float'
        elif length > 1 and 'char' in typename:
            # char of length > 1 are considered UTF-8 data
            pycstruct_type_name = 'utf-'
        elif 'unsigned' in typename:
            pycstruct_type_name = 'uint'
        else:
            pycstruct_type_name = 'int'


        return '{0}{1}'.format(pycstruct_type_name, typesize)

    def _get_basic_type_element(self, type_id):
        ''' Finds the basic type element possible hidden behind TypeDef's or ElaboratedType's '''
        elem = self._get_elem_with_id(type_id)
        while elem.tag == 'Typedef' or elem.tag == 'ElaboratedType':
            elem = self._get_elem_with_id(elem.attrib['type'])
        return elem

    def _get_type(self, type_id, structs):
        elem = self._get_basic_type_element(type_id)
    
        member_type = {}
        member_type['length'] = 1
        member_type['reference'] = ''
        if elem.tag == 'ArrayType':
            member_type['length'] = int(elem.attrib['max']) - int(elem.attrib['min']) + 1
            elem = self._get_basic_type_element(elem.attrib['type'])
            if elem.tag == 'ArrayType':
                raise Exception('Nested arrays (matrixes) are not supported.')
        
        if elem.tag == 'FundamentalType':
            member_type['type_name'] = self._fundamental_type_to_pcstruct_type(elem, member_type['length'])
        elif elem.tag == 'PointerType':
            member_type['type_name'] = 'uint{0}'.format(elem.attrib['size'])
        elif elem.tag == 'Struct':
            member_type['type_name'] = 'struct'
            member_type['reference'] = elem.attrib['id']
        elif elem.tag == 'Union':
            member_type['type_name'] = 'union'
            member_type['reference'] = elem.attrib['id']
        else:
            raise Exception('Member type {0} is not supported.'.format(elem.tag))

        return member_type

    
###############################################################################
# Public functions

def parse_c(input_files, byteorder = 'native',  
            castxml_cmd = 'castxml', castxml_extra_args = [],
            cache_path = '', use_cached = False):
    input_files = _listify(input_files)
    xml_filename = _get_hash(input_files) + '.xml'

    if cache_path == '':
        # Use temporary path to store xml
        cache_path = tempfile.gettempdir()
    
    xml_path = os.path.join(cache_path, xml_filename)

    # Generate XML
    if use_cached == False or os.path.isfile(xml_path) == False:
        _run_castxml(input_files, xml_path, castxml_cmd, castxml_extra_args)

    # Parse XML
    castxml_parser = _CastXmlParser(xml_path)
    defs = castxml_parser.parse() 

    return defs



        



        