from ford.sourceform import (
    FortranSourceFile,
    FortranModule,
    FortranBase,
    parse_type,
    ParsedType,
    line_to_variables,
    GenericSource,
)
from ford.fortran_project import find_used_modules
from ford import ProjectSettings
from ford._markdown import MetaMarkdown

from dataclasses import dataclass, field
from typing import Union, List, Optional
from itertools import chain
from textwrap import dedent

import pytest


class FakeProject:
    def __init__(self, procedures=None):
        self.procedures = procedures or []


@pytest.fixture
def parse_fortran_file(copy_fortran_file):
    def parse_file(data, **kwargs):
        filename = copy_fortran_file(data)
        settings = ProjectSettings(**kwargs)
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


def test_type_visibility_attributes(parse_fortran_file):
    """Check that we can set visibility attributes on types, #388"""

    data = """\
    module default_public
      type no_attrs
      end type no_attrs

      type, public :: public_attr
      end type public_attr

      type, private :: private_attr
      end type private_attr

      type, public :: public_attr_private_components
        private
      end type public_attr

      type, private :: private_attr_public_components
        public
      end type private_attr
    end module default_public

    module default_private
      private

      type no_attrs
      end type no_attrs

      type, public :: public_attr
      end type public_attr

      type, private :: private_attr
      end type private_attr

      type, public :: public_attr_private_components
        private
      end type public_attr

      type, private :: private_attr_public_components
        public
      end type private_attr
    end module default_private
    """

    source = parse_fortran_file(data)
    public_no_attrs = source.modules[0].types[0]
    public_public_attr = source.modules[0].types[1]
    public_private_attr = source.modules[0].types[2]
    public_public_attr_components = source.modules[0].types[3]
    public_private_attr_components = source.modules[0].types[4]

    assert public_no_attrs.permission == "public"
    assert public_public_attr.permission == "public"
    assert public_private_attr.permission == "private"
    assert public_public_attr_components.permission == "public"
    assert public_private_attr_components.permission == "private"

    private_no_attrs = source.modules[1].types[0]
    private_public_attr = source.modules[1].types[1]
    private_private_attr = source.modules[1].types[2]
    private_public_attr_components = source.modules[1].types[3]
    private_private_attr_components = source.modules[1].types[4]

    assert private_no_attrs.permission == "private"
    assert private_public_attr.permission == "public"
    assert private_private_attr.permission == "private"
    assert private_public_attr_components.permission == "public"
    assert private_private_attr_components.permission == "private"


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
    assert set(call[-1] for call in program.calls) == expected_calls


