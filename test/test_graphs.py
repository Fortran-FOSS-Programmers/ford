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

      type alpha
      contains
        procedure :: five
        procedure :: six
      end type alpha

    contains
      subroutine one
      end subroutine one
      subroutine two
        call one
      end subroutine two
      subroutine five
      end subroutine five
      function six(this) result(res)
        real :: res
        res = 1
      end function six
    end module c

    submodule (c) c_submod
    end submodule c_submod

    submodule (c:c_submod) c_subsubmod
    end submodule c_subsubmod

    program foo
      use c
      call three
      real :: x
      type(alpha) :: y
      call y%five()
      x = y%six()
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

    graphs = GraphManager(
        "", "", graphdir="", parentdir="..", coloured_edges=True, show_proc_parent=True
    )
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
                "a",
                "b",
                "c",
                "c_submod",
                "c_subsubmod",
                "iso_fortran_env",
                "external_mod",
                "foo::three",
                "foo",
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
                "c::one",
                "foo::three",
                "c::two",
                "foo::four",
                "other_sub",
                "foo",
                "c::alpha%five",
                "c::alpha%six",
            ],
            [
                "proc~three->proc~one",
                "proc~three->proc~two",
                "proc~two->proc~one",
                "proc~three->other_sub",
                "program~foo->proc~three",
                "proc~four->proc~four",
                "program~foo->proc~five",
                "program~foo->proc~six",
            ],
            PROC_GRAPH_KEY,
        ),
        (
            ["typegraph"],
            ["base", "derived", "leaf", "external_type", "thing", "alpha"],
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
            ["a", "b"],
            ["module~b->module~a"],
            MOD_GRAPH_KEY,
        ),
        (
            ["modules", "b", "usedbygraph"],
            ["b", "c", "c_submod", "c_subsubmod", "foo"],
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
            ["base", "derived"],
            ["type~derived->type~base"],
            TYPE_GRAPH_KEY,
        ),
        (
            ["types", "derived", "inherbygraph"],
            ["derived", "leaf", "thing"],
            ["type~leaf->type~derived", "type~thing->type~derived"],
            TYPE_GRAPH_KEY,
        ),
        (
            ["procedures", "two", "callsgraph"],
            ["c::one", "c::two"],
            ["proc~two->proc~one"],
            PROC_GRAPH_KEY,
        ),
        (
            ["procedures", "two", "calledbygraph"],
            ["foo::three", "c::two", "foo"],
            ["proc~three->proc~two", "program~foo->proc~three"],
            PROC_GRAPH_KEY,
        ),
        (
            ["procedures", "three", "usesgraph"],
            ["external_mod", "foo::three"],
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
    node_names = [s.find("text").text for s in soup.svg.find_all("g", class_="node")]
    edge_names = [s.title.text for s in soup.svg.find_all("g", class_="edge")]

    assert sorted(node_names) == sorted(expected_nodes)
    assert sorted(edge_names) == sorted(expected_edges)

    svgs = soup.find_all("svg")
    assert len(svgs) == 2, "Graph and legend"

    legend = svgs[1]
    legend_nodes = [s.title.text for s in legend.find_all("g", class_="node")]
    assert legend_nodes == expected_legend_nodes + ["This Page's Entity"]
    assert legend.find_all("g", class_="edge") == []


def test_graphs_as_table(tmp_path):
    data = """\
    program foo
    contains
      subroutine one
      end subroutine one

      subroutine a
        call one()
      end subroutine a

      subroutine b
        call one()
      end subroutine b

      subroutine c
        call one()
      end subroutine c

      subroutine d
        call one()
      end subroutine d

      subroutine e
        call one()
      end subroutine e

      subroutine f
        call one()
      end subroutine f

      subroutine g
        call one()
      end subroutine g

      subroutine h
        call one()
      end subroutine h
    end program foo
    """

    src_dir = tmp_path / "graphs" / "src"
    src_dir.mkdir(exist_ok=True, parents=True)
    full_filename = src_dir / "test.f90"
    with open(full_filename, "w") as f:
        f.write(dedent(data))

    settings = deepcopy(DEFAULT_SETTINGS)
    settings["src_dir"] = [src_dir]
    settings["graph"] = True
    settings["graph_maxnodes"] = 4
    project = create_project(settings)

    graphs = GraphManager(
        "", "", graphdir="", parentdir="..", coloured_edges=True, show_proc_parent=True
    )
    for entity_list in [
        project.procedures,
        project.programs,
    ]:
        for item in entity_list:
            graphs.register(item)

    graphs.graph_all()
    graphs.output_graphs(0)

    for graph in graphs.procedures:
        if graph.name == "one":
            break
    graph = graph.calledbygraph

    soup = BeautifulSoup(str(graph), features="html.parser")
    node_names = sorted([n.text for n in soup.table.find_all(class_="node")])
    num_arrows = len(soup.table.find_all(class_="triangle-right"))
    # These are the spacing 'w's
    num_ws = len(soup.table.find_all(class_="solidBottom"))

    expected_node_names = [
        "foo::a",
        "foo::b",
        "foo::c",
        "foo::d",
        "foo::e",
        "foo::f",
        "foo::g",
        "foo::h",
    ]

    assert node_names == expected_node_names
    assert num_arrows == len(expected_node_names)
    assert num_ws == len(expected_node_names)
