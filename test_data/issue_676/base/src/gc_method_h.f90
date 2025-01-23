module gc_method_h

  use gc_pointers_h, only: pointers
  implicit none

  private
  public :: t_method, method_constructor

  type, extends(pointers) :: t_method
   contains
     procedure :: init, run
  end type t_method

  abstract interface
     function method_constructor(ptr, nwords, words) result(this)
       import t_method
       class(t_method), pointer :: this
       class(*), intent(in) :: ptr
       integer, intent(in) :: nwords
       character(*), intent(in) :: words(:)
     end function method_constructor
  end interface

CONTAINS

  function init(self) result(ierr)
    class(t_method), intent(inout) :: self
    integer :: ierr
  end function init

  function run(self) result(ierr)
    class(t_method), intent(inout) :: self
    integer :: ierr
  end function run

end module gc_method_h
