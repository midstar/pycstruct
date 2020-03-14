from setuptools import setup

with open("README.md", "r") as fh:
    long_description = fh.read()

setup(name='pycstruct',
      version='0.1.0',
      description='Binary data handling in Python using dictionaries',
      long_description=long_description,
       long_description_content_type="text/markdown",
      url='http://github.com/midstar/pycstruct',
      author='Joel Midstjärna',
      author_email='joel.midstjarna@gmail.com',
      keywords = ['struct', 'enum', 'bitfield', 'binary', 'protocol', 'dict', 'dictionary'], 
      license='MIT',
      packages=['pycstruct'],
      zip_safe=False,
      classifiers=[
      'Development Status :: 3 - Alpha',  
      'Intended Audience :: Developers', 
      'Topic :: Software Development :: Build Tools',
      'License :: OSI Approved :: MIT License',
      'Programming Language :: Python :: 3',
      'Programming Language :: Python :: 3.4',
      'Programming Language :: Python :: 3.5',
      'Programming Language :: Python :: 3.6',
      'Programming Language :: Python :: 3.7'
      ])