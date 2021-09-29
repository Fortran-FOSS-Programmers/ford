# -*- coding: utf-8 -*-
#
#  graphmanager.py
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
import pathlib
import sys
from multiprocessing import Pool

from tqdm import tqdm

from ford.sourceform import (
    FortranFunction,
    FortranSubroutine,
    FortranInterface,
    FortranProgram,
    FortranType,
    FortranModule,
    FortranSubmoduleProcedure,
    FortranSourceFile,
    FortranBlockData,
)
import ford.graphs


def outputFuncWrap(args):
    """Wrapper function for output graphs -- needed to allow multiprocessing to
    pickle the function (must be at top level)"""

    for f in args[0:-1]:
        f.create_svg(args[-1])

    return None


class GraphManager(object):
    """
    Object which contains graphs of module use relations, type relations,
    call trees, etc. It manages these, ensures that everything that is
    needed is added at the correct time, and produces the plots for the
    list pages.

      base_url
        The URL at which the documentation will be stored. If using
        relative URLs then should be '..'.
      outdir
        The directory in which the documentation will be produced.
      graphdir:
        The location of the graphs within the output tree.
    """

    def __init__(
        self,
        base_url: os.PathLike,
        outdir: os.PathLike,
        graphdir: os.PathLike,
        parentdir: os.PathLike,
        coloured_edges: bool,
    ):
        self.graph_objs = []
        self.modules = set()
        self.programs = set()
        self.procedures = set()
        self.types = set()
        self.sourcefiles = set()
        self.blockdata = set()
        self.graphdir = graphdir or ""
        self.webdir = pathlib.Path(base_url) / self.graphdir
        self.usegraph = None
        self.typegraph = None
        self.callgraph = None
        self.filegraph = None
        ford.graphs.set_coloured_edges(coloured_edges)
        ford.graphs.set_graphs_parentdir(parentdir)

    def register(self, obj):
        if obj.meta["graph"]:
            ford.graphs.FortranGraph.data.register(obj, type(obj))
            self.graph_objs.append(obj)

    def graph_all(self):
        for obj in tqdm(
            iter(self.graph_objs), file=sys.stdout, total=len(self.graph_objs), unit=""
        ):
            if isinstance(obj, FortranModule):
                obj.usesgraph = ford.graphs.UsesGraph(obj, self.webdir)
                obj.usedbygraph = ford.graphs.UsedByGraph(obj, self.webdir)
                self.modules.add(obj)
            elif isinstance(obj, FortranType):
                obj.inhergraph = ford.graphs.InheritsGraph(obj, self.webdir)
                obj.inherbygraph = ford.graphs.InheritedByGraph(obj, self.webdir)
                self.types.add(obj)
            elif isinstance(
                obj,
                (
                    FortranFunction,
                    FortranSubroutine,
                    FortranInterface,
                    FortranSubmoduleProcedure,
                ),
            ):
                obj.callsgraph = ford.graphs.CallsGraph(obj, self.webdir)
                obj.calledbygraph = ford.graphs.CalledByGraph(obj, self.webdir)
                obj.usesgraph = ford.graphs.UsesGraph(obj, self.webdir)
                self.procedures.add(obj)
            elif isinstance(obj, FortranProgram):
                obj.usesgraph = ford.graphs.UsesGraph(obj, self.webdir)
                obj.callsgraph = ford.graphs.CallsGraph(obj, self.webdir)
                self.programs.add(obj)
            elif isinstance(obj, FortranSourceFile):
                obj.afferentgraph = ford.graphs.AfferentGraph(obj, self.webdir)
                obj.efferentgraph = ford.graphs.EfferentGraph(obj, self.webdir)
                self.sourcefiles.add(obj)
            elif isinstance(obj, FortranBlockData):
                obj.usesgraph = ford.graphs.UsesGraph(obj, self.webdir)
                self.blockdata.add(obj)
        usenodes = list(self.modules)
        callnodes = list(self.procedures)
        for p in self.programs:
            if len(p.usesgraph.added) > 1:
                usenodes.append(p)
            if len(p.callsgraph.added) > 1:
                callnodes.append(p)
        for p in self.procedures:
            if len(p.usesgraph.added) > 1:
                usenodes.append(p)
        for b in self.blockdata:
            if len(b.usesgraph.added) > 1:
                usenodes.append(b)
        self.usegraph = ford.graphs.ModuleGraph(usenodes, self.webdir, "module~~graph")
        self.typegraph = ford.graphs.TypeGraph(self.types, self.webdir, "type~~graph")
        self.callgraph = ford.graphs.CallGraph(callnodes, self.webdir, "call~~graph")
        self.filegraph = ford.graphs.FileGraph(
            self.sourcefiles, self.webdir, "file~~graph"
        )

    def output_graphs(self, njobs=0):
        if not self.graphdir:
            return
        try:
            os.mkdir(self.graphdir, 0o755)
        except OSError:
            pass
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
            # args.extend([(m.usesgraph, self.graphdir) for m in self.modules])
            # args.extend([(m.usedbygraph, self.graphdir) for m in self.modules])
            # args.extend([(m.inhergraph, self.graphdir) for m in self.types])
            # args.extend([(m.inherbygraph, self.graphdir) for m in self.types])
            # args.extend([(m.callsgraph, self.graphdir) for m in self.procedures])
            # args.extend([(m.calledbygraph, self.graphdir) for m in self.procedures])
            # args.extend([(m.callsgraph, self.graphdir) for m in self.programs])
            # args.extend([(m.usesgraph, self.graphdir) for m in self.programs])
            # args.extend([(m.afferentgraph, self.graphdir) for m in self.sourcefiles])
            # args.extend([(m.efferentgraph, self.graphdir) for m in self.sourcefiles])
            # args.extend([(m.usesgraph, self.graphdir) for m in self.blockdata])

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

            np = min(njobs, len(args))
            pool = Pool(processes=np)
            results = pool.map(outputFuncWrap, args, len(args) / np)  # noqa F841
            pool.close()
            pool.join()

        if self.usegraph:
            self.usegraph.create_svg(self.graphdir)
        if self.typegraph:
            self.typegraph.create_svg(self.graphdir)
        if self.callgraph:
            self.callgraph.create_svg(self.graphdir)
        if self.filegraph:
            self.filegraph.create_svg(self.graphdir)
