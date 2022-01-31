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

import os
import shutil
import re
import copy
import colorsys

from graphviz import Digraph

from ford.sourceform import (
    FortranFunction,
    ExternalFunction,
    FortranSubroutine,
    ExternalSubroutine,
    FortranInterface,
    ExternalInterface,
    FortranProgram,
    FortranType,
    ExternalType,
    FortranModule,
    ExternalModule,
    FortranSubmodule,
    FortranSubmoduleProcedure,
    FortranSourceFile,
    FortranBlockData,
)

_coloured_edges = False


def set_coloured_edges(val):
    """
    Public accessor to set whether to use coloured edges in graph or just
    use black ones.
    """
    global _coloured_edges
    _coloured_edges = val


_parentdir = ""


def set_graphs_parentdir(val):
    """
    Public accessor to set the parent directory of the graphs.
    Needed for relative paths.
    """
    global _parentdir
    _parentdir = val


def rainbowcolour(depth, maxd):
    if _coloured_edges:
        (r, g, b) = colorsys.hsv_to_rgb(float(depth) / maxd, 1.0, 1.0)
        R, G, B = int(255 * r), int(255 * g), int(255 * b)
        return R, G, B
    else:
        return 0, 0, 0


HYPERLINK_RE = re.compile(
    r"^\s*<\s*a\s+.*href=(\"[^\"]+\"|'[^']+').*>(.*)</\s*a\s*>\s*$", re.IGNORECASE
)
WIDTH_RE = re.compile('width="(.*?)pt"', re.IGNORECASE)
HEIGHT_RE = re.compile('height="(.*?)pt"', re.IGNORECASE)
EM_RE = re.compile("<em>(.*)</em>", re.IGNORECASE)

graphviz_installed = True


def newdict(old, key, val):
    new = copy.copy(old)
    new[key] = val
    return new


def is_module(obj, cls):
    return isinstance(obj, (FortranModule, ExternalModule)) or issubclass(
        cls, (FortranModule, ExternalModule)
    )


def is_submodule(obj, cls):
    return isinstance(obj, FortranSubmodule) or issubclass(cls, FortranSubmodule)


def is_type(obj, cls):
    return isinstance(obj, (FortranType, ExternalType)) or issubclass(
        cls, (FortranType, ExternalType)
    )


def is_proc(obj, cls):
    return isinstance(
        obj,
        (
            FortranFunction,
            ExternalFunction,
            FortranSubroutine,
            ExternalSubroutine,
            FortranInterface,
            ExternalInterface,
            FortranSubmoduleProcedure,
        ),
    ) or issubclass(
        cls,
        (
            FortranFunction,
            ExternalFunction,
            FortranSubroutine,
            ExternalSubroutine,
            FortranInterface,
            ExternalInterface,
            FortranSubmoduleProcedure,
        ),
    )


def is_program(obj, cls):
    return isinstance(obj, FortranProgram) or issubclass(cls, FortranProgram)


def is_sourcefile(obj, cls):
    return isinstance(obj, FortranSourceFile) or issubclass(cls, FortranSourceFile)


def is_blockdata(obj, cls):
    return isinstance(obj, FortranBlockData) or issubclass(cls, FortranBlockData)


class GraphData(object):
    """
    Contains all of the nodes which may be displayed on a graph.
    """

    def __init__(self):
        self.submodules = {}
        self.modules = {}
        self.types = {}
        self.procedures = {}
        self.programs = {}
        self.sourcefiles = {}
        self.blockdata = {}

    def register(self, obj, cls=type(None), hist={}):
        """
        Takes a FortranObject and adds it to the appropriate list, if
        not already present.
        """
        # ~ ident = getattr(obj,'ident',obj)
        if is_submodule(obj, cls):
            if obj not in self.submodules:
                self.submodules[obj] = SubmodNode(obj, self)
        elif is_module(obj, cls):
            if obj not in self.modules:
                self.modules[obj] = ModNode(obj, self)
        elif is_type(obj, cls):
            if obj not in self.types:
                self.types[obj] = TypeNode(obj, self, hist)
        elif is_proc(obj, cls):
            if obj not in self.procedures:
                self.procedures[obj] = ProcNode(obj, self, hist)
        elif is_program(obj, cls):
            if obj not in self.programs:
                self.programs[obj] = ProgNode(obj, self)
        elif is_sourcefile(obj, cls):
            if obj not in self.sourcefiles:
                self.sourcefiles[obj] = FileNode(obj, self)
        elif is_blockdata(obj, cls):
            if obj not in self.blockdata:
                self.blockdata[obj] = BlockNode(obj, self)
        else:
            raise BadType(
                "Object type {} not recognized by GraphData".format(type(obj).__name__)
            )

    def get_node(self, obj, cls=type(None), hist={}):
        """
        Returns the node corresponding to obj. If does not already exist
        then it will create it.
        """
        # ~ ident = getattr(obj,'ident',obj)
        if obj in self.modules and is_module(obj, cls):
            return self.modules[obj]
        elif obj in self.submodules and is_submodule(obj, cls):
            return self.submodules[obj]
        elif obj in self.types and is_type(obj, cls):
            return self.types[obj]
        elif obj in self.procedures and is_proc(obj, cls):
            return self.procedures[obj]
        elif obj in self.programs and is_program(obj, cls):
            return self.programs[obj]
        elif obj in self.sourcefiles and is_sourcefile(obj, cls):
            return self.sourcefiles[obj]
        elif obj in self.blockdata and is_blockdata(obj, cls):
            return self.blockdata[obj]
        else:
            self.register(obj, cls, hist)
            return self.get_node(obj, cls, hist)


