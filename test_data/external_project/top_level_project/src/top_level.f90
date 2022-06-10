program top_level
  !! This program uses a module from some external source, whose
  !! documentation will be linked to from this documentation
  use external_module
  use remote_module

  implicit none

  type, extends(test) :: maintest
    character(len=10) :: label
  end type

  call external_sub
  call remote_sub
end program top_level
