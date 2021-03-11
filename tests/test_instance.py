import unittest
import pycstruct


class TestInstance(unittest.TestCase):
    def test_instance(self):

        # First define a complex definition structure
        car_type = pycstruct.EnumDef(size=4)
        car_type.add("Sedan", 0)
        car_type.add("Station_Wagon", 5)
        car_type.add("Bus", 7)
        car_type.add("Pickup", 12)

        sedan_properties = pycstruct.StructDef()
        sedan_properties.add("uint16", "sedan_code")

        station_wagon_properties = pycstruct.StructDef()
        station_wagon_properties.add("int32", "trunk_volume")

        bus_properties = pycstruct.StructDef()
        bus_properties.add("int32", "number_of_passangers")
        bus_properties.add("uint16", "number_of_entries")
        bus_properties.add("bool8", "is_accordion_bus")

        pickup_properties = pycstruct.StructDef()
        pickup_properties.add("int32", "truck_bed_volume")

        type_specific_properties = pycstruct.StructDef(union=True)
        type_specific_properties.add(sedan_properties, "sedan")
        type_specific_properties.add(station_wagon_properties, "station_wagon")
        type_specific_properties.add(bus_properties, "bus")
        type_specific_properties.add(pickup_properties, "pickup")

        car_properties = pycstruct.BitfieldDef()
        car_properties.add("env_class", 3, signed=True)
        car_properties.add("registered", 1)
        car_properties.add("over_3500_kg", 1)

        car_properties2 = pycstruct.BitfieldDef()
        car_properties2.add("prop1", 7)
        car_properties2.add("prop2", 3)
        car_properties2.add("prop3", 2)

        car = pycstruct.StructDef()
        car.add("uint16", "year")
        car.add("utf-8", "model", length=50)
        car.add("utf-8", "registration_number", length=10)
        car.add("int32", "last_owners", length=10)
        car.add(car_properties, "properties")
        car.add(car_properties2, "properties2", same_level=True)
        car.add(car_type, "type")
        car.add(type_specific_properties, "type_properties")

        garage = pycstruct.StructDef()
        garage.add(car, "cars", length=20)
        garage.add("uint8", "nbr_registered_parkings")

        house = pycstruct.StructDef()
        house.add("uint8", "nbr_of_levels")
        house.add(garage, "garage")

        #####################################################################
        # Create an instance of a Bitfield (car_properties)

        # Buffer is empty
        instance = car_properties.instance()  # Create from BitfieldDef
        self.assertEqual(instance.env_class, 0)
        self.assertEqual(instance.registered, 0)
        self.assertEqual(instance.over_3500_kg, 0)

        instance.env_class = -2
        instance.registered = 0
        instance.over_3500_kg = 1
        self.assertEqual(instance.env_class, -2)
        self.assertEqual(instance.registered, 0)
        self.assertEqual(instance.over_3500_kg, 1)

        # Test that buffer is updated correctly
        bytes_instance = bytes(instance)
        dict_repr = car_properties.deserialize(bytes_instance)
        self.assertEqual(dict_repr["env_class"], -2)
        self.assertEqual(dict_repr["registered"], 0)
        self.assertEqual(dict_repr["over_3500_kg"], 1)

        # Create instance from buffer
        dict_repr["env_class"] = 1
        dict_repr["registered"] = 1
        dict_repr["over_3500_kg"] = 0
        bytes_struct = car_properties.serialize(dict_repr)
        instance = pycstruct.Instance(car_properties, bytes_struct)
        self.assertEqual(instance.env_class, 1)
        self.assertEqual(instance.registered, 1)
        self.assertEqual(instance.over_3500_kg, 0)

        # Value too large
        self.assertRaises(Exception, instance.env_class, 5)
        # Value invalid type
        self.assertRaises(Exception, instance.env_class, "invalid")
        # Non existing value
        try:
            x = instance.invalid
            t.assertTrue(False)
        except:
            pass
        try:
            instance.invalid = 1
            t.assertTrue(False)
        except:
            pass

        #####################################################################
        # Create an instance of a simple Struct (bus_properties)

        # Create instance of car_properties instance
        instance = pycstruct.Instance(bus_properties)
        self.assertEqual(instance.number_of_passangers, 0)
        self.assertEqual(instance.number_of_entries, 0)
        self.assertEqual(instance.is_accordion_bus, False)

        instance.number_of_passangers = 55
        instance.number_of_entries = 3
        instance.is_accordion_bus = True
        self.assertEqual(instance.number_of_passangers, 55)
        self.assertEqual(instance.number_of_entries, 3)
        self.assertEqual(instance.is_accordion_bus, True)

        #####################################################################
        # Create an instance of a union (type_specific_properties)
        instance = pycstruct.Instance(type_specific_properties)
        self.assertEqual(instance.sedan.sedan_code, 0)
        self.assertEqual(instance.station_wagon.trunk_volume, 0)
        self.assertEqual(instance.bus.number_of_passangers, 0)
        self.assertEqual(instance.bus.number_of_entries, 0)
        self.assertEqual(instance.bus.is_accordion_bus, 0)
        self.assertEqual(instance.pickup.truck_bed_volume, 0)

        instance.station_wagon.trunk_volume = 1234
        # Since this a union the truck_bed_volume should also be updated to
        # the same value since it has same offset and data type
        self.assertEqual(instance.station_wagon.trunk_volume, 1234)
        self.assertEqual(instance.pickup.truck_bed_volume, 1234)

        #####################################################################
        # Create an instance of a complex Struct (house)
        instance = house.instance()  # Create directly from StructDef
        instance.nbr_of_levels = 92
        instance.garage.cars[0].year = 2012
        instance.garage.cars[0].registration_number = "ABC123"
        instance.garage.cars[0].last_owners[0] = 1
        instance.garage.cars[0].properties.registered = True
        instance.garage.cars[0].prop2 = 3
        instance.garage.cars[0].type = "Station_Wagon"
        instance.garage.cars[0].type_properties.sedan.sedan_code = 5
        instance.garage.cars[10].year = 1999
        instance.garage.cars[10].registration_number = "CDE456"
        instance.garage.cars[10].last_owners[5] = 2
        instance.garage.cars[10].properties.registered = False
        instance.garage.cars[10].prop2 = 2
        instance.garage.cars[10].type = "Bus"
        instance.garage.cars[10].type_properties.station_wagon.trunk_volume = 500
        instance.garage.cars[19].year = 2021
        instance.garage.cars[19].registration_number = "EFG789"
        instance.garage.cars[19].last_owners[9] = 3
        instance.garage.cars[19].properties.registered = True
        instance.garage.cars[19].prop2 = 1
        instance.garage.cars[19].type = "Pickup"
        instance.garage.cars[19].type_properties.bus.number_of_entries = 3
        instance.garage.nbr_registered_parkings = 255

        # Test that buffer is updated correctly
        bytes_instance = bytes(instance)
        dict_repr = house.deserialize(bytes_instance)
        self.assertEqual(dict_repr["nbr_of_levels"], 92)
        self.assertEqual(dict_repr["garage"]["cars"][0]["year"], 2012)
        self.assertEqual(
            dict_repr["garage"]["cars"][0]["registration_number"], "ABC123"
        )
        self.assertEqual(dict_repr["garage"]["cars"][0]["last_owners"][0], 1)
        self.assertEqual(
            dict_repr["garage"]["cars"][0]["properties"]["registered"], True
        )
        self.assertEqual(dict_repr["garage"]["cars"][0]["prop2"], 3)
        self.assertEqual(dict_repr["garage"]["cars"][0]["type"], "Station_Wagon")
        self.assertEqual(
            dict_repr["garage"]["cars"][0]["type_properties"]["sedan"]["sedan_code"], 5
        )
        self.assertEqual(dict_repr["garage"]["cars"][10]["year"], 1999)
        self.assertEqual(
            dict_repr["garage"]["cars"][10]["registration_number"], "CDE456"
        )
        self.assertEqual(dict_repr["garage"]["cars"][10]["last_owners"][5], 2)
        self.assertEqual(
            dict_repr["garage"]["cars"][10]["properties"]["registered"], False
        )
        self.assertEqual(dict_repr["garage"]["cars"][10]["prop2"], 2)
        self.assertEqual(dict_repr["garage"]["cars"][10]["type"], "Bus")
        self.assertEqual(
            dict_repr["garage"]["cars"][10]["type_properties"]["station_wagon"][
                "trunk_volume"
            ],
            500,
        )
        self.assertEqual(dict_repr["garage"]["cars"][19]["year"], 2021)
        self.assertEqual(
            dict_repr["garage"]["cars"][19]["registration_number"], "EFG789"
        )
        self.assertEqual(dict_repr["garage"]["cars"][19]["last_owners"][9], 3)
        self.assertEqual(
            dict_repr["garage"]["cars"][19]["properties"]["registered"], True
        )
        self.assertEqual(dict_repr["garage"]["cars"][19]["prop2"], 1)
        self.assertEqual(dict_repr["garage"]["cars"][19]["type"], "Pickup")
        self.assertEqual(
            dict_repr["garage"]["cars"][19]["type_properties"]["bus"][
                "number_of_entries"
            ],
            3,
        )
        self.assertEqual(dict_repr["garage"]["nbr_registered_parkings"], 255)

        #############################################
        # Test to string method
        stringrep = str(instance)
        self.assertTrue("type_properties.station_wagon.trunk_volume : 5" in stringrep)
        self.assertTrue("last_owners : [0, 0, 0, 0, 0, 2, 0, 0, 0, 0]" in stringrep)
        self.assertTrue("garage.nbr_registered_parkings : 255" in stringrep)

        #############################################
        # Invalid usage
        self.assertRaises(Exception, house._element_offset, "invalid")
        self.assertRaises(Exception, pycstruct.Instance, car_type)  # Enum not possible
        try:
            instance.garage = 5
            t.assertTrue(False)
        except:
            pass

    def test_instance_list_basictype(self):
        struct = pycstruct.StructDef()
        struct.add("int16", "list", length=3)

        buffer = bytearray(struct.size())
        struct_instance = struct.instance(buffer)
        instance = struct_instance.list

        self.assertEqual(instance[0], 0)
        self.assertEqual(instance[1], 0)
        self.assertEqual(instance[2], 0)

        instance[0] = 1234
        instance[1] = 567
        instance[2] = 8901

        self.assertEqual(instance[0], 1234)
        self.assertEqual(instance[1], 567)
        self.assertEqual(instance[2], 8901)

        # Test bytes on array
        bytes_array = bytes(instance)
        bytes_instance = bytes(struct_instance)
        self.assertEqual(bytes_array, bytes_instance)

        # Test that buffer is updated correctly
        dict_repr = struct.deserialize(bytes_instance)
        self.assertEqual(dict_repr["list"][0], 1234)
        self.assertEqual(dict_repr["list"][1], 567)
        self.assertEqual(dict_repr["list"][2], 8901)

        # Create instance from buffer
        dict_repr["list"][0] = 1111
        dict_repr["list"][1] = -2222
        dict_repr["list"][2] = 3333
        bytes_struct = struct.serialize(dict_repr)
        struct_instance = struct.instance(bytes_struct)
        instance = struct_instance.list
        self.assertEqual(instance[0], 1111)
        self.assertEqual(instance[1], -2222)
        self.assertEqual(instance[2], 3333)

    def test_instance_list_complex(self):
        enum = pycstruct.EnumDef(size=4)
        enum.add("e1", 0)
        enum.add("e2", 5)
        enum.add("e3", 7)
        enum.add("e4", 9)
        enum.add("e5", 12)

        bitfield = pycstruct.BitfieldDef()
        bitfield.add("bf1", 7)
        bitfield.add("bf2", 5)

        substruct = pycstruct.StructDef()
        substruct.add("uint8", "ss1")
        substruct.add("int32", "ss2")

        struct = pycstruct.StructDef()
        struct.add(enum, "enum", length=2)
        struct.add(bitfield, "bitfield", length=3)
        struct.add(substruct, "substruct", length=13)

        #####################################################################
        # Enum list
        buffer = bytearray(struct.size())
        struct_instance = struct.instance(buffer)
        instance = struct_instance.enum
        self.assertEqual(len(instance), 2)
        self.assertEqual(instance[0], "e1")
        self.assertEqual(instance[1], "e1")
        instance[0] = "e2"
        instance[1] = "e3"
        bytes_instance = bytes(struct_instance)
        dict_repr = struct.deserialize(bytes_instance)
        self.assertEqual(dict_repr["enum"][0], "e2")
        self.assertEqual(dict_repr["enum"][1], "e3")
        dict_repr["enum"][0] = "e5"
        dict_repr["enum"][1] = "e4"
        bytes_struct = struct.serialize(dict_repr)
        instance = struct.instance(bytes_struct).enum
        self.assertEqual(instance[0], "e5")
        self.assertEqual(instance[1], "e4")

        #####################################################################
        # Bitfield list
        buffer = bytearray(struct.size())
        struct_instance = struct.instance(buffer)
        instance = struct_instance.bitfield
        self.assertEqual(len(instance), 3)
        self.assertEqual(instance[0].bf1, 0)
        self.assertEqual(instance[0].bf2, 0)
        self.assertEqual(instance[1].bf1, 0)
        self.assertEqual(instance[1].bf2, 0)
        self.assertEqual(instance[2].bf1, 0)
        self.assertEqual(instance[2].bf2, 0)
        instance[0].bf1 = 1
        instance[0].bf2 = 2
        instance[1].bf1 = 3
        instance[1].bf2 = 4
        instance[2].bf1 = 5
        instance[2].bf2 = 6
        self.assertEqual(instance[0].bf1, 1)
        self.assertEqual(instance[0].bf2, 2)
        self.assertEqual(instance[1].bf1, 3)
        self.assertEqual(instance[1].bf2, 4)
        self.assertEqual(instance[2].bf1, 5)
        self.assertEqual(instance[2].bf2, 6)
        bytes_instance = bytes(struct_instance)
        dict_repr = struct.deserialize(bytes_instance)
        self.assertEqual(dict_repr["bitfield"][0]["bf1"], 1)
        self.assertEqual(dict_repr["bitfield"][0]["bf2"], 2)
        self.assertEqual(dict_repr["bitfield"][1]["bf1"], 3)
        self.assertEqual(dict_repr["bitfield"][1]["bf2"], 4)
        self.assertEqual(dict_repr["bitfield"][2]["bf1"], 5)
        self.assertEqual(dict_repr["bitfield"][2]["bf2"], 6)
        dict_repr["bitfield"][0]["bf1"] = 7
        dict_repr["bitfield"][0]["bf2"] = 8
        dict_repr["bitfield"][1]["bf1"] = 9
        dict_repr["bitfield"][1]["bf2"] = 10
        dict_repr["bitfield"][2]["bf1"] = 11
        dict_repr["bitfield"][2]["bf2"] = 12
        bytes_struct = struct.serialize(dict_repr)
        instance = struct.instance(bytes_struct).bitfield
        self.assertEqual(instance[0].bf1, 7)
        self.assertEqual(instance[0].bf2, 8)
        self.assertEqual(instance[1].bf1, 9)
        self.assertEqual(instance[1].bf2, 10)
        self.assertEqual(instance[2].bf1, 11)
        self.assertEqual(instance[2].bf2, 12)

        #####################################################################
        # Struct list
        buffer = bytearray(struct.size())
        array_type = struct.get_field_type("substruct")
        struct_instance = struct.instance(buffer)
        instance = struct_instance.substruct
        self.assertEqual(len(instance), 13)
        self.assertEqual(instance[0].ss1, 0)
        self.assertEqual(instance[5].ss2, 0)
        self.assertEqual(instance[7].ss1, 0)
        self.assertEqual(instance[12].ss2, 0)
        instance[0].ss1 = 92
        instance[12].ss2 = 767
        bytes_instance = bytes(struct_instance)
        dict_repr = struct.deserialize(bytes_instance)
        self.assertEqual(dict_repr["substruct"][0]["ss1"], 92)
        self.assertEqual(dict_repr["substruct"][12]["ss2"], 767)

    def test_invalid_accesses(self):
        struct = pycstruct.StructDef()
        struct.add("int8", "list", length=4)
        buffer = b"1234"
        instance = struct.instance(buffer).list
        array_of_struct = struct[1]
        aos_instance = array_of_struct.instance(buffer)

        with self.assertRaises(Exception):
            instance[2] = 5
        with self.assertRaises(Exception):
            x = instance["not a number"]
        with self.assertRaises(Exception):
            x = instance[999]
        with self.assertRaises(Exception):
            aos_instance[0] = 10

    def test_multidim_array(self):
        basetype = pycstruct.pycstruct.BasicTypeDef("uint8", "little")
        arraytype = basetype[4][3][2]
        buffer = b"abcd----------------uvwx"
        instance = arraytype.instance(buffer)
        self.assertEqual(chr(instance[0][0][0]), "a")
        self.assertEqual(chr(instance[0][0][3]), "d")
        self.assertEqual(chr(instance[1][2][0]), "u")
        self.assertEqual(chr(instance[1][2][3]), "x")


if __name__ == "__main__":
    unittest.main()
