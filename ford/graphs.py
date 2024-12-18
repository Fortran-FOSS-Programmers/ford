# -*- coding: utf-8 -*-
#
#  graphs.py
#  This file is part of FORD.
#
#  Copyright 2015 Christopher MacMackin <cmacmackin@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

from __future__ import annotations

import colorsys
import copy
import itertools
import os
import pathlib
import re
from typing import Dict, Iterable, List, Optional, Set, Tuple, Type, Union, cast

from graphviz import Digraph, ExecutableNotFound
from graphviz import version as graphviz_version
from tqdm.contrib.concurrent import process_map

from ford.console import warn
from ford.utils import traverse, ProgressBar

from ford.sourceform import (
    ExternalBoundProcedure,
    ExternalFunction,
    ExternalInterface,
    ExternalModule,
    ExternalProgram,
    ExternalSourceFile,
    ExternalSubmodule,
    ExternalSubroutine,
    ExternalType,
    FortranBlockData,
    FortranContainer,
    FortranInterface,
    FortranModule,
    FortranModuleProcedureInterface,
    FortranProcedure,
    FortranProgram,
    FortranSourceFile,
    FortranSubmodule,
    FortranModuleProcedureImplementation,
    FortranBoundProcedure,
    FortranType,
)

try:
    graphviz_version()
    graphviz_installed = True
except ExecutableNotFound:
    graphviz_installed = False


HYPERLINK_RE = re.compile(
    r"^\s*<\s*a\s+.*href=(\"[^\"]+\"|'[^']+').*>(.*)</\s*a\s*>\s*$", re.IGNORECASE
)
WIDTH_RE = re.compile('width="(.*?)pt"', re.IGNORECASE)
HEIGHT_RE = re.compile('height="(.*?)pt"', re.IGNORECASE)
EM_RE = re.compile("<em>(.*)</em>", re.IGNORECASE)


def newdict(old, key, val):
    new = copy.copy(old)
    new[key] = val
    return new


def is_module(obj):
    return isinstance(obj, FortranModule)


def is_submodule(obj):
    return isinstance(obj, FortranSubmodule)


def is_type(obj):
    return isinstance(obj, FortranType)


def is_proc(obj):
    return isinstance(
        obj,
        (
            FortranProcedure,
            FortranInterface,
            FortranModuleProcedureImplementation,
            FortranBoundProcedure,
        ),
    )


def is_program(obj):
    return isinstance(obj, FortranProgram)


def is_sourcefile(obj):
    return isinstance(obj, FortranSourceFile)


def is_blockdata(obj):
    return isinstance(obj, FortranBlockData)


FortranEntity = Union[FortranContainer, FortranBoundProcedure]
NodeCollection = Dict[FortranEntity, "BaseNode"]


class GraphData:
    """Stores graph nodes representing Fortran entities to be
    displayed in a graph, as well as some customisation options for
    graphs

    Parameters
    ----------
    parent_dir:
        Path to top of site
    coloured_edges:
        If true, arrows between nodes are coloured, otherwise they are black
    show_proc_parent:
        If true, the parent of a procedure is shown in the node label

    """

    def __init__(self, parent_dir: str, coloured_edges: bool, show_proc_parent: bool):
        self.submodules: NodeCollection = {}
        self.modules: NodeCollection = {}
        self.types: NodeCollection = {}
        self.procedures: NodeCollection = {}
        self.programs: NodeCollection = {}
        self.sourcefiles: NodeCollection = {}
        self.blockdata: NodeCollection = {}
        self.parent_dir = parent_dir
        self.coloured_edges = coloured_edges
        self.show_proc_parent = show_proc_parent

    def _get_collection_and_node_type(
        self, obj: FortranEntity
    ) -> Tuple[NodeCollection, Type["BaseNode"]]:
        """Helper function for `register` and `get_node`: get the
        appropriate container for ``obj``, and the corresponding node
        type

        """

        if is_submodule(obj):
            return self.submodules, SubmodNode
        if is_module(obj):
            return self.modules, ModNode
        if is_type(obj):
            return self.types, TypeNode
        if is_proc(obj):
            return self.procedures, ProcNode
        if is_program(obj):
            return self.programs, ProgNode
        if is_sourcefile(obj):
            return self.sourcefiles, FileNode
        if is_blockdata(obj):
            return self.blockdata, BlockNode

        raise BadType(
            f"Unrecognised object type '{type(obj).__name__}' for object '{obj}' when constructing graphs"
        )

    def register(
        self, obj: FortranEntity, hist: Optional[NodeCollection] = None
    ) -> None:
        """Create and store the graph node for ``obj``, if it hasn't
        already been registered

        Parameters
        ----------
        obj:
            Some Fortran entity
        hist:
            Collection of previously seen objects, used when
            registering children during node creation

        """

        collection, NodeType = self._get_collection_and_node_type(obj)
        if obj not in collection:
            collection[obj] = NodeType(obj, self, hist)

    def get_node(
        self, obj: FortranEntity, hist: Optional[NodeCollection] = None
    ) -> BaseNode:
        """Returns the node corresponding to ``obj``. If does not
        already exist then it will create it.

        Parameters
        ----------
        obj:
            Some Fortran entity
        hist:
            Collection of previously seen objects, used when
            registering children during node creation

        """
        hist = hist or {}

        if obj in hist:
            return hist[obj]

        collection, _ = self._get_collection_and_node_type(obj)
        if obj not in collection:
            self.register(obj, hist)

        return collection[obj]

    def get_module_node(self, mod: Union[FortranModule, str]) -> ModNode:
        if isinstance(mod, str):
            # Most likely a third-party module
            mod = ExternalModule(mod)
        return cast(ModNode, self.get_node(mod))

    def get_procedure_node(
        self,
        procedure: Union[FortranProcedure, str],
        hist: NodeCollection,
    ) -> ProcNode:
        if isinstance(procedure, str):
            # Most likely a third-party procedure
            procedure = ExternalSubroutine(procedure)
            procedure.proctype = "unknown"

        return cast(ProcNode, self.get_node(procedure, hist))

    def get_type_node(
        self, type_: Union[FortranType, str], hist: NodeCollection
    ) -> TypeNode:
        if isinstance(type_, str):
            # Most likely a third-party type
            type_ = ExternalType(type_)

        return cast(TypeNode, self.get_node(type_, hist))


