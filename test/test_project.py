from ford.sourceform import FortranSourceFile
from ford.fortran_project import Project

from collections import defaultdict

import pytest


@pytest.fixture
def copy_fortran_file(tmp_path):
    def copy_file(data):
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        filename = src_dir / "test.f90"
        with open(filename, "w") as f:
            f.write(data)
        settings = defaultdict(str)
        settings["docmark"] = "!"
        settings["encoding"] = "utf-8"
        settings["src_dir"] = [str(src_dir)]
        settings["extensions"] = ["f90"]
        return settings

    return copy_file


def test_use_without_rename(copy_fortran_file):
    data = """\
    module module1
      use module2, only: routine_1
      implicit none
      private
      interface routine
          module procedure :: routine_1
      end interface routine
      public :: routine
    end module module1

    module module2
      implicit none
      private
      public :: routine_1
    contains
      subroutine routine_1(i)
        integer,intent(in) :: i
        write(*,*) i
      end subroutine routine_1
    end module module2
    """

    settings = copy_fortran_file(data)
    project = Project(settings)
    project.correlate()
    assert set(project.modules[0].all_procs.keys()) == {"routine_1", "routine"}


def test_use_and_rename(copy_fortran_file):
    data = """\
    module module1
      use module2, only: routine_1 => routine
      implicit none
      private
      interface routine
          module procedure :: routine_1
      end interface routine
      public :: routine
    end module module1

    module module2
      implicit none
      private
      public :: routine
    contains
      subroutine routine(i)
        integer,intent(in) :: i
        write(*,*) i
      end subroutine routine
    end module module2
    """

    settings = copy_fortran_file(data)
    project = Project(settings)
    project.correlate()
    assert set(project.modules[0].all_procs.keys()) == {"routine_1", "routine"}


def test_module_use_only_everything(copy_fortran_file):
    data = """\
    module default_access
      ! No access keyword
      integer :: int_public, int_private
      private :: int_private
      real :: real_public
      real, private :: real_private

      type :: type_public
        complex :: component_public
        complex, private :: component_private
      end type type_public

      type :: type_private
        character(len=1) :: string_public
        character(len=1), private :: string_private
      end type type_private

      private :: sub_private, func_private, type_private

    contains
      subroutine sub_public
      end subroutine sub_public

      subroutine sub_private
      end subroutine sub_private

      integer function func_public()
      end function func_public

      integer function func_private()
      end function func_private
    end module default_access

    module use_only_everything
      use default_access, only : int_public, real_public, type_public, sub_public, func_public
    end module use_only_everything
    """

    settings = copy_fortran_file(data)
    project = Project(settings)
    project.correlate()

    # Double-check we're looking at the right module
    assert project.modules[1].name == "use_only_everything"
    assert set(project.modules[1].all_procs.keys()) == {
        "sub_public",
        "func_public",
    }
    assert set(project.modules[1].pub_procs.keys()) == {
        "sub_public",
        "func_public",
    }
    assert set(project.modules[1].all_types.keys()) == {
        "type_public",
    }
    assert set(project.modules[1].pub_types.keys()) == {
        "type_public",
    }
    assert set(project.modules[1].all_vars.keys()) == {
        "int_public",
        "real_public",
    }
    assert set(project.modules[1].pub_vars.keys()) == {
        "int_public",
        "real_public",
    }


