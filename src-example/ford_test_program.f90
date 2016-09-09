        program ford_test_program
          !! Simple Fortran program to demonstrate the usage of FORD and to test its installation
          use iso_fortran_env, only: output_unit, real64
          implicit none
          real (real64) :: global_pi = acos(-1)
          !! a global variable, initialized to the value of pi

         type foo
           integer :: foo_stuff
         contains
           procedure :: do_foo_stuff
         end type

         type, extends(foo) :: bar
         end type

         write(output_unit,'(A)') 'Small test program'
         call do_stuff(20)

        contains
          subroutine do_foo_stuff(this)
            class(foo) :: this
          end subroutine

          subroutine do_stuff(repeat)
            !! This is documentation for our subroutine that does stuff and things.
            !! This text is captured by ford
            integer, intent(in) :: repeat
            !! The number of times to repeatedly do stuff and things
            integer :: i
            !! internal loop counter

            ! the main content goes here and this is comment is not processed by FORD
            do i=1,repeat
               global_pi = acos(-1)
            end do
          end subroutine do_stuff

          subroutine linalg(A,x,b)
            !! Solve Ax = b with linear algebra magic
            real, intent(in) :: A(:,:)
            !! The a matrix to invert etc.
            real, intent(in) :: b(:)
            !! The right hand side
            real, intent(out) :: x(:)
            !! The solution to Ax = b

            !! do some stuff, ensure proper bounds etc.
          end subroutine linalg
        end program ford_test_program