def get_call_nodes(
    calls: List[Union[str, FortranEntity]],
    visited: Optional[Set[Union[str, FortranEntity]]] = None,
    result: Optional[Set[Union[str, FortranEntity]]] = None,
) -> Set[Union[str, FortranEntity]]:
    """
    takes a list of calls, and returns a set of all the calls that should
    be nodes in the graph

    not all calls are a node, some are not visible, and some are simple
    procedure bindings (bindings that bind one visible procedure to one label)

    these should be skipped, and show a call to their descendant instead
    """

    if visited is None:
        visited = set()
    if result is None:
        result = set()

    for call in calls:
        # ensure we haven't already visited this call
        if call in visited:
            continue
        visited.add(call)

        # value for if the call is a simple binding
        is_simple_binding = (
            isinstance(call, FortranBoundProcedure)
            and len(call.bindings) == 1
            and not isinstance(call.bindings[0], FortranBoundProcedure)
            and (call.deferred or getattr(call.bindings[0], "visible", False))
        )

        if getattr(call, "visible", True) and not is_simple_binding:
            # If the call is visible and isn't a simple binding, add it to the result.
            result.add(call)
        else:
            # If the call is not visible or a simple binding, recursively call the function on the children of the call.
            calls = getattr(call, "calls", []) + getattr(call, "bindings", [])
            get_call_nodes(calls, visited, result)

    return result


class BaseNode:
    """Graph node representing some Fortran entity

    Parameters
    ----------
    obj:
        Fortran entity instance or name
    graph_data:
        Collection of nodes for other entities
    hist:

    """

    colour = "#777777"

    def __init__(
        self,
        obj: Union[FortranEntity, str],
        graph_data: GraphData,
        hist: Optional[NodeCollection] = None,
    ):
        self.attribs = {"color": self.colour, "fontcolor": "white", "style": "filled"}
        if isinstance(
            obj,
            (
                ExternalModule,
                ExternalSubmodule,
                ExternalType,
                ExternalBoundProcedure,
                ExternalSubroutine,
                ExternalFunction,
                ExternalInterface,
                ExternalSubroutine,
                ExternalProgram,
                ExternalSourceFile,
            ),
        ):
            obj = str(obj)

        self.url = None
        if isinstance(obj, str):
            self.fromstr = True
            if m := HYPERLINK_RE.match(obj):
                self.url = m.group(1)[1:-1]
                self.name = m.group(2)
            else:
                self.name = obj
            self.ident = self.name
        else:
            self.fromstr = False
            d = obj.get_dir() or "none"
            self.ident = f"{d}~{obj.ident}"
            self.name = obj.name
            if m := EM_RE.search(self.name):
                self.name = f"<<i>{m.group(1).strip()}</i>>"
            self.url = obj.get_url()

        self.attribs["label"] = self.name
        if self.url and getattr(obj, "visible", True):
            if self.fromstr or hasattr(obj, "external_url"):
                self.attribs["URL"] = self.url
            else:
                self.attribs["URL"] = graph_data.parent_dir + self.url
        self.afferent = 0
        self.efferent = 0

    def __eq__(self, other):
        return self.ident == other.ident

    def __lt__(self, other):
        return self.ident < other.ident

    def __hash__(self):
        # When making graphs in parallel, nodes might not have all
        # their attributes at some point?
        try:
            return hash(self.ident)
        except AttributeError:
            return id(self)


class ModNode(BaseNode):
    colour = "#337AB7"

    def __init__(self, obj, gd, hist=None):
        super().__init__(obj, gd)
        self.uses = set()
        self.used_by = set()
        self.children = set()
        if self.fromstr:
            return
        for u in obj.uses:
            n = gd.get_module_node(u)
            n.used_by.add(self)
            n.afferent += 1
            self.uses.add(n)
            self.efferent += n.efferent


class SubmodNode(ModNode):
    colour = "#5bc0de"

    def __init__(self, obj, gd, hist=None):
        super().__init__(obj, gd)
        del self.used_by
        if self.fromstr:
            return
        if obj.parent_submodule:
            self.ancestor = gd.get_node(obj.parent_submodule)
        else:
            self.ancestor = gd.get_module_node(obj.ancestor_module)
        self.ancestor.children.add(self)
        self.efferent += 1
        self.ancestor.afferent += 1


class TypeNode(BaseNode):
    colour = "#5cb85c"

    def __init__(self, obj, gd, hist=None):
        super().__init__(obj, gd)
        self.ancestor = None
        self.children = set()
        self.comp_types = {}
        self.comp_of = {}
        if self.fromstr:
            return

        hist = newdict(hist or {}, obj, self)

        if hasattr(obj, "external_url"):
            # Stop following chain, as this object is in an external project
            return

        if obj.extends:
            self.ancestor = gd.get_type_node(obj.extends, hist)
            self.ancestor.children.add(self)
            self.ancestor.visible = getattr(obj.extends, "visible", True)

        for var in obj.local_variables:
            if var.vartype not in ["type", "class"]:
                continue

            proto = var.proto[0]
            if proto == "*":
                continue

            node = gd.get_type_node(proto, hist)

            node.visible = getattr(proto, "visible", True)
            if self in node.comp_of:
                node.comp_of[self] += ", " + var.name
            else:
                node.comp_of[self] = var.name
            if node in self.comp_types:
                self.comp_types[node] += ", " + var.name
            else:
                self.comp_types[node] = var.name


