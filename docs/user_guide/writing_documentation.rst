=======================
 Writing Documentation
=======================

FORD usage is based on *projects*. A project is just whatever piece of
software you want to document. Normally it would either be a program
or a library. Each project will have its own `Markdown
<http://daringfireball.net/projects/markdown/syntax>`__ file which
contains a description of the project. For details on some of the
non-Markdown syntax which can be used with FORD, see below. Various
`options <sec-project-options>` can be specified in this file,
such as where to look for your projects source files, where to output
the documentation, and information about the author. See
`example-project-file.md
<https://github.com/Fortran-FOSS-Programmers/ford/blob/master/example/example-project-file.md>`__
for a sample project file.

Other documentation is placed within the code. This is described in more
detail below.

Indicating Documentation
------------------------

In modern (post 1990) Fortran, comments are indicated by an
exclamation mark (``!``). FORD will ignore a normal comment like
this. However, comments with two exclamation marks (``!!``) are
interpreted as documentation and will be captured for inclusion in the
output. If desired, the character(s) designating documentation
`can be changed <option-docmark>`. By default, FORD documentation
comes *after* whatever it is that you are documenting, either at the
end of the line or on a subsequent line. This was chosen because it
was felt it is easier to make your documentation readable from within
the source-code this way. This::

   subroutine feed_pets(cats, dogs, food, angry)
       !! Feeds your cats and dogs, if enough food is available. If not enough
       !! food is available, some of your pets will get angry.

       ! Arguments
       integer, intent(in)  :: cats
           !! The number of cats to keep track of.
       integer, intent(in)  :: dogs
           !! The number of dogs to keep track of.
       real, intent(inout)  :: food
           !! The ammount of pet food (in kilograms) which you have on hand.
       integer, intent(out) :: angry
           !! The number of pets angry because they weren't fed.
           
       !...
       return
   end subroutine feed_pets

looks better/more readable than::

   !! Feeds your cats and dogs, if enough food is available. If not enough
   !! food is available, some of your pets will get angry.
   subroutine feed_pets(cats, dogs, food, angry)

       ! Arguments
       !! The number of cats to keep track of.
       integer, intent(in)  :: cats
       !! The number of dogs to keep track of.
       integer, intent(in)  :: dogs
       !! The ammount of pet food (in kilograms) which you have on hand.
       real, intent(inout)  :: food
       !! The number of pets angry because they weren't fed.
       integer, intent(out) :: angry
           
       !...
       return
   end subroutine feed_pets

in the opinion of this author, especially with regards to the list of
arguments. Since version 1.0.0 it is now possible to place
documentation before the code which it is documenting. To do so, use
the ``predocmark``, which is set to ``>`` by default (it may be
changed in the specify in the meta-data of your `project file
<sec-project-options>`).  In the first line of your preceding
documentation, use ``!>`` rather than the usual ``!!``. This can be
used on all lines of the preceding documentation if desired, but this
is not necessary.

For longer blocks of documentation, it can be inconvenient to
continually type the “docmark”. For such situations, the ``docmark_alt``
(set to ``*`` by default) may be used in the first line of the
documentation comment. Any immediately following lines containing only a
comment will then be included in the block of documentation, without
needing the “docmark”. The same effect can be achieved for preceding
documentation by using the ``predocmark_alt``, set to ``|`` by default.
Both of these may be changed in the project file meta-data.

Legacy fixed-form FORTRAN code is now supported, using the `fixed2free
<https://github.com/ylikx/fortran-legacy-tools/tree/master/fixed2free>`__
utility. Files with extensions ``.f``, ``.for``, ``.F``, or ``.FOR``
are interpreted as fixed-form, but these settings can be changed in
the `project file <option-fixed_extensions>`. However, from a
stylistic point of view, it is strongly recommended that free-form
Fortran is used for all new code; this feature has only been added to
support legacy code.

By default, FORD will preprocess any files with extensions ``.F90``,
``.F95``, ``.F03``, ``.F08``, ``.F15``, ``.F``, or ``.FOR`` prior to
parsing them for documentation. This behaviour can `be
disabled <option-preprocess>`
or `different
extensions <option-fpp_extensions>`
can be specified, if desired. Note that any syntax-highlighted source
code which is displayed in the output will be shown in its
non-preprocessed form. The default preprocessor is CPP in legacy mode
(the same as used by gfortran), but arbitrary preprocessors may be
specified.

Markdown
--------

All documentation, both that provided within the source files and that
given in the project file, should be written in
`Markdown <http://daringfireball.net/projects/markdown/syntax>`__. In
addition to the standard Markdown syntax, you can use all of the
features in Python’s `Markdown
Extra <https://pythonhosted.org/Markdown/extensions/extra.html>`__.
Other Markdown extensions automatically loaded are
`CodeHilite <https://pythonhosted.org/Markdown/extensions/code_hilite.html>`__
which will provide syntax highlighting for any code fragments you place
in your documentation and
`Meta-Data <https://pythonhosted.org/Markdown/extensions/meta_data.html>`__.
The latter is used internally as a way for the user to provide extra
information to and/or customize the behaviour of FORD (see
[[Documentation Meta-Data]]). Information on providing meta-data and
what types of data FORD will look for can be found in the next section.

LaTeX Support
-------------

You can insert LaTeX into your documentation, which will be rendered
by `MathJax <http://docs.mathjax.org>`__. Inline math is designated by
``\(...\)``, math displayed on its own line is indicated by
``$$...$$`` or ``\[...\]``, and a numbered equation is designated by
``\begin{equation}...\end{equation}``. Inline math will not be
displayed with the traditional ``$...$``, as there is too much risk
that dollar signs used elsewhere will be misinterpreted. You can refer
back to number equations as you would in a LaTeX document. For more
details on that feature, see the `MathJax Documentation
<http://docs.mathjax.org/en/latest/input/tex/eqnumbers.html>`__.

