import pycstruct

person = pycstruct.StructDef()
person.add('utf-8', 'name', length=50)
person.add('uint32', 'age')
person.add('float32','height')
person.add('bool8', 'is_male')
person.add('uint32', 'nbr_of_children')
person.add('uint32', 'child_ages', length=10)

mrGreen = {}
mrGreen['name'] = "MR Green"
mrGreen['age'] = 50
mrGreen['height'] = 1.93
mrGreen['is_male'] = True
mrGreen['nbr_of_children'] = 3
mrGreen['child_ages'] = [13,24,12]

buffer = person.serialize(mrGreen)

f = open('simple_example_mr_green.dat','wb')
f.write(buffer)
f.close()