class ProcNode(BaseNode):
    COLOURS = {
        "subroutine": "#d9534f",
        "function": "#d94e8f",
        "interface": "#A7506F",
        "boundproc": "#A7506F",
    }

    @property
    def colour(self):
        return ProcNode.COLOURS.get(self.proctype, super().colour)

    def __init__(self, obj, gd: GraphData, hist=None):
        # ToDo: Figure out appropriate way to handle interfaces to routines in submodules.
        self.proctype = getattr(obj, "proctype", "").lower()
        if self.proctype == "" and isinstance(obj, FortranBoundProcedure):
            self.proctype = "boundproc"
        super().__init__(obj, gd)

        if isinstance(obj, FortranBoundProcedure):
            binder = getattr(obj, "parent", None)
            parent = getattr(binder, "parent", None)
        else:
            parent = getattr(obj, "parent", None)
            binder = getattr(getattr(obj, "binding", None), "parent", None)

        parent_label = ""
        binding_label = ""
        if parent and gd.show_proc_parent:
            parent_label = f"{parent.name}::"
        if binder:
            binding_label = f"{binder.name}%"

        self.attribs["label"] = f"{parent_label}{binding_label}{self.name}"

        self.uses = set()
        self.calls = set()
        self.called_by = set()
        self.interfaces = set()
        self.interfaced_by = set()

        if self.fromstr:
            return

        hist = newdict(hist or {}, obj, self)

        for u in getattr(obj, "uses", []):
            n = gd.get_module_node(u)
            n.used_by.add(self)
            self.uses.add(n)

        for call in get_call_nodes(
            getattr(obj, "calls", []) + getattr(obj, "bindings", [])
        ):
            n = gd.get_procedure_node(call, hist)
            n.called_by.add(self)
            self.calls.add(n)

        if self.proctype != "interface":
            return

        for m in getattr(obj, "modprocs", []):
            if m.procedure and getattr(m.procedure, "visible", True):
                n = gd.get_procedure_node(m.procedure, hist)
                n.interfaced_by.add(self)
                self.interfaces.add(n)

        if (
            isinstance(obj, FortranModuleProcedureInterface)
            and isinstance(obj.procedure.module, (str, FortranProcedure))
            and getattr(obj.procedure.module, "visible", True)
        ):
            n = gd.get_procedure_node(obj.procedure.module, hist)
            n.interfaced_by.add(self)
            self.interfaces.add(n)


class ProgNode(BaseNode):
    colour = "#f0ad4e"

    def __init__(self, obj, gd, hist=None):
        super().__init__(obj, gd)
        self.uses = set()
        self.calls = set()
        if self.fromstr:
            return
        for u in obj.uses:
            n = gd.get_module_node(u)
            n.used_by.add(self)
            self.uses.add(n)

        for call in get_call_nodes(obj.calls):
            n = gd.get_procedure_node(call, hist)
            n.called_by.add(self)
            self.calls.add(n)


class BlockNode(BaseNode):
    colour = "#5cb85c"

    def __init__(self, obj, gd, hist=None):
        super().__init__(obj, gd)
        self.uses = set()
        if self.fromstr:
            return
        for u in obj.uses:
            n = gd.get_module_node(u)
            n.used_by.add(self)
            self.uses.add(n)


class FileNode(BaseNode):
    colour = "#f0ad4e"

    def __init__(self, obj, gd, hist=None):
        super().__init__(obj, gd)
        self.afferent = set()  # Things depending on this file
        self.efferent = set()  # Things this file depends on

        if self.fromstr:
            return

        hist = newdict(hist or {}, obj, self)

        for mod in itertools.chain(
            obj.modules,
            obj.submodules,
            obj.functions,
            obj.subroutines,
            obj.programs,
            obj.blockdata,
        ):
            for dep in mod.deplist:
                if dep.source_file == obj:
                    continue
                n = hist.get(dep.source_file, gd.get_node(dep.source_file, hist))
                n.afferent.add(self)
                self.efferent.add(n)


def _edge(
    tail: BaseNode, head: BaseNode, style: str, colour: str, label: Optional[str] = None
) -> Dict:
    return {
        "tail_node": tail,
        "head_node": head,
        "edge": {
            "tail_name": tail.ident,
            "head_name": head.ident,
            "style": style,
            "color": colour,
            "label": label,
        },
    }


def _solid_edge(
    tail: BaseNode, head: BaseNode, colour: str, label: Optional[str] = None
) -> Dict:
    return _edge(tail, head, "solid", colour, label)


def _dashed_edge(
    tail: BaseNode, head: BaseNode, colour: str, label: Optional[str] = None
) -> Dict:
    return _edge(tail, head, "dashed", colour, label)


