==================
 Developers Guide
==================

This is a very rough outline of how FORD works internally.

#. Input arguments are parsed and normalised in `parse_arguments`. The
   dictionary of metadata created by `markdown.extensions.meta
   <https://python-markdown.github.io/extensions/meta_data/>`_ is not
   usually in exactly the form we need, so we make sure all the
   arguments are the types we're expecting, and relative paths are
   converted to absolute paths.

#. We then create a `Project`: a collection of all the entities in a
   software project. There is a single `Project` for a given software
   project, but multiple projects can be linked together through the
   `option-externalize` and `option-external` options.

   The project instance iterates over all the source files in
   `option-src_dir` and opens any files with `option-extensions`
   extensions as `FortranSourceFile`, and any with
   `option-extra_filetypes` extensions as `GenericSource`. Fortran
   files with `option-fpp_extensions` are preprocessed using
   `option-preprocessor` first.

#. `FortranSourceFile`: Represents a single Fortran source file. The
   raw source is first fed through `FortranReader` before being parsed
   into an Abstract Syntax Tree (AST) [#f1]_ with `FortranContainer`.

#. `FortranReader`: Custom reader for Fortran files that converts them
   in a normalised form that makes parsing them easier.

#. `FortranContainer`: Represents some kind of Fortran entity that can
   contain other entities: so, things like programs, modules,
   procedures, and types. Variables are *not* represented by
   `FortranContainer`, because they can't contain other entities.

   This class also does the bulk of the parsing into the AST in its
   ``__init__`` constructor. The result is tree of objects, each with
   lists of the various entities they contain. For entities defined in
   the same file, these lists will be the actual objects representing
   those entities; for those defined in other files, they'll just be
   strings for now.

   At the end of parsing a particular entity, its ``_cleanup`` method
   will be called, which will do things like, for example, collating
   all the public entities in a module.

#. After each file has been parsed, the lists of entities are added to
   the `Project`'s lists of all the entities in the whole project.

#. After all the files have been parsed, the documentation comments are
   converted from Markdown to HTML, recursively down from the source
   files. At this point, metadata in the comments is also parsed.

#. Entities defined in other files are now "correlated" with their
   concrete objects. This is done recursively from
   `Project.correlate`, first by finding which modules are ``use``\ d
   by each entity, and then looking up names in the corresponding
   `FortranModule`.

#. Another recursive pass is done of the project to convert internal
   `links <writing-links>` to actual HTML links using `sub_links`.

#. The static pages are processed with `get_page_tree`.

#. `Documentation` then processes the `Jinja2
   <https://jinja.palletsprojects.com/en/3.0.x/>`_ templates to create
   the actual HTML files.

#. Lastly, if requested, the project is dumped to a JSON file using
   `external`. This is not a full dump of the project, but just the
   tree of entities and the paths to their respective documentation.

.. rubric:: Footnotes

.. [#f1] Sort of. It's not the full AST of the file, just of the bits
         FORD needs to know/care about. It's also not really a
         traditional AST, as each node collates the different types of
         entities into separate collections