class BaseNode(object):
    colour = "#777777"

    def __init__(self, obj):
        self.attribs = {"color": self.colour, "fontcolor": "white", "style": "filled"}
        self.fromstr = type(obj) is str
        self.url = None
        if self.fromstr:
            m = HYPERLINK_RE.match(obj)
            if m:
                self.url = m.group(1)[1:-1]
                self.name = m.group(2)
            else:
                self.name = obj
            self.ident = self.name
        else:
            d = obj.get_dir()
            if not d:
                d = "none"
            self.ident = d + "~" + obj.ident
            self.name = obj.name
            m = EM_RE.search(self.name)
            if m:
                self.name = "<<i>" + m.group(1).strip() + "</i>>"
            self.url = obj.get_url()
        self.attribs["label"] = self.name
        if self.url and getattr(obj, "visible", True):
            if self.fromstr or hasattr(obj, "external_url"):
                self.attribs["URL"] = self.url
            else:
                self.attribs["URL"] = _parentdir + self.url
        self.afferent = 0
        self.efferent = 0

    def __eq__(self, other):
        return self.ident == other.ident

    def __hash__(self):
        return hash(self.ident)


class ModNode(BaseNode):
    colour = "#337AB7"

    def __init__(self, obj, gd):
        super(ModNode, self).__init__(obj)
        self.uses = set()
        self.used_by = set()
        self.children = set()
        if not self.fromstr:
            for u in obj.uses:
                n = gd.get_node(u, FortranModule)
                n.used_by.add(self)
                n.afferent += 1
                self.uses.add(n)
                self.efferent += n.efferent


class SubmodNode(ModNode):
    colour = "#5bc0de"

    def __init__(self, obj, gd):
        super(SubmodNode, self).__init__(obj, gd)
        del self.used_by
        if not self.fromstr:
            if obj.ancestor:
                self.ancestor = gd.get_node(obj.ancestor, FortranSubmodule)
            else:
                self.ancestor = gd.get_node(obj.ancestor_mod, FortranModule)
            self.ancestor.children.add(self)
            self.efferent += 1
            self.ancestor.afferent += 1


class TypeNode(BaseNode):
    colour = "#5cb85c"

    def __init__(self, obj, gd, hist={}):
        super(TypeNode, self).__init__(obj)
        self.ancestor = None
        self.children = set()
        self.comp_types = dict()
        self.comp_of = dict()
        if not self.fromstr:
            if obj.extends:
                if obj.extends in hist:
                    self.ancestor = hist[obj.extends]
                else:
                    self.ancestor = gd.get_node(
                        obj.extends, FortranType, newdict(hist, obj, self)
                    )
                self.ancestor.children.add(self)
                self.ancestor.visible = getattr(obj.extends, "visible", True)

            if hasattr(obj, "external_url"):
                # Stop following chain, as this object is in an external project
                return

            for var in obj.local_variables:
                if (var.vartype == "type" or var.vartype == "class") and var.proto[
                    0
                ] != "*":
                    if var.proto[0] == obj:
                        n = self
                    elif var.proto[0] in hist:
                        n = hist[var.proto[0]]
                    else:
                        n = gd.get_node(
                            var.proto[0], FortranType, newdict(hist, obj, self)
                        )
                    n.visible = getattr(var.proto[0], "visible", True)
                    if self in n.comp_of:
                        n.comp_of[self] += ", " + var.name
                    else:
                        n.comp_of[self] = var.name
                    if n in self.comp_types:
                        self.comp_types[n] += ", " + var.name
                    else:
                        self.comp_types[n] = var.name


class ProcNode(BaseNode):
    @property
    def colour(self):
        if self.proctype.lower() == "subroutine":
            return "#d9534f"
        elif self.proctype.lower() == "function":
            return "#d94e8f"
        elif self.proctype.lower() == "interface":
            return "#A7506F"
            # ~ return '#c77c25'
        else:
            return super(ProcNode, self).colour

    def __init__(self, obj, gd, hist={}):
        # ToDo: Figure out appropriate way to handle interfaces to routines in submodules.
        self.proctype = getattr(obj, "proctype", "")
        super(ProcNode, self).__init__(obj)
        self.uses = set()
        self.calls = set()
        self.called_by = set()
        self.interfaces = set()
        self.interfaced_by = set()
        if not self.fromstr:
            for u in getattr(obj, "uses", []):
                n = gd.get_node(u, FortranModule)
                n.used_by.add(self)
                self.uses.add(n)
            for c in getattr(obj, "calls", []):
                if getattr(c, "visible", True):
                    if c == obj:
                        n = self
                    elif c in hist:
                        n = hist[c]
                    else:
                        n = gd.get_node(c, FortranSubroutine, newdict(hist, obj, self))
                    n.called_by.add(self)
                    self.calls.add(n)
            if obj.proctype.lower() == "interface":
                for m in getattr(obj, "modprocs", []):
                    if m.procedure and getattr(m.procedure, "visible", True):
                        if m.procedure in hist:
                            n = hist[m.procedure]
                        else:
                            n = gd.get_node(
                                m.procedure, FortranSubroutine, newdict(hist, obj, self)
                            )
                        n.interfaced_by.add(self)
                        self.interfaces.add(n)
                if (
                    hasattr(obj, "procedure")
                    and obj.procedure.module
                    and obj.procedure.module is not True
                    and getattr(obj.procedure.module, "visible", True)
                ):
                    if obj.procedure.module in hist:
                        n = hist[obj.procedure.module]
                    else:
                        n = gd.get_node(
                            obj.procedure.module,
                            FortranSubroutine,
                            newdict(hist, obj, self),
                        )
                    n.interfaced_by.add(self)
                    self.interfaces.add(n)


