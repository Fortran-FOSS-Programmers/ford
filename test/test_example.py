import shutil
import sys
import pathlib
import re
from urllib.parse import urlparse

import ford
from ford.graphs import graphviz_installed

from bs4 import BeautifulSoup
import pytest

from conftest import chdir


pytestmark = pytest.mark.filterwarnings("ignore::bs4.MarkupResemblesLocatorWarning")

HEADINGS = re.compile(r"h[1-4]")
ANY_TEXT = re.compile(r"h[1-4]|p")


def front_page_list(settings, items):
    max_frontpage_items = int(settings.max_frontpage_items)
    return sorted(items)[:max_frontpage_items]


@pytest.fixture(scope="module")
def example_project(tmp_path_factory):
    this_dir = pathlib.Path(__file__).parent
    tmp_path = tmp_path_factory.getbasetemp() / "example"
    shutil.copytree(this_dir / "../example", tmp_path)

    with pytest.MonkeyPatch.context() as m, chdir(tmp_path):
        m.setattr(sys, "argv", ["ford", "example-project-file.md"])
        ford.run()

    with open(tmp_path / "example-project-file.md", "r") as f:
        project_file = f.read()

    project_file, project_settings = ford.load_settings(project_file, tmp_path)
    settings, _ = ford.parse_arguments({}, project_file, project_settings, tmp_path)

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

    expected_pages = {
        settings.project,
        "Notes",
        "Source Files",
        "Block Data",
        "Modules",
        "Procedures",
        "Derived Types",
        "Programs",
        "Abstract Interfaces",
        "Namelists",
    }
    assert expected_pages == link_names


def test_jumbotron(example_index):
    """This test will probably break if a different theme or HTML/CSS
    framework is used"""

    index, settings = example_index
    jumbotron = index.find("div", id="jumbotron")

    jumbotron_text = (p.text for p in jumbotron("p"))
    assert settings.summary in jumbotron_text

    links = [link["href"] for link in jumbotron("a")]

    for location_link in [
        "project_bitbucket",
        "project_download",
        "project_github",
        "project_gitlab",
        "project_sourceforge",
        "project_website",
    ]:
        if (link := getattr(settings, location_link)) is not None:
            assert link in links


def test_developer_info_box(example_index):
    index, settings = example_index

    # Assume that we have something like:
    #     `<div><h2>Developer Info</h2> .. box </div>`
    developer_info = index.find(string="Developer Info").parent.parent

    dev_text = [tag.text for tag in developer_info(ANY_TEXT)]

    assert settings.author in dev_text
    assert settings.author_description in dev_text


def test_latex(example_index):
    index, settings = example_index

    tex_tags = index("script", type=re.compile("math/tex.*"))

    assert len(tex_tags) == 4


def test_source_file_links(example_index):
    index, settings = example_index

    source_files_box = index.find(ANY_TEXT, string="Source Files").parent
    source_files_list = sorted([f.text for f in source_files_box("li")])

    assert source_files_list == front_page_list(
        settings,
        [
            "ford_test_module.fpp",
            "ford_test_program.f90",
            "ford_example_type.f90",
            "ford_interfaces.f90",
            "ford_f77_example.f",
        ],
    )


def test_module_links(example_index):
    index, settings = example_index

    modules_box = index.find(ANY_TEXT, string="Modules").parent
    modules_list = sorted([f.text for f in modules_box("li")])

    assert modules_list == front_page_list(
        settings, ["test_module", "ford_example_type_mod", "interfaces"]
    )


def test_procedures_links(example_index):
    index, settings = example_index

    proceduress_box = index.find(ANY_TEXT, string="Procedures").parent
    proceduress_list = sorted([f.text for f in proceduress_box("li")])

    procedures = front_page_list(
        settings,
        [
            "decrement",
            "do_foo_stuff",
            "do_stuff",
            "increment",
            "check",
            "apply_check",
            "higher_order_unary_f",
        ],
    )
    assert proceduress_list == procedures


