import unittest, os, sys, shutil, tempfile, test_pycstruct

test_dir = os.path.dirname(os.path.realpath(__file__))
proj_dir = os.path.dirname(test_dir)

sys.path.append(proj_dir)
import pycstruct


class TestCParser(unittest.TestCase):
    def test_run_castxml_invalid(self):
        _run_castxml = pycstruct.cparser._run_castxml
        _get_hash = pycstruct.cparser._get_hash

        input_files = ["dont_exist.c"]

        # Non existing command
        self.assertRaises(
            Exception, _run_castxml, input_files, "out.xml", castxml_cmd="dontexist"
        )

        # Existing but failing
        self.assertRaises(
            Exception, _run_castxml, input_files, "out.xml", castxml_cmd="python3"
        )

        # Will not fail command execution but no XML produced
        self.assertRaises(
            Exception, _run_castxml, input_files, "out.xml", castxml_cmd="echo"
        )

        # This one will pass - fake output
        _ = _get_hash(input_files)

    def test_get_hash(self):
        _get_hash = pycstruct.cparser._get_hash

        hash = _get_hash(["one"])
        self.assertEqual(len(hash), 10)

        hash2 = _get_hash(["one", "two"])
        self.assertEqual(len(hash2), 10)

        self.assertNotEqual(hash, hash2)

        hash3 = _get_hash(["one", "two"])
        self.assertEqual(hash3, hash2)

    def test_listify(self):
        _listify = pycstruct.cparser._listify

        alist = ["hello"]
        another_list = _listify(alist)
        self.assertEqual(alist, another_list)

        from_str_list = _listify("hello")
        self.assertEqual(from_str_list, alist)

    def test_xml_parse(self):
        _CastXmlParser = pycstruct.cparser._CastXmlParser
        parser = _CastXmlParser(os.path.join(test_dir, "savestruct.xml"))
        meta = parser.parse()
        self.assertTrue("Data" in meta)
        self.assertTrue(meta["Data"]["type"] == "struct")

        type_meta_parser = pycstruct.cparser._TypeMetaParser(meta, "little")
        instance = type_meta_parser.parse()
        self.assertTrue("Data" in instance)
        self.assertTrue(isinstance(instance["Data"], pycstruct.StructDef))

        test_pycstruct.check_struct(self, instance["Data"], "struct_little.dat")

    def test_xml_parse_nopack(self):
        _CastXmlParser = pycstruct.cparser._CastXmlParser
        parser = _CastXmlParser(os.path.join(test_dir, "savestruct_nopack.xml"))
        meta = parser.parse()
        self.assertTrue("Data" in meta)
        self.assertTrue(meta["Data"]["type"] == "struct")

        type_meta_parser = pycstruct.cparser._TypeMetaParser(meta, "little")
        instance = type_meta_parser.parse()
        self.assertTrue("Data" in instance)
        self.assertTrue(isinstance(instance["Data"], pycstruct.StructDef))

        test_pycstruct.check_struct(self, instance["Data"], "struct_little_nopack.dat")

    def test_xml_parse_special_cases(self):
        _CastXmlParser = pycstruct.cparser._CastXmlParser
        parser = _CastXmlParser(os.path.join(test_dir, "special_cases.xml"))
        sys.stderr.write(
            "\n\n>> Below test will result in a Warning. This is expected!\n\n"
        )
        meta = parser.parse()
        sys.stderr.write("\n>> End of expected warning.\n")

        type_meta_parser = pycstruct.cparser._TypeMetaParser(meta, byteorder="little")
        instance = type_meta_parser.parse()
        self.assertTrue("with_volatile" in instance)
        self.assertTrue("filled_enum" in instance)
        self.assertTrue("signed_enum" in instance)
        self.assertTrue("different_char_arrays" in instance)
        self.assertTrue("struct_with_struct_inside" in instance)
        self.assertTrue("struct_inside" in instance)

        # Check types of different_char_arrays members.
        # Since type cannot be read out from StructDef
        # for individual members we use the __str__
        # representation
        char_array_str = str(instance["different_char_arrays"])
        rows = char_array_str.splitlines()
        self.assertEqual(rows[1].split()[1], "utf-8")
        self.assertEqual(rows[2].split()[1], "uint8")
        self.assertEqual(rows[3].split()[1], "int8")

        # Check struct with struct inside
        s_dict = instance["struct_with_struct_inside"].create_empty_data()
        self.assertEqual(len(s_dict.keys()), 1)
        self.assertTrue("inside" in s_dict)
        self.assertEqual(len(s_dict["inside"].keys()), 2)
        self.assertTrue("inside_a" in s_dict["inside"])
        self.assertTrue("inside_b" in s_dict["inside"])

    # @unittest.skipIf(True, 'temporary skipped')
    def test_xml_parse_embedded(self):
        _CastXmlParser = pycstruct.cparser._CastXmlParser
        parser = _CastXmlParser(os.path.join(test_dir, "embedded_struct.xml"))
        meta = parser.parse()
        self.assertTrue("car_type" in meta)
        self.assertTrue(meta["car_type"]["type"] == "enum")
        self.assertTrue("sedan_properties_s" in meta)
        self.assertTrue(meta["sedan_properties_s"]["type"] == "struct")
        self.assertTrue("station_wagon_properties_s" in meta)
        self.assertTrue(meta["station_wagon_properties_s"]["type"] == "struct")
        self.assertTrue("bus_properties_s" in meta)
        self.assertTrue(meta["bus_properties_s"]["type"] == "struct")
        self.assertTrue("pickup_properties_s" in meta)
        self.assertTrue(meta["pickup_properties_s"]["type"] == "struct")
        self.assertTrue("type_specific_properties_u" in meta)
        self.assertTrue(meta["type_specific_properties_u"]["type"] == "union")
        self.assertTrue("car_properties_s" in meta)
        self.assertTrue(meta["car_properties_s"]["type"] == "bitfield")
        self.assertTrue("car_s" in meta)
        self.assertTrue(meta["car_s"]["type"] == "struct")
        self.assertTrue("garage_s" in meta)
        self.assertTrue(meta["garage_s"]["type"] == "struct")
        self.assertTrue("house_s" in meta)
        self.assertTrue(meta["house_s"]["type"] == "struct")

        type_meta_parser = pycstruct.cparser._TypeMetaParser(meta, "little")
        instance = type_meta_parser.parse()
        self.assertTrue("car_type" in instance)
        self.assertTrue(isinstance(instance["car_type"], pycstruct.EnumDef))
        self.assertTrue("type_specific_properties_u" in instance)
        self.assertTrue(
            isinstance(instance["type_specific_properties_u"], pycstruct.StructDef)
        )
        self.assertEqual(instance["type_specific_properties_u"]._type_name(), "union")
        self.assertTrue("car_properties_s" in instance)
        self.assertTrue(isinstance(instance["car_properties_s"], pycstruct.BitfieldDef))
        self.assertTrue("house_s" in instance)
        self.assertTrue(isinstance(instance["house_s"], pycstruct.StructDef))
        self.assertEqual(instance["house_s"]._type_name(), "struct")

        test_pycstruct.check_embedded_struct(
            self, instance["house_s"], "embedded_struct.dat"
        )

    def test_xml_parse_embedded_nopack(self):
        _CastXmlParser = pycstruct.cparser._CastXmlParser
        parser = _CastXmlParser(os.path.join(test_dir, "embedded_struct_nopack.xml"))
        meta = parser.parse()
        self.assertTrue("car_type" in meta)

        type_meta_parser = pycstruct.cparser._TypeMetaParser(meta, "little")
        instance = type_meta_parser.parse()
        self.assertTrue("car_type" in instance)

        test_pycstruct.check_embedded_struct(
            self, instance["house_s"], "embedded_struct_nopack.dat"
        )

    def test_xml_parse_bitfield_struct(self):
        _CastXmlParser = pycstruct.cparser._CastXmlParser
        parser = _CastXmlParser(os.path.join(test_dir, "bitfield_struct.xml"))
        meta = parser.parse()
        type_meta_parser = pycstruct.cparser._TypeMetaParser(meta, "little")
        instance = type_meta_parser.parse()

        with open(os.path.join(test_dir, "bitfield_struct.dat"), "rb") as f:
            inbytes = f.read()
        result = instance["Data"].deserialize(inbytes)

        self.assertEqual(result["m1"], -11111)
        self.assertEqual(result["bf1a"], 2)
        self.assertEqual(result["bf1b"], 3)
        self.assertEqual(result["m2"], 44)
        self.assertEqual(result["bf2a"], 5)
        self.assertEqual(result["bf2b"], 66)
        self.assertEqual(result["bf3a"], 7)
        self.assertEqual(result["bf3b"], 8)
        self.assertEqual(result["m3"], 99)

    def test_xml_parse_ndim_array_struct(self):
        _CastXmlParser = pycstruct.cparser._CastXmlParser
        parser = _CastXmlParser(os.path.join(test_dir, "ndim_array_struct.xml"))
        meta = parser.parse()
        type_meta_parser = pycstruct.cparser._TypeMetaParser(meta, "little")
        instance = type_meta_parser.parse()

        with open(os.path.join(test_dir, "ndim_array_struct.dat"), "rb") as f:
            inbytes = f.read()
        result = instance["Data"].deserialize(inbytes)

        self.assertIn("array_of_int", result)
        self.assertEqual(result["array_of_int"], [[1, 2], [3, 4], [5, 6], [7, 8]])

        self.assertIn("array_of_strings", result)
        self.assertEqual(result["array_of_strings"][0][0], "0 x 0 = 0")
        self.assertEqual(result["array_of_strings"][3][1], "3 x 1 = 3")

        self.assertIn("array_of_struct", result)
        self.assertEqual(result["array_of_struct"][0][0]["a"], 255)
        self.assertEqual(result["array_of_struct"][0][0]["b"], 0)
        self.assertEqual(result["array_of_struct"][1][0]["b"], 2)
        self.assertEqual(result["array_of_struct"][3][0]["b"], 6)
        self.assertEqual(result["array_of_struct"][3][1]["b"], 7)

    @unittest.skipIf(shutil.which("castxml") == None, "castxml is not installed")
    def test_run_castxml_real(self):
        _run_castxml = pycstruct.cparser._run_castxml
        input_files = [os.path.join(test_dir, "savestruct.c")]
        output_file = "test_output.xml"

        # Generate standard
        _run_castxml(input_files, output_file)
        self.assertTrue(os.path.isfile(output_file))
        os.remove(output_file)

        # Valid extra arguments
        _run_castxml(input_files, output_file, castxml_extra_args=["-dI"])
        self.assertTrue(os.path.isfile(output_file))
        os.remove(output_file)

        # Invalid extra arguments
        self.assertRaises(
            Exception,
            _run_castxml,
            input_files,
            output_file,
            castxml_extra_args=["--invalid"],
        )

    @unittest.skipIf(shutil.which("castxml") == None, "castxml is not installed")
    def test_run_parse_file_real(self):
        input_file = os.path.join(test_dir, "savestruct.c")

        # Use default cache
        result = pycstruct.parse_file(input_file)
        self.assertTrue("Data" in result)

        xml_filename = (
            pycstruct.cparser._get_hash(pycstruct.cparser._listify(input_file)) + ".xml"
        )
        xml_path = os.path.join(tempfile.gettempdir(), xml_filename)
        self.assertTrue(os.path.isfile(xml_path))
        os.remove(xml_path)

        # Use custom cache path
        result = pycstruct.parse_file(input_file, cache_path=".")
        self.assertTrue("Data" in result)
        self.assertTrue(os.path.isfile(xml_filename))
        first_timestamp = os.path.getmtime(xml_filename)

        # Re-run using cache path
        result = pycstruct.parse_file(input_file, cache_path=".", use_cached=True)
        self.assertTrue("Data" in result)
        self.assertTrue(os.path.isfile(xml_filename))
        second_timestamp = os.path.getmtime(xml_filename)

        # Check that file was NOT updated
        self.assertEqual(first_timestamp, second_timestamp)

        # Re-run again not using cache path
        result = pycstruct.parse_file(input_file, cache_path=".", use_cached=False)
        self.assertTrue("Data" in result)
        self.assertTrue(os.path.isfile(xml_filename))
        third_timestamp = os.path.getmtime(xml_filename)

        # Check that file WAS updated
        self.assertNotEqual(first_timestamp, third_timestamp)

        os.remove(xml_filename)

    @unittest.skipIf(shutil.which("castxml") == None, "castxml is not installed")
    def test_run_parse_str_real(self):
        c_str = """
    struct a_struct {
      int member_a;
      int member_b;
    };
    union a_union {
      int umember_a;
      int umember_b;
    };
    """

        result = pycstruct.parse_str(c_str)
        self.assertTrue("a_struct" in result)
        self.assertTrue("a_union" in result)


if __name__ == "__main__":
    unittest.main()
