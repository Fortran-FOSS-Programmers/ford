module config_mod
   use remote_module
   implicit none
contains

   function create() result(config)
      type (remote_type) :: config
      ! Checks call chain following when using external entities
      config%cptr%buffer(1:1) = 10
   end function create
end module config_mod


module myAbort
  use external_module
  type, public, extends(solverAborts_type) :: vel_abortCriteria_type

    !> Maximal velocity that will be tolerated in the simulation.
    real :: velmax = 0.15

  contains

    procedure :: load => abortCriteria_load

  end type solverAborts_type

contains

  subroutine abortCriteria_load(me, conf)
    use external_module, only: abort_fraction
    ! -------------------------------------------------------------------- !
    !> Object to hold the solver specific configuration parameters.
    class(vel_abortCriteria_type), intent(inout) :: me

    !> Handle to the configuration.
    integer, intent(in) :: conf

    me%velmax = real(conf)*abort_fraction()

  end subroutine mus_abortCriteria_load

end module myAbort

program top_level
  !! This program uses a module from some external source, whose
  !! documentation will be linked to from this documentation.
  !! This uses [[remote_sub]].
  use external_module
  use remote_module
  use myAbort

  implicit none

  type, extends(test) :: maintest
    character(len=10) :: label
  end type maintest

  call external_sub
  call remote_sub
end program top_level
