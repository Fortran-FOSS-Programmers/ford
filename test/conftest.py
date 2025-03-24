import ford
import pathlib
import pytest
from textwrap import dedent
import subprocess
from contextlib import contextmanager
import os

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
    return lambda data, extension=".f90": copy_file(
        data, tmp_path / "src", f"test{extension}"
    )


@pytest.fixture
def copy_settings_file(tmp_path):
    return lambda data: copy_file(data, tmp_path, "test.md")


@pytest.fixture
def restore_nameselector():
    yield
    ford.sourceform.namelist = ford.sourceform.NameSelector()


def gfortran_is_not_installed():
    """Returns False if gfortran is not (detectably) installed"""
    out = subprocess.run("command -v gfortran", shell=True, check=False)
    return out.returncode != 0


@contextmanager
def chdir(directory):
    oldwd = os.getcwd()
    os.chdir(directory)
    yield
    os.chdir(oldwd)
