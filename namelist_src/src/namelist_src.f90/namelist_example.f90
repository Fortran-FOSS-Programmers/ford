!! docstring for mod_a
module mod_a
  implicit none
  !! docstring for var_a
  integer :: var_a
end module mod_a

!! docstring for mod_b
module mod_b
  use mod_a
  implicit none
  !! docstring for var_b
  integer :: var_b
end module mod_b

!! docstring for prog
program prog
  implicit none
  !! docstring for var_c
  integer :: var_c

    character(len=*), parameter :: namelist_string = "&
         & &namelist_a &
         &   var_a = 1 &
         &   var_b = 1 &
         &   var_c = 1 &
         &   var_d = 1 &
         & /"

  call sub(namelist_string)
contains
  !! docstring for sub
  subroutine sub(string)
    use mod_b
    !! docstring var_d
    integer :: var_d
    character(len=*), intent(in) :: string

    namelist /namelist_a/ var_a, var_b, var_c, var_d
    read(string, nml=namelist_a)
    write(*, *) "Read in:"
    write(*, nml=namelist_a)

  end subroutine sub
end program prog
