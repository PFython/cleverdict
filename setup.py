import pathlib
from setuptools import setup, find_packages
# from distutils.core import setup

NAME = "cleverdict"
URL = f'https://github.com/pfython/{NAME}'
HERE = pathlib.Path(__file__).parent
VERSION = "1.7.2"

setup(name = 'cleverdict',
      packages = find_packages(),
      version = VERSION,
      license='MIT',
      description = 'A data structure which allows both object attributes and dictionary keys and values to be used simultaneously and interchangeably.',
      long_description=README,
      long_description_content_type="text/markdown",
      author = 'Peter Fison',
      author_email = 'peter@southwestlondon.tv',
      url = URL,
      download_url = f'{URL}/archive/{VERSION}.tar.gz',
      keywords = [NAME, 'data', 'attribute', 'key', 'value', 'attributes', 'keys', 'values', 'database', 'utility', 'tool', "clever", "dictionary", "att", "__getattr__", "__setattr__", "getattr", "setattr"],
      install_requires=[],
      # https://pypi.org/classifiers/
      classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Object Brokering',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',],)

# Update VERSION (above) then run the following from the command prompt:

# python -m pip install setuptools wheel twine
# python setup.py sdist
# python -m twine upload --repository testpypi dist/*

# Then:
# pip install -i https://test.pypi.org/simple/ cleverdict

# And when you're ready to go fully public:
# python -m twine upload --repository pypi dist/*
