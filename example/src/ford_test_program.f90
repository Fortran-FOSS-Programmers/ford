
!> This is a normal doxygen comment
!> @param global_pi This is a doxygen comment for global pi
!> This should show?
program ford_test_program
  !! Simple Fortran program to demonstrate the usage of FORD and to test its installation
  use iso_fortran_env, only: output_unit, real64
  use json_module
  implicit none
  real (real64) :: global_pi = acos(-1)
  !! a global variable, initialized to the value of pi

  type foo
    integer :: foo_stuff
  contains
    procedure :: do_foo_stuff
  end type foo

  type, extends(foo) :: bar
  end type bar

  write(output_unit,'(A)') 'Small test program'
  call do_stuff(20)

contains
!> @details this is a summary
  subroutine do_foo_stuff(this)
    use test_module, only: increment
    class(foo) :: this
    call increment(this%foo_stuff)
  end subroutine do_foo_stuff

!> @deprecated true
!> @param repeat This is a doxygen comment for the name variable repeat
  subroutine do_stuff(repeat)
    !! This is documentation for our subroutine that does stuff and things.
    !! This text is captured by ford
    integer, intent(in) :: repeat
    integer :: i
    !! internal loop counter

    ! the main content goes here and this is comment is not processed by FORD
    do i=1,repeat
      global_pi = acos(-1)
    end do
  end subroutine do_stuff

!> @deprecated true
  subroutine linalg(A,x,b)
    !! Solve Ax = b with linear algebra magic
    real, intent(in) :: A(:,:)
    !! The a matrix to invert etc.
    real, intent(inout) :: b(:)
    !! The right hand side
    real, intent(out), optional, dimension(:), allocatable :: x
    !! The solution to Ax = b

    ! do some stuff, ensure proper bounds etc.
  end subroutine linalg

  function multidimension_string(n)
    !! Function with a complicated return value
    integer, intent(in) :: n
    !! How big to make the string
    character(kind=kind('a'), len=4), dimension(:, :), allocatable :: multidimension_string
    !! A really complex return type
  end function multidimension_string

end program ford_test_program
