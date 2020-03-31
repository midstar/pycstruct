import unittest, os, sys, shutil

test_dir = os.path.dirname(os.path.realpath(__file__))
proj_dir = os.path.dirname(test_dir)

sys.path.append(proj_dir)
import pycstruct

class TestCParser(unittest.TestCase):

  def test_run_castxml_invalid(self):
    _run_castxml = pycstruct.cparser._run_castxml
    _get_hash = pycstruct.cparser._get_hash

    input_files = ['dont_exist.c']

    # Non existing command
    self.assertRaises(Exception, _run_castxml, input_files, 'out.xml', castxml_cmd='dontexist')

    # Existing but failing 
    self.assertRaises(Exception, _run_castxml, input_files, 'out.xml', castxml_cmd='python3')

    # Will not fail command execution but no XML produced
    self.assertRaises(Exception, _run_castxml, input_files, 'out.xml', castxml_cmd='echo')

    # This one will pass - fake output
    xml_filename = _get_hash(input_files)




  def test_get_hash(self):
    _get_hash = pycstruct.cparser._get_hash

    hash = _get_hash(['one'])
    self.assertEqual(len(hash), 10)

    hash2 = _get_hash(['one', 'two'])
    self.assertEqual(len(hash2), 10)

    self.assertNotEqual(hash, hash2)

    hash3 = _get_hash(['one', 'two'])
    self.assertEqual(hash3, hash2)

  def test_listify(self):
    _listify = pycstruct.cparser._listify

    alist = ['hello']
    another_list = _listify(alist)
    self.assertEqual(alist, another_list)

    from_str_list = _listify('hello')
    self.assertEqual(from_str_list, alist)

    


  def test_xml_parse(self):
    _CastXmlParser = pycstruct.cparser._CastXmlParser
    parser = _CastXmlParser(os.path.join(test_dir, 'savestruct.xml'))
    structs = parser.parse()
    structdefs = parser._to_structdefs(structs, 'native')

  @unittest.skipIf(shutil.which('castxml') == None, 'castxml is not installed')
  def test_run_castxml_real(self):
    _run_castxml = pycstruct.cparser._run_castxml
    input_files = [os.path.join(test_dir, 'savestruct.c')]
    output_file = 'test_output.xml'

    # Generate standard
    _run_castxml(input_files, output_file)
    self.assertTrue(os.path.isfile(output_file))
    os.remove(output_file)

    # Valid extra arguments
    _run_castxml(input_files, output_file, castxml_extra_args=['-dI'])
    self.assertTrue(os.path.isfile(output_file))
    os.remove(output_file)

    # Invalid extra arguments
    self.assertRaises(Exception, _run_castxml, input_files, output_file, castxml_extra_args=['--invalid'])

  @unittest.skipIf(shutil.which('castxml') == None, 'castxml is not installed')
  def test_run_parse_c_real(self):
    input_files = [os.path.join(test_dir, 'savestruct.c')]
    




if __name__ == '__main__':
  unittest.main()