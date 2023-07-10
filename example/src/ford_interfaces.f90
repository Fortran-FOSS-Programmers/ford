module interfaces
  !! This module demostrates how FORD handles various aspects of
  !! interfaces

  abstract interface
    integer pure function unary_f_t(n)
      !! This defines a named interface for some functions with the
      !! same signature
      implicit none
      integer, intent(in) :: n
      !! Scalar number
    end function unary_f_t
  end interface

  procedure(unary_f_t), pointer, public :: unary_f => null()
  !! This is a procedure pointer with a named interface

  interface generic_unary_f
    !! This is an interface that gives a generic name to multiple
    !! specific (distinguishable) implementations
    procedure unary_f
      !! This is pointer procedure above

    real pure function real_unary_f(x)
      !! A `real` version of our function
      real, intent(in) :: x
    end function real_unary_f

    module procedure :: higher_order_unary_f
      !! A function defined in this module
  end interface generic_unary_f

contains

  pure integer function higher_order_unary_f(f, n)
    !! This is `apply`
    procedure(unary_f_t) :: f
      !! Some function to apply
    integer, intent(in) :: n
      !! Number to call `f` with
    higher_order_unary_f = f(n)
  end function higher_order_unary_f
end module interfaces