def test_module_use_only_everything_change_access(copy_fortran_file):
    data = """\
    module default_access
      ! No access keyword
      integer :: int_public, int_private
      private :: int_private
      real :: real_public
      real, private :: real_private

      type :: type_public
        complex :: component_public
        complex, private :: component_private
      end type type_public

      type :: type_private
        character(len=1) :: string_public
        character(len=1), private :: string_private
      end type type_private

      private :: sub_private, func_private, type_private

    contains
      subroutine sub_public
      end subroutine sub_public

      subroutine sub_private
      end subroutine sub_private

      integer function func_public()
      end function func_public

      integer function func_private()
      end function func_private
    end module default_access

    module use_only_change_access
      use default_access, only : int_public, real_public, type_public, sub_public, func_public
      private
      public :: int_public, sub_public
    end module use_only_change_access
    """

    settings = copy_fortran_file(data)
    project = Project(settings)
    project.correlate()

    # Double-check we're looking at the right module
    assert project.modules[1].name == "use_only_change_access"
    assert set(project.modules[1].all_procs.keys()) == {
        "sub_public",
        "func_public",
    }
    assert set(project.modules[1].pub_procs.keys()) == {
        "sub_public",
    }
    assert set(project.modules[1].all_types.keys()) == {
        "type_public",
    }
    assert set(project.modules[1].pub_types.keys()) == set()
    assert set(project.modules[1].all_vars.keys()) == {
        "int_public",
        "real_public",
    }
    assert set(project.modules[1].pub_vars.keys()) == {
        "int_public",
    }


def test_module_use_everything(copy_fortran_file):
    data = """\
    module default_access
      ! No access keyword
      integer :: int_public, int_private
      private :: int_private
      real :: real_public
      real, private :: real_private

      type :: type_public
        complex :: component_public
        complex, private :: component_private
      end type type_public

      type :: type_private
        character(len=1) :: string_public
        character(len=1), private :: string_private
      end type type_private

      private :: sub_private, func_private, type_private

    contains
      subroutine sub_public
      end subroutine sub_public

      subroutine sub_private
      end subroutine sub_private

      integer function func_public()
      end function func_public

      integer function func_private()
      end function func_private
    end module default_access

    module use_everything
      use default_access
    end module use_everything
    """

    settings = copy_fortran_file(data)
    project = Project(settings)
    project.correlate()

    # Double-check we're looking at the right module
    assert project.modules[1].name == "use_everything"
    assert set(project.modules[1].all_procs.keys()) == {
        "sub_public",
        "func_public",
    }
    assert set(project.modules[1].pub_procs.keys()) == {
        "sub_public",
        "func_public",
    }
    assert set(project.modules[1].all_types.keys()) == {
        "type_public",
    }
    assert set(project.modules[1].pub_types.keys()) == {
        "type_public",
    }
    assert set(project.modules[1].all_vars.keys()) == {
        "int_public",
        "real_public",
    }
    assert set(project.modules[1].pub_vars.keys()) == {
        "int_public",
        "real_public",
    }


def test_module_use_everything_reexport(copy_fortran_file):
    data = """\
    module default_access
      ! No access keyword
      integer :: int_public, int_private
      private :: int_private
      real :: real_public
      real, private :: real_private

      type :: type_public
        complex :: component_public
        complex, private :: component_private
      end type type_public

      type :: type_private
        character(len=1) :: string_public
        character(len=1), private :: string_private
      end type type_private

      private :: sub_private, func_private, type_private

    contains
      subroutine sub_public
      end subroutine sub_public

      subroutine sub_private
      end subroutine sub_private

      integer function func_public()
      end function func_public

      integer function func_private()
      end function func_private
    end module default_access

    module use_everything
      use default_access
    end module use_everything

    module reexport
      use use_everything
    end module reexport
    """

    settings = copy_fortran_file(data)
    project = Project(settings)
    project.correlate()

    # Double-check we're looking at the right module
    assert project.modules[2].name == "reexport"
    assert set(project.modules[2].all_procs.keys()) == {
        "sub_public",
        "func_public",
    }
    assert set(project.modules[2].pub_procs.keys()) == {
        "sub_public",
        "func_public",
    }
    assert set(project.modules[2].all_types.keys()) == {
        "type_public",
    }
    assert set(project.modules[2].pub_types.keys()) == {
        "type_public",
    }
    assert set(project.modules[2].all_vars.keys()) == {
        "int_public",
        "real_public",
    }
    assert set(project.modules[2].pub_vars.keys()) == {
        "int_public",
        "real_public",
    }
