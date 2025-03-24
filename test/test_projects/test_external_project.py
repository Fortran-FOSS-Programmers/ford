import shutil
import sys
import os
import pathlib
from urllib.parse import urlparse
import json
from typing import Dict, Any

import ford

from bs4 import BeautifulSoup
import pytest

from conftest import chdir

REMOTE_TYPE_JSON: Dict[str, Any] = {
    "name": "remote_type",
    "external_url": "./type/remote_type.html",
    "obj": "type",
    "extends": None,
    "variables": [
        {
            "name": "cptr",
            "external_url": "./type/config.html#variable-cptr",
            "obj": "variable",
            "vartype": "type",
            "permission": "public",
        },
    ],
    "boundprocs": [],
    "permission": "public",
}

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
        "pub_types": {"remote_type": REMOTE_TYPE_JSON},
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
        "types": [REMOTE_TYPE_JSON],
        "variables": [],
    }
]


class MockResponse:
    @staticmethod
    def read():
        return json.dumps(REMOTE_MODULES_JSON).encode("utf-8")


@pytest.fixture(scope="module")
def monkeymodule(request):
    """pytest won't let us use function-scope fixtures in module-scope
    fixtures, so we need to reimplement this with module scope"""
    mpatch = pytest.MonkeyPatch()
    yield mpatch
    mpatch.undo()


@pytest.fixture(scope="module")
def external_project(tmp_path_factory, monkeymodule):
    """Generate the documentation for an "external" project and then
    for a "top level" one that uses the first.

    A remote external project is simulated through a mocked `urlopen`
    which returns `REMOTE_MODULES_JSON`

    """

    this_dir = pathlib.Path(__file__).parent
    path = tmp_path_factory.getbasetemp() / "external_project"
    shutil.copytree(this_dir / "../../test_data/external_project", path)

    external_project = path / "external_project"
    top_level_project = path / "top_level_project"

    # Run FORD in the two projects
    # First project has "externalize: True" and will generate JSON dump
    with monkeymodule.context() as m, chdir(external_project):
        m.setattr(sys, "argv", ["ford", "doc.md"])
        ford.run()

    def mock_open(*args, **kwargs):
        return MockResponse()

    # Second project uses JSON from first to link to external modules
    with monkeymodule.context() as m, chdir(top_level_project):
        m.setattr(sys, "argv", ["ford", "doc.md"])
        m.setattr(ford.external_project, "urlopen", mock_open)
        ford.run()

    # Make sure we're in a directory where relative paths won't
    # resolve correctly
    os.chdir("/")

    return top_level_project, external_project


def test_external_project(external_project):
    """Check that we can build external projects and get the links correct"""

    top_level_project, _ = external_project

    # Read generated HTML
    program_dir = top_level_project / "doc/program"
    with open(program_dir / "top_level.html", "r") as f:
        top_program_html = BeautifulSoup(f.read(), features="html.parser")

    # Find links to external modules
    uses_box = top_program_html.find(string="Uses").parent.parent.parent
    links = {
        tag.text: tag.a["href"] for tag in uses_box("li", class_="list-inline-item")
    }

    assert len(links) == 3
    assert "external_module" in links
    local_url = urlparse(links["external_module"])
    local_path = program_dir / local_url.path
    assert local_path.is_file()

    assert "remote_module" in links
    remote_url = urlparse(links["remote_module"])
    assert remote_url.scheme == "https"


def test_procedure_module_use_links_(external_project):
    """Check that links to external modules used by functions are correct"""

    top_level_project, _ = external_project

    # Read generated HTML
    proc_dir = top_level_project / "doc/proc"
    with open(proc_dir / "abortcriteria_load.html", "r") as f:
        procedure_html = BeautifulSoup(f.read(), features="html.parser")

    # Find links to external modules
    uses_box = procedure_html.find(string="Uses").parent.parent.parent
    links = {
        tag.text: tag.a["href"] for tag in uses_box("li", class_="list-inline-item")
    }

    assert len(links) == 1
    assert "external_module" in links
    local_url = urlparse(links["external_module"])
    local_path = proc_dir / local_url.path
    assert local_path.is_file()


def test_external_ford_link(external_project):
    """Test #696 -- malformed [[ford]] links to external entities"""

    top_level_project, _ = external_project

    prog_dir = top_level_project / "doc/program"
    with open(prog_dir / "top_level.html") as f:
        prog_html = BeautifulSoup(f.read(), features="html.parser")

    link = prog_html.find("a", string="remote_sub")
    assert link["href"] == "https://example.com/proc/remote_sub.html"