@pytest.mark.parametrize(
    ["call_segment", "expected"],
    [
        (
            """
            USE m_baz, ONLY: t_bar
            USE m_foo, ONLY: t_baz

            TYPE(t_bar) :: v_bar
            TYPE(t_baz) :: var
            var = v_bar%p_foo()
            """,
            ["p_foo"],
        ),
        (
            """
            USE m_baz, ONLY: t_bar

            TYPE(t_bar) :: v_bar
            INTEGER :: var
            var = v_bar%v_foo(1)
            """,
            [],
        ),
        (
            """
            USE m_baz, ONLY: t_bar

            TYPE(t_bar) :: v_bar
            INTEGER :: var
            var = [v_bar%v_foo(1)]
            """,
            [],
        ),
        (
            """
            USE m_baz, ONLY: t_bar

            TYPE(t_bar) :: v_bar
            INTEGER, DIMENSION(:), ALLOCATABLE :: var
            var = v_bar%v_baz%p_baz()
            """,
            ["p_baz"],
        ),
        (
            """
            USE m_baz, ONLY: t_bar
            USE m_foo, ONLY: t_baz

            TYPE(t_bar) :: v_bar
            TYPE(t_baz) :: var
            var = v_bar%t_foo%p_foo()
            """,
            ["p_foo"],
        ),
        (
            """
            USE m_baz, ONLY: t_bar
            USE m_foo, ONLY: t_baz

            TYPE(t_bar) :: v_bar
            TYPE(t_baz) :: var(1)
            var = [v_bar%t_foo%p_foo()]
            """,
            ["p_foo"],
        ),
        (
            """
            USE m_baz, ONLY: t_bar

            TYPE(t_bar), DIMENSION(2) :: v_bar
            INTEGER :: var
            var = v_bar(1)%v_baz%v_faz(1)
            """,
            [],
        ),
        (
            """
            USE m_baz, ONLY: t_bar

            TYPE(t_bar), DIMENSION(2) :: v_bar
            call v_bar(1)%renamed()
            """,
            ["renamed"],
        ),
        (
            """
            USE m_baz, ONLY: t_bar

            TYPE(t_bar), DIMENSION(2) :: v_bar
            call v_bar ( 1 ) % p_bar
            """,
            ["p_bar"],
        ),
        (
            """
            USE m_baz, ONLY: t_bar

            TYPE(t_bar) :: v_bar
            call v_bar % p_bar ( v_bar % v_baz % p_baz () )
            """,
            ["p_bar", "p_baz"],
        ),
        (
            """
            USE m_foo, ONLY: t_baz
            USE m_baz, ONLY: p_buz

            TYPE(t_baz) :: var_baz
            call p_buz(var_baz%p_baz())
            """,
            ["p_baz", "p_buz"],
        ),
        (
            """
            USE m_foo, ONLY: t_baz

            TYPE(t_baz) :: var_baz
            write(*,*) var_baz%p_baz()
            """,
            ["p_baz"],
        ),
        (
            """
            USE m_baz, ONLY: t_bar
            TYPE(t_bar) :: v_bar
            ASSOCIATE (tmp => v_bar)
                CALL tmp%p_bar()
            END ASSOCIATE
            """,
            ["p_bar"],
        ),
        (
            """
            USE m_baz, ONLY: t_bar
            TYPE(t_bar) :: v_bar
            INTEGER, DIMENSION(2) :: var
            ASSOCIATE (tmp => v_bar%v_baz)
                var = tmp%p_baz()
            END ASSOCIATE
            """,
            ["p_baz"],
        ),
        (
            """
            USE m_baz, ONLY: t_bar
            TYPE(t_bar) :: v_bar
            INTEGER :: var
            ASSOCIATE (tmp => v_bar%v_baz)
                ASSOCIATE (tmp2 => tmp%p_baz())
                END ASSOCIATE
            END ASSOCIATE
            """,
            ["p_baz"],
        ),
        (
            """
            USE m_baz, ONLY: t_bar
            TYPE(t_bar) :: v_bar
            INTEGER, DIMENSION(1) :: var_arr
            ASSOCIATE (tmp => v_bar%v_baz)
                ASSOCIATE (tmp => tmp%v_faz)
                    var_arr = tmp
                END ASSOCIATE
                var_arr = tmp%p_baz()
            END ASSOCIATE
            """,
            ["p_baz"],
        ),
        (
            """
            USE m_baz, ONLY: t_bar
            INTEGER :: var = 10
            ASSOCIATE (tmp => var)
                var = tmp
            END ASSOCIATE
            """,
            [],
        ),
        (
            """
            USE m_baz, ONLY: t_bar
            TYPE(t_bar) :: v_bar
            ASSOCIATE (tmp => v_bar%p_foo())
                PRINT *, tmp
            END ASSOCIATE
            """,
            ["p_foo"],
        ),
        (
            """
            USE m_baz, ONLY: t_bar
            TYPE(t_bar) :: v_bar
            INTEGER, DIMENSION(2) :: var_arr
            ASSOCIATE (tmp => v_bar, arr => var_arr)
                CALL tmp%p_bar()
                arr = tmp%v_baz%p_baz()
            END ASSOCIATE
            """,
            ["p_bar", "p_baz"],
        ),
        (
            """
            USE m_baz, ONLY: t_bar
            TYPE(t_bar) :: v_bar
            INTEGER, DIMENSION(2) :: var_arr
            ASSOCIATE (tmp => v_bar)
                ASSOCIATE (tmp2 => tmp%v_baz%p_baz())
                END ASSOCIATE
            END ASSOCIATE
            """,
            ["p_baz"],
        ),
        (
            """
            ASSOCIATE (tmp => p_faz(p_fuz(1)))
            END ASSOCIATE
            """,
            ["p_faz", "p_fuz"],
        ),
        (
            """
            USE m_baz, ONLY: t_unknown_parent
            TYPE(t_unknown_parent)
            call t_unknown_parent%known_method()
            """,
            ["known_method"],
        ),
    ],
)
def test_type_chain_function_and_subroutine_calls(
    parse_fortran_file, call_segment, expected
):
    data = f"""\
    MODULE m_foo
        IMPLICIT NONE
        TYPE :: t_baz
            INTEGER, DIMENSION(:), ALLOCATABLE :: v_faz
        CONTAINS
            PROCEDURE :: p_baz
        END TYPE t_baz

        CONTAINS

        FUNCTION p_baz(self) RESULT(ret_val)
            CLASS(t_baz), INTENT(IN) :: self
            INTEGER, DIMENSION(:), ALLOCATABLE :: ret_val
        END FUNCTION p_baz

    END MODULE m_foo

    MODULE m_bar
        TYPE :: t_foo
            INTEGER, DIMENSION(:), ALLOCATABLE :: v_foo
        CONTAINS
            PROCEDURE :: p_foo
        END TYPE t_foo

        CONTAINS

        FUNCTION p_foo(self) RESULT(ret_val)
            USE m_foo, ONLY: t_baz

            CLASS(t_foo), INTENT(IN) :: self
            TYPE(t_baz) :: ret_val
        END FUNCTION p_foo

    END MODULE m_bar

    MODULE m_baz

        USE m_foo, ONLY: t_baz
        USE m_bar, ONLY: t_foo
        USE unknown_module
        TYPE, EXTENDS(t_foo) :: t_bar
            TYPE(t_baz) :: v_baz
        CONTAINS
            PROCEDURE :: p_bar
            PROCEDURE :: renamed => p_bar
        END TYPE t_bar

        TYPE, EXTENDS(unknown_type) :: t_unknown_parent
        CONTAINS
            PROCEDURE, NOPASS :: known_method
        END TYPE

        CONTAINS

        SUBROUTINE p_bar(self)
            CLASS(t_bar), INTENT(IN) :: self
        END SUBROUTINE p_bar

        SUBROUTINE p_buz(var_int)
            INTEGER, DIMENSION(2), INTENT(IN) :: var_int
        END SUBROUTINE p_buz

        SUBROUTINE known_method()
        END SUBROUTINE

    END MODULE m_baz

    MODULE m_main

        CONTAINS
        
        FUNCTION p_faz(arg) RESULT(ret_val)
            INTEGER, INTENT(IN) :: arg
            INTEGER :: ret_val
        END FUNCTION p_faz

        FUNCTION p_fuz(arg) RESULT(ret_val)
            INTEGER, INTENT(IN) :: arg
            INTEGER :: ret_val
        END FUNCTION p_fuz
        
        SUBROUTINE main
            {call_segment}
        END SUBROUTINE main

    END MODULE m_main
    """

    fortran_file = parse_fortran_file(data)
    fp = FakeProject()
    modules = {module.name: module for module in fortran_file.modules}
    for module in modules.values():
        find_used_modules(module, modules.values(), [], [])

    # correlation order is important
    modules["m_foo"].correlate(fp)
    modules["m_bar"].correlate(fp)
    modules["m_baz"].correlate(fp)
    modules["m_main"].correlate(fp)

    main_subroutines = {sub.name: sub for sub in modules["m_main"].subroutines}
    calls = main_subroutines["main"].calls

    assert len(calls) == len(expected)

    calls_sorted = sorted(calls, key=lambda x: getattr(x, "name", x))
    expected_sorted = sorted(expected)
    for call, expected_name in zip(calls_sorted, expected_sorted):
        assert isinstance(call, FortranBase)

        assert call.name == expected_name


