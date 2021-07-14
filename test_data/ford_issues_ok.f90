! compile wtih
!> ifort /fpp /openmp ford_issues.f90


module ford_issues
#if defined(__GFORTRAN__)

#else
  use ifport
#endif  
  use omp_lib
  
  implicit none

contains


  ! this is function with args that have comments
	integer function func_with_args(a, & 
  &                               b, & ! this is not OK
  &                               c ) ! this is not OK  
    integer :: a, b, c
  
    func_with_args = a+b
	end function 


  ! this is OK
	integer function func_with_bracket()
    double precision :: auxf, L_min
    
    ! this is OK  
    auxf = ( 1.0d0 - L_min)
    
    ! this fails  
!  File "e:\nosave\code\gitrepos\ford\ford\reader.py", line 218, in __next__
! raise Exception("Alternate documentation lines can not be inline: {}".format(line))
! Exception: Alternate documentation lines can not be inline:     auxf = ( 1.0d0 - L_min)!* (1.0d0 - L_min)    
!!    auxf = ( 1.0d0 - L_min)!* (1.0d0 - L_min)
  
    func_with_bracket = 5
	end function 


    ! this fails
!  File "e:\nosave\code\gitrepos\ford\ford\sourceform.py", line 1371, in _initialize
!  for arg in self.SPLIT_RE.split(line.group(3)[1:-1]):
! TypeError: 'NoneType' object is not subscriptable
!!	integer function func_without_bracket
integer function func_without_bracket()
    integer :: omp_p
    
    ! this also fails
! File "e:\nosave\code\gitrepos\ford\ford\reader.py", line 261, in __next__
! raise Exception("Can not start a new line in Fortran with \"&\": {}".format(line))
! Exception: Can not start a new line in Fortran with "&": & PRIVATE( omp_p )
!!    !$OMP PARALLEL DEFAULT(SHARED) &
!!   & PRIVATE( omp_p )

    !$OMP CRITICAL
      write(*,*)  'thread ', omp_get_thread_num(), '/', omp_get_num_threads(), ' started'
    !$OMP END CRITICAL

    !$OMP END PARALLEL
      
    func_without_bracket = 10
	end function 
  
  

end module ford_issues


program main
  use ford_issues
  implicit none
  
  integer :: i(3)
  i(1) = func_with_args(0,1,0)
  i(2) = func_with_bracket()
  i(3) = func_without_bracket()
  write(*,*) 'ford_issues', i
  
end program

