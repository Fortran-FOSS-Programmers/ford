.. _sec-command-line-options:

======================
 Command Line Options
======================

The command-line interface is given below:

::

   usage: ford [-h] [-d SRC_DIR] [-p PAGE_DIR] [-o OUTPUT_DIR] [-s CSS]
               [-r REVISION] [--exclude EXCLUDE] [--exclude_dir EXCLUDE_DIR]
               [-e EXTENSIONS] [-m MACRO] [-w] [-g] [--no-search] [-q] [-V] [--debug]
               [-I INCLUDE]
               project_file

.. _cli-SRC_DIR:

SRC_DIR
^^^^^^^

The directory where the source-files are to be found for this project.
This must not be a subdirectory of the OUTPUT_DIR (see below). This
option may be repeated to specify multiple project directories. Paths
are evaluated relative to the current working directory. (*default:* ``./src``)

.. _cli-PAGE_DIR:

PAGE_DIR
^^^^^^^^

A directory containing markdown files to be processed into individuals
pages within the documentation. See `sec-writing-pages` for
details. Paths are evaluated relative to the current working directory.

.. _cli-OUTPUT_DIR:

OUTPUT_DIR
^^^^^^^^^^

The directory where the project output will be placed. **Any content
already present there will be deleted.** Paths are evaluated relative
to the current working directory. (*default:* ./doc)

.. _cli-CSS:

CSS
^^^

The path to a custom style-sheet which can be used to modify the
appearance of the output. Paths are evaluated relative to the current working directory.

.. _cli-REVISION:

REVISION
^^^^^^^^

The name of the source code revision being documented.

.. _cli-EXCLUDE:

EXCLUDE
^^^^^^^

A source file which should not be docuemnted. Provide only the
file-name, not the full path. This option may be repeated to specify
multiple files to be excluded.

.. _cli-EXCLUDE_DIR:

EXCLUDE_DIR
^^^^^^^^^^^

A directory whose contents should not be documented. Provide only the
directory-name, not the full path. This option may be repeated to
specify multiple directories to be excluded.

.. _cli-EXTENSIONS:

EXTENSIONS
^^^^^^^^^^

File extensions which will be read by FORD for documentation. This
option may be repeated to specify multiple extensions. These
extensions are only for free-form code. Extensions for fixed-form code
may be specified in the `project file <option-fixed_extensions>`.
(*default:* f90, f95, f03, f08, f15, F90, F95, F03, F08, F15)

.. _cli-INCLUDE:

INCLUDE
^^^^^^^

Directory in which to search for include files, used either by the
preprocessor or Fortran’s intrinsic ``include`` function. This option
may be repeated to specify multiple include directories. Paths are
evaluated relative to the current working directory.

.. _cli-MACRO:

MACRO
^^^^^

Macros of the form ``name`` or ``name=value`` to be used when
`preprocessing <option-preprocess>` files. This option may be repeated
to specify multiple macros.

.. _cli-warn:

``-w``/``--warn``
^^^^^^^^^^^^^^^^^

Print warnings for every undocumented item encountered.

.. _cli-quiet:

``-q``/``--quiet``
^^^^^^^^^^^^^^^^^^

Do not print any description of progress.

.. _cli-no-search:

``--no-search``
^^^^^^^^^^^^^^^

Do not create the search feature in the documentation. As creating this
is time-consuming, it may be useful to turn it off if your project is
large.

.. _cli-graph:

``-g``/``--graph``
^^^^^^^^^^^^^^^^^^

Enable graph generation. This only overrides the value in the project
file if the file specifies ``graph: false``. If the project file
specifies ``graph: true``, running FORD without this flag will still
generate graphs.

.. _cli-debug:

``--debug``
^^^^^^^^^^^

Allows FORD to crash and display a Python backtrace if an error is
encountered when parsing a file.

.. _cli-project_file:

project_file
^^^^^^^^^^^^

The file containing a description of your project and various settings
for FORD.

--------------

Settings specified at the command-line will override those specified in
the project file.