if graphviz_installed:
    # Create the legends for the graphs. These are their own separate graphs,
    # without edges
    gd = GraphData("", False, False)

    # Graph nodes for a bunch of fake entities that we'll use in the legend
    _module = gd.get_node(ExternalModule("Module"))
    _submodule = gd.get_node(ExternalSubmodule("Submodule"))
    _type = gd.get_node(ExternalType("Type"))
    _subroutine = gd.get_node(ExternalSubroutine("Subroutine"))
    _function = gd.get_node(ExternalFunction("Function"))
    _interface = gd.get_node(ExternalInterface("Interface"))
    _boundproc = gd.get_node(ExternalBoundProcedure("Type Bound Procedure"))
    _unknown_proc = ExternalSubroutine("Unknown Procedure Type")
    _unknown_proc.proctype = "Unknown"
    _unknown = gd.get_node(_unknown_proc)
    _program = gd.get_node(ExternalProgram("Program"))
    _sourcefile = gd.get_node(ExternalSourceFile("Source File"))

    def _make_legend(entities):
        """Make a legend containing a collection of entities"""
        dot = Digraph(
            "Graph Key",
            graph_attr={"size": "8.90625,1000.0", "concentrate": "false"},
            node_attr={
                "shape": "box",
                "height": "0.0",
                "margin": "0.08",
                "fontname": "Helvetica",
                "fontsize": "10.5",
            },
            edge_attr={"fontname": "Helvetica", "fontsize": "9.5"},
            format="svg",
            engine="dot",
        )
        for entity in entities:
            dot.node(entity.name, **entity.attribs)
        dot.node("This Page's Entity")
        return dot.pipe().decode("utf-8")

    mod_svg = _make_legend([_module, _submodule, _subroutine, _function, _program])
    type_svg = _make_legend([_type])
    call_svg = _make_legend(
        [_subroutine, _function, _interface, _boundproc, _unknown, _program]
    )
    file_svg = _make_legend([_sourcefile])
else:
    mod_svg = ""
    type_svg = ""
    call_svg = ""
    file_svg = ""

NODE_DIAGRAM = "<p>Nodes of different colours represent the following: </p>"

MOD_GRAPH_KEY = f"""
{NODE_DIAGRAM}
{mod_svg}
<p>Solid arrows point from a submodule to the (sub)module which it is
descended from. Dashed arrows point from a module or program unit to 
modules which it uses.
</p>
"""  # noqa W291

TYPE_GRAPH_KEY = f"""
{NODE_DIAGRAM}
{type_svg}
<p>Solid arrows point from a derived type to the parent type which it
extends. Dashed arrows point from a derived type to the other
types it contains as a components, with a label listing the name(s) of
said component(s).
</p>
"""

CALL_GRAPH_KEY = f"""
{NODE_DIAGRAM}
{call_svg}
<p>Solid arrows point from a procedure to one which it calls. Dashed 
arrows point from an interface to procedures which implement that interface.
This could include the module procedures in a generic interface or the
implementation in a submodule of an interface in a parent module.
</p>
"""  # noqa W291

FILE_GRAPH_KEY = f"""
{NODE_DIAGRAM}
{file_svg}
<p>Solid arrows point from a file to a file which it depends on. A file
is dependent upon another if the latter must be compiled before the former
can be.
</p>
"""

COLOURED_NOTICE = """Where possible, edges connecting nodes are
given different colours to make them easier to distinguish in
large graphs."""

del call_svg
del file_svg
del type_svg
del mod_svg


