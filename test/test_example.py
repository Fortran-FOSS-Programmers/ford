import shutil
import sys
import os
import pathlib
import re

import ford

from bs4 import BeautifulSoup
import pytest


HEADINGS = re.compile(r"h[1-4]")
ANY_TEXT = re.compile(r"h[1-4]|p")


@pytest.fixture(scope="module")
def example_project(tmp_path_factory):
    this_dir = pathlib.Path(__file__).parent
    tmp_path = tmp_path_factory.getbasetemp() / "example"
    shutil.copytree(this_dir / "../example", tmp_path)

    with pytest.MonkeyPatch.context() as m:
        os.chdir(tmp_path)
        m.setattr(sys, "argv", ["ford", "example-project-file.md"])
        ford.run()

    with open(tmp_path / "example-project-file.md", "r") as f:
        project_file = f.read()
    settings, _, _ = ford.parse_arguments({}, project_file, tmp_path)

    doc_path = tmp_path / "doc"

    return doc_path, settings


def read_html(filename):
    with open(filename, "r") as f:
        return BeautifulSoup(f.read(), features="html.parser")


@pytest.fixture(scope="module")
def example_index(example_project):
    path, settings = example_project
    index = read_html(path / "index.html")
    return index, settings


def test_nav_bar(example_index):
    index, settings = example_index

    navbar_links = index.nav("a")
    link_names = {link.text.strip() for link in navbar_links}

    for expected_page in (
        settings["project"],
        "Source Files",
        "Modules",
        "Procedures",
        "Derived Types",
        "Program",
    ):
        assert expected_page in link_names


def test_jumbotron(example_index):
    """This test will probably break if a different theme or HTML/CSS
    framework is used"""

    index, settings = example_index
    jumbotron = index.find("div", "jumbotron")

    jumbotron_text = (p.text for p in jumbotron("p"))
    assert settings["summary"] in jumbotron_text

    links = [link["href"] for link in jumbotron("a")]

    for location_link in [
        "project_bitbucket",
        "project_download",
        "project_github",
        "project_gitlab",
        "project_sourceforge",
        "project_website",
    ]:
        if settings[location_link] is not None:
            assert settings[location_link] in links


def test_developer_info_box(example_index):
    index, settings = example_index

    # Assume that we have something like:
    #     `<div><h2>Developer Info</h2> .. box </div>`
    developer_info = index.find(string="Developer Info").parent.parent

    dev_text = [tag.text for tag in developer_info(ANY_TEXT)]

    for expected_text in ["author", "author_description"]:
        assert settings[expected_text] in dev_text


def test_latex(example_index):
    index, settings = example_index

    tex_tags = index("script", type=re.compile("math/tex.*"))

    assert len(tex_tags) == 4


def test_source_file_links(example_index):
    index, settings = example_index

    source_files_box = index.find(ANY_TEXT, string="Source Files").parent
    source_files_list = sorted([f.text for f in source_files_box("li")])

    assert source_files_list == sorted(
        ["ford_test_module.fpp", "ford_test_program.f90"]
    )


def test_module_links(example_index):
    index, settings = example_index

    modules_box = index.find(ANY_TEXT, string="Modules").parent
    modules_list = [f.text for f in modules_box("li")]

    assert modules_list == ["test_module"]


def test_procedures_links(example_index):
    index, settings = example_index

    proceduress_box = index.find(ANY_TEXT, string="Procedures").parent
    proceduress_list = sorted([f.text for f in proceduress_box("li")])

    assert proceduress_list == sorted(
        ["decrement", "do_foo_stuff", "do_stuff", "increment"]
    )


def test_types_links(example_index):
    index, settings = example_index

    types_box = index.find(ANY_TEXT, string="Derived Types").parent
    types_list = [f.text for f in types_box("li")]

    assert types_list == ["bar", "foo"]
