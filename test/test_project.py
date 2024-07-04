from ford.fortran_project import Project, find_all_files
from ford.settings import ProjectSettings, ExtraFileType
from ford.utils import normalise_path
from ford.sourceform import (
    FortranVariable,
    FortranProgram,
    FortranSubroutine,
    FortranModule,
    NameSelector,
)
from ford._markdown import MetaMarkdown
import ford.sourceform

from itertools import chain

import pytest
from bs4 import BeautifulSoup


@pytest.fixture
def copy_fortran_file(tmp_path):
    # Reset unique name tracker
    setattr(ford.sourceform, "namelist", NameSelector())

    def copy_file(data) -> ProjectSettings:
        src_dir = tmp_path / "src"
        src_dir.mkdir()
        filename = src_dir / "test.f90"
        with open(filename, "w") as f:
            f.write(data)
        return ProjectSettings(src_dir=src_dir)

    return copy_file


def create_project(settings: ProjectSettings):
    project = Project(settings)
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


def test_use_within_interface(copy_fortran_file):
    data = """\
    module module1
      implicit none
      private
      interface
        subroutine routine_1()
          use module2, only: routine_2
        end subroutine routine_1
      end interface
      public :: routine
    end module module1

    module module2
      implicit none
      private
      public :: routine_2
    contains
      subroutine routine_2(i)
        integer,intent(in) :: i
        write(*,*) i
      end subroutine routine_2
    end module module2
    """

    settings = copy_fortran_file(data)
    project = create_project(settings)
    assert "routine_2" in project.modules[0].all_procs["routine_1"].procedure.all_procs


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
    settings.display = ["public"]
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
    settings.display = ["public"]
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
    settings.display = ["public", "private"]
    project = create_project(settings)

    type_names = set([t.name for t in project.types])
    assert type_names == {"no_attrs", "public_attr", "private_attr"}


def test_display_private_module_procedure(copy_fortran_file):
    data = """\
      module foo
        interface
          module subroutine bar()
          end subroutine bar
        end interface
      end module foo

      submodule (foo) baz
      contains
        module procedure bar
        end procedure
      end submodule baz
      """

    settings = copy_fortran_file(data)
    settings.display = ["public", "protected", "private"]

    project = create_project(settings)
    assert project.submodprocedures[0].name == "bar"


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


def test_generic_interface_inherited_attrs(copy_fortran_file):
    data = """\
    module module1
      implicit none
      interface routine
        module subroutine routine_1(var)
          integer, dimension(:) :: var
        end subroutine routine_1
      end interface
      public :: routine
    end module module1

    submodule(module1) module2
      implicit none
    contains
      module procedure routine_1
      end procedure
    end submodule module2
    """

    settings = copy_fortran_file(data)
    project = create_project(settings)

    module_implementation = project.modules[0].all_procs["routine_1"].module
    # Check that the module implementation has been linked
    assert not isinstance(module_implementation, bool)
    # Check that mod proc has the inherited arg
    assert isinstance(module_implementation.args[0], FortranVariable)


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

    settings = ProjectSettings(
        src_dir=tmp_path, exclude_dir=normalise_path(tmp_path, "sub1")
    )
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

    settings = ProjectSettings(src_dir=tmp_path, exclude="exclude.f90")
    project = Project((settings))

    program_names = {program.name for program in project.programs}
    assert program_names == {"foo"}


def test_find_all_files(tmp_path):
    src = tmp_path / "src"
    src.mkdir(parents=True)
    sub1 = src / "sub1"
    sub1.mkdir()
    sub2 = src / "sub2"
    sub2.mkdir()
    (src / "file1.f90").touch()
    (src / "file2.F90").touch()
    (sub1 / "file3.f").touch()
    (sub1 / "not_this.f90").touch()
    (sub2 / "file4.c").touch()
    (sub2 / "not_this.f90").touch()

    exclude_dir = src / "bad_dir"
    exclude_dir.mkdir()
    exclude_sub = exclude_dir / "sub1"
    exclude_sub.mkdir()
    (exclude_dir / "file5.f90").touch()
    (exclude_sub / "file6.f90").touch()

    src2 = tmp_path / "src2"
    src2.mkdir()
    (src2 / "file7.f90").touch()

    settings = ProjectSettings(
        exclude=["src/sub1/not_this.f90"],
        exclude_dir=["src/bad_dir"],
        src_dir=[src, src2],
        extra_filetypes={"c": ExtraFileType("c", "//")},
    )
    settings.normalise_paths(tmp_path)

    files = sorted(find_all_files(settings))

    expected_files = sorted(
        [
            tmp_path / f
            for f in (
                "src/file1.f90",
                "src/file2.F90",
                "src/sub1/file3.f",
                "src/sub2/file4.c",
                "src/sub2/not_this.f90",
                "src2/file7.f90",
            )
        ]
    )

    assert files == expected_files


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
    settings.sort = sort_kind
    settings.display = ["public", "private", "protected"]
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


