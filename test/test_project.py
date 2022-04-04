from ford.sourceform import FortranSourceFile
from ford.fortran_project import Project
from ford import DEFAULT_SETTINGS
from ford.utils import normalise_path

from copy import deepcopy

import markdown
import pytest


@pytest.fixture
def copy_fortran_file(tmp_path):
    def copy_file(data):
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        filename = src_dir / "test.f90"
        with open(filename, "w") as f:
            f.write(data)
        settings = deepcopy(DEFAULT_SETTINGS)
        settings["src_dir"] = [src_dir]
        return settings

    return copy_file


def create_project(settings: dict):
    md_ext = [
        "markdown.extensions.meta",
        "markdown.extensions.codehilite",
        "markdown.extensions.extra",
    ]
    md = markdown.Markdown(
        extensions=md_ext, output_format="html5", extension_configs={}
    )

    project = Project(settings)
    project.markdown(md, "..")
    project.correlate()
    return project


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
    project = create_project(settings)
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
    project = create_project(settings)
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

      type type_public_no_attr
      end type type_public_no_attr

      type, public :: type_public_attr
      end type type_public_attr

      type, private :: type_private_attr
      end type type_private_attr

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
    project = create_project(settings)

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

      type type_public_no_attr
      end type type_public_no_attr

      type, public :: type_public_attr
      end type type_public_attr

      type, private :: type_private_attr
      end type type_private_attr

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
    project = create_project(settings)

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

      type type_no_attr
      end type type_no_attr

      type, public :: type_public_attr
      end type type_public_attr

      type, private :: type_private_attr
      end type type_private_attr

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
    project = create_project(settings)

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
        "type_no_attr",
        "type_public_attr",
    }
    assert set(project.modules[1].pub_types.keys()) == {
        "type_public",
        "type_no_attr",
        "type_public_attr",
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

      type type_no_attr
      end type type_no_attr

      type, public :: type_public_attr
      end type type_public_attr

      type, private :: type_private_attr
      end type type_private_attr

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
    project = create_project(settings)

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
        "type_no_attr",
        "type_public_attr",
    }
    assert set(project.modules[2].pub_types.keys()) == {
        "type_public",
        "type_no_attr",
        "type_public_attr",
    }
    assert set(project.modules[2].all_vars.keys()) == {
        "int_public",
        "real_public",
    }
    assert set(project.modules[2].pub_vars.keys()) == {
        "int_public",
        "real_public",
    }


def test_member_in_other_module(copy_fortran_file):
    data = """\
    module module1
      use module2, only: testInterface
      type, public, abstract :: external_type
      contains
        procedure(testInterface), nopass, deferred :: testProc
      end type external_type
    end module module1

    module module2
      type, public, abstract :: internal_type
      contains
        procedure(testInterface), nopass, deferred :: testProc
      end type internal_type

      abstract interface
        pure function testInterface(input) result(output)
          real, intent(in) :: input
          real :: output
        end function testInterface
      end interface
    end module module2
    """

    settings = copy_fortran_file(data)
    project = create_project(settings)

    module1 = project.modules[0]
    module2 = project.modules[1]

    assert (
        module1.all_types["external_type"].boundprocs[0].proto
        is module2.all_types["internal_type"].boundprocs[0].proto
    )

    assert (
        module2.all_types["internal_type"].boundprocs[0].proto.name == "testInterface"
    )


def test_display_derived_types(copy_fortran_file):
    """Check that we can set visibility attributes on types, #388"""

    data = """\
    module foo
      type no_attrs
      end type no_attrs

      type, public :: public_attr
      end type public_attr

      type, private :: private_attr
      end type private_attr
    end module foo
    """

    settings = copy_fortran_file(data)
    settings["display"] = ["public"]
    project = Project(settings)
    project.correlate()

    type_names = set([t.name for t in project.types])
    assert type_names == {"no_attrs", "public_attr"}


def test_display_derived_types_default_private(copy_fortran_file):
    """Check that we can set visibility attributes on types, #388"""

    data = """\
    module foo
      private

      type no_attrs
      end type no_attrs

      type, public :: public_attr
      end type public_attr

      type, private :: private_attr
      end type private_attr
    end module foo
    """

    settings = copy_fortran_file(data)
    settings["display"] = ["public"]
    project = create_project(settings)

    type_names = set([t.name for t in project.types])
    assert type_names == {"public_attr"}


