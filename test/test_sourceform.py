from ford.sourceform import FortranSourceFile, FortranModule

from collections import defaultdict

import pytest


@pytest.fixture
def parse_fortran_file(tmp_path):
    def parse_file(data):
        filename = tmp_path / "test.f90"
        with open(filename, "w") as f:
            f.write(data)
        settings = defaultdict(str)
        settings["docmark"] = "!"
        settings["encoding"] = "utf-8"

        return FortranSourceFile(str(filename), settings)

    return parse_file


def test_extends(parse_fortran_file):
    """Check that types can be extended"""

    data = """\
    program foo
    !! base type
    type :: base
    end type base

    !! derived type
    type, extends(base) :: derived
    end type

    !! derived type but capitalised
    type, EXTENDS(base) :: derived_capital
    end type

    end program foo
    """

    fortran_type = parse_fortran_file(data)

    assert len(fortran_type.programs) == 1

    program = fortran_type.programs[0]

    assert len(program.types) == 3
    assert program.types[1].extends == "base"
    assert program.types[2].extends == "base"


def test_submodule_procedure_contains(parse_fortran_file):
    """Check that submodule procedures can have 'contains' statements"""

    data = """\
    module foo_m
      implicit none
      interface
        module subroutine foo()
          implicit none
        end subroutine
      end interface
    end module

    submodule(foo_m) foo_s
      implicit none
    contains
      module procedure foo
      contains
        subroutine bar()
        end subroutine
      end procedure
    end submodule
    """

    fortran_type = parse_fortran_file(data)

    assert len(fortran_type.modules) == 1
    assert len(fortran_type.submodules) == 1
    submodule = fortran_type.submodules[0]
    assert len(submodule.modprocedures) == 1
    module_procedure = submodule.modprocedures[0]
    assert len(module_procedure.subroutines) == 1


def test_backslash_in_character_string(parse_fortran_file):
    """Bad escape crash #296"""

    data = r"""\
    module test_module
    character(len=*),parameter,public:: q = '(?)'
    character(len=*),parameter,public:: a  = '\a'
    character(len=*),parameter,public:: b  = '\b'
    character(len=*),parameter,public:: c  = '\c'
    end module test_module
    """

    source = parse_fortran_file(data)
    module = source.modules[0]

    expected_variables = {"q": r"'(?)'", "a": r"'\a'", "b": r"'\b'", "c": r"'\c'"}

    for variable in module.variables:
        assert variable.initial == expected_variables[variable.name]


def test_sync_images_in_submodule_procedure(parse_fortran_file):
    """Crash on sync images inside module procedure in submodule #237"""

    data = """\
    module stuff
      interface
        module subroutine foo()
        end subroutine
      end interface
    end module

    submodule(stuff) sub_stuff
      implicit none
    contains
      module procedure foo
        sync images(1)
      end procedure
    end submodule
    """

    parse_fortran_file(data)


def test_function_and_subroutine_call_on_same_line(parse_fortran_file):
    """Regex does not check for nested calls #256"""

    data = """\
    program test
    call bar(foo())
    contains
    integer function foo()
    end function foo
    subroutine bar(thing)
      integer, intent(in) :: thing
    end subroutine bar
    end program test
    """

    fortran_file = parse_fortran_file(data)
    program = fortran_file.programs[0]
    assert len(program.calls) == 2
    expected_calls = {"bar", "foo"}
    assert set(program.calls) == expected_calls


def test_component_access(parse_fortran_file):
    data = """\
    module mod1
        integer :: anotherVar(20)
        type typeOne
            integer :: ivar(10)
        end type typeOne
        type(typeOne) :: One
    end module mod1

    module mod2
        type typeTwo
            integer :: ivar(10)
        end type typeTwo
        type(typeTwo) :: Two
    end module mod2

    subroutine with_space
        use mod2
        integer :: a
        a = 3
        Two% ivar(:) = a
    end subroutine with_space

    program main
        integer :: i, j
        integer :: zzz(5)

        type typeThree
            integer :: ivar(10)
        end type typeThree
        type(typeThree) :: Three

        call with_space()
        call without_space()
        anotherVar(3) = i
        j = zzz(3)

        Three% ivar(3) = 7
    end program
    """

    fortran_file = parse_fortran_file(data)

    expected_variables = {"i", "j", "zzz", "Three"}
    actual_variables = {var.name for var in fortran_file.programs[0].variables}
    assert actual_variables == expected_variables


def test_format_statement(parse_fortran_file):
    data = """\
    program test_format_statement
      implicit none
      write (*, 300)
    300 format (/1X, 44('-'), ' Begin of test2 Calculation ', 33('-')//)
    end program test_format_statement
    """

    fortran_file = parse_fortran_file(data)
    assert fortran_file.programs[0].calls == []


def test_enumerator_with_kind(parse_fortran_file):
    """Checking enumerators with specified kind, issue #293"""

    data = """\
    module some_enums
      use, intrinsic :: iso_fortran_env, only : int32
      enum, bind(c)
        enumerator :: item1, item2
        enumerator :: list1 = 100_int32, list2
        enumerator :: fixed_item1 = 0, fixed_item2
      end enum
    end module some_enums
    """

    fortran_file = parse_fortran_file(data)
    enum = fortran_file.modules[0].enums[0]
    assert enum.variables[0].name == "item1"
    assert enum.variables[0].initial == 0
    assert enum.variables[1].name == "item2"
    assert enum.variables[1].initial == 1
    assert enum.variables[2].name == "list1"
    assert enum.variables[2].initial == "100_int32"
    assert enum.variables[3].name == "list2"
    assert enum.variables[3].initial == 101
    assert enum.variables[4].name == "fixed_item1"
    assert enum.variables[4].initial == "0"
    assert enum.variables[5].name == "fixed_item2"
    assert enum.variables[5].initial == 1


