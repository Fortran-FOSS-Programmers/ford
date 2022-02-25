import shutil
import sys
import os
import pathlib
import re
from urllib.parse import urlparse
import json

import ford

from bs4 import BeautifulSoup
import pytest


REMOTE_MODULES_JSON = [
    {
        "name": "remote_module",
        "external_url": "./module/remote_module.html",
        "obj": "module",
        "pub_procs": {
            "remote_sub": {
                "name": "remote_sub",
                "external_url": "./proc/remote_sub.html",
                "obj": "proc",
                "proctype": "Subroutine",
                "functions": [],
                "subroutines": [],
                "interfaces": [],
                "absinterfaces": [],
                "types": [],
                "variables": [],
            },
        },
        "pub_absints": {},
        "pub_types": {},
        "pub_vars": {},
        "functions": [],
        "subroutines": [
            {
                "name": "remote_sub",
                "external_url": "./proc/remote_sub.html",
                "obj": "proc",
                "proctype": "Subroutine",
                "functions": [],
                "subroutines": [],
                "interfaces": [],
                "absinterfaces": [],
                "types": [],
                "variables": [],
            }
        ],
        "interfaces": [],
        "absinterfaces": [],
        "types": [],
        "variables": [],
    }
]


@pytest.fixture
def copy_project_files(tmp_path):
    this_dir = pathlib.Path(__file__).parent
    shutil.copytree(
        this_dir / "../../test_data/external_project", tmp_path / "external_project"
    )
    return tmp_path / "external_project"


class MockResponse:
    @staticmethod
    def read():
        return json.dumps(REMOTE_MODULES_JSON).encode("utf-8")


def test_external_project(copy_project_files, monkeypatch, restore_macros):
    """Check that we can build external projects and get the links correct

    This is a rough-and-ready test that runs FORD via subprocess, and
    so won't work unless FORD has been installed.

    It also relies on access to the internet and an external URL out
    of our control.

    """

    path = copy_project_files
    external_project = path / "external_project"
    top_level_project = path / "top_level_project"

    # Run FORD in the two projects
    # First project has "externalize: True" and will generate JSON dump
    with monkeypatch.context() as m:
        os.chdir(external_project)
        m.setattr(sys, "argv", ["ford", "doc.md"])
        ford.run()

    def mock_open(*args, **kwargs):
        return MockResponse()

    # Second project uses JSON from first to link to external modules
    with monkeypatch.context() as m:
        os.chdir(top_level_project)
        m.setattr(sys, "argv", ["ford", "doc.md"])
        m.setattr(ford.utils, "urlopen", mock_open)
        ford.run()

    # Make sure we're in a directory where relative paths won't
    # resolve correctly
    os.chdir("/")

    # Read generated HTML
    with open(top_level_project / "doc/program/top_level.html", "r") as f:
        top_program_html = BeautifulSoup(f.read(), features="html.parser")

    # Find links to external modules
    uses_box = top_program_html.find(string="Uses").parent.parent.parent
    links = {tag.text: tag.a["href"] for tag in uses_box("li", class_=None)}

    assert len(links) == 2
    assert "external_module" in links
    local_url = urlparse(links["external_module"])
    assert pathlib.Path(local_url.path).is_file()

    assert "remote_module" in links
    remote_url = urlparse(links["remote_module"])
    assert remote_url.scheme == "https"