class FortranGraph:
    """Graph of some relationship for a given entity

    Parameters
    ----------
    root:
        Top-level entity or entities in graph
    data:
        Collection of nodes and graph customisation options
    ident:
        Alternative identification for graph, and used as base name
        for saved files. If there are multiple entities in ``root``,
        and ``ident`` isn't given, it is set from the first entity in
        ``root``

    Attributes
    ----------
    hop_nodes:
        Nodes of the hop which exceed the maximum
    hop_edges:
        Edges of the hop which exceed the maximum
    added:
        Set of nodes in graph
    max_nesting:
        Maximum number of hops allowed. Set from maximum value of
        ``graph_maxdepth`` in ``root.meta``
    max_nodes:
        Maximum number of nodes allowed. Set from maximum value of
        ``graph_maxnodes`` in ``root.meta``
    warn:
        If true, show warnings if graphs exceed ``max_nesting`` or
        ``max_nodes``
    truncated:
        Nesting level where the graph was truncated
    """

    RANKDIR = "RL"
    _should_add_nested_nodes = False
    _legend = ""

    def __init__(
        self,
        root: Union[FortranContainer, Iterable[FortranContainer]],
        data: GraphData,
        ident: Optional[str] = None,
    ):
        self.root = []
        self.data = data
        self.hop_nodes: List[BaseNode] = []
        self.hop_edges: List[BaseNode] = []
        self.added: Set[BaseNode] = set()
        self.max_nesting = 0
        self.max_nodes = 1
        self.warn = False
        self.truncated = -1

        if not isinstance(root, Iterable):
            root = [root]
        root = sorted(list(root))

        for r in root:
            self.root.append(self.data.get_node(r))
            if hasattr(r, "meta"):
                self.max_nesting = max(self.max_nesting, int(r.meta.graph_maxdepth))
                self.max_nodes = max(self.max_nodes, int(r.meta.graph_maxnodes))
            if hasattr(r, "settings"):
                self.warn = self.warn or (r.settings.warn)

        ident = ident or f"{root[0].get_dir()}~~{root[0].ident}"
        self.ident = f"{ident}~~{self.__class__.__name__}"
        self.imgfile = self.ident
        self.dot = Digraph(
            self.ident,
            graph_attr={
                "size": "8.90625,1000.0",
                "rankdir": self.RANKDIR,
                "concentrate": "true",
                "id": self.ident,
            },
            node_attr={
                "shape": "box",
                "height": "0.0",
                "margin": "0.08",
                "fontname": "Helvetica",
                "fontsize": "10.5",
            },
            edge_attr={"fontname": "Helvetica", "fontsize": "9.5"},
            format="svg",
            engine="dot",
        )
        # add root nodes to the graph
        for n in sorted(self.root):
            if len(self.root) == 1:
                self.dot.node(n.ident, label=n.attribs["label"])
            else:
                self.dot.node(n.ident, **n.attribs)
            self.added.add(n)
        # add nodes and edges depending on the root nodes to the graph
        self.add_nodes(self.root)

        if graphviz_installed:
            self.svg_src = self.dot.pipe().decode("utf-8")
            self.svg_src = self.svg_src.replace(
                "<svg ", '<svg id="' + re.sub(r"[^\w]", "", self.ident) + '" '
            )
            if match := WIDTH_RE.search(self.svg_src):
                width = int(match.group(1))
            else:
                width = 0
            if isinstance(self, (ModuleGraph, CallGraph, TypeGraph)):
                self.scaled = width >= 855
            else:
                self.scaled = width >= 641
        else:
            self.svg_src = ""
            self.scaled = False

    def add_to_graph(self, nodes, edges, nesting):
        """
        Adds nodes and edges to the graph as long as the maximum number
        of nodes is not exceeded.
        All edges are expected to have a reference to an entry in nodes.
        If the list of nodes is not added in the first hop due to graph
        size limitations, they are stored in hop_nodes.
        If the graph was extended the function returns True, otherwise the
        result will be False.
        """
        if (len(nodes) + len(self.added)) > self.max_nodes:
            if nesting < 2:
                self.hop_nodes = nodes
                self.hop_edges = edges
            self.truncated = nesting
            return False

        for n in sorted(nodes):
            strattribs = {key: str(a) for key, a in n.attribs.items()}
            self.dot.node(n.ident, **strattribs)
        for edge in edges:
            self.dot.edge(**edge["edge"])
        self.added.update(nodes)
        return True

    def __str__(self):
        """
        The string of the graph is its HTML representation.
        It will only be created if it is not too large.
        If the graph is overly large but can represented by a single node
        with many dependencies it will be shown as a table instead to ease
        the rendering in browsers.
        """

        graph_as_table = len(self.hop_nodes) > 0 and len(self.root) == 1

        # Do not render empty graphs
        if len(self.added) <= 1 and not graph_as_table:
            return ""

        # Do not render overly large graphs.
        if len(self.added) > self.max_nodes:
            if self.warn:
                warn(
                    f"Not showing graph {self.ident} as it would exceed the maximal number of {self.max_nodes} nodes"
                )
            return ""

        # Do not render incomplete graphs.
        if len(self.added) < len(self.root):
            if self.warn:
                warn(f"Not showing graph {self.ident} as it would be incomplete")
            return ""

        if self.truncated > 0 and self.warn:
            warn(f"Graph {self.ident} is truncated after {self.truncated} hops")

        if graph_as_table:
            rettext = self._make_graph_as_table()
        # generate svg graph
        else:
            rettext = f'<div class="depgraph">{self.svg_src}</div>'
            # add zoom ability for big graphs
            if self.scaled:
                zoomName = re.sub(r"[^\w]", "", self.ident)
                rettext += f"""\
                <script>
                  var pan{zoomName} = svgPanZoom('#{zoomName}',
                    {{zoomEnabled: true, controlIconsEnabled: true, fit: true, center: true,}}
                  );
                </script>"""

        graph_help_name = f"{self.__class__.__name__}-help-text"

        legend_graph = f"""\
          <div>
            <a type="button" class="graph-help" data-bs-toggle="modal" href="#{graph_help_name}">Help</a>
          </div>
          <div class="modal fade" id="{graph_help_name}" tabindex="-1" role="dialog">
            <div class="modal-dialog modal-lg" role="document">
              <div class="modal-content">
                <div class="modal-header">
                  <h4 class="modal-title" id="-graph-help-label">Graph Key</h4>
                  <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">{self._legend} {COLOURED_NOTICE if self.data.coloured_edges else ""}</div>
            </div>
          </div>
        </div>"""
        return rettext + legend_graph

    def _make_graph_as_table(self):
        # generate a table graph if maximum number of nodes gets exceeded in
        # the first hop and there is only one root node.

        # Base templates for the arrows along edges
        arrow_shaft = '<td class="{style}{text_loc}">{label}</td>'
        arrow_right = f'{arrow_shaft}<td rowspan="2" class="triangle-right"></td>'
        arrow_left = f'<td rowspan="2" class="triangle-left"></td>{arrow_shaft}'

        # Work out if the root node is the head or tail of the
        # arrow, and which direction the arrows point in
        if self.hop_edges[0]["edge"]["tail_name"] == self.root[0].ident:
            key = "head_node"
            root_on_left = self.RANKDIR == "LR"
            arrowtemp = arrow_right if root_on_left else arrow_left
        else:
            key = "tail_node"
            root_on_left = self.RANKDIR == "RL"
            arrowtemp = arrow_left if root_on_left else arrow_right

        # Sort nodes in alphabetical order by either the head or
        # tail node's label
        self.hop_edges.sort(key=lambda x: x[key].attribs["label"].lower())

        # Now construct each node and associated edge as a single row in a table.
        # The root node takes up one column and spans all rows
        total_rows = len(self.hop_nodes) * 2 + 1
        root = f'<td class="root" rowspan="{total_rows}">{self.root[0].attribs["label"]}</td>'
        rows = ""
        for edge in self.hop_edges:
            style = edge["edge"]["style"]
            # The 'w' here is in white and is used to correctly position the arrow
            # shaft in the centre of the arrowhead
            label = edge["edge"]["label"] or "w"
            text_loc = "Bottom" if label == "w" else "Text"
            arrow_args = {"style": style, "label": label, "text_loc": text_loc}
            arrow = arrowtemp.format(**arrow_args)
            attribs = edge[key].attribs
            try:
                link = f'<a href="{attribs["URL"]}">{attribs["label"]}</a></td>'
            except KeyError:
                link = f'{attribs["label"]}</td>'

            node = f'<td rowspan="2" class="node" bgcolor="{attribs["color"]}">{link}'

            root_arrow = (
                f"{root}{arrow}{node}" if root_on_left else f"{node}{arrow}{root}"
            )
            rows += f'<tr>{root_arrow}</tr>\n<tr><td class="{style}Top">w</td></tr>\n'
            # Root node is handled by first row in table, so clear it
            root = ""

        return f'<table class="graph">\n{rows}</table>\n'

    def __nonzero__(self):
        return self.__bool__()

    def __bool__(self):
        return bool(self.__str__())

    def create_svg(self, out_location: pathlib.Path):
        if len(self.added) > len(self.root):
            out_location = pathlib.Path(out_location)
            self._create_image_file(out_location / self.imgfile)

    def _create_image_file(self, filename: pathlib.Path):
        if not graphviz_installed:
            return

        self.dot.render(str(filename), cleanup=False)
        filename.rename(str(filename) + ".gv")

    def add_nodes(self, nodes, nesting=1):
        """Add nodes and edges to this graph, based on the collection ``nodes``

        Subclasses should implement `FortranGraph.add_node`, and optionally
        `FortranGraph.extra_attributes`

        """
        hop_nodes = set()  # nodes in this hop
        hop_edges = []  # edges in this hop

        total_len = len(nodes)

        def rainbowcolour(depth, maxd):
            if not self.data.coloured_edges:
                return "#000000"
            (r, g, b) = colorsys.hsv_to_rgb(float(depth) / maxd, 1.0, 1.0)
            return f"#{int(255 * r):02X}{int(255 * g):02X}{int(255 * b):02X}"

        for i, node in enumerate(sorted(nodes)):
            colour = rainbowcolour(i, total_len)

            self.add_node(hop_nodes, hop_edges, node, colour)

        if not self.add_to_graph(hop_nodes, hop_edges, nesting):
            return

        self.extra_attributes()

        if self._should_add_nested_nodes:
            self._add_nested_nodes(hop_nodes, nesting)

    def _add_nested_nodes(self, hop_nodes, nesting):
        """Handles nested nodes"""
        if len(hop_nodes) == 0:
            return

        if nesting < self.max_nesting:
            self.add_nodes(hop_nodes, nesting=nesting + 1)
        else:
            self.truncated = nesting

    def add_node(self, hop_nodes, hop_edges, node, colour):
        """Add a single node and its edges to this graph, typically by
        iterating over parents/children

        """

        raise NotImplementedError

    def extra_attributes(self):
        """Add any extra attributes to the graph"""
        pass


