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
            '--macro FCOMPILER=_GFORTRAN_ --macro GIT_HASH="e29e9ab8f2eb8d01292fee68588b8bbed560e00b" --macro GIT_HASH_MAKEFILES="73078bc4547279aae4978c5c3b128bbdcce172a6" --macro GIT_HASH_UTILS="28fddcbb26fb561d28242fa1a44b5c6edca3dc72" --macro GIT_VERSION="8.2.0-2-ge29e9ab8" --macro GIT_BRANCH="master"  --macro MPI --macro NETCDF --macro NEW_DIAG --macro F200X_INTRINSICS --macro SPFUNC=_SPF200X_ --macro GS2_BUILD_TAG="None" -I../externals/utils -I../src/geo -I../externals/neasyf/src -I../src/config_auto_gen -I../src -I../include -r e29e9ab8f2eb8d01292fee68588b8bbed560e00b',  # noqa E501
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
        (
            "https://github.com/fortran-lang/stdlib",
            "stdlib/API-doc-FORD-file.md",
            # The linear algebra files cause massive slowdown, although I'm not sure why yet
            '--config=exclude=["**/*linalg**"]',
        ),
        (
            "https://github.com/jacobwilliams/Fortran-Astrodynamics-Toolkit",
            "Fortran-Astrodynamics-Toolkit/ford.md",
            "",
        ),
        (
            "https://github.com/jacobwilliams/bspline-fortran",
            "bspline-fortran/ford.md",
            "",
        ),
        ("https://github.com/jacobwilliams/dvode", "dvode/ford.md", ""),
        ("https://github.com/jacobwilliams/csv-fortran", "csv-fortran/ford.md", ""),
        (
            "https://github.com/jacobwilliams/json-fortran",
            "json-fortran/json-fortran.md",
            "",
        ),
        (
            "https://github.com/jacobwilliams/pyplot-fortran",
            "pyplot-fortran/ford.md",
            "",
        ),
        ("https://github.com/jacobwilliams/quadpack", "quadpack/ford.md", ""),
        ("https://github.com/szaghi/FLAP", "FLAP/doc/main_page.md", ""),
        ("https://github.com/szaghi/FiNeR", "FiNeR/doc/main_page.md", ""),
        ("https://github.com/szaghi/VTKFortran", "VTKFortran/doc/main_page.md", ""),
        ("https://github.com/toml-f/toml-f", "toml-f/docs.md", ""),
        ("https://github.com/ylikx/forpy", "forpy/forpy_project.md", ""),
        (
            "https://github.com/cibinjoseph/C81-Interface",
            "C81-Interface/ford_input.md",
            "-p ford_input",
        ),
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
    ],
)
def test_copus(tmp_path, url, config_file, flags):
    os.chdir(tmp_path)

    subprocess.run(
        f"git clone --recurse-submodules --depth=1 {url}", check=True, shell=True
    )

    with pytest.MonkeyPatch.context() as m:
        command = f"ford {flags} {config_file}"
        m.setattr(sys, "argv", command.split())
        ford.run()