class ProgNode(BaseNode):
    colour = "#f0ad4e"

    def __init__(self, obj, gd):
        super(ProgNode, self).__init__(obj)
        self.uses = set()
        self.calls = set()
        if not self.fromstr:
            for u in obj.uses:
                n = gd.get_node(u, FortranModule)
                n.used_by.add(self)
                self.uses.add(n)
            for c in obj.calls:
                if getattr(c, "visible", True):
                    n = gd.get_node(c, FortranSubroutine)
                    n.called_by.add(self)
                    self.calls.add(n)


class BlockNode(BaseNode):
    colour = "#5cb85c"

    def __init__(self, obj, gd):
        super(BlockNode, self).__init__(obj)
        self.uses = set()
        if not self.fromstr:
            for u in obj.uses:
                n = gd.get_node(u, FortranModule)
                n.used_by.add(self)
                self.uses.add(n)


class FileNode(BaseNode):
    colour = "#f0ad4e"

    def __init__(self, obj, gd, hist={}):
        super(FileNode, self).__init__(obj)
        self.afferent = set()  # Things depending on this file
        self.efferent = set()  # Things this file depends on
        if not self.fromstr:
            for mod in obj.modules:
                for dep in mod.deplist:
                    if dep.hierarchy[0] == obj:
                        continue
                    elif dep.hierarchy[0] in hist:
                        n = hist[dep.hierarchy[0]]
                    else:
                        n = gd.get_node(
                            dep.hierarchy[0],
                            FortranSourceFile,
                            newdict(hist, obj, self),
                        )
                    n.afferent.add(self)
                    self.efferent.add(n)
            for mod in obj.submodules:
                for dep in mod.deplist:
                    if dep.hierarchy[0] == obj:
                        continue
                    elif dep.hierarchy[0] in hist:
                        n = hist[dep.hierarchy[0]]
                    else:
                        n = gd.get_node(
                            dep.hierarchy[0],
                            FortranSourceFile,
                            newdict(hist, obj, self),
                        )
                    n.afferent.add(self)
                    self.efferent.add(n)
            for proc in obj.functions + obj.subroutines:
                for dep in proc.deplist:
                    if dep.hierarchy[0] == obj:
                        continue
                    elif dep.hierarchy[0] in hist:
                        n = hist[dep.hierarchy[0]]
                    else:
                        n = gd.get_node(
                            dep.hierarchy[0],
                            FortranSourceFile,
                            newdict(hist, obj, self),
                        )
                    n.afferent.add(self)
                    self.efferent.add(n)
            for prog in obj.programs:
                for dep in prog.deplist:
                    if dep.hierarchy[0] == obj:
                        continue
                    elif dep.hierarchy[0] in hist:
                        n = hist[dep.hierarchy[0]]
                    else:
                        n = gd.get_node(
                            dep.hierarchy[0],
                            FortranSourceFile,
                            newdict(hist, obj, self),
                        )
                    n.afferent.add(self)
                    self.efferent.add(n)
            for block in obj.blockdata:
                for dep in block.deplist:
                    if dep.hierarchy[0] == obj:
                        continue
                    elif dep.hierarchy[0] in hist:
                        n = hist[dep.hierarchy[0]]
                    else:
                        n = gd.get_node(
                            dep.hierarchy[0],
                            FortranSourceFile,
                            newdict(hist, obj, self),
                        )
                    n.afferent.add(self)
                    self.efferent.add(n)