class ModuleGraph(FortranGraph):
    """Shows the relationship between modules and submodules"""

    _legend = MOD_GRAPH_KEY

    def add_node(self, hop_nodes, hop_edges, node, colour):
        for nu in sorted(node.uses):
            if nu not in self.added:
                hop_nodes.add(nu)
            hop_edges.append(_dashed_edge(node, nu, colour))

        if hasattr(node, "ancestor"):
            if node.ancestor not in self.added:
                hop_nodes.add(node.ancestor)
            hop_edges.append(_solid_edge(node, node.ancestor, colour))

    def extra_attributes(self):
        self.dot.attr("graph", size="11.875,1000.0")


class UsesGraph(FortranGraph):
    """Graphs how modules use other modules, including ancestor (sub)modules"""

    _should_add_nested_nodes = True
    _legend = MOD_GRAPH_KEY

    def add_node(self, hop_nodes, hop_edges, node, colour):
        for nu in sorted(node.uses):
            if nu not in self.added:
                hop_nodes.add(nu)
            hop_edges.append(_dashed_edge(node, nu, colour))

        if hasattr(node, "ancestor"):
            if node.ancestor not in self.added:
                hop_nodes.add(node.ancestor)
            hop_edges.append(_solid_edge(node, node.ancestor, colour))


class UsedByGraph(FortranGraph):
    """Graphs how modules are used by other modules"""

    _should_add_nested_nodes = True
    _legend = MOD_GRAPH_KEY

    def add_node(self, hop_nodes, hop_edges, node, colour):
        for nu in sorted(getattr(node, "used_by", [])):
            if nu not in self.added:
                hop_nodes.add(nu)
            hop_edges.append(_dashed_edge(nu, node, colour))
        for c in sorted(getattr(node, "children", [])):
            if c not in self.added:
                hop_nodes.add(c)
            hop_edges.append(_solid_edge(c, node, colour))


class FileGraph(FortranGraph):
    """Graphs relationships between source files"""

    _legend = FILE_GRAPH_KEY

    def add_node(self, hop_nodes, hop_edges, node, colour):
        for ne in sorted(node.efferent):
            if ne not in self.added:
                hop_nodes.add(ne)
            hop_edges.append(_solid_edge(ne, node, colour))


class EfferentGraph(FortranGraph):
    """Shows the relationship between the files which this one depends on"""

    _should_add_nested_nodes = True
    _legend = FILE_GRAPH_KEY

    def add_node(self, hop_nodes, hop_edges, node, colour):
        for ne in sorted(node.efferent):
            if ne not in self.added:
                hop_nodes.add(ne)
            hop_edges.append(_dashed_edge(node, ne, colour))


class AfferentGraph(FortranGraph):
    """Shows the relationship between files which depend upon this one"""

    _should_add_nested_nodes = True
    _legend = FILE_GRAPH_KEY

    def add_node(self, hop_nodes, hop_edges, node, colour):
        for na in sorted(node.afferent):
            if na not in self.added:
                hop_nodes.add(na)
            hop_edges.append(_dashed_edge(na, node, colour))


