module test_module
  implicit none

  interface
    module subroutine check()
      !! Docstring on the interface
    end subroutine check
  end interface

contains
  subroutine increment(x)
    !! Increase argument by one
    integer, intent(inout) :: x
    x = x + 1
  end subroutine increment

#ifdef HAS_DECREMENT
  subroutine decrement(x)
    !! Decrease argument by one
    !!
    !! Only publicly accessible if `"HAS_DECREMENT"` preprocessor
    !! macro is defined
    integer, intent(inout) :: x
    x = x - 1
  end subroutine decrement
#endif

  subroutine apply_check(f)
    !! deprecated: true
    !!
    !! Takes a function and immediately calls it
    procedure(check) :: f
    !! Some function to call
    call f()
  end subroutine apply_check
end module test_module

submodule (test_module) test_submodule
  !! display: private
  !!
  !! Submodule specific docs
contains
  module subroutine check()
    !! Docstring on the implementation
    print*, "checking"
  end subroutine check
end submodule test_submodule
