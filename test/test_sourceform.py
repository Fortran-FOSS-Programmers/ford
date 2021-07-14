from ford.sourceform import FortranSourceFile

from collections import defaultdict


def test_extends(tmp_path):
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

    filename = tmp_path / "test.f90"
    with open(filename, "w") as f:
        f.write(data)

    settings = defaultdict(str)
    settings["docmark"] = "!"
    settings["encoding"] = "utf-8"

    fortran_type = FortranSourceFile(str(filename), settings)

    assert len(fortran_type.programs) == 1

    program = fortran_type.programs[0]

    assert len(program.types) == 3
    assert program.types[1].extends == "base"
    assert program.types[2].extends == "base"


def test_submodule_procedure_contains(tmp_path):
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

    filename = tmp_path / "test.f90"
    with open(filename, "w") as f:
        f.write(data)

    settings = defaultdict(str)
    settings["docmark"] = "!"
    settings["encoding"] = "utf-8"

    fortran_type = FortranSourceFile(str(filename), settings)

    assert len(fortran_type.modules) == 1
    assert len(fortran_type.submodules) == 1
    submodule = fortran_type.submodules[0]
    assert len(submodule.modprocedures) == 1
    module_procedure = submodule.modprocedures[0]
    assert len(module_procedure.subroutines) == 1


def test_backslash_in_character_string(tmp_path):
    """Bad escape crash #296"""

    data = r"""\
    module test_module
    character(len=*),parameter,public:: q = '(?)'
    character(len=*),parameter,public:: a  = '\a'
    character(len=*),parameter,public:: b  = '\b'
    character(len=*),parameter,public:: c  = '\c'
    end module test_module
    """

    filename = tmp_path / "test.f90"
    with open(filename, "w") as f:
        f.write(data)

    settings = defaultdict(str)
    settings["docmark"] = "!"
    settings["encoding"] = "utf-8"

    source = FortranSourceFile(str(filename), settings)
    module = source.modules[0]

    expected_variables = {"q": r"'(?)'", "a": r"'\a'", "b": r"'\b'", "c": r"'\c'"}

    for variable in module.variables:
        assert variable.initial == expected_variables[variable.name]


def test_sync_images_in_submodule_procedure(tmp_path):
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

    filename = tmp_path / "test.f90"
    with open(filename, "w") as f:
        f.write(data)

    settings = defaultdict(str)
    settings["docmark"] = "!"
    settings["encoding"] = "utf-8"

    FortranSourceFile(str(filename), settings)


def test_function_and_subroutine_call_on_same_line(tmp_path):
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

    filename = tmp_path / "test.f90"
    with open(filename, "w") as f:
        f.write(data)

    settings = defaultdict(str)
    settings["docmark"] = "!"
    settings["encoding"] = "utf-8"

    fortran_file = FortranSourceFile(str(filename), settings)
    program = fortran_file.programs[0]
    assert len(program.calls) == 2
