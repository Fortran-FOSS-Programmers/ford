.. _sec-project-options:

======================
 Project File Options
======================

You can specify various options and information for your project in the
meta-data of your project file. Quoting from the `Markdown
Meta-Data <https://pythonhosted.org/Markdown/extensions/meta_data.html>`__
page (and not intending to give an example of the meta-data fields
supported by FORD):

Meta-data consists of a series of keywords and values defined at the
beginning of a markdown document like this:

.. code:: text

   Title:   My Document
   Summary: A brief description of my document.
   Authors: Waylan Limberg
            John Doe
   Date:    October 2, 2007
   blank-value:
   base_url: http://example.com

   This is the first paragraph of the document.

The keywords are case-insensitive and may consist of letters,
numbers, underscores and dashes and must end with a colon. The values
consist of anything following the colon on the line and may even be
blank.

If a line is indented by 4 or more spaces, that line is assumed to be
an additional line of the value for the previous keyword. A keyword
may have as many lines as desired (note that these **must** be
spaces and not tabs).

The first blank line ends all meta-data for the document. Therefore,
the first line of a document must not be blank. All meta-data is
stripped from the document prior to any further processing by
Markdown.

Project file options will be overriden by `command line options
<sec-command-line-options>` .See `./example/example-project-file.md
<https://github.com/Fortran-FOSS-Programmers/ford/blob/master/example/example-project-file.md>`__
for a sample project file.

Except where noted, all paths in options are interpreted relative to the path of
the project file.

*N.B.!*: Markdown comments must not appear within the meta data section!
Typical markdown commenting strategies may be used within the markdown
body of the project file, BUT NOT WITHIN THE META-DATA SECTION! After
declaring meta-data HTML block comments of the form

.. code:: html

   <!-- This is a multi line
   comment!

   wow
   -->

or markdown phony link comments may be used:

.. code:: markdown

   [comment 1 goes here, this will declare a phony link target. Just make sure not to reference the null anchor]:#

The options which can be specified in the meta-data are listed below.
Defaults are included in the description, if they exist.

Project Information
-------------------

Information about your project.

.. _option-doc_license:

doc_license
^^^^^^^^^^^

The license under which the *documentation* is released. See `option-license`
for possible values.

.. _option-favicon:

favicon
^^^^^^^

The path to a custom favicon which will be used by the HTML
documentation. If left blank, it will default to an icon for FORD.

.. _option-gitter_sidecar:

gitter_sidecar
^^^^^^^^^^^^^^

The name of the project’s chatroom on `Gitter <https://gitter.im>`_,
which can then be displayed using the Gitter
`sidecar <https://sidecar.gitter.im/>`_.

.. _option-license:

license
^^^^^^^

The licenses under which the software is released. Options are:

- **bsd**: `FreeBSD Documentation License <http://www.freebsd.org/copyright/freebsd-doc-license.html>`_
- **by**: `Creative Commons attribution <http://creativecommons.org/licenses/by/4.0/>`_
- **by-nc**: `Creative Commons attribution, non-commercial <http://creativecommons.org/licenses/by-nc/4.0/>`_
- **by-nc-nd**: `Creative Commons attribution, non-commercial, non derivatives <http://creativecommons.org/licenses/by-nc-nd/4.0/>`_
- **by-nc-sa**: `Creative Commons attribution, non-commercial, share-alike <http://creativecommons.org/licenses/by-nc-sa/4.0/>`_
- **by-nd**: `Creative Commons attribution, no derivatives <http://creativecommons.org/licenses/by-nd/4.0/>`_
- **by-sa**: `Creative Commons attribution, share-alike <http://creativecommons.org/licenses/by-sa/4.0/>`_
- **gfdl**: `GNU Free Documentation License <http://www.gnu.org/licenses/old-licenses/fdl-1.2.en.html>`_
- **isc**: `ISC (Internet Systems Consortium) License <https://opensource.org/licenses/ISC>`_
- **mit**: `MIT <https://opensource.org/licenses/MIT>`_
- **opl**: `Open Publication License <http://opencontent.org/openpub/>`_
- **pdl**: `Public Documentation License <http://www.openoffice.org/licenses/PDL.html>`_

