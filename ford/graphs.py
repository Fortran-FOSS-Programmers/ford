#!/usr/bin/env python
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

from __future__ import print_function
import sys
import os
import shutil
import re
import copy
#Python 2 or 3:
if (sys.version_info[0]>2):
    from urllib.parse import quote
else:
    from urllib import quote
import colorsys

from graphviz import Digraph

from ford.sourceform import FortranFunction, FortranSubroutine, FortranInterface, FortranProgram, FortranType, FortranModule, FortranSubmodule, FortranSubmoduleProcedure, FortranSourceFile, FortranBlockData

_coloured_edges = False
def set_coloured_edges(val):
    '''
    Public accessor to set whether to use coloured edges in graph or just 
    use black ones.
    '''
    global _coloured_edges
    _coloured_edges = val

def rainbowcolour(depth, maxd):
    if _coloured_edges:
        (r, g, b) = colorsys.hsv_to_rgb(float(depth) / maxd, 1.0, 1.0)
        R, G, B = int(255 * r), int(255 * g), int(255 * b)
        return R, G, B
    else:
        return 0, 0, 0

HYPERLINK_RE = re.compile("^\s*<\s*a\s+.*href=(\"[^\"]+\"|'[^']+').*>(.*)</\s*a\s*>\s*$",re.IGNORECASE)
WIDTH_RE = re.compile('width="(.*?)pt"',re.IGNORECASE)
HEIGHT_RE = re.compile('height="(.*?)pt"',re.IGNORECASE)
EM_RE = re.compile('<em>(.*)</em>',re.IGNORECASE)

graphviz_installed = True

def newdict(old,key,val):
    new = copy.copy(old)
    new[key] = val
    return new

def is_module(obj,cls):
    return isinstance(obj,FortranModule) or issubclass(cls,FortranModule)

def is_submodule(obj,cls):
    return isinstance(obj,FortranSubmodule) or issubclass(cls,FortranSubmodule)
    
def is_type(obj,cls):
    return isinstance(obj,FortranType) or issubclass(cls,FortranType)

def is_proc(obj,cls):
    return (isinstance(obj,(FortranFunction,FortranSubroutine,
                            FortranInterface,FortranSubmoduleProcedure))
         or issubclass(cls,(FortranFunction,FortranSubroutine,
                               FortranInterface,FortranSubmoduleProcedure)))

def is_program(obj, cls):
    return isinstance(obj,FortranProgram) or issubclass(cls,FortranProgram)

def is_sourcefile(obj, cls):
    return isinstance(obj,FortranSourceFile) or issubclass(cls,FortranSourceFile)
    
def is_blockdata(obj, cls):
    return isinstance(obj,FortranBlockData) or issubclass(cls,FortranBlockData)

    
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

    def register(self,obj,cls=type(None),hist={}):
        """
        Takes a FortranObject and adds it to the appropriate list, if
        not already present.
        """
        #~ ident = getattr(obj,'ident',obj)
        if is_submodule(obj,cls):
            if obj not in self.submodules: self.submodules[obj] = SubmodNode(obj,self)
        elif is_module(obj,cls):
            if obj not in self.modules: self.modules[obj] = ModNode(obj,self)
        elif is_type(obj,cls):
            if obj not in self.types: self.types[obj] = TypeNode(obj,self)
        elif is_proc(obj,cls):
            if obj not in self.procedures: self.procedures[obj] = ProcNode(obj,self,hist)
        elif is_program(obj,cls):
            if obj not in self.programs: self.programs[obj] = ProgNode(obj,self)
        elif is_sourcefile(obj,cls):
            if obj not in self.sourcefiles: self.sourcefiles[obj] = FileNode(obj,self)
        elif is_blockdata(obj,cls):
            if obj not in self.blockdata: self.blockdata[obj] = BlockNode(obj,self)
        else:
            raise BadType("Object type {} not recognized by GraphData".format(type(obj).__name__))
    
    def get_node(self,obj,cls=type(None),hist={}):
        """
        Returns the node corresponding to obj. If does not already exist
        then it will create it.
        """
        #~ ident = getattr(obj,'ident',obj)
        if obj in self.modules and is_module(obj,cls):
            return self.modules[obj]
        elif obj in self.submodules and is_submodule(obj,cls):
            return self.submodules[obj]
        elif obj in self.types and is_type(obj,cls):
            return self.types[obj]
        elif obj in self.procedures and is_proc(obj,cls):
            return self.procedures[obj]
        elif obj in self.programs and is_program(obj,cls):
            return self.programs[obj]
        elif obj in self.sourcefiles and is_sourcefile(obj,cls):
            return self.sourcefiles[obj]
        elif obj in self.blockdata and is_blockdata(obj,cls):
            return self.blockdata[obj]
        else:
            self.register(obj,cls,hist)
            return self.get_node(obj,cls,hist)


