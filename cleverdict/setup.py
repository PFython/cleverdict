import pathlib
from setuptools import setup
HERE = pathlib.Path(__file__).parent
README = (HERE / "README.md").read_text()
# setup(
#   name="cleverdict",
#   version="0.0.1",
#   description="A data structure which allows both object attributes and dictionary keys and values to be used simultaneously and interchangeably.",
#   long_description=README,
#   long_description_content_type="text/markdown",
#   author="Peter Fison",
#   author_email="peter@southwestlondon.tv",
#   license="MIT",
#   packages=["cleverdict"],
#   zip_safe=False
# )

from distutils.core import setup
setup(
  name = 'cleverdict',
  packages = ['cleverdict'],
  version = '0.1',
  license='MIT',
  description = 'A data structure which allows both object attributes and dictionary keys and values to be used simultaneously and interchangeably.',
  author = 'Peter Fison',
  author_email = 'peter@southwestlondon.tv',
  url = 'https://github.com/pfython/cleverdict',
  download_url = 'https://github.com/pfython/cleverdict/archive/v_01.tar.gz',
  keywords = ['data', 'attribute', 'key', 'value', 'attributes', 'keys', 'values', 'database', 'utility', 'tool'],
  install_requires=[
          'validators',
          'beautifulsoup4',
      ],
  classifiers=[
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',
    'License :: MIT License',
    'Programming Language :: Python :: 3.8',
  ],
)

# Run the following from the command prompt:
# python setup.py sdist