def test_call_in_module_procedure(parse_fortran_file):
    data = """\
    module foo
      type :: nuz
      contains
        procedure :: cor
      end type nuz
      interface
        module subroutine bar()
        end subroutine bar
      end interface
    contains
      function cor(this_) result (ret_val)
        class (nuz), intent(in) :: this_
        real :: ret_val
      end function cor
    end module foo

    submodule(foo) baz
    contains
      module procedure bar
        type (nuz) :: var
        real :: val
        val = var%cor()
      end procedure bar
    end submodule baz
    """
    expected = ["cor"]

    fortran_file = parse_fortran_file(data, display=["public", "protected", "private"])
    fp = FakeProject()
    modules = {
        module.name: module
        for module in chain(fortran_file.modules, fortran_file.submodules)
    }
    for module in modules.values():
        find_used_modules(module, modules.values(), [], [])

    # correlation order is important
    modules["foo"].correlate(fp)
    modules["baz"].correlate(fp)

    main_subroutines = {sub.name: sub for sub in modules["baz"].modprocedures}
    calls = main_subroutines["bar"].calls

    assert len(calls) == len(expected)

    calls_sorted = sorted(calls, key=lambda x: getattr(x, "name", x))
    expected_sorted = sorted(expected)
    for call, expected_name in zip(calls_sorted, expected_sorted):
        assert isinstance(call, FortranBase)

        assert call.name == expected_name


def test_submodule_private_var_call(parse_fortran_file):
    data = """\
    module foo
      type :: nuz
        integer :: var
      end type nuz

      type(nuz), dimension(2), private :: pri_var

      interface
        module subroutine bar()
        end subroutine bar
      end interface
    end module foo

    submodule(foo) baz
    contains
      module procedure bar
        integer :: val
        val = pri_var(1)%var
      end procedure bar
    end submodule baz
    """

    fortran_file = parse_fortran_file(data)
    fp = FakeProject()
    modules = {
        module.name: module
        for module in chain(fortran_file.modules, fortran_file.submodules)
    }
    for module in modules.values():
        find_used_modules(module, modules.values(), [], [])

    # correlation order is important
    modules["foo"].correlate(fp)
    modules["baz"].correlate(fp)

    main_subroutines = {sub.name: sub for sub in modules["baz"].modprocedures}
    calls = main_subroutines["bar"].calls

    assert calls == []


def test_internal_proc_arg_var_call(parse_fortran_file):
    data = """\
    module foo
      type :: nuz
        integer :: var
      end type nuz
      type(nuz), dimension(2), private :: pri_var
    contains
      subroutine bar(nuz_var)
        class(nuz), dimension(2) :: nuz_var
      contains
        subroutine baz
          integer :: val
          val = nuz_var(1)%var
        end subroutine baz
      end subroutine bar
    end module foo
    """

    fortran_file = parse_fortran_file(data)
    fp = FakeProject()
    modules = {module.name: module for module in fortran_file.modules}
    for module in modules.values():
        find_used_modules(module, modules.values(), [], [])

    # correlation order is important
    modules["foo"].correlate(fp)

    calls = modules["foo"].subroutines[0].subroutines[0].calls

    assert calls == []


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
    """No function calls in `format` statements are allowed, so don't
    confuse them with format specifiers. Issue #350"""

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
    fortran_file.modules[0].correlate(FakeProject())

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
    fortran_file.modules[0].correlate(FakeProject())

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
    fortran_file.modules[0].correlate(FakeProject())

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


def test_module_procedure_case(parse_fortran_file):
    """Check that submodule procedures in interface blocks are parsed correctly. Issue #353"""
    data = """\
    module a
      implicit none
      interface
        MODULE SUBROUTINE square( x )
          integer, intent(inout):: x
        END SUBROUTINE square
        module subroutine cube( x )
          integer, intent(inout):: x
        end subroutine cube
        MODULE FUNCTION square_func( x )
          integer, intent(in):: x
        END FUNCTION square_func
        module function cube_func( x )
          integer, intent(inout):: x
        end function cube_func
      end interface
    end module a

    submodule (a) b
      implicit none
    contains
      MODULE PROCEDURE square
        x = x * x
      END PROCEDURE square
      module PROCEDURE cube
        x = x * x * x
      END PROCEDURE cube
      MODULE PROCEDURE square_func
        square_func = x * x
      END PROCEDURE square_func
      module procedure cube_func
        cube_func = x * x * x
      end procedure cube_func
    end submodule b
    """

    fortran_file = parse_fortran_file(data)
    module = fortran_file.modules[0]
    assert len(module.interfaces) == 4
    assert module.interfaces[0].procedure.module
    assert module.interfaces[1].procedure.module
    assert module.interfaces[2].procedure.module
    assert module.interfaces[3].procedure.module


def test_submodule_ancestors(parse_fortran_file):
    """Check that submodule ancestors and parents are correctly identified"""

    data = """\
    module mod_a
    end module mod_a

    submodule (mod_a) mod_b
    end submodule mod_b

    submodule (mod_a) mod_c
    end submodule mod_c

    submodule (mod_a:mod_c) mod_d
    end submodule mod_d
    """

    fortran_file = parse_fortran_file(data)

    mod_b = fortran_file.submodules[0]
    mod_c = fortran_file.submodules[1]
    mod_d = fortran_file.submodules[2]

    assert mod_b.parent_submodule is None
    assert mod_b.ancestor_module == "mod_a"

    assert mod_c.parent_submodule is None
    assert mod_c.ancestor_module == "mod_a"

    assert mod_d.parent_submodule == "mod_c"
    assert mod_d.ancestor_module == "mod_a"