class BaseNode(object):
    colour = '#777777'
    def __init__(self,obj):
        self.attribs = {'color':self.colour,
                        'fontcolor':'white',
                        'style':'filled'}
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
            if not d: d = 'none'
            self.ident = d + '~' + obj.ident
            self.name = obj.name
            m = EM_RE.search(self.name)
            if m: self.name = '<<i>'+m.group(1).strip()+'</i>>'
            self.url = obj.get_url()
        self.attribs['label'] = self.name
        if self.url and getattr(obj,'visible',True): self.attribs['URL'] = self.url
        self.afferent = 0
        self.efferent = 0


class ModNode(BaseNode):
    colour = '#337AB7'
    def __init__(self,obj,gd):
        super(ModNode,self).__init__(obj)
        self.uses = set()
        self.used_by = set()
        self.children = set()
        if not self.fromstr:
            for u in obj.uses:
                n = gd.get_node(u,FortranModule)
                n.used_by.add(self)
                n.afferent += 1
                self.uses.add(n)
                self.efferent += n.efferent


class SubmodNode(ModNode):
    colour = '#5bc0de'
    def __init__(self,obj,gd):
        super(SubmodNode,self).__init__(obj,gd)
        del self.used_by
        if not self.fromstr:
            if obj.ancestor:
                self.ancestor = gd.get_node(obj.ancestor,FortranSubmodule)
            else:
                self.ancestor = gd.get_node(obj.ancestor_mod,FortranModule)
            self.ancestor.children.add(self)
            self.efferent += 1
            self.ancestor.afferent += 1


class TypeNode(BaseNode):
    colour = '#5cb85c'
    def __init__(self,obj,gd):
        super(TypeNode,self).__init__(obj)
        self.ancestor = None
        self.children = set()
        self.comp_types = dict()
        self.comp_of = dict()
        if not self.fromstr:
            if obj.extends:
                self.ancestor = gd.get_node(obj.extends,FortranType)
                self.ancestor.children.add(self)
                self.ancestor.visible = getattr(obj.extends,'visible',True)
            for var in obj.variables:
                if (var.vartype == 'type' or var.vartype == 'class') and var.proto[0] != '*':
                    if var.proto[0] == obj:
                        n = self
                    else:
                        n = gd.get_node(var.proto[0],FortranType)
                    n.visible = getattr(var.proto[0],'visible',True)
                    if self in n.comp_of:
                        n.comp_of[self] += ', ' + var.name
                    else:
                        n.comp_of[self] = var.name
                    if n in self.comp_types:
                        self.comp_types[n] += ', ' + var.name
                    else:
                        self.comp_types[n] = var.name


