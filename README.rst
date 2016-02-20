FORD
====

This is an automatic documentation generator for modern Fortran
programs. FORD stands for FORtran Documenter. As you may know, "to ford"
refers to crossing a river (or other body of water). It does not, in
this context, refer to any company or individual associated with cars.

Ford was written due to
`Doxygen <http://www.stack.nl/~dimitri/doxygen/>`__'s poor handling of
Fortran and the lack of comparable alternatives.
`ROBODoc <http://rfsber.home.xs4all.nl/Robo/index.html>`__ can't
actually extract any information from the source code and just about any
other automatic documentation software I found was either proprietary,
didn't work very well for Fortran, or was limited in terms of how it
produced its output.
`f90doc <http://erikdemaine.org/software/f90doc/>`__ is quite good and I
managed to modify it so that it could handle most of Fortran 2003, but
it produces rather ugly documentation, can't provide as many links
between different parts of the documentation as I'd like, and is written
in Perl (which I'm not that familiar with and which lacks the sort of
libraries found in Python for producing HTML content).

The goal of FORD is to be able to reliably produce documentation for
modern Fortran software which is informative and nice to look at. The
documentation should be easy to write and non-obtrusive within the code.
While it will never be as feature-rich as Doxygen, hopefully FORD will
be able to provide a good alternative for documenting Fortran projects.

Capabilities
------------

Current features include:

-  the ability to extract information about variables, procedures,
   procedure arguments, derived types, programs, and modules from the
   source code.
-  the ability to extract documentation from comments in the source
   code.
-  LaTeX support in documentation using
   `MathJax <http://www.mathjax.org/>`__.
-  searchable documentation, using `Tipue
   Search <http://www.tipue.com/search/>`__.
-  author description and social media (including Github!) links.
-  links to download the source code.
-  links to individual files, both in their raw form or in HTML with
   syntax highlighting.
-  use of Markdown to type-set documentation.
-  links between related parts of the software.
-  Bootstrap CSS for the documentation, making it both functional and
   pretty.
-  configurable settings.
-  ability to create a hiearchical set of pages containing general information,
   not associated with any particular part of the source code.
-  display an entry for non-Fortran source files with file-level documentation
   and syntax highlighted code.


Installation
------------

The simplest way to install FORD is using
`pip <https://pip.pypa.io/en/latest/>`__. This can be done with the
command

::

    sudo pip install ford

Pip will automatically handle all dependencies for you. If you do not
have administrative rights on the computer where you want to produce
documentation, pip will allow you to install FORD and its dependencies
in a `virtualenv <https://virtualenv.pypa.io/en/latest/>`__ located
somewhere in your home directory.

If you prefer, you can install all of those dependencies manually and clone
FORD from Github. Then place FORD somewhere in your PYTHONPATH.

Alternatively, FORD is available through the `Homebrew <http://brew.sh>`__ package
manager for Mac OS X. To update Homebrew and install FORD, run these commands in
a terminal:

::

    brew update
    brew install FORD

If you would like to install the latest development (master) branch from github,
simply add the :code:`--HEAD` flag: :code:`brew install --HEAD FORD`


Documentation
-------------

More complete documentation can be found in the `project wiki <ttps://github.com/cmacmackin/ford/wiki>`__.


License
-------

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but **without any warrenty**; without even the implied warranty of
**merchantability** or **fitness for a particular purpose**.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see the `GNU website <http://www.gnu.org/licenses/gpl.htm>`__.

Documents produced by FORD are derivative works derived from the input used in their production;
they are not affected by this license.
