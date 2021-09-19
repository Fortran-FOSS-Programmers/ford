import sys
import pytest
from collections import defaultdict
import ford
import ford.fortran_project

# Ford default src folder
DEFAULT_SRC = "src"

@pytest.fixture
def copy_fortran_file(tmp_path):
    def copy_file(fortran_data):
        src_dir = tmp_path / DEFAULT_SRC
        src_dir.mkdir()
        filename = src_dir / "test.f90"
        with open(filename, "w") as f:
            f.write(fortran_data)
        return src_dir
    return copy_file

@pytest.fixture
def copy_settings_file(tmp_path):
    def copy_settings(data):
        md_file = tmp_path / "ford.md"
        with open(md_file, "w") as f:
            f.write(data)
        return md_file
    return copy_settings



import warnings

def test_extra_mods_empty(copy_fortran_file, copy_settings_file, monkeypatch, tmp_path):
    """This checks that extra_mods is parsed correctly in input md file"""

    data = """\
module test
end module test
"""
    settings = """\
extra_mods:
"""

    copy_fortran_file(data)
    md_file = copy_settings_file(settings)

    # Modify command line args with argv to use
    with monkeypatch.context() as m:
        m.setattr(sys, 'argv', ["ford", str(md_file)])
        ford.run()


def test_extra_mods_intrinsic(copy_fortran_file, copy_settings_file, monkeypatch, tmp_path):
    """This checks that adding extra_mods doesn't change the module variable INTRINSIC_MODS"""
    data = """\
module test
end module test
"""
    settings = """\
extra_mods: dummy: dummy_module
"""
    # Initial value of intrinsic mods
    old_intrinsic_mods = ford.fortran_project.INTRINSIC_MODS.copy()

    # set up project data
    copy_fortran_file(data)
    md_file = copy_settings_file(settings)

    # Modify command line args with argv to use
    with monkeypatch.context() as m:
        m.setattr(sys, 'argv', ["ford", str(md_file)])
        ford.run()

    # Check that the module level variable has not been changed
    assert ford.fortran_project.INTRINSIC_MODS == old_intrinsic_mods