class ProcNode(BaseNode):
    @property
    def colour(self):
        if self.proctype.lower() == 'subroutine':
            return '#d9534f'
        elif self.proctype.lower() == 'function':
            return '#d94e8f'
        elif self.proctype.lower() == 'interface':
            return '#A7506F'
            #~ return '#c77c25'
        else:
            return super(ProcNode,self).colour
    
    def __init__(self,obj,gd,hist={}):
        #ToDo: Figure out appropriate way to handle interfaces to routines in submodules.
        self.proctype = getattr(obj,'proctype','')
        super(ProcNode,self).__init__(obj)
        self.uses = set()
        self.calls = set()
        self.called_by = set()
        self.interfaces = set()
        self.interfaced_by = set()
        if not self.fromstr:
            for u in getattr(obj,'uses',[]):
                n = gd.get_node(u,FortranModule)
                n.used_by.add(self)
                self.uses.add(n)
            for c in getattr(obj,'calls',[]):
                if getattr(c,'visible',True):
                    if c == obj:
                        n = self
                    elif c in hist:
                        n = hist[c]
                    else:
                        n = gd.get_node(c,FortranSubroutine,newdict(hist,obj,self))
                    n.called_by.add(self)
                    self.calls.add(n)
            if obj.proctype.lower() == 'interface':
                for m in getattr(obj,'modprocs',[]):
                    if m.procedure and getattr(m.procedure,'visible',True):
                        if m.procedure in hist:
                            n = hist[m.procedure]
                        else:
                            n = gd.get_node(m.procedure,FortranSubroutine,newdict(hist,obj,self))
                        n.interfaced_by.add(self)
                        self.interfaces.add(n)
                if hasattr(obj,'procedure') and obj.procedure.module and obj.procedure.module != True and getattr(obj.procedure.module,'visible',True):
                    if obj.procedure.module in hist:
                        n = hist[obj.procedure.module]
                    else:
                        n = gd.get_node(obj.procedure.module,FortranSubroutine,newdict(hist,obj,self))
                    n.interfaced_by.add(self)
                    self.interfaces.add(n)


class ProgNode(BaseNode):
    colour = '#f0ad4e'
    def __init__(self,obj,gd):
        super(ProgNode,self).__init__(obj)
        self.uses = set()
        self.calls = set()
        if not self.fromstr:
            for u in obj.uses:
                n = gd.get_node(u,FortranModule)
                n.used_by.add(self)
                self.uses.add(n)
            for c in obj.calls:
                if getattr(c,'visible',True):
                    n = gd.get_node(c,FortranSubroutine)
                    n.called_by.add(self)
                    self.calls.add(n)


class BlockNode(BaseNode):
    colour = '#5cb85c'
    def __init__(self,obj,gd):
        super(BlockNode,self).__init__(obj)
        self.uses = set()
        if not self.fromstr:
            for u in obj.uses:
                n = gd.get_node(u,FortranModule)
                n.used_by.add(self)
                self.uses.add(n)


class FileNode(BaseNode):
    colour = '#f0ad4e'
    def __init__(self,obj,gd,hist={}):
        super(FileNode,self).__init__(obj)
        self.afferent = set() # Things depending on this file
        self.efferent = set() # Things this file depends on
        if not self.fromstr:
            for mod in obj.modules:
                for dep in mod.deplist:
                    if dep.hierarchy[0] == obj:
                        continue
                    elif dep.hierarchy[0] in hist:
                        n = hist[dep.hierarchy[0]]
                    else:
                        n = gd.get_node(dep.hierarchy[0],FortranSourceFile,newdict(hist,obj,self))
                    n.afferent.add(self)
                    self.efferent.add(n)
            for mod in obj.submodules:
                for dep in mod.deplist:
                    if dep.hierarchy[0] == obj:
                        continue
                    elif dep.hierarchy[0] in hist:
                        n = hist[dep.hierarchy[0]]
                    else:
                        n = gd.get_node(dep.hierarchy[0],FortranSourceFile,newdict(hist,obj,self))
                    n.afferent.add(self)
                    self.efferent.add(n)
            for proc in obj.functions + obj.subroutines:
                for dep in proc.deplist:
                    if dep.hierarchy[0] == obj:
                        continue
                    elif dep.hierarchy[0] in hist:
                        n = hist[dep.hierarchy[0]]
                    else:
                        n = gd.get_node(dep.hierarchy[0],FortranSourceFile,newdict(hist,obj,self))
                    n.afferent.add(self)
                    self.efferent.add(n)
            for prog in obj.programs:
                for dep in prog.deplist:
                    if dep.hierarchy[0] == obj:
                        continue
                    elif dep.hierarchy[0] in hist:
                        n = hist[dep.hierarchy[0]]
                    else:
                        n = gd.get_node(dep.hierarchy[0],FortranSourceFile,newdict(hist,obj,self))
                    n.afferent.add(self)
                    self.efferent.add(n)
            for block in obj.blockdata:
                for dep in block.deplist:
                    if dep.hierarchy[0] == obj:
                        continue
                    elif dep.hierarchy[0] in hist:
                        n = hist[dep.hierarchy[0]]
                    else:
                        n = gd.get_node(dep.hierarchy[0],FortranSourceFile,newdict(hist,obj,self))
                    n.afferent.add(self)
                    self.efferent.add(n)