@pytest.mark.parametrize(
    ["variable_decl", "expected"],
    [
        ("integer i", ParsedType("integer", "i")),
        ("integer :: i", ParsedType("integer", ":: i")),
        ("integer ( int32 ) :: i", ParsedType("integer", ":: i", "int32")),
        ("real r", ParsedType("real", "r")),
        ("real(real64) r", ParsedType("real", "r", "real64")),
        ("REAL( KIND  =  8) :: r, x, y", ParsedType("real", ":: r, x, y", "8")),
        ("REAL( 8 ) :: r, x, y", ParsedType("real", ":: r, x, y", "8")),
        ("complex*16 znum", ParsedType("complex", "znum", "16")),
        (
            "character(len=*) :: string",
            ParsedType("character", ":: string", strlen="*"),
        ),
        (
            "character(len=:) :: string",
            ParsedType("character", ":: string", strlen=":"),
        ),
        ("character(12) :: string", ParsedType("character", ":: string", strlen="12")),
        (
            "character(var) :: string",
            ParsedType("character", ":: string", strlen="var"),
        ),
        ("character :: string", ParsedType("character", ":: string", strlen="1")),
        (
            "character(LEN=12) :: string",
            ParsedType("character", ":: string", strlen="12"),
        ),
        (
            "CHARACTER(KIND= kind('0') ,  len =12) :: string",
            ParsedType("character", ":: string", kind='kind("a")', strlen="12"),
        ),
        (
            "CHARACTER(KIND=kanji,  len =12) :: string",
            ParsedType("character", ":: string", kind="kanji", strlen="12"),
        ),
        (
            "CHARACTER(  len =   12,KIND=kanji) :: string",
            ParsedType("character", ":: string", kind="kanji", strlen="12"),
        ),
        (
            "CHARACTER( 12,kanji ) :: string",
            ParsedType("character", ":: string", kind="kanji", strlen="12"),
        ),
        (
            "CHARACTER(  kind=    kanji) :: string",
            ParsedType("character", ":: string", kind="kanji", strlen="1"),
        ),
        ("double PRECISION dp", ParsedType("double precision", "dp")),
        ("DOUBLE   complex dc", ParsedType("double complex", "dc")),
        (
            "type(something) :: thing",
            ParsedType("type", ":: thing", proto=["something", ""]),
        ),
        (
            "type(character(kind=kanji, len=10)) :: thing",
            ParsedType("type", ":: thing", proto=["character", "kind=kanji,len=10"]),
        ),
        (
            "class(foo) :: thing",
            ParsedType("class", ":: thing", proto=["foo", ""]),
        ),
        (
            "procedure(bar) :: thing",
            ParsedType("procedure", ":: thing", proto=["bar", ""]),
        ),
        ("Vec :: vector", ParsedType("vec", ":: vector")),
        ("Mat :: matrix", ParsedType("mat", ":: matrix")),
    ],
)
def test_parse_type(variable_decl, expected):
    # Tokeniser will have previously replaced strings with index into
    # this list
    capture_strings = ['"a"']
    result = parse_type(variable_decl, capture_strings, ["Vec", "Mat"])
    assert result.vartype == expected.vartype
    assert result.kind == expected.kind
    assert result.strlen == expected.strlen
    assert result.proto == expected.proto
    assert result.rest == expected.rest


class FakeSource:
    def __init__(self):
        self.text = iter(["end subroutine", "end module"])

    def __next__(self):
        return next(self.text)

    def pass_back(self, line):
        pass


@dataclass
class FakeParent:
    strings: List[str] = field(default_factory=lambda: ['"Hello"', "'World'"])
    settings: ProjectSettings = field(default_factory=ProjectSettings)
    obj: str = "module"
    parent = None
    display: List[str] = field(default_factory=list)
    _to_be_markdowned: List[FortranBase] = field(default_factory=list)


def _make_list_str() -> List[str]:
    """This is just to stop mypy complaining for ``attribs`` below"""
    return []


@dataclass
class FakeVariable:
    name: str
    vartype: str
    parent: Optional[FakeParent] = field(default_factory=FakeParent)
    attribs: Optional[List[str]] = field(default_factory=_make_list_str)
    intent: str = ""
    optional: bool = False
    permission: str = "public"
    parameter: bool = False
    kind: Optional[str] = None
    strlen: Optional[str] = None
    proto: Union[None, str, List[str]] = None
    doc_list: List[str] = field(default_factory=list)
    points: bool = False
    initial: Optional[str] = None


@pytest.mark.parametrize(
    ["line", "expected_variables"],
    [
        ("integer foo", [FakeVariable("foo", "integer")]),
        ("integer :: foo", [FakeVariable("foo", "integer")]),
        (
            "real :: foo, bar",
            [FakeVariable("foo", "real"), FakeVariable("bar", "real")],
        ),
        (
            "real, allocatable :: foo",
            [FakeVariable("foo", "real", attribs=["allocatable"])],
        ),
        (
            "integer, intent ( in  out)::zing",
            [FakeVariable("zing", "integer", intent="inout")],
        ),
        (
            "real(real64), optional, intent(in) :: foo, bar",
            [
                FakeVariable("foo", "real", kind="real64", optional=True, intent="in"),
                FakeVariable("bar", "real", kind="real64", optional=True, intent="in"),
            ],
        ),
        (
            "character ( len = 24 , kind = 4), parameter :: char = '0', far = '1'",
            [
                FakeVariable(
                    "char",
                    "character",
                    strlen="24",
                    kind="4",
                    parameter=True,
                    initial='"Hello"',
                ),
                FakeVariable(
                    "far",
                    "character",
                    strlen="24",
                    kind="4",
                    parameter=True,
                    initial="'World'",
                ),
            ],
        ),
        (
            "procedure(foo) :: bar",
            [FakeVariable("bar", "procedure", proto=["foo", ""])],
        ),
        (
            "type(foo) :: bar = 42",
            [FakeVariable("bar", "type", proto=["foo", ""], initial="42")],
        ),
        (
            "class(foo) :: var1, var2",
            [
                FakeVariable("var1", "class", proto=["foo", ""]),
                FakeVariable("var2", "class", proto=["foo", ""]),
            ],
        ),
        (
            "class(*) :: polymorphic",
            [FakeVariable("polymorphic", "class", proto=["*", ""])],
        ),
    ],
)
def test_line_to_variable(line, expected_variables):
    variables = line_to_variables(FakeSource(), line, "public", FakeParent())
    attributes = expected_variables[0].__dict__
    attributes.pop("parent")

    for variable, expected in zip(variables, expected_variables):
        for attr in attributes:
            variable_attr = getattr(variable, attr)
            expected_attr = getattr(expected, attr)
            assert variable_attr == expected_attr, attr

    if len(expected_variables) > 1:
        for attr in attributes:
            attribute = getattr(variable, attr)
            if not isinstance(attribute, list):
                continue
            proto_ids = [id(getattr(variable, attr)) for variable in variables]
            assert len(proto_ids) == len(set(proto_ids)), attr


