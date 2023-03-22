import ford

import subprocess
import os
import sys

import pytest


@pytest.mark.slow
@pytest.mark.parametrize(
    ("url", "config_file", "flags"),
    [
        (
            "https://bitbucket.org/gyrokinetics/gs2",
            "gs2/docs/docs.config.md",
            '--macro FCOMPILER=_GFORTRAN_ --macro GIT_HASH="a0efef2c9a499e2516e2bca7cf17e372741b96ea" --macro GIT_HASH_MAKEFILES="84aca9698fb00defc74d38ad6395a557114a9e76" --macro GIT_HASH_UTILS="0c8148c28064f5fc5025a3b1c6fff39d520b1c0b" --macro GIT_VERSION="8.1.2-327-ga0efef2c" --macro GIT_BRANCH="master" --macro MPI --macro ISO_C_BINDING --macro NEW_DIAG --macro FFT=_FFTW3_ --macro NETCDF --macro GK_NETCDF_DEFAULT_COMPRESSION_ON --macro F200X_INTRINSICS --macro SPFUNC=_SPF200X_ --macro GK_HAS_COMPILER_OPTIONS_2008 --macro WITH_EIG --macro HAVE_MPI --macro FORTRAN_NETCDF --macro ISO_C_BINDING -r a0efef2c9a499e2516e2bca7cf17e372741b96ea',  # noqa E501
        ),
        (
            "https://github.com/D3DEnergetic/FIDASIM",
            "FIDASIM/docs/fidasim.md",
            "-d ../src -d ../tables -d ../lib/idl -d ../lib/python/fidasim -p ../docs/user-guide -o ../docs/html",
        ),
        ("https://github.com/QcmPlab/HoneyTools", "HoneyTools/docs.config", ""),
        (
            "https://github.com/cibinjoseph/naturalFRUIT",
            "naturalFRUIT/ford_input.md",
            "",
        ),
        ("https://github.com/fortran-lang/fftpack", "fftpack/API-doc-FORD-file.md", ""),
        ("https://github.com/fortran-lang/fpm", "fpm/docs.md", ""),
        ("https://github.com/fortran-lang/stdlib", "stdlib/API-doc-FORD-file.md", ""),
        (
            "https://github.com/jacobwilliams/Fortran-Astrodynamics-Toolkit",
            "Fortran-Astrodynamics-Toolkit/fortran-astrodynamics-toolkit.md",
            "",
        ),
        (
            "https://github.com/jacobwilliams/bspline-fortran",
            "bspline-fortran/bspline-fortran.md",
            "",
        ),
        ("https://github.com/jacobwilliams/dvode", "dvode/ford.md", ""),
        (
            "https://github.com/jacobwilliams/fortran-csv-module",
            "fortran-csv-module/fortran-csv-module.md",
            "",
        ),
        (
            "https://github.com/jacobwilliams/json-fortran",
            "json-fortran/json-fortran.md",
            "",
        ),
        (
            "https://github.com/jacobwilliams/pyplot-fortran",
            "pyplot-fortran/pyplot-fortran.md",
            "",
        ),
        ("https://github.com/jacobwilliams/quadpack", "quadpack/quadpack.md", ""),
        ("https://github.com/szaghi/FLAP", "FLAP/doc/main_page.md", ""),
        ("https://github.com/szaghi/FiNeR", "FiNeR/doc/main_page.md", ""),
        ("https://github.com/szaghi/VTKFortran", "VTKFortran/doc/main_page.md", ""),
        ("https://github.com/toml-f/toml-f", "toml-f/docs.md", ""),
        ("https://github.com/ylikx/forpy", "forpy/forpy_project.md", ""),
        # The following all specify markdown extension config in a
        # non-supported way
        # (
        #     "https://github.com/Fortran-FOSS-Programmers/FOODIE",
        #     "FOODIE/doc/main_page.md",
        #     "--debug",
        # ),
        # (
        #     "https://github.com/Fortran-FOSS-Programmers/FoXy",
        #     "FoXy/doc/main_page.md",
        #     "--debug",
        # ),
        # ("https://github.com/szaghi/HASTY", "HASTY/doc/main_page.md", ""),
        # ("https://github.com/szaghi/BeFoR64", "BeFoR64/doc/main_page.md", ""),
        # ("https://github.com/szaghi/FURY", "FURY/doc/main_page.md", ""),
        # Source files require fypp
        # ("https://github.com/cp2k/dbcsr", "dbcsr/DBCSR.md", "--debug"),
        # output_dir subdirectory of src_dir, requires manually deleting
        # (
        #     "https://github.com/cibinjoseph/C81-Interface",
        #     "C81-Interface/ford_input.md",
        #     "-p ford_input",
        # ),
    ],
)
def test_copus(tmp_path, url, config_file, flags):
    os.chdir(tmp_path)

    subprocess.run(f"git clone --depth=1 {url}", check=True, shell=True)

    with pytest.MonkeyPatch.context() as m:
        command = f"ford {flags} {config_file}"
        m.setattr(sys, "argv", command.split())
        ford.run()
