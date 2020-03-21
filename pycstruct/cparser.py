import xml.etree.ElementTree as ET
import os, logging, json, pycstruct

logger = logging.getLogger('pycstruct')

class CParser():
    def __init__(self, c_filename, byteorder = 'native'):
        self.c_filename = c_filename

        #TBD

    def _parse_xml(self, xml_filename):

        self.root = ET.parse(xml_filename).getroot()

        # Figure out the identity of the file we try to parse
        c_filename = os.path.basename(self.c_filename)
        file_id = ''
        for child in self.root.findall("File"):
            name = os.path.basename(child.attrib['name'])
            if name == c_filename:
                file_id = child.attrib['id']
                break
        if file_id == '':
            raise Exception('File XML element with name attribute {0} not identified in {1}'.format(c_filename, xml_filename))

        # Find all structs defined in this file
        #xml_structs = self.root.findall("Struct[@file='{0}']".format(file_id))
        xml_structs = self.root.findall("Struct")

        # Create a new dict with metadata about the struct
        structs = {} # Keyed on id
        for xml_struct in xml_structs:
            id = xml_struct.attrib['id']
            name = xml_struct.attrib['name']
            if name == '':
                # Does not have a name - check for TypeDef
                name = self._get_typedef_name(id)
            struct = {}
            struct['name'] = name
            struct['size'] = int(int(self._get_attrib(xml_struct, 'size', '0'))/8)
            struct['align'] = int(int(self._get_attrib(xml_struct, 'align', '8'))/8)
            struct['members_ids'] = self._get_attrib(xml_struct, 'members', '').split()
            struct['members'] = []
            struct['supported'] = True
            struct['structdef'] = None
            structs[id] = struct

        # Figure out the member names and types of each struct
        for id, struct in structs.items():
            for member_id in struct['members_ids']:
                xml_member = self._get_elem_with_id(member_id)
                if xml_member.tag != 'Field':
                    logger.warning('Struct {0} has a member of type {1} which is not supported.\n  - Struct will be ignored.'.format(
                        struct['name'], xml_member.tag))
                    struct['supported'] = False
                    break
                member = {}
                member['name'] = xml_member.attrib['name']
                try:
                    member_type = self._get_type(xml_member.attrib['type'], structs)
                    member['type'] = member_type['type_name']
                    member['length'] = member_type['length']
                    member['reference'] = member_type['reference']
                except Exception as e:
                    logger.warning('Struct {0} has a member {1} could not be handled:\n  - {2}\n  - Struct will be ignored.'.format(
                        struct['name'], member['name'], e.args[0]))
                    struct['supported'] = False
                    break        
                struct['members'].append(member)

        return structs

    def _to_structdefs(self, structs, byteorder):
        result = {}
        for id, struct in structs.items():
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

        structdef = pycstruct.StructDef(byteorder, struct['align'])
        for member in struct['members']:
            if member['type'] == 'struct':
                other_struct = structs[member['reference']]
                if other_struct['supported'] == False:
                    raise Exception('Member {0} is of type struct {1} that is not supported'.format(
                        member['name'], other_struct['name']))
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
        ''' Find ut the typedef name of a type which do not have a name '''

        # First check if there is a connected ElaboratedType element
        try:
            type_id = self._get_elem_with_attrib('ElaboratedType', 'type', type_id).attrib['id']
        except:
            pass

        # Now find the TypeDef element connected to the type or ElaboratedType element
        return self._get_elem_with_attrib('Typedef', 'type', type_id).attrib['name']

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
        else:
            raise Exception('Member type {0} is not supported.'.format(elem.tag))

        return member_type

        



        



        