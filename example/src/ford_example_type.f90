module ford_example_type_mod
  !! Summary of this module
  !!
  !! A longer description of the purpose of this module
  implicit none

  private
  public :: say_interface

  type, abstract, public :: say_type_base
    !! An abstract base type that has a deferred `say` function
  contains
    procedure(say_interface), deferred :: say
    !! Deferred type-bound procedure with a procedure prototype
  end type say_type_base

  type, public :: example_type
    !! Some type that can say hello.
    !!
    !! This type's docs demonstrate how documentation is rendered
    !! differently for public/private components, and for type-bound
    !! procedure bindings and the procedures themselves.
    private
    integer :: counter = 1
    !! Internal counter
    character(len=:), allocatable, public :: name
    !! Name of this instance
    !!
    !! More documentation
  contains
    procedure :: say_hello => example_type_say
    !! This will document the type-bound procedure *binding*, rather
    !! than the procedure itself. The specific procedure docs will be
    !! rendered on the [[example_type]] page.
    !!
    !! This binding has more documentation beyond the summary
    procedure, private, nopass :: say_int
    procedure, private, nopass :: say_real
    generic :: say_number => say_int, say_real
    !! This generic type-bound procedure has two bindings

    final :: example_type_finalise
    !! This is the finaliser, called when the instance is destroyed.
    !!
    !! This finaliser has more documentation beyond the summary
  end type example_type

  interface example_type
    !! This is a constructor for our type
    !!
    !! This constructor has more documentation that won't appear in
    !! the procedure list, but should appear in the type page
    module procedure make_new_type
  end interface example_type

  interface
    subroutine say_interface(self)
      !! Abstract interface for 'say' functions
      import say_type_base
      class(say_type_base), intent(inout) :: self
    end subroutine say_interface
  end interface

contains

  subroutine example_type_say(self)
    !! Prints how many times this instance has said hello
    !!
    !! This subroutine has more documentation that won't appear in the
    !! summary in the procedure list, but should appear in the type
    !! page.
    class(example_type), intent(inout) :: self
    write(*, '(a, " has said hello ", i0, " times.")') self%name, self%counter
    self%counter = self%counter + 1
  end subroutine example_type_say

  type(example_type) function make_new_type() result(self)
    !! This is the documentation for the specific constructor
    !!
    !! More documentation
    self%name = "some-default-name"
  end function make_new_type

  subroutine example_type_finalise(self)
    !! Cleans up an [[example_type(type)]] instance
    !!
    !! More documentation
    type(example_type), intent(inout) :: self
    call self%say_hello()
    write(*, '(a, " says goodbye")') self%name
  end subroutine example_type_finalise

  subroutine say_int(int)
    !! Prints an integer
    integer, intent(in) :: int
    write(*, '(i0)') int
  end subroutine say_int

  subroutine say_real(r)
    !! Prints a real
    real, intent(in) :: r
    write(*, '(g0)') r
  end subroutine say_real

end module ford_example_type_mod
