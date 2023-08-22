from ford.tree_sitter_parser import tree_sitter_parser_available, TreeSitterParser
from ford.sourceform import FortranSourceFile
from ford.settings import ProjectSettings

from textwrap import dedent

import pytest


@pytest.mark.skipif(not tree_sitter_parser_available, reason="Requires tree-sitter")
def test_tree_sitter_parser():
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

    parser = TreeSitterParser()
    tree = parser.parser.parse(data)

    fortran_file = FortranSourceFile(
        "imaginary.f90",
        ProjectSettings(),
        parser,
        source=tree.root_node,
    )
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
