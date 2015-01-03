#Inline
This is an automatic documentation generator for modern Fortran programs.
It is provisionally called Inline, to reflect the fact that it allows a
programmer to write inline documentation as comments within their program.

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
  in one file but used in another. This will be used to generate hyperlinks
  when producing the documentation.
- Convert comments into HTML. Assume that they have been written in Markdown.
  Also make sure to process LaTeX. Consider how images will be handled. Perhaps
  the user should specify a directory where they are stored which will then
  be copied into the output directory (a bit like how Pelican works)?
- Produce the documentation. This will be done using Jinja2 templates. Perhaps
  allow the user to provide their own template, if desired.