Special Environments
--------------------

Much like in Doxygen, you can use a ``@note`` environment to place the
succeeding documentation into a special boxed paragraph. This syntax may
be used at any location in the documentation comment and it will include
as the note’s contents anything until the first use of ``@endnote``
(provided there are no new ``@note`` or other environments, described
below, started before then). If no such ``@endnote`` tag can be found
then the note’s contents will include until the end of the paragraph
where the environment was activated. Other environments which behave the
same way are ``@warning``, ``@todo``, and ``@bug``.

Note that these designations are case-insensitive (which, as Fortran
programmers, we’re all used to). If these environments are used within
the first paragraph of something’s documentation and you do not manually
specify a summary, then the environment will be included in the summary
of your documentation. If you do not want it included, just place the
environment in a new paragraph of its own.

“Include” Capabilities
----------------------

FORD uses Chris MacMackin's `Markdown-Include
<https://github.com/cmacmackin/markdown-include>`__ extension. The
syntax ``{!file-name.md!}`` in any of your documentation will be
replaced by the contents of file-name.md. This will be the first thing
done when processing Markdown, and thus all Markdown syntax within
file-name.md will be processed correctly. You can nest these include
statments as many times as you like. All file paths are evaluated
relative to the directory containing the project file, unless set to
do otherwise.

Environment Variables
---------------------

FORD uses Chris MacMackin's `ford.md_environ` extension (bundled with
FORD). The syntax ``${ENVIRONMENT_VAR}`` will be replaced by the
contents of environment variable ``ENVIRONMENT_VAR`` if it is defined,
or an empty string otherwise.

Aliases
-------

FORD allows the use of text macros or aliases to substitute for common
snippets, such as URLs. These are handy for internal links in the
documentation, such as to the `static pages <sec-writing-pages>`.
There are three predefined macros:

- ``|url|``: the `project URL <option-project_url>`
- ``|media|``: the (absolute) path to the `media directory <option-media_dir>`
- ``|page|``: the `static page directory <option-page_dir>`

You can defined additional custom aliases with the `alias
<option-alias>` option.

.. _writing-links:

Links
-----

In addition to conventional Markdown links, FORD provides its own syntax
for linking to other parts of the documentation. The general syntax for
this is ``[[component(type):item(type)]]``:

-  ``component`` is the name of the component of your project’s code
   whose documentation is to be linked to. It could be a procedure,
   module, or anything else with its own page of documentation. This is
   the only item which is mandatory.
-  ``type`` (optional) is ``component``\ ’s type of Fortran construct.
   This is necessary if you have multiple items with the same name (such
   as a type and its public constructor). If multiple items with the
   same name exist and ``type`` is not specified then FORD’s behaviour
   is undefined; it will link to the first of those items which it
   finds. The available options are “procedure”, “subroutine”,
   “function”, “proc” (all of which are interchangeable and specify a
   procedure), “interface”, “absinterface” (both of which are for
   abstract interfaces), “block” (for the legacy ``block data`` program
   unit), and “type”, “file”, “module”, and “program” (which are
   self-explanatory).
-  ``item`` (optional) specifies an item within ``component`` which is
   to be linked to. The link’s target will be ``item``\ ’s location on
   ``component``\ ’s page. If ``item`` is not present then the colon in
   the link must be omitted.
-  ``type`` (optional, but ``item`` must also be present) is
   ``item``\ ’s type of Fortran construct. It can be used in the same
   manner as the component ``type``, but has different options. These
   are “variable”, “type”, “constructor”, “interface”, “absinterface”
   (abstract interface), “subroutine”, “function”, “final” (finalization
   procedure), “bound” (type-bound procedure), “modproc” (module
   procedure in a generic interface block), and “common”. None of these
   options are interchangeable. If no description is given then its
   meaning should be self-explanatory. If you specify an option that can
   not exist within ``component`` (for example, if ``component`` is a
   module and ``item`` is “bound”) then a warning message is issued and
   the link is not generated.

If you have an overridden constructor a derived type, then it is
strongly recommended that you specify ``item`` should you wish to link
to either of them. Otherwise FORD will not know whether you are
referring to the derived type itself or the interface for its
constructor.

.. _non-fortran-source-files:

Non-Fortran Source Files
------------------------

As of version 4.5.0, FORD now offers limited support for non-Fortran
source files. While it will not analyze the code within such files, it
can extract documentation for the file as a whole and display it on its
own page, as done for Fortran source files. An attempt will also be made
to apply syntax highlighting to the contents of the file (although this
may fail if non-standard file extensions are used). This may be useful
for documenting build scripts or C wrappers.

To use this feature, the option ``extra_filetypes`` should be specified
in the `project
file <option-extra_filetypes>`.
It can hold multiple values, each of which should be on its own line.
Entries consist of the extension for the file-type which FORD is to
analyze and the comment character(s), separated by a space. FORD only
supports single-line comments. An example entry of this sort is

.. code:: text

   extra_filetypes: c   //
                    sh  #
                    py  #
                    tex %

To write documentation in these files, simply place one of the usual
documentation characters after the specified comment characters. Note
that the default documentation marker could cause problems in source
files using a “shebang” at the start.

**Experimental:** You can now explicitly specify the
`lexer <http://pygments.org/docs/lexers/>`__ for syntax highlighing by
adding its name next to the comment symbol:

.. code:: text

   extra_filetypes: inc ! fortran.FortranFixedLexer