def test_uses(copy_fortran_file):
    """Check that module `USE`s are matched up correctly"""

    data = """\
    module mod_a
    end module mod_a

    module mod_b
      use mod_a
    end module mod_b

    module mod_c
      use mod_a
      use mod_b
    end module mod_c

    module mod_d
      use external_module
    end module mod_d
    """

    settings = copy_fortran_file(data)
    settings.extra_mods = {"external_module": "http://example.com"}

    project = create_project(settings)
    mod_a = project.modules[0]
    mod_b = project.modules[1]
    mod_c = project.modules[2]
    mod_d = project.modules[3]

    assert mod_a.uses == set()
    assert mod_b.uses == {mod_a}
    assert mod_c.uses == {mod_a, mod_b}

    for link in mod_d.uses:
        assert link.get_url() == "http://example.com"


def test_submodule_uses(copy_fortran_file):
    """Check that module `USE`s are matched up correctly"""

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

    settings = copy_fortran_file(data)

    project = create_project(settings)
    mod_a = project.modules[0]
    mod_b = project.submodules[0]
    mod_c = project.submodules[1]
    mod_d = project.submodules[2]

    assert mod_a.uses == set()

    assert mod_b.parent_submodule is None
    assert mod_b.ancestor_module == mod_a

    assert mod_c.parent_submodule is None
    assert mod_c.ancestor_module == mod_a

    assert mod_d.parent_submodule == mod_c
    assert mod_d.ancestor_module == mod_a


def test_make_links(copy_fortran_file):
    links = "[[a]] [[b(type)]] [[b:c]] [[a:d]] [[b:e]] [[F(proc)]] [[A:G]] [[H]] [[I]]"

    data = f"""\
    module a !! {links}
      type b !! {links}
        integer :: c !! {links}
      contains
        final :: d !! {links}
        procedure :: e !! {links}
      end type b

      interface b !! {links}
        module procedure f
      end interface b

      type(b) :: g !! {links}
    contains
      subroutine d(self) !! {links}
        type(b) :: self !! {links}
      end subroutine d
      subroutine e(self) !! {links}
        class(b) :: self !! {links}
      end subroutine e
      function f() !! {links}
        type(b) :: f !! {links}
      end function f
    end module a

    program h !! {links}
    end program h

    submodule (a) i !! {links}
    end submodule i
    """
    settings = copy_fortran_file(data)
    project = create_project(settings)
    md = MetaMarkdown(project=project)
    project.markdown(md)

    expected_links = {
        "a": "../module/a.html",
        "b": "../type/b.html",
        "c": "../type/b.html#variable-c",
        "d": "../proc/d.html",
        "e": "../type/b.html#boundprocedure-e",
        "f": "../proc/f.html",
        "g": "../module/a.html#variable-g",
        "h": "../program/h.html",
        "i": "../module/i.html",
    }

    for item in chain(
        project.files[0].children,
        project.types[0].children,
        project.procedures[0].children,
        project.procedures[2].children,
    ):
        docstring = BeautifulSoup(item.doc, features="html.parser")
        link_locations = {a.string: a.get("href", None) for a in docstring("a")}

        assert link_locations == expected_links, (item, item.name)


def test_make_links_with_entity_spec(copy_fortran_file):
    links = (
        "[[a(module)]] [[b(type)]] [[b(type):c(variable)]] "
        "[[A(MODULE):D(SUBROUTINE)]] [[B(TYPE):E]] [[F(PROC)]] "
        "[[A(module):G(variable)]] [[H(program)]] [[I(SUBMODULE)]]"
    )

    data = f"""\
    module a !! {links}
      type b !! {links}
        integer :: c !! {links}
      contains
        final :: d !! {links}
        procedure :: e !! {links}
      end type b

      interface b !! {links}
        module procedure f
      end interface b

      type(b) :: g !! {links}
    contains
      subroutine d(self) !! {links}
        type(b) :: self !! {links}
      end subroutine d
      subroutine e(self) !! {links}
        class(b) :: self !! {links}
      end subroutine e
      function f() !! {links}
        type(b) :: f !! {links}
      end function f
    end module a

    program h !! {links}
    end program h

    submodule (a) i !! {links}
    end submodule i
    """
    settings = copy_fortran_file(data)
    project = create_project(settings)
    md = MetaMarkdown(project=project)
    project.markdown(md)

    expected_links = {
        "a": "../module/a.html",
        "b": "../type/b.html",
        "c": "../type/b.html#variable-c",
        "d": "../proc/d.html",
        "e": "../type/b.html#boundprocedure-e",
        "f": "../proc/f.html",
        "g": "../module/a.html#variable-g",
        "h": "../program/h.html",
        "i": "../module/i.html",
    }

    for item in chain(
        project.files[0].children,
        project.types[0].children,
        project.procedures[0].children,
        project.procedures[2].children,
    ):
        docstring = BeautifulSoup(item.doc, features="html.parser")
        link_locations = {a.string: a.get("href", None) for a in docstring("a")}

        assert link_locations == expected_links, (item, item.name)