.. _option-privacy_policy_url:

privacy_policy_url
^^^^^^^^^^^^^^^^^^

URL of the privacy policy of the project.

.. _option-project:

project
^^^^^^^

The name of this project. (*default:* Fortran Project)

.. _option-project_bitbucket:

project_bitbucket
^^^^^^^^^^^^^^^^^

The URL of the BitBucket repository for this project.

.. _option-project_download:

project_download
^^^^^^^^^^^^^^^^

A URL from which to download the source or binaries for this project.

.. _option-project_github:

project_github
^^^^^^^^^^^^^^

The URL of the Github repository for this project.

.. _option-project_gitlab:

project_gitlab
^^^^^^^^^^^^^^

The URL of the Gitlab repository for this project.

.. _option-project_sourceforge:

project_sourceforge
^^^^^^^^^^^^^^^^^^^

The Sourceforge repository for this project.

.. _option-project_url:

project_url
^^^^^^^^^^^

The URL at which the documentation will be available. If left blank then
relative URLs will be used for links. This can be used within any documentation
with the `macro <option-macro>` ``|url|``. (*default:* blank, i.e. relative
links)

.. _option-project_website:

project_website
^^^^^^^^^^^^^^^

The homepage for this project.

.. _option-summary:

summary
^^^^^^^

A summary of the description of your project. If present it will be
printed in a “Jumbotron” element at the top of the documentation index
page. This will be processed by Markdown before being used.

.. _option-terms_of_service_url:

terms_of_service_url
^^^^^^^^^^^^^^^^^^^^

URL of the terms of service of the project

Author Information
------------------

Information about the author.

.. _option-author:

author
^^^^^^

The name of the person(s) or organization who wrote this project.

.. _option-author_description:

author_description
^^^^^^^^^^^^^^^^^^

A brief description of the author. You could provide biographical
details or links to other work, for example. This will be processed by
Markdown before being used.

.. _option-author_pic:

author_pic
^^^^^^^^^^

A picture of or avatar for the author.

.. _option-bitbucket:

bitbucket
^^^^^^^^^

The author’s BitBucket page.

.. _option-email:

email
^^^^^

The author’s email address.

.. _option-facebook:

facebook
^^^^^^^^

The author’s Facebook profile.

.. _option-github:

github
^^^^^^

The author’s Github page.

.. _option-gitlab:

gitlab
^^^^^^

The author’s Gitlab page.

.. _option-google_plus:

google_plus
^^^^^^^^^^^

The author’s Google+

.. _option-linkedin:

linkedin
^^^^^^^^

The author’s LinkedIn profile.

.. _option-twitter:

twitter
^^^^^^^

The author’s Twitter.

.. _option-website:

website
^^^^^^^

The author’s website.

Directories
-----------

Settings specifying where to look (and not to look) for documentation.

.. _option-copy_subdir:

copy_subdir
^^^^^^^^^^^

A list of subdirectories to copy verbatim into the generated documentation. See
`sec-copy_subdir` for a more detailed explanation of this option. (*optional*)


.. _option-exclude_dir:

exclude_dir
^^^^^^^^^^^

Directories whose contents should not be included in documentation. Each
excluded directory must be on its own line. Provide the relative path to
directory from the top level project file.

.. _option-include:

include
^^^^^^^

Directories in which the C preprocessor searches for any
``#include``\ ed files, such as headers. These directories will also be
searched for files loaded using Fortran’s intrinsic ``include``
statement. Each directory must appear on its own line.

.. _option-media_dir:

media_dir
^^^^^^^^^

A directory containing any images or other content which you will use or link to
in your documentation. This will be placed at the root of your documentation
file-tree, with the name “media”. The URL of this directory can be accessed
within your documentation using the `macro <option-macro>`
``|media|``.

.. _option-md_base_dir:

md_base_dir
^^^^^^^^^^^

The directory relative to which any “included” Markdown files’ paths are
specified. (*default:* directory containing the project file.)

