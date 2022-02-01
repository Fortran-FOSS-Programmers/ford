module test_module
  implicit none
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
