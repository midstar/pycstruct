import unittest
from pycstruct import pycstruct

try:
    import numpy
except:
    numpy = None


class TestDtype(unittest.TestCase):
    def setUp(self):
        if numpy is None:
            self.skipTest("numpy is not installed")

    def deserialize(self, type_t, data):
        r1 = type_t.deserialize(data)
        r2 = numpy.frombuffer(data, dtype=type_t.dtype(), count=1)[0]
        return r1, r2

    def test_uint32(self):
        type_t = pycstruct.BasicTypeDef("uint32", "little")
        data = b"\x01\x02\x03\x04"
        r1, r2 = self.deserialize(type_t, data)
        assert r1 == r2

    def test_float32(self):
        type_t = pycstruct.BasicTypeDef("float32", "little")
        data = b"\x01\x02\x03\x04"
        r1, r2 = self.deserialize(type_t, data)
        assert r1 == r2

    def test_rgba_struct(self):
        data = b"\x01\x02\x03\x00"
        type_t = pycstruct.StructDef()
        type_t.add("uint8", "r")
        type_t.add("uint8", "g")
        type_t.add("uint8", "b")
        type_t.add("uint8", "a")
        r1, r2 = self.deserialize(type_t, data)
        assert r1["r"] == r2["r"]
        assert r1["g"] == r2["g"]
        assert r1["b"] == r2["b"]
        assert r1["a"] == r2["a"]

    def test_string_in_struct(self):
        data = b"\x64\x64\x64\x64"
        type_t = pycstruct.StructDef()
        type_t.add("utf-8", "text", 4)
        r1, r2 = self.deserialize(type_t, data)
        assert r1["text"] == r2["text"].decode("ascii")

    def test_array_in_struct(self):
        data = b"\x01\x02\x03\x00"
        type_t = pycstruct.StructDef()
        type_t.add("uint8", "data", 4)
        r1, r2 = self.deserialize(type_t, data)
        numpy.testing.assert_array_equal(r1["data"], r2["data"])

    def test_struct_in_struct(self):
        data = b"\x01\x02\x03\x00\x11\x12\x13\x10"
        rgba_t = pycstruct.StructDef()
        rgba_t.add("uint8", "r")
        rgba_t.add("uint8", "g")
        rgba_t.add("uint8", "b")
        rgba_t.add("uint8", "a")

        type_t = pycstruct.StructDef()
        type_t.add(rgba_t, "color1", 1)
        type_t.add(rgba_t, "color2", 1)

        r1, r2 = self.deserialize(type_t, data)
        assert r1["color1"]["r"] == r2["color1"]["r"]
        assert r1["color1"]["g"] == r2["color1"]["g"]
        assert r1["color2"]["r"] == r2["color2"]["r"]
        assert r1["color2"]["g"] == r2["color2"]["g"]

    def test_array_of_struct_in_struct(self):
        data = b"\x01\x02\x03\x00\x11\x12\x13\x10"
        rgba_t = pycstruct.StructDef()
        rgba_t.add("uint8", "r")
        rgba_t.add("uint8", "g")
        rgba_t.add("uint8", "b")
        rgba_t.add("uint8", "a")

        type_t = pycstruct.StructDef()
        type_t.add(rgba_t, "colors", 2)

        r1, r2 = self.deserialize(type_t, data)
        assert r1["colors"][0]["r"] == r2["colors"][0]["r"]
        assert r1["colors"][0]["g"] == r2["colors"][0]["g"]
        assert r1["colors"][1]["r"] == r2["colors"][1]["r"]
        assert r1["colors"][1]["g"] == r2["colors"][1]["g"]

    def test_union(self):
        data = b"\x01\x02\x03\x00"
        any_uint_t = pycstruct.StructDef(union=True)
        any_uint_t.add("uint8", "u1")
        any_uint_t.add("uint16", "u2")
        any_uint_t.add("uint32", "u4")

        r1, r2 = self.deserialize(any_uint_t, data)
        assert r1["u1"] == r2["u1"]
        assert r1["u2"] == r2["u2"]
        assert r1["u4"] == r2["u4"]

    def test_union_of_structs(self):
        data = b"\x01\x02\x03\x00"

        rgba_t = pycstruct.StructDef()
        rgba_t.add("uint8", "r")
        rgba_t.add("uint8", "g")
        rgba_t.add("uint8", "b")
        rgba_t.add("uint8", "a")

        color_t = pycstruct.StructDef(union=True)
        color_t.add("uint32", "uint32")
        color_t.add(rgba_t, "rgba")
        color_t.add("uint8", "ubyte", length=4)

        r1, r2 = self.deserialize(color_t, data)
        assert r1["uint32"] == r2["uint32"]
        numpy.testing.assert_array_equal(r1["ubyte"], r2["ubyte"])
        assert r1["rgba"]["b"] == r2["rgba"]["b"]

    def test_pad_and_same_level(self):
        bitfield_t = pycstruct.BitfieldDef()
        bitfield_t.add("one_bit")
        type_t = pycstruct.StructDef(alignment=4)
        type_t.add("int8", "a")
        # Pad will be inserted here
        type_t.add("int32", "b")
        type_t.add(bitfield_t, "bf", same_level=True)
        assert len(type_t.dtype()) != 0

    def test_unsupported_basictype(self):
        type_t = pycstruct.StructDef()
        type_t.add("bool8", "a")

        with self.assertRaisesRegex(Exception, "Basic type"):
            type_t.dtype()

    def test_unsupported_bitfields(self):
        bitfield_t = pycstruct.BitfieldDef()
        bitfield_t.add("one_bit")
        foo_t = pycstruct.StructDef()
        foo_t.add(bitfield_t, "thing")

        with self.assertRaisesRegex(Exception, "BitfieldDef"):
            foo_t.dtype()

    def test_unsupported_enum(self):
        enum_t = pycstruct.EnumDef()
        enum_t.add("first")
        foo_t = pycstruct.StructDef()
        foo_t.add(enum_t, "thing")

        with self.assertRaisesRegex(Exception, "EnumDef"):
            foo_t.dtype()