def test_markdown_header_bug286(parse_fortran_file):
    """Check that markdown headers work, issue #286"""
    data = """\
    module myModule
    contains
      subroutine printSquare(x)
        !! ## My Header
        !! This should be one section, but the header doesn't work
        integer, intent(in) :: x
        write(*,*) x*x
      end subroutine printSquare
    end module myModule
    """

    fortran_file = parse_fortran_file(data)
    md = MetaMarkdown()

    subroutine = fortran_file.modules[0].subroutines[0]
    subroutine.markdown(md)

    assert subroutine.doc.startswith("<h2>My Header</h2>")


def test_markdown_codeblocks_bug286(parse_fortran_file):
    """Check that markdown codeblocks work, issue #287"""
    data = """\
    module myModule
    contains
      subroutine printSquare(x)
        !! This codeblock should not be inline:
        !! ```
        !! printSquare(4)
        !! ```
        integer, intent(in) :: x
        write(*,*) x*x
      end subroutine printSquare
    end module myModule
    """

    fortran_file = parse_fortran_file(data)
    md = MetaMarkdown()

    subroutine = fortran_file.modules[0].subroutines[0]
    subroutine.markdown(md)

    assert "<code>printSquare(4)" in subroutine.doc
    assert "<div" in subroutine.doc


def test_markdown_meta_reset(parse_fortran_file):
    """Check that markdown metadata is reset between entities"""
    data = """\
    module myModule
      !! version: 0.1.0
    contains
      subroutine printSquare(x)
        !! author: Test name
        integer, intent(in) :: x
        write(*,*) x*x
      end subroutine printSquare
      subroutine printCube(x)
        integer, intent(in) :: x
        write(*,*) x*x*x
      end subroutine printCube
    end module myModule
    """

    fortran_file = parse_fortran_file(data)
    md = MetaMarkdown()
    module = fortran_file.modules[0]
    module.markdown(md)
    assert module.meta.version == "0.1.0"
    assert module.subroutines[0].meta.author == "Test name"
    assert module.subroutines[1].meta.author is None


def test_multiline_attributes(parse_fortran_file):
    """Check that specifying attributes over multiple lines works"""

    data = """\
    program prog
      real x
      dimension x(:)
      allocatable x
      integer, allocatable, dimension(:) :: y
      complex z
      allocatable z(:)

      allocate(x(1), y(1), z(1))
    end program prog
    """

    fortran_file = parse_fortran_file(data)
    prog = fortran_file.programs[0]

    for variable in prog.variables:
        assert (
            "allocatable" in variable.attribs
        ), f"Missing 'allocatable' in '{variable}' attributes"
        assert (
            variable.dimension == "(:)" or "dimension(:)" in variable.attribs
        ), f"Wrong dimension for '{variable}'"


def test_markdown_source_meta(parse_fortran_file):
    """Check that specifying 'source' in the procedure meta block is processed"""

    data = """\
    subroutine with_source
    !! source: true
    !!
    !! some docs
    end subroutine with_source
    """

    md = MetaMarkdown()

    fortran_file = parse_fortran_file(data)
    subroutine = fortran_file.subroutines[0]
    subroutine.markdown(md)

    assert subroutine.meta.source is True
    assert "with_source" in subroutine.src


def test_markdown_source_settings(parse_fortran_file):
    """Check that specifying 'source' in the settings works"""

    data = """\
    subroutine with_source
    !! some docs
    end subroutine with_source
    """

    md = MetaMarkdown()
    fortran_file = parse_fortran_file(data, source=True)
    subroutine = fortran_file.subroutines[0]
    subroutine.markdown(md)

    assert subroutine.meta.source is True
    assert "with_source" in subroutine.src


@pytest.mark.parametrize(
    ["snippet", "expected_error", "expected_name"],
    (
        (
            "program foo\n contains\n contains",
            "Multiple CONTAINS",
            "foo",
        ),
        (
            "program foo\n interface bar\n contains",
            "Unexpected CONTAINS",
            "bar",
        ),
        ("end", "END statement", "test.f90"),
        ("program foo\n module procedure bar", "Unexpected MODULE PROCEDURE", "foo"),
        ("program foo\n module bar", "Unexpected MODULE", "foo"),
        (
            "program foo\n submodule (foo) bar \n end program foo",
            "Unexpected SUBMODULE",
            "program 'foo'",
        ),
        ("program foo\n program bar", "Unexpected PROGRAM", "foo"),
        (
            "program foo\n end program foo\n program bar \n end program bar",
            "Multiple PROGRAM",
            "test.f90",
        ),
        (
            "program foo\n subroutine bar \n end subroutine \n end program",
            "Unexpected SUBROUTINE",
            "program 'foo'",
        ),
        (
            "program foo\n integer function bar() \n end function bar\n end program foo",
            "Unexpected FUNCTION",
            "program 'foo'",
        ),
    ),
)
def test_bad_parses(snippet, expected_error, expected_name, parse_fortran_file):
    with pytest.raises(ValueError) as e:
        parse_fortran_file(snippet, dbg=False)

    assert expected_error in e.value.args[0]
    assert expected_name in e.value.args[0]


