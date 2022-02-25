program top_level
  !! This program uses a module from some external source, whose
  !! documentation will be linked to from this documentation
  use external_module
  use remote_module
  implicit none
  call external_sub
  call remote_sub
end program top_level