def test_display_private_derived_types(copy_fortran_file):
    """Check that we can set visibility attributes on types, #388"""

    data = """\
    module foo
      private

      type no_attrs
      end type no_attrs

      type, public :: public_attr
      end type public_attr

      type, private :: private_attr
      end type private_attr
    end module foo
    """

    settings = copy_fortran_file(data)
    settings["display"] = ["public", "private"]
    project = create_project(settings)

    type_names = set([t.name for t in project.types])
    assert type_names == {"no_attrs", "public_attr", "private_attr"}


def test_interface_type_name(copy_fortran_file):
    """Check for shared prototype list"""
    data = """\
    module foo
      type name_t
      end type name_t

      type(name_t) :: var, var2
    end module foo
    """

    settings = copy_fortran_file(data)
    project = create_project(settings)
    proto_names = [var.proto[0].name for var in project.modules[0].variables]
    assert proto_names == ["name_t", "name_t"]


def test_imported_interface_type_name(copy_fortran_file):
    """Check for shared prototype list"""
    data = """\
    module foo
      type name_t
      end type name_t
    end module foo

    module bar
      use foo
      type(name_t), allocatable :: var(:), var2(:)
    end module bar
    """

    settings = copy_fortran_file(data)
    project = create_project(settings)
    proto_names = [var.proto[0].name for var in project.modules[1].variables]
    assert proto_names == ["name_t", "name_t"]


def test_abstract_interface_type_name(copy_fortran_file):
    """Check for shared prototype list"""
    data = """\
    module foo
      abstract interface
        subroutine hello
        end subroutine hello
      end interface

      procedure(hello) :: proc1, proc2
    end module foo
    """

    settings = copy_fortran_file(data)
    project = create_project(settings)
    proto_names = [var.proto[0].name for var in project.modules[0].variables]
    assert proto_names == ["hello", "hello"]


def test_imported_abstract_interface_type_name(copy_fortran_file):
    """Check for shared prototype list"""
    data = """\
    module foo
      abstract interface
        subroutine hello
        end subroutine hello
      end interface

    contains
      integer function goodbye()
        goodbye = 1
      end function goodbye
    end module foo

    module bar
      use foo
      procedure(hello) :: proc1, proc2
      procedure(goodbye) :: proc3, proc4
    end module bar
    """

    settings = copy_fortran_file(data)
    project = create_project(settings)
    proto_names = [var.proto[0].name for var in project.modules[1].variables]
    assert proto_names == ["hello", "hello", "goodbye", "goodbye"]


def test_display_internal_procedures(copy_fortran_file):
    """_very_ basic test of 'proc_internals' setting"""

    data = """\
    subroutine no_display_internals
    !! some docs
    integer :: local_variable
    !! This shouldn't be displayed
    end subroutine no_display_internals

    subroutine display_internals
    !! proc_internals: true
    !!
    !! some docs
    integer :: local_variable
    !! This shouldn't be displayed
    end subroutine display_internals
    """

    settings = copy_fortran_file(data)
    project = create_project(settings)

    subroutine1 = project.procedures[0]
    subroutine2 = project.procedures[1]

    assert subroutine1.variables == []
    assert len(subroutine2.variables) == 1
    assert subroutine2.variables[0].name == "local_variable"


def test_exclude_dir(tmp_path):
    exclude_dir = tmp_path / "sub1" / "sub2"
    exclude_dir.mkdir(parents=True)
    src = tmp_path / "src"
    src.mkdir()

    with open(src / "include.f90", "w") as f:
        f.write("program foo\nend program")
    with open(exclude_dir / "exclude.f90", "w") as f:
        f.write("program bar\nend program")

    settings = deepcopy(DEFAULT_SETTINGS)
    settings["src_dir"] = [tmp_path]
    settings["exclude_dir"] = [normalise_path(tmp_path, "sub1")]
    project = Project(settings)

    program_names = {program.name for program in project.programs}
    assert program_names == {"foo"}