def test_routine_iterator(parse_fortran_file):
    data = """\
    module foo
      interface
        module subroutine modsub1()
        end subroutine modsub1
        module subroutine modsub2()
        end subroutine modsub2
        module integer function modfunc1()
        end function modfunc1
        module integer function modfunc2()
        end function modfunc2
      end interface
    contains
      subroutine sub1()
      end subroutine sub1
      subroutine sub2()
      end subroutine sub2
      integer function func1()
      end function func1
      integer function func2()
      end function func2
    end module foo

    submodule (foo) bar
    contains
      module subroutine modsub1
      end subroutine modsub1
      module subroutine modsub2
      end subroutine modsub2
      module procedure modfunc1
      end procedure modfunc1
      module procedure modfunc2
      end procedure modfunc2

      subroutine sub3()
      end subroutine sub3
      subroutine sub4()
      end subroutine sub4
      integer function func3()
      end function func3
      integer function func4()
      end function func4
    end submodule bar
    """

    fortran_file = parse_fortran_file(data)

    module = fortran_file.modules[0]
    assert sorted([proc.name for proc in module.routines]) == [
        "func1",
        "func2",
        "sub1",
        "sub2",
    ]

    submodule = fortran_file.submodules[0]
    assert sorted([proc.name for proc in submodule.routines]) == [
        "func3",
        "func4",
        "modfunc1",
        "modfunc2",
        "modsub1",
        "modsub2",
        "sub3",
        "sub4",
    ]


def test_type_component_permissions(parse_fortran_file):
    data = """\
    module default_access
      private
      type :: type_default
        complex :: component_public
        complex, private :: component_private
      contains
        procedure :: sub_public
        procedure, private :: sub_private
      end type type_default

      type, public :: type_public
        public
        complex :: component_public
        complex, private :: component_private
      contains
        public
        procedure :: sub_public
        procedure, private :: sub_private
      end type type_public

      type :: type_private
        private
        character(len=1), public :: string_public
        character(len=1) :: string_private
      contains
        private
        procedure, public :: sub_public
        procedure :: sub_private
      end type type_private

      type :: type_public_private
        public
        character(len=1) :: string_public
        character(len=1), private :: string_private
      contains
        private
        procedure, public :: sub_public
        procedure :: sub_private
      end type type_public_private

      type :: type_private_public
        private
        character(len=1), public :: string_public
        character(len=1) :: string_private
      contains
        public
        procedure :: sub_public
        procedure, private :: sub_private
      end type type_private_public

      public :: type_default, type_private_public, type_public_private
    contains
      subroutine sub_public
      end subroutine sub_public

      subroutine sub_private
      end subroutine sub_private
    end module default_access
    """

    fortran_file = parse_fortran_file(data)
    fortran_file.modules[0].correlate(FakeProject())

    for ftype in fortran_file.modules[0].types:
        assert (
            ftype.variables[0].permission == "public"
        ), f"{ftype.name}::{ftype.variables[0].name}"
        assert (
            ftype.variables[1].permission == "private"
        ), f"{ftype.name}::{ftype.variables[1].name}"
        assert (
            ftype.boundprocs[0].permission == "public"
        ), f"{ftype.name}::{ftype.boundprocs[0].name}"
        assert (
            ftype.boundprocs[1].permission == "private"
        ), f"{ftype.name}::{ftype.boundprocs[1].name}"


def test_variable_formatting(parse_fortran_file):
    data = """\
    module foo_m
      character(kind=kind('a'), len=4), dimension(:, :), allocatable :: multidimension_string
      type :: bar
      end type bar
      type(bar), parameter :: something = bar()
    contains
      type(bar) function quux()
      end function quux
    end module foo_m
    """

    fortran_file = parse_fortran_file(data)
    fortran_file.modules[0].correlate(FakeProject())
    variable0 = fortran_file.modules[0].variables[0]
    variable1 = fortran_file.modules[0].variables[1]

    assert variable0.full_type == "character(kind=kind('a'), len=4)"
    assert (
        variable0.full_declaration
        == "character(kind=kind('a'), len=4), dimension(:, :), allocatable"
    )
    assert variable1.full_type == "type(bar)"
    assert variable1.full_declaration == "type(bar), parameter"

    function = fortran_file.modules[0].functions[0]
    assert function.retvar.full_declaration == "type(bar)"


def test_url(parse_fortran_file):
    data = """\
    program prog_foo
      integer :: int_foo
    contains
      subroutine sub_foo
      end subroutine sub_foo
      function func_foo()
      end function func_foo
    end program prog_foo

    module mod_foo
      real :: real_foo
      interface inter_foo
        module procedure foo1, foo2
      end interface inter_foo
      type :: foo_t
        integer :: int_bar
      end type
      enum, bind(C)
        enumerator :: red = 4, blue = 9
        enumerator :: yellow
      end enum
    contains
      subroutine foo1()
      end subroutine foo1
      subroutine foo2(x)
        integer :: x
      end subroutine foo2
    end module mod_foo

    submodule (mod_foo) submod_foo
    end submodule submod_foo
    """

    fortran_file = parse_fortran_file(data)
    program = fortran_file.programs[0]
    module = fortran_file.modules[0]
    submodule = fortran_file.submodules[0]

    assert program.get_dir() == "program"
    assert module.get_dir() == "module"
    assert submodule.get_dir() == "module"
    assert program.subroutines[0].get_dir() == "proc"
    assert program.functions[0].get_dir() == "proc"
    assert module.subroutines[0].get_dir() == "proc"
    assert module.interfaces[0].get_dir() == "interface"
    assert program.variables[0].get_dir() is None
    assert module.variables[0].get_dir() is None
    assert module.enums[0].get_dir() is None

    assert program.full_url.endswith("program/prog_foo.html")
    assert module.full_url.endswith("module/mod_foo.html")
    assert submodule.full_url.endswith("module/submod_foo.html")
    assert program.subroutines[0].full_url.endswith("proc/sub_foo.html")
    assert program.functions[0].full_url.endswith("proc/func_foo.html")
    assert module.subroutines[0].full_url.endswith("proc/foo1.html")
    assert module.interfaces[0].full_url.endswith("interface/inter_foo.html")
    assert program.variables[0].full_url.endswith(
        "program/prog_foo.html#variable-int_foo"
    )
    assert module.variables[0].full_url.endswith(
        "module/mod_foo.html#variable-real_foo"
    )


def test_single_character_interface(parse_fortran_file):
    data = """\
    module a
      interface b !! some comment
        module procedure c
      end interface b
    end module a
    """
    fortran_file = parse_fortran_file(data)
    assert fortran_file.modules[0].interfaces[0].name == "b"
    assert fortran_file.modules[0].interfaces[0].doc_list == [" some comment"]


