#FORD
This is an automatic documentation generator for modern Fortran programs.
FORD stands for FORtran Documenter. As you may know, "to ford" refers to
crossing a river (or other body of water). It does not, in this context, refer
to any company or individual associated with cars.

##Basic Usage

##Options

##Documentation Syntax

##ToDo
This software is still extremely young and much remains to be done. Various
things which I'd like to do at some point include:

- Write proper documentation.
- Assemble a list of dependencies.


- Support some of the old Fortran 77 ways of doing things, as these are often
  still used. This includes PARAMETER statements, EXTERNAL statements.
- Add the ability to produce dependency diagrams and inheritance diagrams for
  modules and types, respectively.
- Make more options configurable from the command-line.
- Integrate the Pelican MathJax plugin.
- Add MathJax support.
- Add a search feature.
- Test on some more code, including that of other people, who may have different
  coding styles.
- Add the ability to identify function calls and use this to work out
  call-trees (subroutine calls are already captured).
- Add the option for users to specify a Creative Commons license for their
  documentation, which will be inserted into the page footer.
- Make it possible to over-ride the display options within  a particular
  part of the code and for an individual item within the code.
- Provide an option to force all (non-string) text which is captured to be
  lower case.
- Add the ability to recognize the use of intrinsic modules
- Improve the handling of parameterized derived types, particularly for
  variables of that type.
- Improve the sidebar for source files so that it will link to the items that it
  lists.
- Allow the user to provide a favicon.
- Provide a directory in which the user can place any images and/or other
  media they want available.
- Use summaries of the description in some places
- Improve the way procedures are handled as arguments. In particular, allow
  any abstract interface which was used as a template to be visible somehow.

Things which ideally I would do, but are not currently on the radar include:

- Add the ability for people to customize appearance of the output more (this
  would require drastic changes to the template system).
- Support fixed-form Fortran (doable, but low priority).
- Add the ability to identify type-bound procedure calls and use these to
  construct call-trees. This would be extremely difficult, as it would
  require keeping track of names and types of variables throughout the code.


##Approach
The basic algorithm for generating the documentation is as follows:

- Get instructions from user. These are to be passes as command-line arguments.
  At some future time it might be nice to provide the option of a config file,
  but for a CLI will be fine.
- Parse each file which is to be documented.

   - Create a file object. This will contain any documentation meant for the
     file as a whole and a list of any file contents.
   - Create module, subroutine, function, and/or program objects for each of
     these structures within the file. Each of these objects will also store
	 comments, contents, and parameters.
   - Continue to recurse into these structures, adding interface, type,
     variable, subroutine and function objects as necessary.

- Perform further analysis on the parsed code, correlating anything defined
  in one place but used in another. This will be used to generate hyperlinks
  when producing the documentation.
- Convert comments into HTML. Assume that they have been written in Markdown.
  Also make sure to process LaTeX. Consider how images will be handled. Perhaps
  the user should specify a directory where they are stored which will then
  be copied into the output directory (a bit like how Pelican works)?
- Produce the documentation. This will be done using Jinja2 templates. Perhaps
  allow the user to provide their own template, if desired.