class TypeGraph(FortranGraph):
    """Graphs inheritance and composition relationships between derived types"""

    _legend = TYPE_GRAPH_KEY

    def add_node(self, hop_nodes, hop_edges, node, colour):
        for keys in node.comp_types.keys():
            if keys not in self.added:
                hop_nodes.add(keys)
        for c in node.comp_types:
            if c not in self.added:
                hop_nodes.add(c)
            hop_edges.append(_dashed_edge(node, c, colour, node.comp_types[c]))
        if node.ancestor:
            if node.ancestor not in self.added:
                hop_nodes.add(node.ancestor)
            hop_edges.append(_solid_edge(node, node.ancestor, colour))

    def extra_attributes(self):
        self.dot.attr("graph", size="11.875,1000.0")


class InheritsGraph(FortranGraph):
    """Graphs types that this type inherits from"""

    _should_add_nested_nodes = True
    _legend = TYPE_GRAPH_KEY

    def add_node(self, hop_nodes, hop_edges, node, colour):
        for c in node.comp_types:
            if c not in self.added:
                hop_nodes.add(c)
            hop_edges.append(_dashed_edge(node, c, colour, node.comp_types[c]))
        if node.ancestor:
            if node.ancestor not in self.added:
                hop_nodes.add(node.ancestor)
            hop_edges.append(_solid_edge(node, node.ancestor, colour))


class InheritedByGraph(FortranGraph):
    """Graphs types that inherit this type"""

    _should_add_nested_nodes = True
    _legend = TYPE_GRAPH_KEY

    def add_node(self, hop_nodes, hop_edges, node, colour):
        for c in node.comp_of:
            if c not in self.added:
                hop_nodes.add(c)
            hop_edges.append(_dashed_edge(c, node, colour, node.comp_of[c]))
        for c in node.children:
            if c not in self.added:
                hop_nodes.add(c)
            hop_edges.append(_solid_edge(c, node, colour))


class CallGraph(FortranGraph):
    """
    Adds edges indicating the call-tree for the procedures listed in
    the nodes.
    """

    RANKDIR = "LR"
    _legend = CALL_GRAPH_KEY

    def add_node(self, hop_nodes, hop_edges, node, colour):
        for p in sorted(node.calls):
            if p not in hop_nodes:
                hop_nodes.add(p)
            if getattr(node, "proctype", "") != "boundproc":
                hop_edges.append(_solid_edge(node, p, colour))
            else:
                hop_edges.append(_dashed_edge(node, p, colour))
        for p in sorted(getattr(node, "interfaces", [])):
            if p not in hop_nodes:
                hop_nodes.add(p)
            hop_edges.append(_dashed_edge(node, p, colour))

    def extra_attributes(self):
        self.dot.attr("graph", size="11.875,1000.0")
        self.dot.attr("graph", concentrate="false")


class CallsGraph(FortranGraph):
    """Graphs procedures that this procedure calls"""

    RANKDIR = "LR"
    _should_add_nested_nodes = True
    _legend = CALL_GRAPH_KEY

    def add_node(self, hop_nodes, hop_edges, node, colour):
        for p in sorted(node.calls):
            if p not in self.added:
                hop_nodes.add(p)
            if getattr(node, "proctype", "") != "boundproc":
                hop_edges.append(_solid_edge(node, p, colour))
            else:
                hop_edges.append(_dashed_edge(node, p, colour))
        for p in sorted(getattr(node, "interfaces", [])):
            if p not in self.added:
                hop_nodes.add(p)
            hop_edges.append(_dashed_edge(node, p, colour))

    def extra_attributes(self):
        self.dot.attr("graph", concentrate="false")


class CalledByGraph(FortranGraph):
    """Graphs procedures called by this procedure"""

    RANKDIR = "LR"
    _should_add_nested_nodes = True
    _legend = CALL_GRAPH_KEY

    def add_node(self, hop_nodes, hop_edges, node, colour):
        if isinstance(node, ProgNode):
            return
        for p in sorted(node.called_by):
            if p not in self.added:
                hop_nodes.add(p)
            hop_edges.append(_solid_edge(p, node, colour))
        for p in sorted(getattr(node, "interfaced_by", [])):
            if p not in self.added:
                hop_nodes.add(p)
            hop_edges.append(_dashed_edge(p, node, colour))

    def extra_attributes(self):
        self.dot.attr("graph", concentrate="false")


