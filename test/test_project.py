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