def test_types_links(example_index):
    index, settings = example_index

    types_box = index.find(ANY_TEXT, string="Derived Types").parent
    types_list = sorted([f.text for f in types_box("li")])

    assert types_list == sorted(["bar", "foo", "example_type", "say_type_base"])


def test_types_type_bound_procedure(example_project):
    path, _ = example_project
    index = read_html(path / "type/example_type.html")

    bound_procedures_section = index.find("h2", string="Type-Bound Procedures").parent

    assert "This will document" in bound_procedures_section.text, "Binding summary"
    assert (
        "This binding has more documentation" in bound_procedures_section.text
    ), "Binding full docstring"
    assert (
        "Prints how many times" in bound_procedures_section.ul.text
    ), "Full procedure summary"
    assert (
        "This subroutine has more documentation" in bound_procedures_section.ul.text
    ), "Full procedure full docstring"


def test_types_constructor_summary(example_project):
    path, _ = example_project
    index = read_html(path / "type/example_type.html")

    constructor_section = index.find("h2", string="Constructor").parent

    assert "This is a constructor for our type" in constructor_section.text
    assert "This constructor has more documentation" in constructor_section.text
    assert "specific constructor" in constructor_section.ul.text
    assert "More documentation" in constructor_section.ul.text


def test_types_constructor_page(example_project):
    path, _ = example_project
    index = read_html(path / "interface/example_type.html")

    constructor_section = index.find("h2", string=re.compile("example_type")).parent

    assert "This is a constructor for our type" in constructor_section.text
    assert "This constructor has more documentation" in constructor_section.text
    assert "specific constructor" in constructor_section.text
    assert "More documentation" in constructor_section.text


def test_types_finaliser(example_project):
    path, _ = example_project
    index = read_html(path / "type/example_type.html")

    finaliser_section = index.find("h2", string="Finalization Procedures").parent

    assert "This is the finaliser" in finaliser_section.text
    assert "This finaliser has more documentation" in finaliser_section.text
    assert "Cleans up" in finaliser_section.ul.text
    assert "More documentation" in finaliser_section.ul.text


@pytest.mark.skipif(not graphviz_installed, reason="Requires graphviz")
def test_graph_submodule(example_project):
    path, _ = example_project
    index = read_html(path / "module/test_submodule.html")

    graph_nodes = index.svg.find_all("g", class_="node")

    assert len(graph_nodes) == 2
    titles = sorted([node.find("text").text for node in graph_nodes])
    assert titles == sorted(["test_module", "test_submodule"])


def test_procedure_return_value(example_project):
    path, _ = example_project
    index = read_html(path / "proc/multidimension_string.html")

    retvar = index.find(string=re.compile("Return Value")).parent
    assert (
        "character(kind=kind('a'), len=4), dimension(:, :), allocatable" in retvar.text
    )


def test_info_bar(example_project):
    path, _ = example_project
    index = read_html(path / "proc/decrement.html")

    info_bar = index.find(id="info-bar")
    assert "creativecommons" in info_bar.find(id="meta-license").a["href"]
    assert "of total for procedures" in info_bar.find(id="statements").a["title"]
    assert "4 statements" in info_bar.find(id="statements").a.text

    breadcrumb = info_bar.find(class_="breadcrumb")
    assert len(breadcrumb("li")) == 3
    breadcrumb_text = [crumb.text for crumb in breadcrumb("li")]
    assert breadcrumb_text == ["ford_test_module.fpp", "test_module", "decrement"]


