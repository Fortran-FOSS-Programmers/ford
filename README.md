#FORD
This is an automatic documentation generator for modern Fortran programs.
FORD stands for FORtran Documenter. As you may know, "to ford" refers to
crossing a river (or other body of water). It does not, in this context, refer
to any company or individual associated with cars.

##Basic Usage

##Options

##Documentation Syntax

##ToDo
This software is still extremely young and much remains to be done. Immediate
goals are:

- Fix the documentation for any procedures which are passed as arguments.
  Currently they will show up in the header for a procedure, but not in the
  detailed list of arguments.
- Add try/except structures so that FORD will be able to exit gracefully
  from any errors.
- Write proper documentation.
- Add a list of modules used to the output.
- Place my custom CSS within its own file rather than just in the header of
  my base HTML template.
- Assemble a list of dependencies.
- Add support for someone providing a custom CSS file.
- Display meta-data for more types of objects.
- Add a better footer for pages.

The completion of (most of) these goals should be doable quite quickly. At this
point FORD will have reached v0.2. Some longer-term goals include:

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

Things which ideally I would do, but are not currently on the radar include:
- Add the ability for people to customize the output more (this would require
  drastic changes to the template system).
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

