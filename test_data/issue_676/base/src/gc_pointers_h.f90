module gc_pointers_h
  implicit none

  private
  public :: pointers

  type :: pointers
   contains
    procedure :: check
  end type pointers

  interface pointers
    module procedure pointers_constructor
  end interface pointers

  interface
     module function pointers_constructor( gencat )result( this )
      class(*), pointer, intent( in ) :: gencat
      type( pointers ) :: this
    end function pointers_constructor

    module subroutine check( self )
      class( pointers ), intent( in ) :: self
    end subroutine check
  end interface

 CONTAINS

end module gc_pointers_h
