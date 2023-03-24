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
      use external_mod

      type base
      end type base

      type, extends(base) :: derived
      end type derived

      type, extends(derived) :: leaf
        type(external_type) :: component
      end type leaf

      type thing
        type(derived) :: part
      end type thing

    contains
      subroutine one
      end subroutine one
      subroutine two
        call one
      end subroutine two
    end module c

    submodule (c) c_submod
    end submodule c_submod

    submodule (c:c_submod) c_subsubmod
    end submodule c_subsubmod

    program foo
      use c
      call three
    contains
      subroutine three
        use external_mod
        call one
        call two
        call two
        call other_sub
      end subroutine three

      recursive subroutine four
        call four
      end subroutine four
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


MOD_GRAPH_KEY = ["Module", "Submodule", "Subroutine", "Function", "Program"]
PROC_GRAPH_KEY = [
    "Subroutine",
    "Function",
    "Interface",
    "Unknown Procedure Type",
    "Program",
]
TYPE_GRAPH_KEY = ["Type"]


@pytest.mark.skipif(not graphviz_installed, reason="Requires graphviz")
@pytest.mark.parametrize(
    ("graph_name", "expected_nodes", "expected_edges", "expected_legend_nodes"),
    [
        (
            ["usegraph"],
            [
                "module~a",
                "module~b",
                "module~c",
                "module~c_submod",
                "module~c_subsubmod",
                "iso_fortran_env",
                "external_mod",
                "proc~three",
                "program~foo",
            ],
            [
                "module~b->module~a",
                "module~c->module~b",
                "module~c->iso_fortran_env",
                "module~c->external_mod",
                "module~c_submod->module~c",
                "module~c_subsubmod->module~c_submod",
                "proc~three->external_mod",
                "program~foo->module~c",
            ],
            MOD_GRAPH_KEY,
        ),
        (
            ["callgraph"],
            [
                "proc~one",
                "proc~three",
                "proc~two",
                "proc~four",
                "other_sub",
                "program~foo",
            ],
            [
                "proc~three->proc~one",
                "proc~three->proc~two",
                "proc~two->proc~one",
                "proc~three->other_sub",
                "program~foo->proc~three",
                "proc~four->proc~four",
            ],
            PROC_GRAPH_KEY,
        ),
        (
            ["typegraph"],
            ["type~base", "type~derived", "type~leaf", "external_type", "type~thing"],
            [
                "type~leaf->type~derived",
                "type~derived->type~base",
                "type~leaf->external_type",
                "type~thing->type~derived",
            ],
            TYPE_GRAPH_KEY,
        ),
        (
            ["modules", "b", "usesgraph"],
            ["module~a", "module~b"],
            ["module~b->module~a"],
            MOD_GRAPH_KEY,
        ),
        (
            ["modules", "b", "usedbygraph"],
            [
                "module~b",
                "module~c",
                "module~c_submod",
                "module~c_subsubmod",
                "program~foo",
            ],
            [
                "module~c->module~b",
                "module~c_submod->module~c",
                "module~c_subsubmod->module~c_submod",
                "program~foo->module~c",
            ],
            MOD_GRAPH_KEY,
        ),
        (
            ["types", "derived", "inhergraph"],
            ["type~base", "type~derived"],
            ["type~derived->type~base"],
            TYPE_GRAPH_KEY,
        ),
        (
            ["types", "derived", "inherbygraph"],
            ["type~derived", "type~leaf", "type~thing"],
            ["type~leaf->type~derived", "type~thing->type~derived"],
            TYPE_GRAPH_KEY,
        ),
        (
            ["procedures", "two", "callsgraph"],
            ["proc~one", "proc~two"],
            ["proc~two->proc~one"],
            PROC_GRAPH_KEY,
        ),
        (
            ["procedures", "two", "calledbygraph"],
            ["proc~three", "proc~two", "program~foo"],
            ["proc~three->proc~two", "program~foo->proc~three"],
            PROC_GRAPH_KEY,
        ),
        (
            ["procedures", "three", "usesgraph"],
            ["external_mod", "proc~three"],
            ["proc~three->external_mod"],
            MOD_GRAPH_KEY,
        ),
    ],
)
def test_graphs(
    make_project_graphs,
    graph_name,
    expected_nodes,
    expected_edges,
    expected_legend_nodes,
):
    graphs = make_project_graphs

    # Get the graph we want from the graph manager. This might be a
    # top-level graph, showing an overview of the project, or it might
    # be a graph for a particular object. In the latter case, we need
    # to also find the object from the appropriate collection
    if len(graph_name) == 1:
        graph = getattr(graphs, graph_name[0])
    else:
        collection, obj_name, name = graph_name
        for graph in getattr(graphs, collection):
            if graph.name == obj_name:
                break
        graph = getattr(graph, name)

    soup = BeautifulSoup(str(graph), features="html.parser")
    # Get nodes and edges just in the graph, and not in the legend
    node_names = [s.title.text for s in soup.svg.find_all("g", class_="node")]
    edge_names = [s.title.text for s in soup.svg.find_all("g", class_="edge")]

    assert sorted(node_names) == sorted(expected_nodes)
    assert sorted(edge_names) == sorted(expected_edges)

    svgs = soup.find_all("svg")
    assert len(svgs) == 2, "Graph and legend"

    legend = svgs[1]
    legend_nodes = [s.title.text for s in legend.find_all("g", class_="node")]
    assert legend_nodes == expected_legend_nodes + ["This Page's Entity"]
    assert legend.find_all("g", class_="edge") == []
