from setuptools import setup, find_packages
from codecs import open  # To use a consistent encoding
from os import path

here = path.abspath(path.dirname(__file__))

# Get the long description from the relevant file
with open(path.join(here, 'README.rst'), encoding='utf-8') as f:
    long_description = f.read()

setup(
  name = 'FORD',
  packages = ['ford'],
  include_package_data = True,
  version = '4.6.0',
  description = 'FORD, standing for FORtran Documenter, is an automatic documentation generator for modern Fortran programs.',
  long_description = long_description,
  author = 'Chris MacMackin',
  author_email = 'cmacmackin@gmail.com',
  url = 'https://github.com/cmacmackin/ford/', 
  download_url = 'https://github.com/cmacmackin/ford/tarball/4.6.0',
  keywords = ['Markdown', 'Fortran', 'documentation', 'comments'],
  classifiers=[
        # How mature is this project? Common values are
        #   3 - Alpha
        #   4 - Beta
        #   5 - Production/Stable
        'Development Status :: 5 - Production/Stable',

        # Indicate who your project is intended for
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Documentation',
        'Topic :: Text Processing :: Markup :: HTML',
        'Topic :: Documentation',
        'Topic :: Utilities',

        # Pick your license as you wish (should match "license" above)
        'License :: OSI Approved :: GNU General Public License v3 (GPLv3)',

        # Specify the Python versions you support here. In particular, ensure
        # that you indicate whether you support Python 2, Python 3 or both.
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
    ],
  install_requires = ['markdown','markdown-include >= 0.5.1','toposort',
                      'jinja2 >= 2.1','pygments','beautifulsoup4','graphviz'],
  entry_points = {
    'console_scripts': [
        'ford=ford:run',
    ],
  }
)
