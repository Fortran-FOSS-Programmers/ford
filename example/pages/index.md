title: Notes
author: Jane Bloggs
copy_subdir: ../images
ordered_subpage: subpage2.md
ordered_subpage: subpage1.md
---

You can also add additional documentation as static pages by
specifying `page_dir` in your project file. See [the documentation on
static pages][1] for more details.

This image has been included by copying a whole directory, using
`copy_subdir: ../images`:

![Fortran Logo](../images/Fortran_logo.svg)

This directory has subpages, including some where the ordering is
specified using `ordered_subpage`. The [static pages docs][1] have more information on how
this works.

[1]: https://forddocs.readthedocs.io/en/latest/user_guide/writing_pages.html