def test_side_panel(example_project):
    path, _ = example_project
    index = read_html(path / "program/ford_test_program.html")

    side_panel = index.find(id="sidebar")
    assert "None" not in side_panel.text

    side_panels = side_panel.find_all(class_="card-header")
    assert len(side_panels) == 4

    variables_panel = side_panels[0].parent.parent
    assert len(variables_panel("a")) == 2
    assert variables_panel.a.text.strip() == "Variables"
    variables_anchor_link = variables_panel("a")[1]
    assert variables_anchor_link.text.strip() == "global_pi"
    assert (
        variables_anchor_link["href"]
        == "../program/ford_test_program.html#variable-global_pi"
    )

    subroutines_panel = side_panels[3].parent.parent
    assert len(subroutines_panel("a")) == 4
    assert subroutines_panel.a.text.strip() == "Subroutines"
    subroutines_anchor_link = subroutines_panel("a")[1]
    assert subroutines_anchor_link.text.strip() == "do_foo_stuff"
    assert (
        subroutines_anchor_link["href"]
        == "../program/ford_test_program.html#proc-do_foo_stuff"
    )

    type_index = read_html(path / "type/example_type.html")
    constructor_panel = type_index.find(id="cons-0")
    assert constructor_panel.a.text.strip() == "example_type"
    assert (
        constructor_panel.a["href"]
        == "../type/example_type.html#interface-example_type"
    )
    finaliser_panel = type_index.find(id="fins-0")
    assert finaliser_panel.a.text.strip() == "example_type_finalise"
    assert (
        finaliser_panel.a["href"]
        == "../type/example_type.html#finalproc-example_type_finalise"
    )

    check_index = read_html(path / "interface/check.html")
    check_sidebar = check_index.find(id="sidebar")
    assert "None" in check_sidebar.text.strip()
    assert check_sidebar.find_all(class_="card-primary") == []


def test_variable_lists(example_project):
    path, _ = example_project
    index = read_html(path / "program/ford_test_program.html")

    varlist = index.find(class_="varlist")
    assert "Type" in varlist.thead.text
    assert "Attributes" in varlist.thead.text
    assert "Name" in varlist.thead.text
    assert "Initial" in varlist.thead.text
    assert "Optional" not in varlist.thead.text
    assert "Intent" not in varlist.thead.text

    assert len(varlist("tr")) == 2
    assert varlist.tbody.tr.find(class_="anchor")["id"] == "variable-global_pi"
    expected_declaration = "real(kind=real64) :: global_pi = acos(-1) a global variable, initialized to the value of pi"
    declaration_no_whitespace = varlist.tbody.text.replace("\n", "").replace(" ", "")
    assert declaration_no_whitespace == expected_declaration.replace(" ", "")


def test_deprecated(example_project):
    path, _ = example_project
    index = read_html(path / "module/test_module.html")

    apply_check_box = index.find(id="proc-apply_check").parent
    assert apply_check_box.h3.span.text == "Deprecated"


def test_private_procedure_links(example_project):
    path, _ = example_project
    index = read_html(path / "type/example_type.html")

    subroutine_box = index.find("h3", string=re.compile("example_type_say"))
    assert subroutine_box.a is None


def test_public_procedure_links(example_project):
    path, _ = example_project
    index = read_html(path / "module/test_module.html")

    subroutine_box = index.find(id="proc-increment").parent
    assert subroutine_box.a is not None
    assert subroutine_box.a["href"] == "../proc/increment.html"


def test_all_internal_links_resolve(example_project):
    """Opens every HTML file, finds all internal links and checks that
    they resolve to files that actually exist. Furthermore, if the
    link has a fragment ("#something"), check that that fragment
    exists in the specified file.

    """

    path, _ = example_project
    html_files = {}

    for html in path.glob("**/*.html"):
        with open(html, "r") as f:
            html_files[html] = BeautifulSoup(f.read(), features="html.parser")

    for html, index in html_files.items():
        for a_tag in index("a"):
            link = urlparse(a_tag.get("href", ""))
            if link.netloc or link.scheme == "mailto" or not link.path:
                continue

            assert not link.path.startswith(
                "/"
            ), f"absolute path in {a_tag} on page {html}"

            link_path = (html.parent / link.path).resolve()
            assert link_path.exists(), f"{a_tag} on page {html}"

            if not link.fragment:
                continue

            # Check that fragments resolve too
            index2 = html_files[link_path]
            assert index2.find("a", href=re.compile(link.fragment)), html