.. _option-page_dir:

page_dir
^^^^^^^^

A directory containing markdown files to be processed into individuals
pages within the documentation. See `sec-writing-pages` for details.

.. _option-src_dir:

src_dir
^^^^^^^

The directories where the source-files are to be found for this project.
These must not be a subdirectory of the output_dir (see below). Multiple
directories can be listed, each on their own line. (*default:* ./src)

Source File Settings
--------------------

Settings related to individual source files.

.. _option-encoding:

encoding
^^^^^^^^

The text encoding to use when opening source files (*default*: ``utf-8``)

.. _option-exclude:

exclude
^^^^^^^

Source files which should not be included in documentation. Each
excluded file must be on its own line. Provide only the file-name, not
the full path.

.. _option-extensions:

extensions
^^^^^^^^^^

File extensions which will be read by FORD for documentation. Each
extension must be on its own line. These extensions are only for
free-form code; see `option-fixed_extensions` for fixed-form
extensions. (*default:* f90, f95, f03, f08, f15, F90, F95, F03, F08,
F15)

.. _option-extra_filetypes:

extra_filetypes
^^^^^^^^^^^^^^^

Non-Fortran source files from which documentation should be extracted
(see `non-fortran-source-files`). Multiple values may be provided,
each on its own line. Each entry should consist of the extension of
the file-type to be documented, a space, and then the character(s)
designating a comment within such a file. Only single-line comments
are supported.

*Experimental:* You may optionally specify the `Pygments
lexer <http://pygments.org/docs/lexers/>`__ to use when applying
syntax-highlighting to the file, as an additional argument after the
comment character. This should take the form of the module being
imported relative to ``pygments.lexer``. E.g. ``fortran.FortranLexer``
or ``c_cpp.CLexer``. This feature should not be considered stable and
the behaviour may change in future releases.

.. _option-fixed_extensions:

fixed_extensions
^^^^^^^^^^^^^^^^

File extensions which will be read by FORD for documentation, with the
files containing fixed-form code. (*default*: f, for, F, FOR)

.. _option-fixed_length_limit:

fixed_length_limit
^^^^^^^^^^^^^^^^^^

If false, fixed-form code lines are read in their entire length.
Otherwise anything after the 72nd column is ignored. (*default:* true)

Preprocessing
-------------

If desired, your source files can be passed through an arbitrary
preprocessor before being analysed by FORD.

.. _option-fpp_extensions:

fpp_extensions
^^^^^^^^^^^^^^

File extensions which should be preprocessed prior to further analysis.
If the extension is not specified in
`extensions <option-extensions>`
or
`fixed_extensions <option-fixed_extensions>`
then the file will be assumed to be free-form. (*default:* F90, F95,
F03, F08, F15, F, FOR)

.. _option-macro:

macro
^^^^^

Macros to be provided to the C preprocessor when applying it to source
files. Can take the form ``mac-name`` or ``mac-name=mac-value``. Each
macro must appear on its own line.

.. _option-preprocess:

preprocess
^^^^^^^^^^

If set to ‘true’, then any files with extensions in
`fpp_extensions <option-fpp_extensions>`
will be passed through the specified preprocessor, CPP by default.
(*default:* true)

.. _option-preprocessor:

preprocessor
^^^^^^^^^^^^

The preproccessor command to use on files with extensions in `fpp_extensions
<option-fpp_extensions>`. Can include flags as needed. Preprocessor macros and
include paths specified in the project file will automatically be appended using
the CPP interface, which is fairly standard. (*default*:
``cpp -traditional-cpp -E -D__GFORTRAN__``)

Documentation Markers
---------------------

.. _option-docmark:

docmark
^^^^^^^

The symbol(s) following an exclaimation mark which designates that a
comment contains documentation. For excample, if the docmark was ``!``,
comments would then be designated by ``!!``. It should not be the same
as any other docmark. (*default:* ``!``)

.. _option-docmark_alt:

docmark_alt
^^^^^^^^^^^