class FakeModule(FortranModule):
    def __init__(
        self, procedures: dict, interfaces: dict, types: dict, variables: dict
    ):
        self.pub_procs = procedures
        self.pub_absints = interfaces
        self.pub_types = types
        self.pub_vars = variables


def test_module_get_used_entities_all():
    mod_procedures = {"subroutine": "some subroutine"}
    mod_interfaces = {"abstract": "interface"}
    mod_types = {"mytype": "some type"}
    mod_variables = {"x": "some var"}

    module = FakeModule(mod_procedures, mod_interfaces, mod_types, mod_variables)

    procedures, interfaces, types, variables = module.get_used_entities("")

    assert procedures == mod_procedures
    assert interfaces == mod_interfaces
    assert types == mod_types
    assert variables == mod_variables


def test_module_get_used_entities_some():
    mod_procedures = {"subroutine": "some subroutine"}
    mod_interfaces = {"abstract": "interface"}
    mod_types = {"mytype": "some type"}
    mod_variables = {"x": "some var", "y": "some other var"}

    module = FakeModule(mod_procedures, mod_interfaces, mod_types, mod_variables)

    procedures, interfaces, types, variables = module.get_used_entities(
        ", only: x, subroutine"
    )

    assert procedures == mod_procedures
    assert interfaces == {}
    assert types == {}
    assert variables == {"x": mod_variables["x"]}


def test_module_get_used_entities_rename():
    mod_procedures = {"subroutine": "some subroutine"}
    mod_interfaces = {"abstract": "interface"}
    mod_types = {"mytype": "some type"}
    mod_variables = {"x": "some var", "y": "some other var"}

    module = FakeModule(mod_procedures, mod_interfaces, mod_types, mod_variables)

    procedures, interfaces, types, variables = module.get_used_entities(
        ", only: x, y => subroutine"
    )

    assert procedures == {"y": mod_procedures["subroutine"]}
    assert interfaces == {}
    assert types == {}
    assert variables == {"x": mod_variables["x"]}


def test_module_default_access(parse_fortran_file):
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
    """

    fortran_file = parse_fortran_file(data)
    fortran_file.modules[0].correlate(None)

    assert set(fortran_file.modules[0].all_procs.keys()) == {
        "sub_public",
        "func_public",
        "sub_private",
        "func_private",
    }
    assert set(fortran_file.modules[0].pub_procs.keys()) == {
        "sub_public",
        "func_public",
    }
    assert set(fortran_file.modules[0].all_types.keys()) == {
        "type_public",
        "type_private",
    }
    assert set(fortran_file.modules[0].pub_types.keys()) == {
        "type_public",
    }
    assert set(fortran_file.modules[0].all_vars.keys()) == {
        "int_public",
        "int_private",
        "real_public",
        "real_private",
    }
    assert set(fortran_file.modules[0].pub_vars.keys()) == {
        "int_public",
        "real_public",
    }


def test_module_public_access(parse_fortran_file):
    data = """\
    module public_access
      public
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
    end module public_access
    """

    fortran_file = parse_fortran_file(data)
    fortran_file.modules[0].correlate(None)

    assert set(fortran_file.modules[0].all_procs.keys()) == {
        "sub_public",
        "func_public",
        "sub_private",
        "func_private",
    }
    assert set(fortran_file.modules[0].pub_procs.keys()) == {
        "sub_public",
        "func_public",
    }
    assert set(fortran_file.modules[0].all_types.keys()) == {
        "type_public",
        "type_private",
    }
    assert set(fortran_file.modules[0].pub_types.keys()) == {
        "type_public",
    }
    assert set(fortran_file.modules[0].all_vars.keys()) == {
        "int_public",
        "int_private",
        "real_public",
        "real_private",
    }
    assert set(fortran_file.modules[0].pub_vars.keys()) == {
        "int_public",
        "real_public",
    }


def test_module_private_access(parse_fortran_file):
    data = """\
    module private_access
      private
      integer :: int_public, int_private
      public :: int_public
      real :: real_private
      real, public :: real_public

      type :: type_public
        complex :: component_public
        complex, private :: component_private
      end type type_public

      type :: type_private
        character(len=1) :: string_public
        character(len=1), private :: string_private
      end type type_private

      public :: sub_public, func_public, type_public

    contains
      subroutine sub_public
      end subroutine sub_public

      subroutine sub_private
      end subroutine sub_private

      integer function func_public()
      end function func_public

      integer function func_private()
      end function func_private
    end module private_access
    """

    fortran_file = parse_fortran_file(data)
    fortran_file.modules[0].correlate(None)

    assert set(fortran_file.modules[0].all_procs.keys()) == {
        "sub_public",
        "func_public",
        "sub_private",
        "func_private",
    }
    assert set(fortran_file.modules[0].pub_procs.keys()) == {
        "sub_public",
        "func_public",
    }
    assert set(fortran_file.modules[0].all_types.keys()) == {
        "type_public",
        "type_private",
    }
    assert set(fortran_file.modules[0].pub_types.keys()) == {
        "type_public",
    }
    assert set(fortran_file.modules[0].all_vars.keys()) == {
        "int_public",
        "int_private",
        "real_public",
        "real_private",
    }
    assert set(fortran_file.modules[0].pub_vars.keys()) == {
        "int_public",
        "real_public",
    }