def test_exclude(tmp_path):
    exclude_dir = tmp_path / "sub1" / "sub2"
    exclude_dir.mkdir(parents=True)
    src = tmp_path / "src"
    src.mkdir()

    with open(src / "include.f90", "w") as f:
        f.write("program foo\nend program")
    with open(exclude_dir / "exclude.f90", "w") as f:
        f.write("program bar\nend program")

    settings = deepcopy(DEFAULT_SETTINGS)
    settings["src_dir"] = [tmp_path]
    settings["exclude"] = ["exclude.f90"]
    project = Project(settings)

    program_names = {program.name for program in project.programs}
    assert program_names == {"foo"}


@pytest.mark.parametrize(
    "sort_kind, expected_order",
    [
        (
            "src",
            {
                "variables": ["b", "a", "d", "f", "c", "e", "g", "h", "j", "i"],
                "types": ["bet", "alef", "gimel"],
                "subroutines": ["bravo", "alpha", "charlie"],
                "functions": ["beaver", "aardvark", "cat"],
                "absinterfaces": ["apple", "carrot", "banana"],
            },
        ),
        (
            "alpha",
            {
                "variables": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j"],
                "types": ["alef", "bet", "gimel"],
                "subroutines": ["alpha", "bravo", "charlie"],
                "functions": ["aardvark", "beaver", "cat"],
                "absinterfaces": ["apple", "banana", "carrot"],
            },
        ),
        (
            "permission",
            {
                "variables": ["d", "f", "c", "e", "b", "a", "g", "h", "j", "i"],
                "types": ["gimel", "alef", "bet"],
                "subroutines": ["charlie", "alpha", "bravo"],
                "functions": ["cat", "aardvark", "beaver"],
                "absinterfaces": ["apple", "carrot", "banana"],
            },
        ),
        (
            "permission-alpha",
            {
                "variables": ["d", "f", "c", "e", "a", "b", "g", "h", "i", "j"],
                "types": ["gimel", "alef", "bet"],
                "subroutines": ["charlie", "alpha", "bravo"],
                "functions": ["cat", "aardvark", "beaver"],
                "absinterfaces": ["apple", "banana", "carrot"],
            },
        ),
        (
            "type",
            {
                "variables": ["h", "g", "j", "i", "b", "a", "c", "e", "d", "f"],
                "types": ["bet", "alef", "gimel"],
                "subroutines": ["bravo", "alpha", "charlie"],
                "functions": ["cat", "beaver", "aardvark"],
                "absinterfaces": ["apple", "carrot", "banana"],
            },
        ),
        (
            "type-alpha",
            {
                "variables": ["h", "g", "i", "j", "a", "b", "c", "e", "d", "f"],
                "types": ["alef", "bet", "gimel"],
                "subroutines": ["alpha", "bravo", "charlie"],
                "functions": ["cat", "aardvark", "beaver"],
                "absinterfaces": ["apple", "banana", "carrot"],
            },
        ),
    ],
)
def test_sort(copy_fortran_file, sort_kind, expected_order):
    data = """\
    module mod_a
      type :: bet
      end type bet

      type :: alef
      end type alef

      type :: gimel
      end type gimel

      integer, private :: b, a
      type(gimel), public :: d, f
      type(alef), protected :: c, e

      character(len=2, kind=4) :: g
      character(len=1, kind=4) :: h
      character(len=1, kind=8) :: j, i
      private :: g, h, i, j

      abstract interface
        subroutine banana
        end subroutine banana

        function apple()
          import gimel
          class(gimel), allocatable :: apple
        end function apple

        type(alef) function carrot()
          import alef
        end function carrot
      end interface

      public :: gimel, charlie, cat
      protected :: alef, alpha, aardvark
      private :: bet, bravo, beaver

    contains
      subroutine bravo
      end subroutine bravo

      subroutine alpha
      end subroutine alpha

      subroutine charlie
      end subroutine charlie

      type(gimel) function beaver()
      end function beaver

      function aardvark()
        class(gimel), allocatable :: aardvark
      end function aardvark

      type(alef) function cat()
      end function cat
    end module mod_a
    """

    settings = copy_fortran_file(data)
    settings["sort"] = sort_kind
    settings["display"] = ["public", "private", "protected"]
    project = create_project(settings)
    module = project.modules[0]

    for entity_type in [
        "variables",
        "types",
        "subroutines",
        "functions",
        "absinterfaces",
    ]:
        entity_names = [entity.name for entity in getattr(module, entity_type)]
        assert entity_names == expected_order[entity_type], (sort_kind, entity_type)