The symbol(s) following an exclaimation mark which designate that the
following set of comments, until the end of the block, are all
documentation. This mark needs only to be used at the beginning of the
block, after which all regular comments will be treated as
documentation. For excample, if the docmark was ``*``, comments would
then be designated by ``!*``. An example of such a block of
documentation is provided.

.. code:: fortran

   !* This is an example.
   !  Here is another line of comments.
   !
   !  History
   ! ----------
   !  * 1/1/2000 Created

   subroutine blah()

   end subroutine blah

It should not be the same symbol as any other docmark. (*default:*
``*``)

.. _option-predocmark:

predocmark
^^^^^^^^^^

The symbol(s) following an exclaimation mark which designates that a
comment contains documentation preceding the code which it is
documenting. For excample, if the docmark was ``>``, comments would then
be designated by ``!>``. It should not be the same as any other docmark.
(*default:* ``>``)

.. _option-predocmark_alt:

predocmark_alt
^^^^^^^^^^^^^^

The symbol(s) following an exclaimation mark which designate the start
of a block of documentation preceding the code which it is documenting
and that all further comments within this block will be treated as
documentation. For example, if the predocmark_alt was ``#``, comments
would then be designated by ``!#``. It should not be the same as any
other docmark. (*default:* ``|``)

Documentation Settings
----------------------

Settings specifying how to process documentation and what information to
display in the output.

.. _option-alias:

alias
^^^^^

List of aliases in the form ``key = replacement``. In the documentation
``|key|`` can then be used as shorthand for ``replacement``. For
example:

.. code:: markdown

   alias: ford = FORD (the Fortran documentation generator)
          euler = \exp(i \pi) + 1 = 0


   This code uses |ford|.
   Did you know Euler's identity is $$|euler|$$?

becomes:

.. code:: markdown

   This software uses FORD (the Fortran documentation generator).
   Did you know Euler's identity is $$\exp(i \pi) + 1 = 0$$?

Three aliases are pre-defined: ``|url|`` for the project URL,
``|media|`` for the media directory and ``|page|`` for the ``page_dir``.

