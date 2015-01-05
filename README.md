#FORD
This is an automatic documentation generator for modern Fortran programs.
FORD stands for FORtran Documenter. As you may know, "to ford" refers to
crossing a river (or other body of water). It does not, in this context, refer
to any company or individual associated with cars.

##Disclaimer
This is a young project. While it has bee tested somewhat, the testing has been
far from comprehensive. Various options have not been tested and obscure uses
of the Fortran syntax could still potentially cause FORD to crash. If you
get an error message while processing a file, first check to make sure that the
file actually compiles. No effort has been made to be able to process files
which contain syntax errors. Next ensure that you aren't using any of the
lingering FORTRAN77 syntax. If you are still experiencing errors, comment
out the ``try``/``except`` statement on lines 59-63 of
./ford/fortran_project.py. Leave only line 60 uncommented. You will probably
need to remove four spaces from line 60's indentation, as well.
This will give you
a proper Python backtrace. Submit a bug report on this Github page, including
the backtrace and, if possible, the file which FORD crashed while processing.
If an error occurs elsewhere, you will most likely get a backtrace by default.
Once again, please include this backtrace in your bug report.

##Dependencies
In addition to the standard Python libraries, the following modules are needed:

- [Jinja2](http://jinja.pocoo.org/docs/dev/)
- [Pygments](http://pygments.org/)
- [toposort](https://pypi.python.org/pypi/toposort/1.0)
- [Markdown](https://pythonhosted.org/Markdown/)

A near-term goal will be to write a setup script which will check for
these dependencies and install those which are missing. I'd also like to
make FORD available on PyPI so that all dependencies will be installed
automatically.

##Basic Usage
FORD usage is based on _projects_. A project is just whatever piece of software
you want to document. Normally it would either be a program or a library. Each
project will have its own
[Markdown](http://daringfireball.net/projects/markdown/syntax) file which
contains a description of the project. Various options (see below for a
description) can be specified in this file, such as where to look for your
projects source files, where to output the documentation, and information about
the author.

###Running Ford
Once you have written a project file which you're satisfied with, it is time to
run FORD. Make sure that it is in the path/Python-path. The most basic syntax
for running ford is just

```
ford project-file.md
```

Assuming that there are no errors, your documentation will now be available
in the path you indicated for output.

###Writing Documentation
All documentation, both that provided within the source files and that given
in the project file, should be written in
[Markdown](http://daringfireball.net/projects/markdown/syntax). In addition
to the standard Markdown syntax, you can use all of the features in Python's
[Markdown Extra](https://pythonhosted.org/Markdown/extensions/extra.html). Other
Markdown extensions automatically loaded are
[CodeHilite](https://pythonhosted.org/Markdown/extensions/code_hilite.html)
which will provide syntax highlighting for any code fragments you place in your
documentation, [SmartyPants](https://pythonhosted.org/Markdown/extensions/smarty.html) which gives the typographically correct version of various characters,
and [Meta-Data](https://pythonhosted.org/Markdown/extensions/meta_data.html).
The latter is used internally as a way for the user to provide extra information
to and/or customize the behaviour of FORD. Information on providing meta-data
and what types of data FORD will look for can be found in the next section.

In modern (post 1990) Fortran, comments are indicated by an exclamation mark
(!). FORD will ignore a normal comment like this. However, comments with two
exclamation marks (!!) are interpreted as documentation and will be captured
for inclusion in the output. FORD documentation must come _after_ whatever it
is that you are documenting, either at the end of the line or on a subsequent
line. This was chosen because it was felt it is easier to make your
documentation readable from within the source-code this way. This

```fortran
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
```

looks better/more readable than

```fortran
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
```

in the opinion of this author, especially with regards to the list of arguments.
Unfortunately, if you disagree, it is unlikely that there will ever be a switch
available to change this behaviour, as it would require a drastic rewrite of
large parts of the structure of the code.

Please note that legacy Fortran (fixed-form code) is not supported at this
time. If anyone would like to contribute the necessary modifications to
./ford/reader.py to convert fixed-form syntax into free-form, it should not be
difficult (see the approach taken by
[f90doc](http://erikdemaine.org/software/f90doc/)). However, it is not a
priority for me at this time (since I regard fixed-form Fortran as an
abomination which should be wiped from the face of this Earth).

###Output
Output is in HTML. By default, all links will be relative, meaning that the
output can be placed and viewed anywhere. The
[Bootstrap](http://getbootstrap.com/) framework was used to make it easy to
quickly design professional looking pages. An example of some output from
my project [Futility](https://github.com/cmacmackin/futility) is shown below.

![Some example output.](output-example.png)

##Options
###Command-Line Options
###Project File Options
###Meta-Data in Documentation


##ToDo
This software is still extremely young and much remains to be done. Various
things which I'd like to do at some point include:

- Write proper documentation.
- Assemble a list of dependencies.
- Support some of the old Fortran 77 ways of doing things, as these are often
  still used. This includes PARAMETER statements and EXTERNAL statements.
  Support for fixed-form code is less of a priority.
- Add the ability to produce dependency diagrams and inheritance diagrams for
  modules and types, respectively.
- Make more options configurable from the command-line.
- Integrate the Pelican MathJax plugin.
- Add MathJax support.
- Add a search feature.
- Test on some more code, including that of other people, who may have different
  coding styles.
- Add the ability to identify function calls and use this to work out
  call-trees (subroutine calls are already captured, although not yet used
  in any of the output).
- Add the option for users to specify a Creative Commons license for their
  documentation, which will be inserted into the page footer.
- Make it possible to override the display options within a particular
  part of the code and/or for an individual item within the code.
- Provide an option to force all (non-string) text which is captured to be
  lower case.
- Add the ability to recognize the use of intrinsic modules
- Add the ability to allow for ``only`` statements when loading modules and for
  renaming module procedures when loading them.
- Improve the handling of parameterized derived types, particularly for
  variables of that type.
- Improve the sidebar for source files so that it will link to the items that it
  lists.
- Allow the user to provide a favicon.
- Provide a directory in which the user can place any images and/or other
  media they want available.
- Use summaries of the description in some places.
- Improve the way procedures are handled as arguments. In particular, allow
  any abstract interface which was used as a template to be visible somehow.
- Add the ability to search documentation.

Things which ideally I would do, but are not currently on the radar include:

- Add the ability for people to customize appearance of the output more (this
  would require drastic changes to the template system).
- Support fixed-form Fortran (doable, but low priority).
- Add the ability to identify type-bound procedure calls and use these to
  construct call-trees. This would be extremely difficult, as it would
  require keeping track of names and types of variables throughout the code.


##Approach
The basic algorithm for generating the documentation is as follows:

- Get instructions from user. These are to be passes as command-line arguments
  and meta-data within the project file.
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
  Also make sure to process LaTeX (not yet implemented).
- Produce the documentation. This will be done using Jinja2 templates.

