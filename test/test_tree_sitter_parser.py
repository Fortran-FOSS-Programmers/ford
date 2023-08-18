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
        pure integer function bar(x) result(y)
          integer, intent(in) :: x
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
    assert functions[0].name == "bar"
    assert functions[0].retvar == "y"