class FortranGraph(object):
    """
    Object used to construct the graph for some particular entity in the code.
    """

    data = GraphData()
    RANKDIR = "RL"

    def __init__(self, root, webdir="", ident=None):
        """
        Initialize the graph, root is the object or list of objects,
        for which the graph is to be constructed.
        The webdir is the url where the graph should be stored, and
        ident can be provided to override the default identifacation
        of the graph that will be used to construct the name of the
        imagefile. It has to be provided if there are multiple root
        nodes.
        """
        self.root = []  # root nodes
        self.hopNodes = []  # nodes of the hop which exceeded the maximum
        self.hopEdges = []  # edges of the hop which exceeded the maximum
        self.added = set()  # nodes added to the graph
        self.max_nesting = 0  # maximum numbers of hops allowed
        self.max_nodes = 1  # maximum numbers of nodes allowed
        self.warn = False  # should warnings be written?
        self.truncated = -1  # nesting where the graph was truncated
        try:
            for r in root:
                self.root.append(self.data.get_node(r))
                self.max_nesting = max(self.max_nesting, int(r.meta["graph_maxdepth"]))
                self.max_nodes = max(self.max_nodes, int(r.meta["graph_maxnodes"]))
                self.warn = self.warn or (r.settings["warn"])
        except TypeError:
            self.root.append(self.data.get_node(root))
            self.max_nesting = int(root.meta["graph_maxdepth"])
            self.max_nodes = max(self.max_nodes, int(root.meta["graph_maxnodes"]))
            self.warn = root.settings["warn"]
        self.webdir = webdir
        if ident:
            self.ident = ident + "~~" + self.__class__.__name__
        else:
            self.ident = (
                root.get_dir() + "~~" + root.ident + "~~" + self.__class__.__name__
            )
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
        for n in self.root:
            if len(self.root) == 1:
                self.dot.node(n.ident, label=n.name)
            else:
                self.dot.node(n.ident, **n.attribs)
            self.added.add(n)
        # add nodes and edges depending on the root nodes to the graph
        self.add_nodes(self.root)
        # ~ self.linkmap = self.dot.pipe('cmapx').decode('utf-8')
        if graphviz_installed:
            self.svg_src = self.dot.pipe().decode("utf-8")
            self.svg_src = self.svg_src.replace(
                "<svg ", '<svg id="' + re.sub(r"[^\w]", "", self.ident) + '" '
            )
            w = int(WIDTH_RE.search(self.svg_src).group(1))
            if isinstance(self, (ModuleGraph, CallGraph, TypeGraph)):
                self.scaled = w >= 855
            else:
                self.scaled = w >= 641
        else:
            self.svg_src = ""
            self.scaled = False

    def add_to_graph(self, nodes, edges, nesting):
        """
        Adds nodes and edges to the graph as long as the maximum number
        of nodes is not exceeded.
        All edges are expected to have a reference to an entry in nodes.
        If the list of nodes is not added in the first hop due to graph
        size limitations, they are stored in hopNodes.
        If the graph was extended the function returns True, otherwise the
        result will be False.
        """
        if (len(nodes) + len(self.added)) > self.max_nodes:
            if nesting < 2:
                self.hopNodes = nodes
                self.hopEdges = edges
            self.truncated = nesting
            return False
        else:
            for n in nodes:
                self.dot.node(n.ident, **n.attribs)
            for e in edges:
                if len(e) == 5:
                    self.dot.edge(
                        e[0].ident, e[1].ident, style=e[2], color=e[3], label=e[4]
                    )
                else:
                    self.dot.edge(e[0].ident, e[1].ident, style=e[2], color=e[3])
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

        graph_as_table = len(self.hopNodes) > 0 and len(self.root) == 1

        # Do not render empty graphs
        if len(self.added) <= 1 and not graph_as_table:
            return ""

        # Do not render overly large graphs.
        if len(self.added) > self.max_nodes:
            if self.warn:
                print(
                    "Warning: Not showing graph {0} as it would exceed the maximal number of {1} nodes.".format(
                        self.ident, self.max_nodes
                    )
                )
                # Only warn once about this
                self.warn = False
            return ""
        # Do not render incomplete graphs.
        if len(self.added) < len(self.root):
            if self.warn:
                print(
                    "Warning: Not showing graph {0} as it would be incomplete.".format(
                        self.ident
                    )
                )
                # Only warn once about this
                self.warn = False
            return ""

        if self.warn and self.truncated > 0:
            print(
                "Warning: Graph {0} is truncated after {1} hops.".format(
                    self.ident, self.truncated
                )
            )
            # Only warn once about this
            self.warn = False

        zoomName = ""
        svgGraph = ""
        rettext = ""
        if graph_as_table:
            # generate a table graph if maximum number of nodes gets exceeded in
            # the first hop and there is only one root node.
            root = '<td class="root" rowspan="{0}">{1}</td>'.format(
                len(self.hopNodes) * 2 + 1, self.root[0].attribs["label"]
            )
            if self.hopEdges[0][0].ident == self.root[0].ident:
                key = 1
                root_on_left = self.RANKDIR == "LR"
                if root_on_left:
                    arrowtemp = (
                        '<td class="{0}{1}">{2}</td><td rowspan="2"'
                        + 'class="triangle-right"></td>'
                    )
                else:
                    arrowtemp = (
                        '<td rowspan="2" class="triangle-left">'
                        + '</td><td class="{0}{1}">{2}</td>'
                    )
            else:
                key = 0
                root_on_left = self.RANKDIR == "RL"
                if root_on_left:
                    arrowtemp = (
                        '<td rowspan="2" class="triangle-left">'
                        + '</td><td class="{0}{1}">{2}</td>'
                    )
                else:
                    arrowtemp = (
                        '<td class="{0}{1}">{2}</td><td rowspan="2"'
                        + 'class="triangle-right"></td>'
                    )
            # sort nodes in alphabetical order
            self.hopEdges.sort(key=lambda x: x[key].attribs["label"].lower())
            rows = ""
            for i in range(len(self.hopEdges)):
                e = self.hopEdges[i]
                n = e[key]
                if len(e) == 5:
                    arrow = arrowtemp.format(e[2], "Text", e[4])
                else:
                    arrow = arrowtemp.format(e[2], "Bottom", "w")
                node = '<td rowspan="2" class="node" bgcolor="{0}">'.format(
                    n.attribs["color"]
                )
                try:
                    node += '<a href="{0}">{1}</a></td>'.format(
                        n.attribs["URL"], n.attribs["label"]
                    )
                except KeyError:
                    node += n.attribs["label"] + "</td>"
                if root_on_left:
                    rows += "<tr>" + root + arrow + node + "</tr>\n"
                else:
                    rows += "<tr>" + node + arrow + root + "</tr>\n"
                rows += '<tr><td class="{0}Top">w</td></tr>\n'.format(e[2])
                root = ""
            rettext += '<table class="graph">\n' + rows + "</table>\n"

        # generate svg graph
        else:
            rettext += '<div class="depgraph">{0}</div>'
            svgGraph = self.svg_src
            # add zoom ability for big graphs
            if self.scaled:
                zoomName = re.sub(r"[^\w]", "", self.ident)
                rettext += (
                    "<script>var pan{1} = svgPanZoom('#{1}', "
                    "{{zoomEnabled: true,controlIconsEnabled: true, "
                    "fit: true, center: true,}}); </script>"
                )
        rettext += (
            '<div><a type="button" class="graph-help" '
            'data-toggle="modal" href="#graph-help-text">Help</a>'
            '</div><div class="modal fade" id="graph-help-text" '
            'tabindex="-1" role="dialog"><div class="modal-dialog '
            'modal-lg" role="document"><div class="modal-content">'
            '<div class="modal-header"><button type="button" '
            'class="close" data-dismiss="modal" aria-label="Close">'
            '<span aria-hidden="true">&times;</span></button><h4 class'
            '="modal-title" id="-graph-help-label">Graph Key</h4>'
            '</div><div class="modal-body">{2}</div></div></div>'
            "</div>"
        )
        return rettext.format(svgGraph, zoomName, self.get_key())

    def __nonzero__(self):
        return self.__bool__()

    def __bool__(self):
        return bool(self.__str__())

    @classmethod
    def reset(cls):
        cls.data = GraphData()

    def create_svg(self, out_location):
        if len(self.added) > len(self.root):
            self._create_image_file(os.path.join(out_location, self.imgfile))

    def _create_image_file(self, filename):
        if graphviz_installed:
            self.dot.render(filename, cleanup=False)
            shutil.move(
                filename,
                os.path.join(
                    os.path.dirname(filename), os.path.basename(filename) + ".gv"
                ),
            )


class ModuleGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ""
        return MOD_GRAPH_KEY.format(colour_notice)

    def add_nodes(self, nodes, nesting=1):
        """
        Adds nodes and edges for generating the graph showing the relationship
        between modules and submodules listed in nodes.
        """
        hopNodes = set()  # nodes in this hop
        hopEdges = []  # edges in this hop
        # get nodes and edges for this hop
        for i, n in zip(range(len(nodes)), nodes):
            r, g, b = rainbowcolour(i, len(nodes))
            colour = "#%02X%02X%02X" % (r, g, b)
            for nu in n.uses:
                if nu not in self.added:
                    hopNodes.add(nu)
                hopEdges.append((n, nu, "dashed", colour))
            if hasattr(n, "ancestor"):
                if n.ancestor not in self.added:
                    hopNodes.add(n.ancestor)
                hopEdges.append((n, n.ancestor, "solid", colour))
        # add nodes, edges and attributes to the graph if maximum number of
        # nodes is not exceeded
        if self.add_to_graph(hopNodes, hopEdges, nesting):
            self.dot.attr("graph", size="11.875,1000.0")


class UsesGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ""
        return MOD_GRAPH_KEY.format(colour_notice)

    def add_nodes(self, nodes, nesting=1):
        """
        Adds nodes for the modules used by those listed in nodes. Adds
        edges between them. Also does this for ancestor (sub)modules.
        """
        hopNodes = set()  # nodes in this hop
        hopEdges = []  # edges in this hop
        # get nodes and edges for this hop
        for i, n in zip(range(len(nodes)), nodes):
            r, g, b = rainbowcolour(i, len(nodes))
            colour = "#%02X%02X%02X" % (r, g, b)
            for nu in n.uses:
                if nu not in self.added:
                    hopNodes.add(nu)
                hopEdges.append((n, nu, "dashed", colour))
            if hasattr(n, "ancestor"):
                if n.ancestor not in self.added:
                    hopNodes.add(n.ancestor)
                hopEdges.append((n, n.ancestor, "solid", colour))
        # add nodes and edges for this hop to the graph if maximum number of
        # nodes is not exceeded
        if not self.add_to_graph(hopNodes, hopEdges, nesting):
            return
        elif len(hopNodes) > 0:
            if nesting < self.max_nesting:
                self.add_nodes(hopNodes, nesting=nesting + 1)
            else:
                self.truncated = nesting


class UsedByGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ""
        return MOD_GRAPH_KEY.format(colour_notice)

    def add_nodes(self, nodes, nesting=1):
        """
        Adds nodes for modules using or descended from those listed in
        nodes. Adds appropriate edges between them.
        """
        hopNodes = set()  # nodes in this hop
        hopEdges = []  # edges in this hop
        # get nodes and edges for this hop
        for i, n in zip(range(len(nodes)), nodes):
            r, g, b = rainbowcolour(i, len(nodes))
            colour = "#%02X%02X%02X" % (r, g, b)
            for nu in getattr(n, "used_by", []):
                if nu not in self.added:
                    hopNodes.add(nu)
                hopEdges.append((nu, n, "dashed", colour))
            for c in getattr(n, "children", []):
                if c not in self.added:
                    hopNodes.add(c)
                hopEdges.append((c, n, "solid", colour))
        # add nodes and edges for this hop to the graph if maximum number of
        # nodes is not exceeded
        if not self.add_to_graph(hopNodes, hopEdges, nesting):
            return
        elif len(hopNodes) > 0:
            if nesting < self.max_nesting:
                self.add_nodes(hopNodes, nesting=nesting + 1)
            else:
                self.truncated = nesting


class FileGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ""
        return FILE_GRAPH_KEY.format(colour_notice)

    def add_nodes(self, nodes, nesting=1):
        """
        Adds edges showing dependencies between source files listed in
        the nodes.
        """
        hopNodes = set()  # nodes in this hop
        hopEdges = []  # edges in this hop
        # get nodes and edges for this hop
        for i, n in zip(range(len(nodes)), nodes):
            r, g, b = rainbowcolour(i, len(nodes))
            colour = "#%02X%02X%02X" % (r, g, b)
            for ne in n.efferent:
                if ne not in self.added:
                    hopNodes.add(ne)
                hopEdges.append((ne, n, "solid", colour))
        # add nodes and edges to the graph if maximum number of nodes is not
        # exceeded
        self.add_to_graph(hopNodes, hopEdges, nesting)


class EfferentGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ""
        return FILE_GRAPH_KEY.format(colour_notice)

    def add_nodes(self, nodes, nesting=1):
        """
        Adds nodes for the files which this one depends on. Adds
        edges between them.
        """
        hopNodes = set()  # nodes in this hop
        hopEdges = []  # edges in this hop
        # get nodes and edges for this hop
        for i, n in zip(range(len(nodes)), nodes):
            r, g, b = rainbowcolour(i, len(nodes))
            colour = "#%02X%02X%02X" % (r, g, b)
            for ne in n.efferent:
                if ne not in self.added:
                    hopNodes.add(ne)
                hopEdges.append((n, ne, "dashed", colour))
        # add nodes and edges for this hop to the graph if maximum number of
        # nodes is not exceeded
        if not self.add_to_graph(hopNodes, hopEdges, nesting):
            return
        elif len(hopNodes) > 0:
            if nesting < self.max_nesting:
                self.add_nodes(hopNodes, nesting=nesting + 1)
            else:
                self.truncated = nesting


class AfferentGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ""
        return FILE_GRAPH_KEY.format(colour_notice)

    def add_nodes(self, nodes, nesting=1):
        """
        Adds nodes for files which depend upon this one. Adds appropriate
        edges between them.
        """
        hopNodes = set()  # nodes in this hop
        hopEdges = []  # edges in this hop
        # get nodes and edges for this hop
        for i, n in zip(range(len(nodes)), nodes):
            r, g, b = rainbowcolour(i, len(nodes))
            colour = "#%02X%02X%02X" % (r, g, b)
            for na in n.afferent:
                if na not in self.added:
                    hopNodes.add(na)
                hopEdges.append((na, n, "dashed", colour))
        # add nodes and edges for this hop to the graph if maximum number of
        # nodes is not exceeded
        if not self.add_to_graph(hopNodes, hopEdges, nesting):
            return
        elif len(hopNodes) > 0:
            if nesting < self.max_nesting:
                self.add_nodes(hopNodes, nesting=nesting + 1)
            else:
                self.truncated = nesting


class TypeGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ""
        return TYPE_GRAPH_KEY.format(colour_notice)

    def add_nodes(self, nodes, nesting=1):
        """
        Adds edges showing inheritance and composition relationships
        between derived types listed in the nodes.
        """
        hopNodes = set()  # nodes in this hop
        hopEdges = []  # edges in this hop
        # get nodes and edges for this hop
        for i, n in zip(range(len(nodes)), nodes):
            r, g, b = rainbowcolour(i, len(nodes))
            colour = "#%02X%02X%02X" % (r, g, b)
            for keys in n.comp_types.keys():
                if keys not in self.added:
                    hopNodes.add(keys)
            for c in n.comp_types:
                if c not in self.added:
                    hopNodes.add(c)
                hopEdges.append((n, c, "dashed", colour, n.comp_types[c]))
            if n.ancestor:
                if n.ancestor not in self.added:
                    hopNodes.add(n.ancestor)
                hopEdges.append((n, n.ancestor, "solid", colour))
        # add nodes, edges and attributes to the graph if maximum number of
        # nodes is not exceeded
        if self.add_to_graph(hopNodes, hopEdges, nesting):
            self.dot.attr("graph", size="11.875,1000.0")


class InheritsGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ""
        return TYPE_GRAPH_KEY.format(colour_notice)

    def add_nodes(self, nodes, nesting=1):
        """
        Adds nodes for modules using or descended from those listed in
        nodes. Adds appropriate edges between them.
        """
        hopNodes = set()  # nodes in this hop
        hopEdges = []  # edges in this hop
        # get nodes and edges for this hop
        for i, n in zip(range(len(nodes)), nodes):
            r, g, b = rainbowcolour(i, len(nodes))
            colour = "#%02X%02X%02X" % (r, g, b)
            for c in n.comp_types:
                if c not in self.added:
                    hopNodes.add(c)
                hopEdges.append((n, c, "dashed", colour, n.comp_types[c]))
            if n.ancestor:
                if n.ancestor not in self.added:
                    hopNodes.add(n.ancestor)
                hopEdges.append((n, n.ancestor, "solid", colour))
        # add nodes and edges for this hop to the graph if maximum number of
        # nodes is not exceeded
        if not self.add_to_graph(hopNodes, hopEdges, nesting):
            return
        elif len(hopNodes) > 0:
            if nesting < self.max_nesting:
                self.add_nodes(hopNodes, nesting=nesting + 1)
            else:
                self.truncated = nesting


class InheritedByGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ""
        return TYPE_GRAPH_KEY.format(colour_notice)

    def add_nodes(self, nodes, nesting=1):
        """
        Adds nodes for modules using or descended from those listed in
        nodes. Adds appropriate edges between them.
        """
        hopNodes = set()  # nodes in this hop
        hopEdges = []  # edges in this hop
        # get nodes and edges for this hop
        for i, n in zip(range(len(nodes)), nodes):
            r, g, b = rainbowcolour(i, len(nodes))
            colour = "#%02X%02X%02X" % (r, g, b)
            for c in n.comp_of:
                if c not in self.added:
                    hopNodes.add(c)
                hopEdges.append((c, n, "dashed", colour, n.comp_of[c]))
            for c in n.children:
                if c not in self.added:
                    hopNodes.add(c)
                hopEdges.append((c, n, "solid", colour))
        # add nodes and edges for this hop to the graph if maximum number of
        # nodes is not exceeded
        if not self.add_to_graph(hopNodes, hopEdges, nesting):
            return
        elif len(hopNodes) > 0:
            if nesting < self.max_nesting:
                self.add_nodes(hopNodes, nesting=nesting + 1)
            else:
                self.truncated = nesting


class CallGraph(FortranGraph):
    RANKDIR = "LR"

    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ""
        return CALL_GRAPH_KEY.format(colour_notice)

    def add_nodes(self, nodes, nesting=1):
        """
        Adds edges indicating the call-tree for the procedures listed in
        the nodes.
        """
        hopNodes = set()  # nodes in this hop
        hopEdges = []  # edges in this hop
        # get nodes and edges for this hop
        for i, n in zip(range(len(nodes)), nodes):
            r, g, b = rainbowcolour(i, len(nodes))
            colour = "#%02X%02X%02X" % (r, g, b)
            for p in n.calls:
                if p not in hopNodes:
                    hopNodes.add(p)
                hopEdges.append((n, p, "solid", colour))
            for p in getattr(n, "interfaces", []):
                if p not in hopNodes:
                    hopNodes.add(p)
                hopEdges.append((n, p, "dashed", colour))
        # add nodes, edges and attributes to the graph if maximum number of
        # nodes is not exceeded
        if self.add_to_graph(hopNodes, hopEdges, nesting):
            self.dot.attr("graph", size="11.875,1000.0")
            self.dot.attr("graph", concentrate="false")


class CallsGraph(FortranGraph):
    RANKDIR = "LR"

    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ""
        return CALL_GRAPH_KEY.format(colour_notice)

    def add_nodes(self, nodes, nesting=1):
        """
        Adds nodes for modules using or descended from those listed in
        nodes. Adds appropriate edges between them.
        """
        hopNodes = set()  # nodes in this hop
        hopEdges = []  # edges in this hop
        # get nodes and edges for this hop
        for i, n in zip(range(len(nodes)), nodes):
            r, g, b = rainbowcolour(i, len(nodes))
            colour = "#%02X%02X%02X" % (r, g, b)
            for p in n.calls:
                if p not in self.added:
                    hopNodes.add(p)
                hopEdges.append((n, p, "solid", colour))
            for p in getattr(n, "interfaces", []):
                if p not in self.added:
                    hopNodes.add(p)
                hopEdges.append((n, p, "dashed", colour))
        # add nodes, edges and atrributes for this hop to the graph if
        # maximum number of nodes is not exceeded
        if not self.add_to_graph(hopNodes, hopEdges, nesting):
            return
        elif len(hopNodes) > 0:
            if nesting < self.max_nesting:
                self.dot.attr("graph", concentrate="false")
                self.add_nodes(hopNodes, nesting=nesting + 1)
            else:
                self.truncated = nesting


