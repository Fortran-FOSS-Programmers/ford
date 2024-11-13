.. FORD documentation master file, created by
   sphinx-quickstart on Thu Oct  6 09:47:25 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to FORD's documentation!
================================

FORD is an automatic documentation generator for modern Fortran
programs. It stands for FORtran Documenter. As you may know, "to
ford" refers to crossing a river (or other body of water). It does
not, in this context, refer to any company or individual associated
with cars.

The goal of FORD is to be able to reliably produce documentation for
modern Fortran software which is informative and nice to look at. The
documentation should be easy to write and non-obtrusive within the code.
While it will never be as feature-rich as Doxygen, hopefully FORD will
be able to provide a good alternative for documenting Fortran projects.

Capabilities
------------

Current features include:

- extract documentation from comments in the source code,
- extract information about variables, procedures, procedure
  arguments, derived types, programs, and modules from the source
  code,
- LaTeX support in documentation using `MathJax
  <https://www.mathjax.org/>`__,
- searchable documentation, using `Lunr Search
  <https://lunrjs.com>`__,
- author description and social media (including Github!) links,
- links to download the source code,
- links to individual files, both in their raw form or in HTML with
  syntax highlighting,
- use of Markdown to type-set documentation,
- links between related parts of the software,
- Bootstrap CSS for the documentation, making it both functional and
  pretty,
- configurable settings,
- ability to create a hierarchical set of pages containing general information,
  not associated with any particular part of the source code,
- display an entry for non-Fortran source files with file-level documentation
  and syntax highlighted code.

.. _sec-installation:

Installation
------------

The simplest way to install FORD is using
`pip <https://pip.pypa.io/en/latest/>`__. This can be done with the
command::

    pip install ford

Pip will automatically handle all dependencies for you. If you do not
have administrative rights on the computer where you want to produce
documentation, pip will allow you to install FORD and its dependencies
in a `virtualenv <https://virtualenv.pypa.io/en/latest/>`__ located
somewhere in your home directory.

If you prefer, you can install all of those dependencies manually and clone
FORD from Github. Then place FORD somewhere in your PYTHONPATH.

Alternatively, FORD is available through the `Homebrew <https://brew.sh>`__ package
manager for Mac OS X. To update Homebrew and install FORD, run these commands in
a terminal::

    brew update
    brew install FORD

If you would like to install the latest development (master) branch from github,
simply add the :code:`--HEAD` flag: :code:`brew install --HEAD FORD`

FORD is also available through the `spack <https://spack.readthedocs.io/en/latest/>`__ package
manager by running the following command::

    spack install py-ford

Some Projects Using FORD
------------------------

-  `Fortran Package Manager <https://github.com/fortran-lang/fpm>`__
   (`Documentation <https://fpm.fortran-lang.org/index.html>`__)
-  `Fortran Standard Library <https://github.com/fortran-lang/stdlib>`__
   (`Documentation <https://stdlib.fortran-lang.org/index.html>`__)
-  `JSON-Fortran <https://github.com/jacobwilliams/json-fortran>`__
   (`Documentation <http://jacobwilliams.github.io/json-fortran>`__)
-  `TOML-Fortran <https://github.com/toml-f/toml-f>`__
   (`Documentation <http://toml-f.github.io/toml-f>`__)
-  `FLAP <https://github.com/szaghi/FLAP>`__
   (`Documentation <http://szaghi.github.io/FLAP/index.html>`__)
-  `VTKFortran <https://github.com/szaghi/VTKFortran>`__
   (`Documentation <http://szaghi.github.io/VTKFortran/index.html>`__)
-  `bspline-fortran <https://github.com/jacobwilliams/bspline-fortran>`__
   (`Documentation <http://jacobwilliams.github.io/bspline-fortran/>`__)
-  `CommonModules <http://github.com/hornekyle/CommonModules>`__
   (`Documentation <http://hornekyle.github.io/CommonModules>`__)
-  `Aotus <https://apes.osdn.io/pages/aotus>`__
   (`Documentation <https://geb.inf.tu-dresden.de/doxy/aotus/>`__)
-  `fBlog <http://sourceforge.net/projects/fortranblog/>`__
   (`Documentation <http://oceamer.com/~denis/>`__)
-  `CSVIO-f90 <http://gitlab.com/jordi.torne/csvio-f90>`__
   (`Documentation <http://jordi.torne.gitlab.io/csvio-f90>`__)
-  `FIDASIM <https://github.com/D3DEnergetic/FIDASIM>`__
   (`Documentation <http://d3denergetic.github.io/FIDASIM/index.html>`__)
-  `Forpy <https://github.com/ylikx/forpy>`__
   (`Documentation <https://ylikx.github.io/forpy/index.html>`__)
-  `FaiNumber-Fortran <https://github.com/kevinhng86/faiNumber-Fortran>`__
   (`Documentation <https://lib.fai.host/fortran/faiNumber/v1/>`__)
-  `GS2 <https://bitbucket.org/gyrokinetics/gs2>`__
   (`Documentation <https://gyrokinetics.gitlab.io/gs2/>`__)
-  `DBCSR <https://github.com/cp2k/dbcsr>`__
   (`Documentation <https://cp2k.github.io/dbcsr/>`__)
-  `C81-Interface <https://github.com/cibinjoseph/C81-Interface>`__
   (`Documentation <https://cibinjoseph.github.io/C81-Interface/>`__)
-  `naturalFRUIT <https://github.com/cibinjoseph/naturalFRUIT>`__
   (`Documentation <https://cibinjoseph.github.io/naturalFRUIT/index.html>`__)
-  `HoneyTools <https://github.com/QcmPlab/HoneyTools>`__
   (`Documentation <https://qcmplab.github.io/HoneyTools/>`__)

If you are using FORD in one of your projects, feel free to add it here.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   user_guide/index
   developers_guide/index
   api/modules


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
