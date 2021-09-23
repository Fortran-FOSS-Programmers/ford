import copy
import ford
import pathlib
import pytest
from textwrap import dedent

# Ford default src folder
DEFAULT_SRC = "src"


def copy_file(data: str, path: pathlib.Path, filename: str) -> pathlib.Path:
    """Write data to 'path/filename'"""
    path.mkdir(exist_ok=True)
    full_filename = path / filename
    with open(full_filename, "w") as f:
        f.write(dedent(data))
    return full_filename


@pytest.fixture
def copy_fortran_file(tmp_path):
    return lambda data: copy_file(data, tmp_path / "src", "test.f90")


@pytest.fixture
def copy_settings_file(tmp_path):
    return lambda data: copy_file(data, tmp_path, "test.md")


@pytest.fixture
def restore_macros():
    old_macros = copy.copy(ford.utils._MACRO_DICT)
    yield
    ford.utils._MACRO_DICT = copy.copy(old_macros)


@pytest.fixture
def restore_nameselector():
    yield
    ford.sourceform.namelist = ford.sourceform.NameSelector()
