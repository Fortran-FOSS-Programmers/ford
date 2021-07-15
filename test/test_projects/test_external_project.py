import shutil
import os
import pathlib
import re
import subprocess

from bs4 import BeautifulSoup
import pytest


@pytest.fixture
def copy_project_files(tmp_path):
    this_dir = pathlib.Path(__file__).parent
    shutil.copytree(
        this_dir / "../../test_data/external_project", tmp_path / "external_project"
    )
    return tmp_path / "external_project"


def test_external_project(copy_project_files):
    """Check that we can build external projects and get the links correct

    This is a rough-and-ready test that runs FORD via subprocess, and
    so won't work unless FORD has been installed.

    """

    path = copy_project_files
    external_project = path / "external_project"
    top_level_project = path / "top_level_project"

    # Run FORD in the two projects
    # First project has "externalize: True" and will generate JSON dump
    os.chdir(external_project)
    subprocess.run(["ford", "doc.md"], check=True)
    # Second project uses JSON from first to link to external modules
    os.chdir(top_level_project)
    subprocess.run(["ford", "doc.md"], check=True)

    # Read generated HTML
    with open(top_level_project / "doc/program/top_level.html", "r") as f:
        top_program_html = BeautifulSoup(f.read(), features="html.parser")

    # Find link to external module and check it's correct
    external_link = top_program_html.find_all(
        href=re.compile("external_project/doc/module/external_module.html")
    )

    assert len(external_link) == 1
    assert external_link[0].text == "external_module"
