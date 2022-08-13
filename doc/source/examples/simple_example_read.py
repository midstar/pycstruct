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

# Dictionary representation
result = person.deserialize(inbytes)
print('Dictionary object:')
print(str(result))

# Alternative, Instance representation
instance = person.instance(inbytes)
print('\nInstance object:')
print(f'name: {instance.name}')
print(f'nbr_of_children: {instance.nbr_of_children}')
print(f'child_ages[1]: {instance.child_ages[1]}')