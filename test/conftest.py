import pytest


@pytest.fixture
def copy_fortran_file(tmp_path):
    def copy_file(data):
        filename = tmp_path / "test.f90"
        with open(filename, "w") as f:
            f.write(data)
        return filename
    return copy_file
