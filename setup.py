from setuptools import setup

try:
    with open("README.md", "r") as fh:
        long_description = fh.read()
except:
      long_description = ""

setup(name='pycstruct',
      version='0.9.1',
      description='Binary data handling in Python using dictionaries',
      long_description=long_description,
       long_description_content_type="text/markdown",
      url='http://github.com/midstar/pycstruct',
      project_urls={
            'Bug Tracker': 'https://github.com/midstar/pycstruct/issues',
            'Documentation': 'https://pycstruct.readthedocs.io/en/latest/',
            'Source Code': 'https://github.com/midstar/pycstruct',
      },
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
