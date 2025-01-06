from ford.tree_sitter_parser import TreeSitterParser
from ford.sourceform import FortranSourceFile
from ford.settings import ProjectSettings

from textwrap import dedent

import time

import pytest


class FakeProject:
    def __init__(self, procedures=None):
        self.procedures = procedures or []


@pytest.fixture
def parse_fortran_file_ts(copy_fortran_file):
    def parse_file(data, **kwargs):
        filename = copy_fortran_file(data)
        settings = ProjectSettings(**kwargs)
        parser = TreeSitterParser()
        tree = parser.parser.parse(data.encode())
        return FortranSourceFile(str(filename), settings, parser, source=tree.walk())

    return parse_file


data = dedent(
    """
!> predoc
module foo
!! post doc
  !> type predoc
  type :: base
      !! type post doc
      !> variable predoc
      integer :: bar
      !! variable postdoc
  end type
contains
    pure integer function bar(x, a, b) result(y)
      integer, intent(in) :: x, a, b
      real :: zing, zang, zong
      namelist /ben/ zing, zang, zong

      contains
        pure function ziff(z)
          real :: ziff, z
          complex:: fa, ba, ga
          namelist /zaff/ fa, ba, ga
        end function ziff
    end function bar
end module foo
"""
).encode()


def test_tree_sitter_parser():
    parser = TreeSitterParser()
    tree = parser.parser.parse(data)

    time_start = time.time()
    fortran_file = FortranSourceFile(
        "imaginary.f90",
        ProjectSettings(),
        parser,
        source=tree.walk(),
    )
    time_end = time.time()

    print(f"Cursor based: {time_end - time_start}")
    assert len(fortran_file.modules) == 1
    assert fortran_file.modules[0].name == "foo"

    functions = fortran_file.modules[0].functions
    assert len(functions) == 1
    function = functions[0]
    assert function.name == "bar"
    retvar = function.retvar
    assert retvar.name == "y"
    assert retvar.full_type == "integer"
    arg_names = sorted(arg.name for arg in function.args)
    assert arg_names == sorted(["x", "a", "b"])

    assert len(function.namelists) == 1
    assert function.namelists[0].name == "ben"

    assert len(function.functions) == 1


def test_very_basic(parse_fortran_file_ts):
    data = """
    program foo
    end program foo
    """

    fortran_file = parse_fortran_file_ts(data)
    assert len(fortran_file.programs) == 1
    assert fortran_file.programs[0].name == "foo"
if __name__ == "__main__":
    test_tree_sitter_parser()
