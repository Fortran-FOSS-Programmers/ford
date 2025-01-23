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
    path = tmp_path_factory.getbasetemp() / "issue_676"
    shutil.copytree(this_dir / "../../test_data/issue_676", path)

    external_project = path / "base"
    top_level_project = path / "plugin"

    # Generate the individual projects from their common parent
    # directory, to check that local path definitions are
    # relative to the project directory, irrespective of the
    # working directory.
    os.chdir(path)

    # Run FORD in the two projects
    # First project has "externalize: True" and will generate JSON dump
    with monkeymodule.context() as m:
        m.setattr(sys, "argv", ["ford", "base/doc.md"])
        ford.run()

    # Second project uses JSON from first to link to external modules
    with monkeymodule.context() as m:
        m.setattr(sys, "argv", ["ford", "plugin/doc.md"])
        ford.run()

    # Make sure we're in a directory where relative paths won't
    # resolve correctly
    os.chdir("/")

    return top_level_project, external_project


def test_issue676_project(external_project):
    """Check that we can build external projects and get the links correct"""

    top_level_project, _ = external_project

    # Read generated HTML
    module_dir = top_level_project / "doc/module"
    with open(module_dir / "gc_method_fks_h.html", "r") as f:
        top_module_html = BeautifulSoup(f.read(), features="html.parser")

    # Find links to external modules
    uses_box = top_module_html.find(string="Uses").parent.parent.parent
    links = {
        tag.text: tag.a["href"] for tag in uses_box("li", class_="list-inline-item")
    }

    assert len(links) == 1
    assert "gc_method_h" in links
    local_url = urlparse(links["gc_method_h"])
    local_path = module_dir / local_url.path
    assert local_path.is_file()
