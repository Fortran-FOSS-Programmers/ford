import shutil
import sys
import os
import pathlib
import copy
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
def restore_macros_module():
    """pytest won't let us use function-scope fixtures in module-scope
    fixtures, so we need to reimplement this with module scope"""

    old_macros = copy.copy(ford.utils._MACRO_DICT)
    yield
    ford.utils._MACRO_DICT = copy.copy(old_macros)


@pytest.fixture(scope="module")
def external_project(tmp_path_factory, monkeymodule, restore_macros_module):
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
    with monkeymodule.context() as m:
        os.chdir(external_project)
        m.setattr(sys, "argv", ["ford", "doc.md"])
        ford.run()

    def mock_open(*args, **kwargs):
        return MockResponse()

    # Second project uses JSON from first to link to external modules
    with monkeymodule.context() as m:
        os.chdir(top_level_project)
        m.setattr(sys, "argv", ["ford", "doc.md"])
        m.setattr(ford.utils, "urlopen", mock_open)
        ford.run()

    # Make sure we're in a directory where relative paths won't
    # resolve correctly
    os.chdir("/")

    return top_level_project, external_project


def test_external_project(external_project):
    """Check that we can build external projects and get the links correct"""

    top_level_project, _ = external_project

    # Read generated HTML
    with open(top_level_project / "doc/program/top_level.html", "r") as f:
        top_program_html = BeautifulSoup(f.read(), features="html.parser")

    # Find links to external modules
    uses_box = top_program_html.find(string="Uses").parent.parent.parent
    links = {tag.text: tag.a["href"] for tag in uses_box("li", class_=None)}

    assert len(links) == 3
    assert "external_module" in links
    local_url = urlparse(links["external_module"])
    assert pathlib.Path(local_url.path).is_file()

    assert "remote_module" in links
    remote_url = urlparse(links["remote_module"])
    assert remote_url.scheme == "https"


def test_procedure_module_use_links_(external_project):
    """Check that links to external modules used by functions are correct"""

    top_level_project, _ = external_project

    # Read generated HTML
    with open(top_level_project / "doc/proc/abortcriteria_load.html", "r") as f:
        procedure_html = BeautifulSoup(f.read(), features="html.parser")

    # Find links to external modules
    uses_box = procedure_html.find(string="Uses").parent.parent.parent
    links = {tag.text: tag.a["href"] for tag in uses_box("li", class_=None)}

    assert len(links) == 1
    assert "external_module" in links
    local_url = urlparse(links["external_module"])
    assert pathlib.Path(local_url.path).is_file()
