#!/usr/bin/env python
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

from __future__ import print_function
import os

from ford.sourceform import FortranFunction, FortranSubroutine, FortranInterface, FortranProgram, FortranType, FortranModule, FortranSubmodule, FortranSubmoduleProcedure
import ford.graphs

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
    
    def __init__(self,base_url,outdir,graphdir,coloured_edges):
        self.graph_objs = []
        self.modules = set()
        self.programs = set()
        self.procedures = set()
        self.types = set()
        self.graphdir = graphdir
        self.webdir = base_url + '/' + graphdir
        self.usegraph = None
        self.typegraph = None
        self.callgraph = None
        ford.graphs.set_coloured_edges(coloured_edges)

    def register(self,obj):
        if obj.meta['graph'] == 'true':
            ford.graphs.FortranGraph.data.register(obj,type(obj))
            self.graph_objs.append(obj)
        
    def graph_all(self):
        for obj in self.graph_objs:
            if isinstance(obj,FortranModule):
                obj.usesgraph = ford.graphs.UsesGraph(obj,self.webdir)
                obj.usedbygraph = ford.graphs.UsedByGraph(obj,self.webdir)
                self.modules.add(obj)
            elif isinstance(obj,FortranType):
                obj.inhergraph = ford.graphs.InheritsGraph(obj,self.webdir)
                obj.inherbygraph = ford.graphs.InheritedByGraph(obj,self.webdir)
                self.types.add(obj)
            elif isinstance(obj,(FortranFunction,FortranSubroutine,FortranInterface,FortranSubmoduleProcedure)):
                obj.callsgraph = ford.graphs.CallsGraph(obj,self.webdir)
                obj.calledbygraph = ford.graphs.CalledByGraph(obj,self.webdir)
                self.procedures.add(obj)
            elif isinstance(obj,FortranProgram):
                obj.usesgraph = ford.graphs.UsesGraph(obj,self.webdir)
                obj.callsgraph = ford.graphs.CallsGraph(obj,self.webdir)
                self.programs.add(obj)
        usenodes = list(self.modules)
        callnodes = list(self.procedures)
        for p in self.programs:
            if p.usesgraph.numnodes > 1: usenodes.append(p)
            if p.callsgraph.numnodes > 1: callnodes.append(p)
        self.usegraph = ford.graphs.ModuleGraph(usenodes,self.webdir,'module~~graph')
        self.typegraph = ford.graphs.TypeGraph(self.types,self.webdir,'type~~graph')
        self.callgraph = ford.graphs.CallGraph(callnodes,self.webdir,'call~~graph')

    def output_graphs(self):
        if not self.graphdir: return
        try:
            os.mkdir(self.graphdir, 0o755)
        except OSError:
            pass
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
        if self.usegraph:
            self.usegraph.create_svg(self.graphdir)
        if self.typegraph:
            self.typegraph.create_svg(self.graphdir)
        if self.callgraph:
            self.callgraph.create_svg(self.graphdir)