def test_module_procedure_in_module(parse_fortran_file):
    data = """\
    module foo_mod
      interface
        module subroutine quaxx
        end subroutine quaxx
      end interface
    contains
      module procedure quaxx
        print*, "implementation"
      end procedure
    end module foo_mod
    """

    fortran_file = parse_fortran_file(data)
    module = fortran_file.modules[0]
    module.correlate(FakeProject())

    interface = module.interfaces[0]
    assert interface.name == "quaxx"
    modproc = module.modprocedures[0]

    assert interface.procedure.module == modproc
    assert modproc.module == interface


def test_module_interface_same_name_as_interface(parse_fortran_file):
    data = """\
    module foo_m
      interface foo
        module function foo() result(bar)
          logical bar
        end function
      end interface
    contains
      module procedure foo
        bar = .true.
      end procedure
    end module
    """

    fortran_file = parse_fortran_file(data)
    module = fortran_file.modules[0]
    module.correlate(FakeProject())

    interface = module.interfaces[0]
    assert interface.name == "foo"

    modproc = module.modprocedures[0]
    assert modproc.name == "foo"


def test_procedure_pointer(parse_fortran_file):
    data = """\
    module foo
      abstract interface
        integer pure function unary_f_t(n)
          implicit none
          integer, intent(in) :: n
        end function
      end interface

      private

      procedure(unary_f_t), pointer, public :: unary_f => null()

      interface generic_unary_f
        procedure unary_f
      end interface
    end module
    """

    fortran_file = parse_fortran_file(data)
    module = fortran_file.modules[0]
    module.correlate(FakeProject())
    assert len(module.interfaces[0].modprocs) == 0
    assert module.interfaces[0].variables[0].name == "unary_f"


def test_block_data(parse_fortran_file):
    data = """\
    block data name
      !! Block data docstring
      common /name/ foo
      !! Common block docstring

      character*31 foo(1024)
      !! Variable docstring

      data foo /'a', 'b', 'c', 'd', 'e', 1019*'0'/
    end
    """

    fortran_file = parse_fortran_file(data)
    blockdata = fortran_file.blockdata[0]

    assert blockdata.name == "name"
    assert blockdata.doc_list[0].strip() == "Block data docstring"
    assert len(blockdata.common) == 1
    assert blockdata.common[0].doc_list[0].strip() == "Common block docstring"
    assert len(blockdata.variables) == 1
    assert blockdata.variables[0].doc_list[0].strip() == "Variable docstring"


def test_subroutine_empty_args(parse_fortran_file):
    data = """\
    subroutine foo (    )
    end subroutine foo
    """

    fortran_file = parse_fortran_file(data)
    subroutine = fortran_file.subroutines[0]
    assert subroutine.args == []


def test_subroutine_whitespace(parse_fortran_file):
    data = """\
    subroutine foo (  a,b,    c,d  )
      integer :: a, b, c, d
    end subroutine foo
    """

    fortran_file = parse_fortran_file(data)
    subroutine = fortran_file.subroutines[0]
    arg_names = [arg.name for arg in subroutine.args]
    assert arg_names == ["a", "b", "c", "d"]


def test_function_empty_args(parse_fortran_file):
    data = """\
    integer function foo (    )
    end function foo
    """

    fortran_file = parse_fortran_file(data)
    function = fortran_file.functions[0]
    assert function.args == []


def test_function_whitespace(parse_fortran_file):
    data = """\
    integer function foo (  a,b,    c,d  )
      integer :: a, b, c, d
    end function foo
    """

    fortran_file = parse_fortran_file(data)
    function = fortran_file.functions[0]
    arg_names = [arg.name for arg in function.args]
    assert arg_names == ["a", "b", "c", "d"]


def test_bind_name_subroutine(parse_fortran_file):
    data = """\
    subroutine init() bind(C, name="c_init")
    end subroutine init
    """

    fortran_file = parse_fortran_file(data)
    subroutine = fortran_file.subroutines[0]

    assert subroutine.bindC == 'C, name="c_init"'


def test_bind_name_function(parse_fortran_file):
    data = """\
    integer function foo() bind(C, name="c_foo")
    end function foo
    """

    fortran_file = parse_fortran_file(data)
    function = fortran_file.functions[0]

    assert function.bindC == 'C, name="c_foo"'


def test_generic_bound_procedure(parse_fortran_file):
    data = """\
    module subdomain_m
      type subdomain_t
      contains
        procedure no_colon
        procedure :: colon
        generic :: operator(+) => no_colon, colon
      end type
      interface
        module function no_colon(lhs, rhs)
          class(subdomain_t), intent(in) :: lhs
          integer, intent(in) :: rhs
          type(subdomain_t) total
        end function
        module function colon(lhs, rhs)
          class(subdomain_t), intent(in) :: lhs, rhs
          type(subdomain_t) total
        end function
      end interface
    end module
    """

    fortran_file = parse_fortran_file(data)
    fortran_type = fortran_file.modules[0].types[0]

    expected_names = sorted(["no_colon", "colon", "operator(+)"])
    bound_proc_names = sorted([proc.name for proc in fortran_type.boundprocs])
    assert bound_proc_names == expected_names


def test_submodule_procedure_calls(parse_fortran_file):
    """Check that calls inside submodule procedures are correctly correlated"""

    data = """\
    module foo_m
      implicit none
      interface
        module function foo1(start, end) result(res)
          integer, intent(in) :: start, end
          integer :: res
        end function
      end interface
    end module

    submodule(foo_m) foo_s
      implicit none
    contains
      integer function bar(start, end)
        integer, intent(in) :: start, end
        bar = end - start
      end function

      module procedure foo1
        res = bar(start, end)
      end procedure
    end submodule
    """

    fortran_file = parse_fortran_file(data)
    fortran_file.modules[0].correlate(FakeProject())
    submodule = fortran_file.submodules[0]
    submodule.correlate(FakeProject())

    assert submodule.modprocedures[0].calls[0] == submodule.functions[0]


