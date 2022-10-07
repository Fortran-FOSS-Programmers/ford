========================
 Documentation Metadata
========================

When documenting your source files you can provide meta-data at the top
of an item’s documentation. Meta-data is specified in the same way as in
the [[project file|Project File Options]]. There can not be any other
documentation before it; not even a blank line of documentation. This
will work::

   ! Good
   type :: cat
     !! author: C. MacMackin
     !! version: v0.2
     !!
     !! This data-type represents a cat.

but this won’t::

   ! Bad
   type :: cat
     !!
     !! author: C. MacMackin
     !! version: v0.2
     !!
     !! This data-type represents a cat.

The meta-data will be displayed for procedures, derived types, files,
programs, modules, type-bound procedures, and interfaces. It may be
displayed in more cases in future. Recognized types of meta-data are:

.. _metadata-author:

author
^^^^^^

The author of this part of the code. 

.. _metadata-date:

date
^^^^

The date that this part of the code was written (or that the
documentation was written; whichever makes more sense to you).

.. _metadata-license:

license
^^^^^^^

The license for this part of your code. If you want to provide a link
then it will have to be in HTML, as it won’t be processed by Markdown.

.. _metadata-version:

version
^^^^^^^

The version number (or version name) of this part of the code.

.. _metadata-category:

category
^^^^^^^^

A category for this part of the code. In future, FORD may provide
lists of things in each category. Currently it is primarily
decorative, although it is used when the documentation is being
searched.

.. _metadata-summary:

summary
^^^^^^^

A brief description of this part of the code. If not specified, then
FORD will use the first paragraph of the body of your documentation.

.. _metadata-deprecated:

deprecated
^^^^^^^^^^

If this is present and set to ‘true’ then a label saying “Deprecated”
will be placed in the documentation.

.. _metadata-display:

display
^^^^^^^

Overrides the global display settings specified in the `project file
<option-display>`.  It instructs FORD what items to display
documentation for. Options are ‘public’, ‘private’, ‘protected’, or
any combination of those three.  Additionally, ‘none’ specifies that
nothing contained within this item should have its documentation
displayed (although the item’s own documentation will still be
displayed). The option ‘none’ is ignored in source files. Options will
be inherited by any contents of this item.

.. _metadata-proc_internals:

proc_internals
^^^^^^^^^^^^^^

Overrides the global setting specified in the `project file
<option-proc_internals>` indicating whether to display the local
variables, derived types, etc.  within this procedure. May be ``true``
or ``false``. ``false`` is equivalent to settign ``display: none``.

.. _metadata-source:

source
^^^^^^

Overrides the global source settings specified in the `project file
<option-source>`.  If ‘true’, then the syntax-highlighted source code
for this item will be displayed at the bottom of its page of
documentation. Note that this only applies for procedures, programs,
and derived types. Further note that FORD will not be able to extract
the source code if the name of the item is on a different line from
the type of item or is on a line containing semi-colons. Line
continuation and semi-colons will also prevent extraction from working
if they occur on the closing line of the subroutine. For example::

   subroutine &
     example (a)
     integer, intent(inout) :: a
     a = a + 1
     return
   end subroutine example

However, in the case of procedure’s, the argument list may be on a
different line from the item’s name.

If warnings are turned on at the `command line <ford---warn>` or in the
`project file <option-warn>`, then a message will be produced if an
item’s source code is not successfully extracted.

.. _metadata-graph:

graph
^^^^^

Overrides the global graph settings specified in the `project file
<option-graph>` for this particular entity in the code. If set to
‘false’, it no graphs will be produced on its page of documentation
and it will not be included in any of the project-wide graphs which
are displayed on list pages.