class FortranGraph(object):
    """
    Object used to construct the graph for some particular entity in the code.
    """
    data = GraphData()
    def __init__(self,root,webdir='',ident=None):
        """
        root is the object for which the graph is being constructed
        """
        self.numnodes = 0
        self.added = []
        self.root = []
        try:
            for r in root:
                self.root.append(self.data.get_node(r))
        except:
            self.root.append(self.data.get_node(root))
        self.webdir = webdir
        if ident:
            self.ident = ident + '~~' + self.__class__.__name__
        else:
            self.ident = root.get_dir() + '~~' + root.ident + '~~' + self.__class__.__name__
        self.imgfile = self.ident
        self.dot = Digraph(self.ident,
                           graph_attr={'size':'8.90625,1000.0',
                                       'rankdir':'LR',
                                       'concentrate':'true',
                                       'id':self.ident},
                           node_attr={'shape':'box',
                                      'height':'0.0',
                                      'margin':'0.08',
                                      'fontname':'Helvetica',
                                      'fontsize':'10.5'},
                           edge_attr={'fontname':'Helvetica',
                                      'fontsize':'9.5'},
                           format='svg', engine='dot')
        self.add_node(self.root,(len(self.root) == 1))
        #~ self.linkmap = self.dot.pipe('cmapx').decode('utf-8')
        if graphviz_installed:
            self.svg_src = self.dot.pipe().decode('utf-8')
            self.svg_src = self.svg_src.replace('<svg ','<svg id="' + re.sub('[^\w]','',self.ident) + '" ')
            w = int(WIDTH_RE.search(self.svg_src).group(1))
            if isinstance(self,(ModuleGraph,CallGraph,TypeGraph)):
                self.scaled = (w >= 855)
            else:
                self.scaled = (w >= 641)
        else:
            self.svg_src = ''
            self.scaled = False


    def add_node(self,nodes,root=False):
        """
        Adds nodes to the graph. nodes is a list of node-type objects, 
        and root is a boolean indicating whether this is the root of the
        graph.
        """    
        recurse = []
        if root:
            for n in nodes:
                if n.ident not in self.added:
                    self.dot.node(n.ident,label=n.name)
                    self.numnodes += 1
                    self.added.append(n.ident)
                    recurse.append(n)
        else:
            for n in nodes:
                if n.ident not in self.added:
                    self.dot.node(n.ident,**n.attribs)
                    self.numnodes += 1
                    self.added.append(n.ident)
                    recurse.append(n)
        self.add_more_nodes(recurse)

    def __str__(self):
        if self.numnodes <= 1 or not graphviz_installed: return ''
        if self.scaled:
            rettext = """
                <div class="depgraph">{0}</div>
                <script>var pan{1} = svgPanZoom('#{1}', {{
                    zoomEnabled: true,
                    controlIconsEnabled: true,
                    fit: true,
                    center: true,}});
                    </script>
                <div><a type="button" class="graph-help" data-toggle="modal" href="#graph-help-text">Help</a></div>
                <div class="modal fade" id="graph-help-text" tabindex="-1" role="dialog">
                  <div class="modal-dialog modal-lg" role="document">
                    <div class="modal-content">
                      <div class="modal-header">
                        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                        <h4 class="modal-title" id="-graph-help-label">Graph Key</h4>
                      </div>
                      <div class="modal-body">
                        {2}
                      </div>
                    </div>
                  </div>
                </div>
                """
        else:
            rettext = """
                <div class="depgraph">{0}</div>
                <div><a type="button" class="graph-help" data-toggle="modal" href="#graph-help-text">Help</a></div>
                <div class="modal fade" id="graph-help-text" tabindex="-1" role="dialog">
                  <div class="modal-dialog modal-lg" role="document">
                    <div class="modal-content">
                      <div class="modal-header">
                        <button type="button" class="close" data-dismiss="modal" aria-label="Close"><span aria-hidden="true">&times;</span></button>
                        <h4 class="modal-title" id="-graph-help-label">Graph Key</h4>
                      </div>
                      <div class="modal-body">
                        {2}
                      </div>
                    </div>
                  </div>
                </div>
                """
        wdir = self.webdir.strip()
        if wdir[-1] == '/': wdir = wdir[0:-1]
        link = quote(wdir + '/' + self.imgfile + '.' + self.dot.format)
        return rettext.format(self.svg_src,re.sub('[^\w]','',self.ident),self.get_key())
    
    def __nonzero__(self):
        return self.__bool__()
    
    def __bool__(self):
        return(bool(self.__str__()))
    
    @classmethod
    def reset(cls):
        cls.data = GraphData()
    
    def create_svg(self, out_location):
        if self.numnodes > 1:
            self._create_image_file(os.path.join(out_location, self.imgfile))
    
    def _create_image_file(self,filename):
        if graphviz_installed:
            self.dot.render(filename,cleanup=False)
            shutil.move(filename,os.path.join(os.path.dirname(filename),
                        os.path.basename(filename)+'.gv'))


class ModuleGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ''
        return MOD_GRAPH_KEY.format(colour_notice)
    
    def add_more_nodes(self,nodes):
        """
        Adds edges showing the relationship between modules and submodules
        listed in nodes.
        """
        self.dot.attr('graph',size='11.875,1000.0')
        for i,n in zip(range(len(nodes)),nodes):
            r,g,b = rainbowcolour(i,len(nodes))
            colour = '#%02X%02X%02X' % (r,g,b)
            for nu in n.uses:
                if nu not in nodes and nu.ident not in self.added:
                    self.dot.node(nu.ident,**nu.attribs)
                    self.numnodes += 1
                    self.added.append(nu.ident)
                self.dot.edge(nu.ident,n.ident,style='dashed',color=colour)
            if hasattr(n,'ancestor'):
                if n.ancestor not in nodes and n.ancestor.ident not in self.added:
                    self.dot.node(n.ancestor.ident,**n.ancestor.attribs)
                    self.numnodes += 1
                    self.added.append(n.ancestor.ident)
                self.dot.edge(n.ancestor.ident,n.ident,color=colour)


class UsesGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ''
        return MOD_GRAPH_KEY.format(colour_notice)
    
    def add_more_nodes(self,nodes):
        """
        Adds nodes for the modules used by those listed in nodes. Adds
        edges between them. Also does this for ancestor (sub)modules.
        """
        for i,n in zip(range(len(nodes)),nodes):
            r,g,b = rainbowcolour(i,len(nodes))
            colour = '#%02X%02X%02X' % (r,g,b)
            self.add_node([x for x in n.uses if x.ident not in self.added])
            for nu in n.uses:
                self.dot.edge(nu.ident,n.ident,style='dashed',color=colour)
            if hasattr(n,'ancestor'):
                if n.ancestor.ident not in self.added: self.add_node([n.ancestor])
                self.dot.edge(n.ancestor.ident,n.ident,color=colour)
        

class UsedByGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ''
        return MOD_GRAPH_KEY.format(colour_notice)
    
    def add_more_nodes(self,nodes):
        """
        Adds nodes for modules using or descended from those listed in
        nodes. Adds appropriate edges between them.
        """
        for i,n in zip(range(len(nodes)),nodes):
            r,g,b = rainbowcolour(i,len(nodes))
            colour = '#%02X%02X%02X' % (r,g,b)
            self.add_node([x for x in getattr(n,'used_by',[]) if x.ident not in self.added])
            for nu in getattr(n,'used_by',[]):
                self.dot.edge(n.ident,nu.ident,style='dashed',color=colour)
            self.add_node([x for x in getattr(n,'children',[]) if x.ident not in self.added])
            for c in getattr(n,'children',[]):
                self.dot.edge(n.ident,c.ident,color=colour)


class FileGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ''
        return FILE_GRAPH_KEY.format(colour_notice)
    
    def add_more_nodes(self,nodes):
        """
        Adds edges showing dependencies between source files listed in
        the nodes.
        """
        for i,n in zip(range(len(nodes)),nodes):
            r,g,b = rainbowcolour(i,len(nodes))
            colour = '#%02X%02X%02X' % (r,g,b)
            self.add_node([x for x in n.efferent if x.ident not in self.added])
            for ne in n.efferent:
                self.dot.edge(ne.ident,n.ident,color=colour)


class EfferentGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ''
        return FILE_GRAPH_KEY.format(colour_notice)
    
    def add_more_nodes(self,nodes):
        """
        Adds nodes for the files which this one depends on. Adds
        edges between them.
        """
        for i,n in zip(range(len(nodes)),nodes):
            r,g,b = rainbowcolour(i,len(nodes))
            colour = '#%02X%02X%02X' % (r,g,b)
            self.add_node([x for x in n.efferent if x.ident not in self.added])
            for ne in n.efferent:
                self.dot.edge(ne.ident,n.ident,style='dashed',color=colour)


class AfferentGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ''
        return FILE_GRAPH_KEY.format(colour_notice)
    
    def add_more_nodes(self,nodes):
        """
        Adds nodes for files which depend upon this one. Adds appropriate
        edges between them.
        """
        for i,n in zip(range(len(nodes)),nodes):
            r,g,b = rainbowcolour(i,len(nodes))
            colour = '#%02X%02X%02X' % (r,g,b)
            self.add_node([x for x in n.afferent if x.ident not in self.added])
            for na in n.afferent:
                self.dot.edge(n.ident,na.ident,style='dashed',color=colour)


class TypeGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ''
        return TYPE_GRAPH_KEY.format(colour_notice)
    
    def add_more_nodes(self,nodes):
        """
        Adds edges showing inheritance and composition relationships 
        between derived types listed in the nodes.
        """
        self.dot.attr('graph',size='11.875,1000.0')
        for i,n in zip(range(len(nodes)),nodes):
            r,g,b = rainbowcolour(i,len(nodes))
            colour = '#%02X%02X%02X' % (r,g,b)
            self.add_node([x for x in n.comp_types.keys() if x.ident not in self.added])
            for c in n.comp_types:
                if c not in nodes and c.ident not in self.added:
                    self.dot.node(c.ident,**c.attribs)
                    self.numnodes += 1
                    self.added.append(c.ident)
                self.dot.edge(c.ident,n.ident,style='dashed',label=n.comp_types[c],color=colour)
            if n.ancestor:
                if n.ancestor not in nodes and n.ancestor.ident not in self.added:
                    self.add_node([n.ancestor])
                    self.dot.node(n.ancestor.ident,**n.ancestor.attribs)
                    self.numnodes += 1
                    self.added.append(n.ancestor.ident)
                self.dot.edge(n.ancestor.ident,n.ident,color=colour)


class InheritsGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ''
        return TYPE_GRAPH_KEY.format(colour_notice)
    
    def add_more_nodes(self,nodes):
        """
        Adds nodes for modules using or descended from those listed in
        nodes. Adds appropriate edges between them.
        """
        for i,n in zip(range(len(nodes)),nodes):
            r,g,b = rainbowcolour(i,len(nodes))
            colour = '#%02X%02X%02X' % (r,g,b)
            self.add_node([x for x in n.comp_types.keys() if x.ident not in self.added])
            for c in n.comp_types:
                self.dot.edge(c.ident,n.ident,style='dashed',label=n.comp_types[c],color=colour)
            if n.ancestor:
                if n.ancestor.ident not in self.added: self.add_node([n.ancestor])
                self.dot.edge(n.ancestor.ident,n.ident,color=colour)


class InheritedByGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ''
        return TYPE_GRAPH_KEY.format(colour_notice)
    
    def add_more_nodes(self,nodes):
        """
        Adds nodes for modules using or descended from those listed in
        nodes. Adds appropriate edges between them.
        """
        for i,n in zip(range(len(nodes)),nodes):
            r,g,b = rainbowcolour(i,len(nodes))
            colour = '#%02X%02X%02X' % (r,g,b)
            self.add_node([x for x in n.comp_of.keys() if x.ident not in self.added])
            for c in n.comp_of:
                self.dot.edge(n.ident,c.ident,style='dashed',label=n.comp_of[c],color=colour)
            self.add_node([x for x in n.children if x.ident not in self.added])
            for c in n.children:
                self.dot.edge(n.ident,c.ident,color=colour)


class CallGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ''
        return CALL_GRAPH_KEY.format(colour_notice)
    
    def add_more_nodes(self,nodes):
        """
        Adds edges indicating the call-tree for the procedures listed in
        the nodes.
        """
        self.dot.attr('graph',size='11.875,1000.0')
        self.dot.attr('graph',concentrate='false')
        for i,n in zip(range(len(nodes)),nodes):
            r,g,b = rainbowcolour(i,len(nodes))
            colour = '#%02X%02X%02X' % (r,g,b)
            for p in n.calls:
                if p not in nodes and p.ident not in self.added:
                    self.dot.node(p.ident,**p.attribs)
                    self.numnodes += 1
                    self.added.append(p.ident)
                self.dot.edge(n.ident,p.ident,color=colour)
            for p in getattr(n,'interfaces',[]):
                if p not in nodes and p.ident not in self.added:
                    self.dot.node(p.ident,**p.attribs)
                    self.numnodes += 1
                    self.added.append(p.ident)
                self.dot.edge(n.ident,p.ident,style='dashed',color=colour)
                

class CallsGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ''
        return CALL_GRAPH_KEY.format(colour_notice)
    
    def add_more_nodes(self,nodes):
        """
        Adds nodes for modules using or descended from those listed in
        nodes. Adds appropriate edges between them.
        """
        self.dot.attr('graph',concentrate='false')
        for i,n in zip(range(len(nodes)),nodes):
            r,g,b = rainbowcolour(i,len(nodes))
            colour = '#%02X%02X%02X' % (r,g,b)
            self.add_node([x for x in n.calls if x.ident not in self.added])
            for p in n.calls:
                self.dot.edge(n.ident,p.ident,color=colour)
            self.add_node([x for x in getattr(n,'interfaces',[]) if x.ident not in self.added])
            for p in getattr(n,'interfaces',[]):
                self.dot.edge(n.ident,p.ident,style='dashed',color=colour)


class CalledByGraph(FortranGraph):
    def get_key(self):
        colour_notice = COLOURED_NOTICE if _coloured_edges else ''
        return CALL_GRAPH_KEY.format(colour_notice)
    
    def add_more_nodes(self,nodes):
        """
        Adds nodes for modules using or descended from those listed in
        nodes. Adds appropriate edges between them.
        """
        self.dot.attr('graph',concentrate='false')
        for i,n in zip(range(len(nodes)),nodes):
            r,g,b = rainbowcolour(i,len(nodes))
            colour = '#%02X%02X%02X' % (r,g,b)
            if isinstance(n,ProgNode): continue
            self.add_node([x for x in n.called_by if x.ident not in self.added])
            for p in n.called_by:
                self.dot.edge(p.ident,n.ident,color=colour)
            self.add_node([x for x in getattr(n,'interfaced_by',[]) if x.ident not in self.added])
            for p in getattr(n,'interfaced_by',[]):
                self.dot.edge(p.ident,n.ident,style='dashed',color=colour)


class BadType(Exception):
    """
    Raised when a type is passed to GraphData.register() which is not
    accepted.
    """
    def __init__(self,value):
        self.value = value
    def __str__(self):
        return repr(self.value)
    

# Generate graph keys
gd = GraphData()
class Proc(object):
    def __init__(self,name,proctype):
        self.name = name
        self.proctype = proctype
        self.ident = ''
    def get_url(self):
        return ''
    def get_dir(self):
        return ''
    
sub = Proc('Subroutine','Subroutine')
func = Proc('Function','Function')
intr = Proc('Interface','Interface')
gd.register('Module',FortranModule)
gd.register('Submodule',FortranSubmodule)
gd.register('Type',FortranType)
gd.register(sub,FortranSubroutine)
gd.register(func,FortranFunction)
gd.register(intr,FortranInterface)
gd.register('Unknown Procedure Type',FortranSubroutine)
gd.register('Program',FortranProgram)
gd.register('Source File',FortranSourceFile)

