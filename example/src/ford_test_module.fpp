module test_module
  implicit none

  interface
    module subroutine check()
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
end module test_module

submodule (test_module) test_submodule
contains
  module subroutine check()
    print*, "checking"
  end subroutine check
end submodule test_submodule
