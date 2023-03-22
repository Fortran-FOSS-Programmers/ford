from ford.fortran_project import Project
from ford import DEFAULT_SETTINGS
from ford.graphs import graphviz_installed, GraphManager

from copy import deepcopy
from textwrap import dedent

import markdown
import pytest
from bs4 import BeautifulSoup


def create_project(settings: dict):
    md_ext = [
        "markdown.extensions.meta",
        "markdown.extensions.codehilite",
        "markdown.extensions.extra",
    ]
    md = markdown.Markdown(
        extensions=md_ext, output_format="html", extension_configs={}
    )

    project = Project(settings)
    project.markdown(md, "..")
    project.correlate()
    return project


@pytest.fixture(scope="module")
def make_project_graphs(tmp_path_factory):
    data = """\
    module a
    end module a

    module b
      use a
    end module b

    module c
      use b
      use iso_fortran_env
    end module c

    program foo
    contains
      subroutine one
      end subroutine one
      subroutine two
        call one
      end subroutine two
      subroutine three
        call one
        call two
        call two
      end subroutine three
    end program foo
    """

    src_dir = tmp_path_factory.getbasetemp() / "graphs" / "src"
    src_dir.mkdir(exist_ok=True, parents=True)
    full_filename = src_dir / "test.f90"
    with open(full_filename, "w") as f:
        f.write(dedent(data))

    settings = deepcopy(DEFAULT_SETTINGS)
    settings["src_dir"] = [src_dir]
    settings["graph"] = True
    project = create_project(settings)

    graphs = GraphManager("", "", graphdir="", parentdir="..", coloured_edges=True)
    for entity_list in [
        project.types,
        project.procedures,
        project.submodprocedures,
        project.modules,
        project.submodules,
        project.programs,
        project.files,
        project.blockdata,
    ]:
        for item in entity_list:
            graphs.register(item)

    graphs.graph_all()
    graphs.output_graphs(0)
    return graphs


@pytest.mark.skipif(not graphviz_installed, reason="Requires graphviz")
@pytest.mark.parametrize(
    ("graph", "expected_nodes", "expected_edges", "expected_legend_nodes"),
    [
        (
            "usegraph",
            ["module~a", "module~b", "module~c", "iso_fortran_env"],
            ["module~b->module~a", "module~c->module~b", "module~c->iso_fortran_env"],
            ["Module", "Submodule", "Subroutine", "Function", "Program"],
        ),
        (
            "callgraph",
            ["proc~one", "proc~three", "proc~two"],
            ["proc~three->proc~one", "proc~three->proc~two", "proc~two->proc~one"],
            [
                "Subroutine",
                "Function",
                "Interface",
                "Unknown Procedure Type",
                "Program",
            ],
        ),
    ],
)
def test_module_uses_graph(
    make_project_graphs, graph, expected_nodes, expected_edges, expected_legend_nodes
):
    graphs = make_project_graphs

    soup = BeautifulSoup(str(getattr(graphs, graph)), features="html.parser")
    # Get nodes and edges just in the graph, and not in the legend
    node_names = [s.title.text for s in soup.svg.find_all("g", class_="node")]
    edge_names = [s.title.text for s in soup.svg.find_all("g", class_="edge")]

    assert node_names == expected_nodes
    assert edge_names == expected_edges

    svgs = soup.find_all("svg")
    assert len(svgs) == 2, "Graph and legend"

    legend = svgs[1]
    legend_nodes = [s.title.text for s in legend.find_all("g", class_="node")]
    assert legend_nodes == expected_legend_nodes + ["This Page's Entity"]
    assert legend.find_all("g", class_="edge") == []
