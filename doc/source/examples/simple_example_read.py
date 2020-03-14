import pycstruct

person = pycstruct.StructDef()
person.add('utf-8', 'name', length=50)
person.add('uint32', 'age')
person.add('float32','height')
person.add('bool8', 'is_male')
person.add('uint32', 'nbr_of_children')
person.add('uint32', 'child_ages', length=10)

with open('simple_example.dat', 'rb') as f:
    inbytes = f.read()

result = person.deserialize(inbytes)

print(str(result))