# FORD
[![Latest Version](https://img.shields.io/pypi/v/ford.svg)](https://pypi.python.org/pypi/FORD)
[![Latest homebrew version](https://img.shields.io/homebrew/v/ford.svg?maxAge=2592000)](http://braumeister.org/formula/ford)
[![Latest spack version](https://img.shields.io/spack/v/py-ford)](https://spack.readthedocs.io/en/latest/package_list.html#py-ford)
[![PyPI Total Downloads](https://static.pepy.tech/badge/ford)](https://pepy.tech/project/ford)
[![GitHub license](https://img.shields.io/badge/license-GPL_v3-blue.svg)](./LICENSE)
[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.1422473.svg)](https://doi.org/10.5281/zenodo.1422473)

This is an automatic documentation generator for modern Fortran programs.
FORD stands for FORtran Documenter. As you may know, "to ford" refers to
crossing a river (or other body of water). It does not, in this context, refer
to any company or individual associated with cars.

Ford was written due to [Doxygen](http://www.doxygen.org/)'s
poor handling of Fortran and the lack of comparable alternatives.
[ROBODoc](https://rfsber.home.xs4all.nl/Robo/index.html) can't actually extract
any information from the source code and just about any other automatic
documentation software I found was either proprietary, didn't work very well
for Fortran, or was limited in terms of how it produced its output.
[f90doc](http://erikdemaine.org/software/f90doc/) is quite good and I managed
to modify it so that it could handle most of Fortran 2003, but it produces
rather ugly documentation, can't provide as many links between different parts
of the documentation as I'd like, and is written in Perl (which I'm not that
familiar with and which lacks the sort of libraries found in Python for
producing HTML content).

The goal of FORD is to be able to reliably produce documentation for modern
Fortran software which is informative and nice to look at. The documentation
should be easy to write and non-obtrusive within the code. While it will never
be as feature-rich as Doxygen, hopefully FORD will be able to provide a good
alternative for documenting Fortran projects.

## Capabilities
Current features include:

- the ability to extract information about variables, procedures, procedure
  arguments, derived types, programs, and modules from the source code.
- the ability to extract documentation from comments in the source code.
- LaTeX support in documentation using [MathJax](https://www.mathjax.org/).
- searchable documentation, using [Tipue Search](http://www.tipue.com/search/).
- author description and social media (including Github!) links.
- links to download the source code.
- links to individual files, both in their raw form or in HTML with syntax
  highlighting.
- use of Markdown to type-set documentation.
- links between related parts of the software.
- Bootstrap CSS for the documentation, making it both functional and pretty.
- configurable settings.
- ability to create a hierarchical set of pages containing general information,
  not associated with any particular part of the source code.
- display an entry for non-Fortran source files with file-level documentation
  and syntax highlighted code.

## Installation

The simplest way to install FORD is using [pip](https://pip.pypa.io/en/latest/):

    pip install ford

Pip will automatically handle all dependencies for you. By default this will
place `ford` in `~/.local/bin` -- you might need to add this to your `PATH`.

Alternatively, FORD is available through the [Homebrew](https://brew.sh) package
manager for Mac OS X. To update Homebrew and install FORD, run these commands in
a terminal:

    brew update
    brew install FORD

If you would like to install the latest development (master) branch from github,
simply add the `--HEAD` flag: `brew install --HEAD FORD`

FORD is also available through the
[spack](https://spack.readthedocs.io/en/latest/) package manager by running the
following command:

    spack install py-ford

## Documentation
More complete documentation can be found in the [docs](https://forddocs.readthedocs.io).

## License
This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but **without any warrenty**; without even the implied warranty of
**merchantability** or **fitness for a particular purpose**.  See the
GNU General Public License for more details.

You should have received a [copy](./LICENSE) of the GNU General Public License
along with this program.  If not, see the [GNU website](https://www.gnu.org/licenses/gpl.html).

Documents produced by FORD are derivative works derived from the input used in their production;
they are not affected by this license.