def test_make_links_with_context(copy_fortran_file):
    data = """\
    module a !! [[g]]
      type b !! [[c]] [[e]] [[g]]
        integer :: c
      contains
        procedure :: e
      end type b

      type(b) :: g
    contains
      subroutine d(i) !! [[I]] [[F]] [[F:X]]
        type(b) :: i
        contains
          integer function f(x)
            integer :: x
          end function f
      end subroutine d
    end module a

    program h
    end program h
    """
    settings = copy_fortran_file(data)
    settings.proc_internals = True
    project = create_project(settings)
    md = MetaMarkdown(project=project)
    project.markdown(md)

    expected_links = {
        "a": "../module/a.html",
        "b": "../type/b.html",
        "c": "../type/b.html#variable-c",
        "d": "../proc/d.html",
        "e": "../type/b.html#boundprocedure-e",
        "f": "../proc/d.html#proc-f",
        "g": "../module/a.html#variable-g",
        "h": "../program/h.html",
        "i": "../proc/d.html#variable-i",
        "x": "../proc/d.html#variable-x",
    }

    for item in chain(
        project.files[0].children,
        project.modules[0].children,
        project.types[0].children,
        project.procedures[0].children,
    ):
        docstring = BeautifulSoup(item.doc, features="html.parser")

        for link in docstring("a"):
            assert link.string in expected_links, (item, item.name, link)
            expected_link = expected_links[link.string]

            assert link.get("href", None) == expected_link, (
                item,
                item.name,
                link.string,
            )


def test_submodule_procedure_issue_446(copy_fortran_file):
    data = """\
    module foo_mod
      interface
        module subroutine quaxx
        end subroutine quaxx
      end interface
    end module foo_mod

    submodule (foo_mod) bar_submod
    contains
      module procedure quaxx
        print*, "implementation"
      end procedure
    end submodule bar_submod
    """

    settings = copy_fortran_file(data)
    settings.display = ["public", "private", "protected"]
    project = create_project(settings)
    module = project.modules[0]

    interface = module.interfaces[0]
    assert interface.name == "quaxx"
    submodproc = module.descendants[0].modprocedures[0]

    assert interface.procedure.module == submodproc


def test_find_namelists(copy_fortran_file):
    data = """\
    module mod1
    contains
      subroutine sub1()
        namelist /namelist_b/ var_a
      end subroutine sub1
    end module mod1

    program prog
      integer :: var_b
    contains
      subroutine sub(var_b)
        integer :: var_d, var_a, var_b
        character(len=*), intent(in) :: string
        namelist /namelist_a/ var_a, var_b, var_c, var_d
        read(string, nml=namelist_a)
        write(*, *) "Read in:"
        write(*, nml=namelist_a)
      end subroutine sub
    end program prog
    """
    settings = copy_fortran_file(data)
    project = create_project(settings)
    assert len(project.namelists) == 2
    namelist_names = sorted((namelist.name for namelist in project.namelists))
    expected_names = sorted(("namelist_a", "namelist_b"))
    assert namelist_names == expected_names


def test_find(copy_fortran_file):
    data = """\
    module foo
      type :: test_type
        integer :: sub
      end type test_type
    contains
      subroutine sub
      end subroutine sub
    end module

    program foo
    end program
    """

    settings = copy_fortran_file(data)
    settings.display = ["public", "private"]
    project = create_project(settings)

    test_type = project.find("test_type")
    assert test_type.name == "test_type"

    subroutine_sub = project.find("sub")
    assert subroutine_sub.name == "sub"
    assert isinstance(subroutine_sub, FortranSubroutine)

    component_sub = project.find("test_type", child_name="sub")
    assert component_sub.name == "sub"
    assert isinstance(component_sub, FortranVariable)

    foo = project.find("foo")
    assert foo
    prog_foo = project.find("foo", entity="program")
    assert isinstance(prog_foo, FortranProgram)
    mod_foo = project.find("foo", entity="module")
    assert isinstance(mod_foo, FortranModule)


def test_links_in_deferred_bound_methods(copy_fortran_file):
    """Test for issue #591"""

    data = """\
    module test
        type, abstract :: foo_t
            contains
            !> See [[foo_t]] for more information about [[foo]]
            procedure(foo_iface), deferred :: foo
        end type
        abstract interface
            subroutine foo_iface(self)
                import :: foo_t
                class(foo_t), intent(in) :: self
            end subroutine
        end interface
    end module
    """

    settings = copy_fortran_file(data)
    project = create_project(settings)
    md = MetaMarkdown(settings.md_base_dir, project=project)
    project.markdown(md)

    docstring = BeautifulSoup(
        project.modules[0].types[0].boundprocs[0].doc, features="html.parser"
    )
    links = {link.text: link["href"] for link in docstring.find_all("a")}
    assert links["foo_t"].endswith("foo_t.html")
    assert links["foo"].endswith("foo_t.html#boundprocedure-foo")


def test_hide_undoc(copy_fortran_file):
    data = """\
    module foo
    contains
      !> A subroutine with a docstring
      subroutine with_doc
      end subroutine with_doc

      subroutine no_doc
      end subroutine no_doc
    end module
    """

    settings = copy_fortran_file(data)
    settings.hide_undoc = True
    project = create_project(settings)

    assert len(project.modules[0].subroutines) == 1