Note:
'''''

Aliases can currently only be defined in the project file, and not in
individual docstrings

.. _option-creation_date:

creation_date
^^^^^^^^^^^^^

A Python `datetime
format <https://docs.python.org/3/library/datetime.html#strftime-and-strptime-behavior>`__
to be used if the date and time at which the documentation was generated
is printed in the documentation footer. (*default*:
``%Y-%m-%dT%H:%M:%S.%f%z``)

.. _option-css:

css
^^^

The path to a custom style-sheet which can be used to modify the
appearance of the output.

.. _option-display:

display
^^^^^^^

How much documentation should be printed. Options are ‘public’,
‘private’, ‘protected’, or any combination of those three. Each choice
must be on its own line. If ‘none’ is present, then nothing will be
displayed other than the programs, modules, and procedures contained
within source files (i.e. procedures within modules will not be
displayed). These choice can be overridden for a specific item using
the `documentation meta data <metadata-display>`, and those settings
will be inherited by any items they contain. (*default:* ‘public’ and
‘protected’)

.. _option-external:

external
^^^^^^^^

Paths or URLs of external projects to link to. If an entity is not found in the
sources, FORD will try to look it up in those external projects. If those have
documentation generated by FORD with the externalize option, a link will be
placed into the documentation wherever this entity is referred to. FORD will
look in the provided paths for a ``modules.json`` file.

The difference between ``external`` between ``extra_mods`` is that FORD can link
directly to entities (functions, types, and so on) with ``external``, while only
modules will be linked to using ``extra_mods``.

.. _option-extra_mods:

extra_mods
^^^^^^^^^^

A list of modules (and their external documentation) which are not
included in the project. An entry takes the form ``module_name:url``
where ``module_name`` is its name as it would appear in a ``use``
statement, and ``url`` is the location of its documentation. Any entity
which uses this module will provide a link to the external documentation
in the same way that it would provide a link to the documentation of a
module in the project.

.. _option-extra_vartypes:

extra_vartypes
^^^^^^^^^^^^^^

Any extra types of variables which FORD should look for. This can be
useful when using, for example, the PETSc library. Each variable type
must be on its own line.

.. _option-hide_undoc:

hide_undoc
^^^^^^^^^^

If ``true``, then don't display any undocumented entities (*default*: ``false``)

.. _option-incl_src:

incl_src
^^^^^^^^

This flag toggles visibility of the source files in FORD documentation
output. If set to ``true``, the individual files will be listed and
all contents will be shown on a file page. If ``false``, procedures
will still show the names of the files they are defined in, but there
will be no way to access the contents of the file itself. For showing
the code definitions for individual procedures, modules, and derived
types, see `option-source`. (*default*: ``true``)

.. _option-lower:

lower
^^^^^

If ``true`` then convert all non-string and non-comment source code to
lower case prior to analyzing. (*default*: ``false``)

.. _option-mathjax_config:

mathjax_config
^^^^^^^^^^^^^^

The path to a JavaScript file containing `settings for MathJax
<https://docs.mathjax.org/en/latest/configuration.html#using-plain-javascript>`__.
This might be used to, e.g., `define TeX macros
<https://docs.mathjax.org/en/latest/tex.html#defining-tex-macros>`__.

.. _option-max_frontpage_items:

max_frontpage_items
^^^^^^^^^^^^^^^^^^^

The maximum number of items to list under each category of entity on the front
page. (*default*: 10)

.. _option-md_extensions:

md_extensions
^^^^^^^^^^^^^

The name of any Markdown extensions which you wish to be used when
parsing your documentation. For example, ``markdown.extensions.toc``. Note
that Markdown-Extra, CodeHilite, and Meta-Data are loaded by default.

.. _option-print_creation_date:

print_creation_date
^^^^^^^^^^^^^^^^^^^

If ``true`` then will print the date and time of creation, using the
specified `date format <option-creation_date>`, in the footer of each
page of documentation. (*default*: ``false``)

.. _option-proc_internals:

proc_internals
^^^^^^^^^^^^^^

If ``false`` then the local variables, derived types, etc. within
public procedures will not be included in documentation. This is
equivalent to setting ``display: none`` in the documentation meta data
of each procedure. It can be overriden locally in the `documentation
meta data <metadata-proc_internals>`.  (*default*: ``false``)

.. _option-revision:

revision
^^^^^^^^

The name of the particular revision of your code/documentation, to be
printed in the footer below the license and copyright year.

.. _option-search:

search
^^^^^^

If ``true`` then add a search feature to the documentation. This can
be time-consuming, so you may want to turn it off for large
projects. Note that this process can be sped up if the `lxml
<http://lxml.de/>`__ library is installed. (*default*: ``true``)

.. _option-sort:

sort
^^^^

The order in which to display entities (variables, procedures, etc.) in
the documentation. Options are (*default:* ``src``)

* ``src``: Order which they occur in source code
* ``alpha``: Alphabetical order
* ``permission``: Display public first, then protected, then private.
  Within these categories, items are displayed in the same order as
  they occur in the source code.
* ``permission-alpha``: Display public first, then protected, then
  private. Within these categories, items are displayed in
  alphabetical order.
* ``type``: Sort variables (and functions) by type. For each time,
  items are displayed in the same order as they occur in the source
  code
* ``type-alpha``: Sort variables (and functions) by type. Within these
  categories, items are displayed in alphabetical order.

.. _option-source:

source
^^^^^^

If set to ‘true’, then the syntax-highlighted source code will be
displayed at the bottom of the documentation page for each procedure,
program, and derived type. This behaviour can be overridden for a
given item using the `documentation meta data <metadata-source>`.
FORD may not be able to extract the source code in all cases; see
`metadata-source` for details. To hide source files themselves, see
`option-incl_src`.  Note that this substantially increases
run-time. (*default:* ``false``)

.. _option-version:

version
^^^^^^^

The version name/number of your project.

.. _option-year:

year
^^^^

The year to display in the copyright notice. (*default:* the current
year)

Graph Settings
--------------

FORD can generate call-trees, dependency diagrams, and inheritance
diagrams will be produced for the project. These require
`Graphviz <http://graphviz.org/>`__ to be installed. Note that this can
increase run-time substantially. The following graphs are produced: -
For each module: - a graph showing the modules which it ``use``\ s and,
if a submodule, the (sub)modules it is descended from - a graph showing
which modules ``use`` and which submodules descend from this one - For
each type: - a graph showing all type which it descends from or contains
as a component - a graph showing all types which descend from or contain
as a component this type - For each procedure: - a graph showing all
procedures called by this procedure and (for interfaces) any procedures
which it provides an interface to - a graph showing all procedures which
call this one or provide and interface to it - For each program: - a
graph showing the modules which are ``use``\ d by the program - a graph
showing the procedures called by the program - A graph showing all
module ``use`` dependencies on the module list page - A graph showing
the inheritance structure of all derived types (and their use as
components of other types) on the type list page - A graph showing the
call-tree for all programs and procedures on the procedure list page

Note that, at present, call-trees only work for procedural programming
and will not identify any calls to type-bound procedures. Call-trees are
not supposed to show intrinsic procedures. However, intrinsic procedures
and even keywords may appear in a grey node on the graph. This means
that it this procedure was not known (or overlooked) by the developers.
Please report this is a bug. (*default:* ``false``)

.. _option-coloured_edges:

coloured_edges
^^^^^^^^^^^^^^

If ``true`` then edges connecting nodes in the graphs will be assigned
various colours. This can make large graphs easier to read. Americans,
please note that the proper spelling has been used here. (*default*:
``false``)

.. _option-graph:

graph
^^^^^

If set to ‘true’ then graphs are produced of call trees, dependency
structures, and inheritance diagrams. This behaviour can be overridden
for a given item in the code using the `documentation meta data
<metadata-graph>`.  (*default:* ``false``)

.. _option-graph_maxdepth:

graph_maxdepth
^^^^^^^^^^^^^^

The maximum number of recursions to make when analysing graph
structures. For large projects, producing graphs can be prohibitively
time-consuming and the graphs confusing and unreadable if full recursion
is used, so you may wish to set the maximum to be only a few levels.
(*default:* 10000)

.. _option-graph_maxnodes:

graph_maxnodes
^^^^^^^^^^^^^^

The maximum number of nodes which may be displayed in a graph. For large
projects, graphs become unreadable if they contain too many nodes. A
graph’s depth will be reduced to keep the number of nodes below this
maximum or, if the even a depth of one would result in more nodes than
the maximum, it will be restructured to give a clearer visualisation.
(*default:* 100000000)

Output
------

Where documentation should be written to.

.. _option-externalize:

externalize
^^^^^^^^^^^

Create a ``modules.json`` file under `option-output_dir` containing information
about entities and the URL of their documentation. This allows this project to
be used as an `option-external` link in another project.

.. _option-graph_dir:

graph_dir
^^^^^^^^^

A directory where, if it is specified and ``graphs`` is set to ``true``,
SVG and graphviz copies of all graphs for your project will be placed.
Note that name mangling is applied to the filenames.

.. _option-output_dir:

output_dir
^^^^^^^^^^

The directory where the project output will be placed. **Any content already
present there will be deleted.** (*default:* ./doc)

Run-Time Behaviour
------------------

Miscellaneous options determining how FORD is run and its output.

.. _option-dbg:

dbg
^^^

Allows FORD to crash and display a Python backtrace if an error is
encountered when parsing a file.

.. _option-force:

force
^^^^^

Try to continue as much as possible, even if there are fatal errors when reading
files.

.. _option-parallel:

parallel
^^^^^^^^

The number of CPUs to in multithreading. 0 indicates that the code
should be run in serial. (*default:* number of cores on the computer)

.. _option-quiet:

quiet
^^^^^

If ‘true’, FORD will suppress all output documenting its progress.
(*default:* false)

.. _option-warn:

warn
^^^^

If ‘true’, FORD will print warning messages for any undocumented items
which it encounters and any time it can not find the source code for
some item where it is requested as part of the documentation.
(*default:* false)
