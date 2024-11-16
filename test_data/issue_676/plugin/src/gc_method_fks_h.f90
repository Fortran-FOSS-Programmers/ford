module gc_method_fks_h
  use gc_method_h, only : t_method
  implicit none

  public :: t_method_fks, method_fks_constructor
  private

  !> |cmd| `method fks`
  type, extends( t_method ) :: t_method_fks
   contains
     procedure :: init => method_fks_init
     procedure :: run => method_fks_run
     final :: method_fks_destroy
  end type t_method_fks

  interface method_fks_
     module procedure :: method_fks_constructor
  end interface method_fks_

  interface
     module function method_fks_constructor( ptr, nwords, words )result( this )
      class( t_method ), pointer :: this
      class(*),        intent(in) :: ptr
      integer,         intent( in ) :: nwords
      character(*),    intent( in ) :: words(:)
    end function method_fks_constructor

    module function method_fks_init( self )result(ierr)
      class( t_method_fks ), intent( inout ) :: self
      integer :: ierr
    end function method_fks_init

    module function method_fks_run( self )result(ierr)
      class( t_method_fks ), intent( inout ) :: self
      integer :: ierr
    end function method_fks_run

    module subroutine method_fks_destroy( self )
      type( t_method_fks ), intent(inout) :: self
    end subroutine method_fks_destroy
  end interface

CONTAINS

end module gc_method_fks_h
