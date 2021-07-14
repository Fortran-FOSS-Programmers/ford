module ford_issues
!! ifort /fpp /openmp ford_issues.f90
!!
use ifport
use omp_lib
implicit none
contains
integer function func_with_args(a,                                b,                                c )
integer :: a, b, c
func_with_args = a+b
end function
integer function func_with_bracket()
double precision :: auxf, L_min
auxf = ( 1.0d0 - L_min)
!!    auxf = ( 1.0d0 - L_min)!* (1.0d0 - L_min)
!!
func_with_bracket = 5
end function
!!	integer function func_without_bracket
integer function func_without_bracket()
integer :: omp_p
!!    !$OMP PARALLEL DEFAULT(SHARED) &
!!   & PRIVATE( omp_p )
!!
!!
write(*,*)  'thread ', omp_get_thread_num(), '/', omp_get_num_threads(), ' started'
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