try:
    # Generate key for module graph
    dot = Digraph('Graph Key',graph_attr={'size':'8.90625,1000.0',
                                          'concentrate':'false'},
                              node_attr={'shape':'box',
                                         'height':'0.0',
                                         'margin':'0.08',
                                         'fontname':'Helvetica',
                                         'fontsize':'10.5'},
                              edge_attr={'fontname':'Helvetica',
                                         'fontsize':'9.5'},
                              format='svg', engine='dot')
    for n in [('Module',FortranModule),('Submodule',FortranSubmodule),(sub,FortranSubroutine),(func,FortranFunction),('Program', FortranProgram)]:
        dot.node(getattr(n[0],'name',n[0]),**gd.get_node(n[0],cls=n[1]).attribs)
    dot.node('This Page\'s Entity')
    mod_svg = dot.pipe().decode('utf-8')

    # Generate key for type graph
    dot = Digraph('Graph Key',graph_attr={'size':'8.90625,1000.0',
                                          'concentrate':'false'},
                              node_attr={'shape':'box',
                                         'height':'0.0',
                                         'margin':'0.08',
                                         'fontname':'Helvetica',
                                         'fontsize':'10.5'},
                              edge_attr={'fontname':'Helvetica',
                                         'fontsize':'9.5'},
                              format='svg', engine='dot')
    dot.node('Type',**gd.get_node('Type',cls=FortranType).attribs)
    dot.node('This Page\'s Entity')
    type_svg = dot.pipe().decode('utf-8')

    # Generate key for call graph
    dot = Digraph('Graph Key',graph_attr={'size':'8.90625,1000.0',
                                          'concentrate':'false'},
                              node_attr={'shape':'box',
                                         'height':'0.0',
                                         'margin':'0.08',
                                         'fontname':'Helvetica',
                                         'fontsize':'10.5'},
                              edge_attr={'fontname':'Helvetica',
                                         'fontsize':'9.5'},
                              format='svg', engine='dot')
    for n in [(sub,FortranSubroutine),(func,FortranFunction),(intr, FortranInterface),('Unknown Procedure Type',FortranFunction),('Program', FortranProgram)]:
        dot.node(getattr(n[0],'name',n[0]),**gd.get_node(n[0],cls=n[1]).attribs)
    dot.node('This Page\'s Entity')
    call_svg = dot.pipe().decode('utf-8')

    # Generate key for file graph
    dot = Digraph('Graph Key',graph_attr={'size':'8.90625,1000.0',
                                          'concentrate':'false'},
                              node_attr={'shape':'box',
                                         'height':'0.0',
                                         'margin':'0.08',
                                         'fontname':'Helvetica',
                                         'fontsize':'10.5'},
                              edge_attr={'fontname':'Helvetica',
                                         'fontsize':'9.5'},
                              format='svg', engine='dot')
    dot.node('Source File',**gd.get_node('Source File',cls=FortranSourceFile).attribs)
    dot.node('This Page\'s Entity')
    file_svg = dot.pipe().decode('utf-8')

except RuntimeError:
    print("Warning: Will not be able to generate graphs. Graphviz not installed.")
    graphviz_installed = False
    svg = None

NODE_DIAGRAM = """
<p>Nodes of different colours represent the following: </p>
{}
"""

MOD_GRAPH_KEY = (NODE_DIAGRAM + """
<p>Solid arrows point from a parent (sub)module to the submodule which is
descended from it. Dashed arrows point from a module being used to the
module or program unit using it.{{}}
</p>
""").format(mod_svg)

TYPE_GRAPH_KEY = (NODE_DIAGRAM + """
<p>Solid arrows point from one derived type to another which extends
(inherits from) it. Dashed arrows point from a derived type to another
type containing it as a components, with a label listing the name(s) of
said component(s).{{}}
</p>
""").format(type_svg)

CALL_GRAPH_KEY = (NODE_DIAGRAM + """
<p>Solid arrows point from a procedure to one which it calls. Dashed 
arrows point from an interface to procedures which implement that interface.
This could include the module procedures in a generic interface or the
implementation in a submodule of an interface in a parent module.{{}}
</p>
""").format(call_svg)

FILE_GRAPH_KEY = (NODE_DIAGRAM + """
<p>Solid arrows point from a file to a file which depends upon it. A file 
is dependent upon another if the latter must be compiled before the former
can be.{{}}
</p>
""").format(file_svg)

COLOURED_NOTICE = " Where possible, edges connecting nodes are given " \
                  "different colours to make them easier to distinguish " \
                  "in large graphs."

del call_svg
del file_svg
del type_svg
del mod_svg
del dot
del sub
del func
del intr
