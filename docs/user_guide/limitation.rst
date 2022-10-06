=============
 Limitations
=============

FORD can not handle all conceivable Fortran codes as of yet. Limitations
include:

-  Some FORTRAN77 syntax. ``DATA`` and ``EQUIVALENCE`` statements are
   ignored.
-  Calls to type-bound procedures are not recognized in call-graphs.
-  Implicit typing. FORD does not understand implicit typing, except for
   argument names. In that case, it can not handle non-default implicit
   typing. While this shouldn’t be too hard to implement, it is low
   priority since I don’t really want to be support bad coding style.
-  Files which would be compiled after having been preprocesses will be
   run through gfortran’s preprocessor (or another ones, if specified)
   prior to extracting the documentation. While this means that the
   final API will be reflected in the documentation, it may be less
   useful for developers who might like to know what particular macros
   are for.

Over time, some of all of these issues may be fixed.