def test_submodule_procedure_implementation_links(example_project):
    path, _ = example_project
    module_index = read_html(path / "module/test_module.html")

    interfaces_section = module_index.find("h2", string="Interfaces").parent
    check_heading = interfaces_section.ul.li
    assert "subroutine check" in check_heading.text
    implementation_link = check_heading.a
    assert implementation_link["href"].endswith("proc/check.html")

    proc_index = read_html(path / "proc/check.html")
    check_impl_heading = proc_index.find(string=re.compile("subroutine +check")).parent
    assert check_impl_heading.text.startswith("module subroutine check")
    check_interface_link = check_impl_heading.a
    assert "Interface" in check_interface_link.text
    assert check_interface_link["href"].endswith("interface/check.html")

    interface_index = read_html(path / "interface/check.html")
    check_interface_heading = interface_index.find(
        string=re.compile("subroutine +check")
    ).parent
    assert check_interface_heading.text.startswith("public module subroutine check")
    check_impl_link = check_interface_heading.a
    assert "Implementation" in check_impl_link.text
    assert check_impl_link["href"].endswith("proc/check.html")


def test_interfaces(example_project):
    path, _ = example_project
    interface_mod_page = read_html(path / "module/interfaces.html")

    # Span inside the div we actually want, but this has an id
    box_span = interface_mod_page.find(id="interface-generic_unary_f")
    assert box_span

    box = box_span.parent.parent

    list_items = box("li")
    list_item_titles = sorted([li.h3.text.strip() for li in list_items])
    assert list_item_titles == sorted(
        [
            "public pure function real_unary_f(x)",
            "public pure function higher_order_unary_f(f, n)",
            "Dummy Procedures and Procedure Pointers",
        ]
    )

    assert len(list_items[-1]("tr")) == 2


def test_static_pages(example_project):
    path, _ = example_project
    notes_page = read_html(path / "page/index.html")

    # We should have some "author" metadata, but no date
    assert notes_page.find(id="author").text.strip() == "Jane Bloggs", "author"
    assert notes_page.find(id="date") is None, "date"

    sidebar = notes_page.find(id="sidebar-toc")
    subpage_links = sidebar.find_all("a")

    # Check the links in the sidebare to subpages is correct

    subpage_names = [link.text for link in subpage_links]
    # Note that order matters here, so no `sorted`!
    expected_subpage_names = [
        "Notes",
        "First page",
        "Second page",
        "Subdirectories",
        "Subpage in subdirectory",
        "Yet Another Page",
    ]
    assert subpage_names == expected_subpage_names, "subpages"

    subpage_paths = [pathlib.Path(link["href"]) for link in subpage_links]
    expected_subpage_paths = [
        pathlib.Path(f"{link}.html")
        for link in (
            "index",
            "subpage2",
            "subpage1",
            "subdir/index",
            "subdir/subsubpage",
            "subpage3",
        )
    ]
    assert subpage_paths == expected_subpage_paths, "ordered_subpages"


def test_namelist_lists(example_project):
    path, _ = example_project
    namelist_lists = read_html(path / "lists/namelists.html")

    table = namelist_lists.table
    assert table.a.text == "example_namelist"
    assert table.a["href"] == "../namelist/example_namelist.html"


def test_namelist_page(example_project):
    path, _ = example_project
    namelist_page = read_html(path / "namelist/example_namelist.html")

    table = namelist_page.table
    # First row is header, skip it
    rows = table.find_all("tr")[1:]
    variables = sorted([row.td.text for row in rows])
    expected_variables = sorted(["input", "module_level_variable", "local_variable"])

    assert variables == expected_variables


def test_linking_to_page_alias_from_nested_page(example_project):
    path, _ = example_project
    subsubpage = read_html(path / "page/subdir/subsubpage.html")

    link = subsubpage.find("a", string=re.compile("such as"))
    assert link["href"] == "../subpage1.html"


def test_type_attributes(example_project):
    path, _ = example_project
    type_page = read_html(path / "type/say_type_base.html")

    def_statement = type_page.find(id="type-def-statement")
    assert def_statement.text.strip() == "type, public, abstract :: say_type_base"