class BadType(Exception):
    """
    Raised when a type is passed to GraphData.register() which is not
    accepted.
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


def outputFuncWrap(args):
    """Wrapper function for output graphs -- needed to allow multiprocessing to
    pickle the function (must be at top level)"""

    for f in args[0:-1]:
        f.create_svg(args[-1])

    return None


class GraphManager:
    """Collection of graphs of the various relationships between a set
    of entities

    Contains graphs of module use relations, type relations, call
    trees, etc. It manages these, ensures that everything that is
    needed is added at the correct time, and produces the plots for
    the list pages.

    Parameters
    ----------
    graphdir:
        The location of the graphs within the output tree.
    parentdir:
        Location of top-level directory
    coloured_edges:
        If true, arrows in graphs use different colours to help
        distinguish them
    show_proc_parent:
        If true, show the parent of a procedure in the call graph
        as part of the label
    save_graphs:
        If true, save graphs as separate files, as well as embedding
        them in the HTML
    """

    def __init__(
        self,
        graphdir: os.PathLike,
        parentdir: str,
        coloured_edges: bool,
        show_proc_parent: bool,
        save_graphs: bool = False,
    ):
        self.graph_objs: List[FortranContainer] = []
        self.modules: Set[FortranContainer] = set()
        self.programs: Set[FortranContainer] = set()
        self.procedures: Set[FortranContainer] = set()
        self.internal_procedures: Set[FortranContainer] = set()
        self.bound_procedures: Set[FortranContainer] = set()
        self.types: Set[FortranContainer] = set()
        self.sourcefiles: Set[FortranContainer] = set()
        self.blockdata: Set[FortranContainer] = set()
        self.save_graphs = save_graphs
        self.graphdir = pathlib.Path(graphdir)
        self.usegraph = None
        self.typegraph = None
        self.callgraph = None
        self.filegraph = None
        self.data = GraphData(parentdir, coloured_edges, show_proc_parent)

    def register(self, obj: FortranContainer):
        """Register ``obj`` as a node to be used in graphs"""
        if obj.meta.graph:
            self.data.register(obj)
            self.graph_objs.append(obj)

    def graph_all(self):
        """Create all graphs"""

        for obj in (bar := ProgressBar("Generating graphs", sorted(self.graph_objs))):
            bar.set_current(obj.name)
            if is_module(obj):
                obj.usesgraph = UsesGraph(obj, self.data)
                obj.usedbygraph = UsedByGraph(obj, self.data)
                self.modules.add(obj)
            elif is_type(obj):
                obj.inhergraph = InheritsGraph(obj, self.data)
                obj.inherbygraph = InheritedByGraph(obj, self.data)
                self.types.add(obj)
                # register bound procedures that arn't simple bindings (bindings that bind one procedure to one label)
                for bp in getattr(obj, "boundprocs", []):
                    if not (
                        len(bp.bindings) == 1
                        and not isinstance(bp.bindings[0], FortranBoundProcedure)
                    ):
                        self.bound_procedures.add(bp)
            elif is_proc(obj):
                obj.callsgraph = CallsGraph(obj, self.data)
                obj.calledbygraph = CalledByGraph(obj, self.data)
                obj.usesgraph = UsesGraph(obj, self.data)
                self.procedures.add(obj)
                # regester internal procedures
                for p in traverse(obj, ["subroutines", "functions"]):
                    (
                        self.internal_procedures.add(p)
                        if getattr(p, "visible", False)
                        else None
                    )
            elif is_program(obj):
                obj.usesgraph = UsesGraph(obj, self.data)
                obj.callsgraph = CallsGraph(obj, self.data)
                self.programs.add(obj)
            elif is_sourcefile(obj):
                obj.afferentgraph = AfferentGraph(obj, self.data)
                obj.efferentgraph = EfferentGraph(obj, self.data)
                self.sourcefiles.add(obj)
            elif is_blockdata(obj):
                obj.usesgraph = UsesGraph(obj, self.data)
                self.blockdata.add(obj)

        usenodes = sorted(list(self.modules))
        callnodes = sorted(
            list(self.procedures | self.internal_procedures | self.bound_procedures)
        )
        for p in sorted(self.programs):
            if len(p.usesgraph.added) > 1:
                usenodes.append(p)
            if len(p.callsgraph.added) > 1:
                callnodes.append(p)
        for p in sorted(self.procedures):
            if len(p.usesgraph.added) > 1:
                usenodes.append(p)
        for b in self.blockdata:
            if len(b.usesgraph.added) > 1:
                usenodes.append(b)
        self.usegraph = ModuleGraph(usenodes, self.data, "module~~graph")
        self.typegraph = TypeGraph(self.types, self.data, "type~~graph")
        self.callgraph = CallGraph(callnodes, self.data, "call~~graph")
        self.filegraph = FileGraph(self.sourcefiles, self.data, "file~~graph")

    def output_graphs(self, njobs=0):
        """Save graphs to file"""

        if not self.save_graphs:
            return

        self.graphdir.mkdir(exist_ok=True, parents=True, mode=0o755)

        if njobs == 0:
            for m in self.modules:
                m.usesgraph.create_svg(self.graphdir)
                m.usedbygraph.create_svg(self.graphdir)
            for t in self.types:
                t.inhergraph.create_svg(self.graphdir)
                t.inherbygraph.create_svg(self.graphdir)
            for p in self.procedures:
                p.callsgraph.create_svg(self.graphdir)
                p.calledbygraph.create_svg(self.graphdir)
            for p in self.programs:
                p.callsgraph.create_svg(self.graphdir)
                p.usesgraph.create_svg(self.graphdir)
            for f in self.sourcefiles:
                f.afferentgraph.create_svg(self.graphdir)
                f.efferentgraph.create_svg(self.graphdir)
            for b in self.blockdata:
                b.usesgraph.create_svg(self.graphdir)
        else:
            args = []
            # Note we generate all graphs for a given object in one wrapper call
            # this is to try to ensure we don't get name collisions not present
            # in the serial version (e.g. due to calling usesgraph and usedbygraph on
            # a particular module in two different processes). May not actually be needed
            # commented block above allows testing of one graph per call approach.
            args.extend(
                [(m.usesgraph, m.usedbygraph, self.graphdir) for m in self.modules]
            )
            args.extend(
                [(m.inhergraph, m.inherbygraph, self.graphdir) for m in self.types]
            )
            args.extend(
                [
                    (m.callsgraph, m.calledbygraph, self.graphdir)
                    for m in self.procedures
                ]
            )
            args.extend(
                [(m.callsgraph, m.usesgraph, self.graphdir) for m in self.programs]
            )
            args.extend(
                [
                    (m.afferentgraph, m.efferentgraph, self.graphdir)
                    for m in self.sourcefiles
                ]
            )
            args.extend([(m.usesgraph, self.graphdir) for m in self.blockdata])

            process_map(
                outputFuncWrap,
                args,
                max_workers=njobs,
                desc="Writing graphs",
                chunksize=1,
            )

        for graph in [self.usegraph, self.typegraph, self.callgraph, self.filegraph]:
            if graph:
                graph.create_svg(self.graphdir)