def test_namelist(parse_fortran_file):
    data = """\
    module mod_a
      integer :: var_a
    end module mod_a
    module mod_b
      use mod_a
      integer :: var_b
    end module mod_b

    program prog
      integer :: var_c
    contains
      subroutine sub(var_d)
        use mod_b
        integer, intent(in) :: var_d
        integer :: var_e
        namelist /namelist_a/ var_a, var_b, var_c, var_d, var_e
        !! namelist docstring
      end subroutine sub
    end program prog
    """
    fortran_file = parse_fortran_file(data)
    namelist = fortran_file.programs[0].subroutines[0].namelists[0]
    assert namelist.name == "namelist_a"

    expected_names = sorted(["var_a", "var_b", "var_c", "var_d", "var_e"])
    output_names = sorted(namelist.variables)
    assert output_names == expected_names

    assert namelist.doc_list == [" namelist docstring"]


def test_namelist_correlate(parse_fortran_file):
    data = """\
    program prog
      integer :: var_c
    contains
      subroutine sub(var_b)
        integer, intent(in) :: var_b
        integer :: var_a
        namelist /namelist_a/ var_a, var_b, var_c
      end subroutine sub
    end program prog
    """
    fortran_file = parse_fortran_file(data)
    fortran_file.programs[0].correlate(FakeProject())
    namelist = fortran_file.programs[0].subroutines[0].namelists[0]
    expected_names = sorted(["var_a", "var_b", "var_c"])
    output_names = sorted([variables.name for variables in namelist.variables])
    assert output_names == expected_names


def test_generic_source(tmp_path):
    data = """\
    #! docmark
    #* docmark_alt
    #> predocmark
    #| predocmark_alt
    """

    filename = tmp_path / "generic_source.sh"
    filename.write_text(dedent(data))

    settings = ProjectSettings(
        extra_filetypes=[{"extension": "sh", "comment": "#"}],
    )
    source = GenericSource(filename, settings)
    expected_docs = [
        "docmark",
        "docmark_alt",
        "predocmark",
        "predocmark_alt",
    ]

    assert source.doc_list == expected_docs


def test_type_bound_procedure_formatting(parse_fortran_file):
    data = """\
    module ford_example_type_mod
      type, abstract, public :: example_type
      contains
        procedure :: say_hello => example_type_say
        procedure, private, nopass :: say_int
        procedure, private, nopass :: say_real
        generic :: say_number => say_int, say_real
        procedure(say_interface), deferred :: say
        final :: example_type_finalise
      end type example_type

      interface
        subroutine say_interface(self)
          import say_type_base
          class(say_type_base), intent(inout) :: self
        end subroutine say_interface
      end interface

    contains

      subroutine example_type_say(self)
        class(example_type), intent(inout) :: self
      end subroutine example_type_say

      subroutine example_type_finalise(self)
        type(example_type), intent(inout) :: self
      end subroutine example_type_finalise

      subroutine say_int(int)
        integer, intent(in) :: int
      end subroutine say_int

      subroutine say_real(r)
        real, intent(in) :: r
      end subroutine say_real
    end module ford_example_type_mod
    """

    example_type = parse_fortran_file(data).modules[0].types[0]

    assert example_type.boundprocs[0].full_declaration == "procedure, public"
    assert example_type.boundprocs[1].full_declaration == "procedure, private, nopass"
    assert example_type.boundprocs[2].full_declaration == "procedure, private, nopass"
    assert example_type.boundprocs[3].full_declaration == "generic, public"
    assert (
        example_type.boundprocs[4].full_declaration
        == "procedure(say_interface), public, deferred"
    )


def test_type_num_lines(parse_fortran_file):
    data = """\
    module ford_example_type_mod
      type, abstract, public :: example_type
      contains
        procedure :: say_hello => example_type_say
        procedure, private, nopass :: say_int
        procedure, private, nopass :: say_real
        generic :: say_number => say_int, say_real, say_hello
        procedure(say_interface), deferred :: say
      end type example_type
      interface
        subroutine say_interface(self)
          import say_type_base
          class(say_type_base), intent(inout) :: self
        end subroutine say_interface
      end interface
    contains
      subroutine example_type_say(self)
        class(example_type), intent(inout) :: self
      end subroutine example_type_say
      subroutine say_int(int)
        integer, intent(in) :: int
      end subroutine say_int
      subroutine say_real(r)
        real, intent(in) :: r
      end subroutine say_real
    end module ford_example_type_mod
    """

    project = FakeProject()
    module = parse_fortran_file(data).modules[0]
    module.correlate(project)

    example_type = module.types[0]
    assert example_type.num_lines == 8
    assert example_type.num_lines_all == 8 + 9


def test_associate_array(parse_fortran_file):
    data = """\
    subroutine test()
      associate(phi => [1,2], theta => (/ 3, 4 /))
      end associate
    end subroutine test"""

    # Just check we can parse ok
    parse_fortran_file(data)


def test_blocks_with_type(parse_fortran_file):
    data = """\
    module foo
    contains
      subroutine sub1()
        block
          type :: t1
          end type t1
        end block
      end subroutine sub1
    end module foo
    """

    source = parse_fortran_file(data)
    module = source.modules[0]
    assert len(module.subroutines) == 1


def test_no_space_after_character_type(parse_fortran_file):
    data = """\
    CHARACTER(LEN=250)FUNCTION FirstWord( sString ) RESULT( sRes )
        CHARACTER(LEN=250)sString
    END FUNCTION FirstWord
    """

    source = parse_fortran_file(data)
    function = source.functions[0]
    assert function.name.lower() == "firstword"


def test_summary_handling_bug703(parse_fortran_file):
    """Check that `summary` works, PR #703"""
    data = """\
    !> summary: Lorem ipsum dolor sit amet, consectetur adipiscing elit.
    !>          Fusce ultrices tortor et felis tempus vehicula.
    !>          Nulla gravida, magna ut pharetra.
    !>
    !> Full description
    module test
    end module myModule
    """

    fortran_file = parse_fortran_file(data)
    md = MetaMarkdown()

    module = fortran_file.modules[0]
    module.markdown(md)

    assert "Lorem ipsum" in module.meta.summary
