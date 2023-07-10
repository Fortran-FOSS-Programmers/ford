c> This is an example of a Fortran-77 program documented in FORD
c>
c> FORD uses the `fixed2free` utility to convert fixed-form source to
c> free-form source, which it can then handle with the same parser
c>
c> This example adapted from a BLAS test program
      PROGRAM FORD77
*> Unit for stdout
      INTEGER          NOUT
      PARAMETER        (NOUT=6)
*> Scalars in Common
      INTEGER          ICASE
      LOGICAL          PASS
* Local Scalars
      REAL             SFAC
* External Subroutines
      EXTERNAL         CHECK1, CHECK2, HEADER
*> Common blocks
      COMMON           /COMBLA/ICASE, N, INCX, INCY, MODE, PASS
* Data statements
      DATA             SFAC/9.765625E-4/

      WRITE (NOUT,99999)
      DO 20 IC = 1, 10
         ICASE = IC
         CALL HEADER
         IF (ICASE.LE.5) THEN
            CALL CHECK2(SFAC)
         ELSE IF (ICASE.GE.6) THEN
            CALL CHECK1(SFAC)
         END IF
   20 CONTINUE
      END

      BLOCK DATA combla
!! Initialise variables in common blocks

      COMMON /COMBLA/ ICASE, N, INCX
!! Some common block
      DATA ICASE /4/
      END

      BLOCK DATA unused
!! A different block data block
      COMMON /UNUSED/ OTHER
!! This common block isn't used anywhere
      DATA OTHER /42/
      END

      SUBROUTINE HEADER
c! You can use the usual FORD docmarks with F77 style comments

*> Parameters
      INTEGER          NOUT
      PARAMETER        (NOUT=6)
*> Scalars in Common
      INTEGER          ICASE
*> Local Arrays
      CHARACTER*6      L(2)
*> Common blocks
      COMMON           /COMBLA/ICASE
      DATA             L(1)/'CDOTC '/
      DATA             L(2)/'CDOTU '/
*Executable Statements
      WRITE (NOUT,99999) ICASE, L(ICASE)
      RETURN
*
99999 FORMAT (/' Test of subprogram number',I3,12X,A6)
*
*     End of HEADER
*
      END
      REAL             FUNCTION SDIFF(SA,SB)
*!    COMPUTES DIFFERENCE OF TWO NUMBERS.  C. L. LAWSON, JPL 1974 FEB 15
      REAL                            SA, SB
      SDIFF = SA - SB
      RETURN
      END
