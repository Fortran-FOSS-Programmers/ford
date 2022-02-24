module external_module
  implicit none

  type basis
    integer :: id
  end type basis

  type, extends(basis) :: test
    logical :: ok
  end type

contains
  subroutine external_sub
  end subroutine external_sub
end module external_module