class CalledByGraph(FortranGraph):
    RANKDIR = "LR"

    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ""
        return CALL_GRAPH_KEY.format(colour_notice)

    def add_nodes(self, nodes, nesting=1):
        """
        Adds nodes for modules using or descended from those listed in
        nodes. Adds appropriate edges between them.
        """
        hopNodes = set()  # nodes in this hop
        hopEdges = []  # edges in this hop
        # get nodes and edges for this hop
        for i, n in zip(range(len(nodes)), nodes):
            r, g, b = rainbowcolour(i, len(nodes))
            colour = "#%02X%02X%02X" % (r, g, b)
            if isinstance(n, ProgNode):
                continue
            for p in n.called_by:
                if p not in self.added:
                    hopNodes.add(p)
                hopEdges.append((p, n, "solid", colour))
            for p in getattr(n, "interfaced_by", []):
                if p not in self.added:
                    hopNodes.add(p)
                hopEdges.append((p, n, "dashed", colour))
        # add nodes, edges and atrributes for this hop to the graph if
        # maximum number of nodes is not exceeded
        if not self.add_to_graph(hopNodes, hopEdges, nesting):
            return
        elif len(hopNodes) > 0:
            if nesting < self.max_nesting:
                self.dot.attr("graph", concentrate="false")
                self.add_nodes(hopNodes, nesting=nesting + 1)
            else:
                self.truncated = nesting


class BadType(Exception):
    """
    Raised when a type is passed to GraphData.register() which is not
    accepted.
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


# Generate graph keys
gd = GraphData()


class Proc(object):
    def __init__(self, name, proctype):
        self.name = name
        self.proctype = proctype
        self.ident = ""

    def get_url(self):
        return ""

    def get_dir(self):
        return ""


sub = Proc("Subroutine", "Subroutine")
func = Proc("Function", "Function")
intr = Proc("Interface", "Interface")
gd.register("Module", FortranModule)
gd.register("Submodule", FortranSubmodule)
gd.register("Type", FortranType)
gd.register(sub, FortranSubroutine)
gd.register(func, FortranFunction)
gd.register(intr, FortranInterface)
gd.register("Unknown Procedure Type", FortranSubroutine)
gd.register("Program", FortranProgram)
gd.register("Source File", FortranSourceFile)

try:
    # Generate key for module graph
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
    for n in [
        ("Module", FortranModule),
        ("Submodule", FortranSubmodule),
        (sub, FortranSubroutine),
        (func, FortranFunction),
        ("Program", FortranProgram),
    ]:
        dot.node(getattr(n[0], "name", n[0]), **gd.get_node(n[0], cls=n[1]).attribs)
    dot.node("This Page's Entity")
    mod_svg = dot.pipe().decode("utf-8")

    # Generate key for type graph
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
    dot.node("Type", **gd.get_node("Type", cls=FortranType).attribs)
    dot.node("This Page's Entity")
    type_svg = dot.pipe().decode("utf-8")

    # Generate key for call graph
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
    for n in [
        (sub, FortranSubroutine),
        (func, FortranFunction),
        (intr, FortranInterface),
        ("Unknown Procedure Type", FortranFunction),
        ("Program", FortranProgram),
    ]:
        dot.node(getattr(n[0], "name", n[0]), **gd.get_node(n[0], cls=n[1]).attribs)
    dot.node("This Page's Entity")
    call_svg = dot.pipe().decode("utf-8")

    # Generate key for file graph
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
    dot.node("Source File", **gd.get_node("Source File", cls=FortranSourceFile).attribs)
    dot.node("This Page's Entity")
    file_svg = dot.pipe().decode("utf-8")

except RuntimeError:
    graphviz_installed = False


if graphviz_installed:
    NODE_DIAGRAM = """
    <p>Nodes of different colours represent the following: </p>
    {}
    """

    MOD_GRAPH_KEY = (
        NODE_DIAGRAM
        + """
    <p>Solid arrows point from a submodule to the (sub)module which it is
    descended from. Dashed arrows point from a module or program unit to 
    modules which it uses.{{}}
    </p>
    """  # noqa W291
    ).format(mod_svg)

    TYPE_GRAPH_KEY = (
        NODE_DIAGRAM
        + """
    <p>Solid arrows point from a derived type to the parent type which it
    extends. Dashed arrows point from a derived type to the other
    types it contains as a components, with a label listing the name(s) of
    said component(s).{{}}
    </p>
    """
    ).format(type_svg)

    CALL_GRAPH_KEY = (
        NODE_DIAGRAM
        + """
    <p>Solid arrows point from a procedure to one which it calls. Dashed 
    arrows point from an interface to procedures which implement that interface.
    This could include the module procedures in a generic interface or the
    implementation in a submodule of an interface in a parent module.{{}}
    </p>
    """  # noqa W291
    ).format(call_svg)

    FILE_GRAPH_KEY = (
        NODE_DIAGRAM
        + """
    <p>Solid arrows point from a file to a file which it depends on. A file
    is dependent upon another if the latter must be compiled before the former
    can be.{{}}
    </p>
    """
    ).format(file_svg)

    COLOURED_NOTICE = (
        " Where possible, edges connecting nodes are given "
        "different colours to make them easier to distinguish "
        "in large graphs."
    )

    del call_svg
    del file_svg
    del type_svg
    del mod_svg
    del dot
    del sub
    del func
    del intr
