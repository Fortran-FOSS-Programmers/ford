#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  project.py
#  This file is part of FORD.
#  
#  Copyright 2014 Christopher MacMackin <cmacmackin@gmail.com>
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
import toposort

import ford.sourceform

INTRINSIC_MODS = {'iso_fortran_env': '<a href="https://software.intel.com/en-us/node/511041">iso_fortran_env</a>',
                  'iso_c_binding': '<a href="https://software.intel.com/en-us/node/511038">iso_c_binding</a>',
                  'ieee_arithmetic': '<a href="https://software.intel.com/en-us/node/511043">ieee_arithmetic</a>',
                  'ieee_exceptions': '<a href="https://software.intel.com/en-us/node/511044">ieee_exceptions</a>',
                  'ieee_features': '<a href="https://software.intel.com/en-us/node/511045">ieee_features</a>',
                  'openacc': '<a href="http://www.openacc.org/sites/default/files/OpenACC.2.0a_1.pdf#page=49">openacc</a>',
                  'omp_lib': '<a href="https://gcc.gnu.org/onlinedocs/gcc-4.4.3/libgomp/Runtime-Library-Routines.html">omp_lib</a>',
                  'mpi': '<a href="http://www.mpi-forum.org/docs/mpi-3.1/mpi31-report/node410.htm">mpi</a>',
                  'mpi_f08': '<a href="http://www.mpi-forum.org/docs/mpi-3.1/mpi31-report/node409.htm">mpi_f08</a>',}

class Project(object):
    """
    An object which collects and contains all of the information about the
    project which is to be documented.
    """
    def __init__(self, settings):
        self.settings = settings        
        self.name = settings['project']
        self.topdirs = settings['project_dir']
        self.extensions = settings['extensions']
        self.extra_filetypes = settings['extra_filetypes']
        self.display = settings['display']

        if settings['preprocess'] == 'true':
            fpp_ext = [ext for ext in self.extensions 
                       if ext == ext.upper() and ext != ext.lower()]
        else:
            fpp_ext = []
        
        self.files = []
        self.modules = []
        self.programs = []
        self.procedures = []
        self.absinterfaces = []
        self.types = []
        self.submodules = []
        self.submodprocedures = []
        self.extra_files = []
                
        # Get all files within topdir, recursively
        srctree = []
        for topdir in self.topdirs:
            srctree = os.walk(os.path.relpath(topdir))
            for srcdir in srctree:
                excluded = False
                for ex in settings['exclude_dir']:
                    fragment = srcdir[0]
                    while fragment:
                        excluded = excluded or fragment.endswith(ex)
                        fragment = os.path.split(fragment)[0]
                if excluded: continue
                curdir = srcdir[0]
                for item in srcdir[2]:
                    if item.split('.')[-1] in self.extensions and not item in settings['exclude']:
                        # Get contents of the file
                        print("Reading file {}".format(os.path.relpath(os.path.join(curdir,item))))
                        if item.split('.')[-1] in fpp_ext:
                            preprocessor = settings['preprocessor']
                        else:
                            preprocessor = None
                        if settings['dbg']:
                            self.files.append(
                                ford.sourceform.FortranSourceFile(os.path.join(curdir,item),settings, preprocessor))
                        else:
                            try:
                                self.files.append(ford.sourceform.FortranSourceFile(os.path.join(curdir,item),settings,preprocessor))
                            except Exception as e:
                                print("Warning: Error parsing {}.\n\t{}".format(os.path.relpath(os.path.join(curdir,item)),e.args[0]))
                                continue
                        for module in self.files[-1].modules:
                            self.modules.append(module)
                        for submod in self.files[-1].submodules:
                            self.submodules.append(submod)
                        for function in self.files[-1].functions:
                            function.visible = True
                            self.procedures.append(function)
                        for subroutine in self.files[-1].subroutines:
                            subroutine.visible = True
                            self.procedures.append(subroutine)
                        for program in self.files[-1].programs:
                            program.visible = True
                            self.programs.append(program)
                    elif item.split('.')[-1] in self.extra_filetypes and not item in settings['exclude']:
                        print("Reading file {}".format(os.path.relpath(os.path.join(curdir,item))))
                        if settings['dbg']:
                            self.extra_files.append(ford.sourceform.GenericSource(os.path.join(curdir,item),settings))
                        else:
                            try:
                                self.extra_files.append(ford.sourceform.GenericSource(os.path.join(curdir,item),settings))
                            except Exception as e:
                                print("Warning: Error parsing {}.\n\t{}".format(os.path.relpath(os.path.join(curdir,item)),e.args[0]))
                                continue
        self.allfiles = self.files + self.extra_files                


    def __str__(self):
        return self.name
    
    def correlate(self):
        """
        Associates various constructs with each other.
        """

        print("Correlating information from different parts of your project...")
                        
        non_local_mods = INTRINSIC_MODS        
        for item in self.settings['extra_mods']:
            i = item.index(':')
            if i < 0:
                print('Warning: could not parse extra modules ""'.format(item))
                continue
            name = item[:i].strip()
            url = item[i+1:].strip()
            non_local_mods[name.lower()] = '<a href="{}">{}</a>'.format(url,name)
        
        # Match USE statements up with the right modules
        containers = self.modules + self.procedures + self.programs + self.submodules
        for container in containers:
            id_mods(container,self.modules,non_local_mods,self.submodules)
            
        # Get the order to process other correlations with
        deplist = {}
        
        def get_deps(item):
            uselist = [m[0] for m in mod.uses]
            for proc in item.subroutines:
                uselist.extend(get_deps(proc))
            for proc in item.functions:
                uselist.extend(get_deps(proc))
            for proc in getattr(item,'modprocedures',[]):
                uselist.extend(get_deps(proc))
            return uselist
        
        for mod in self.modules:
            uselist = get_deps(mod)
            uselist = [m for m in uselist if type(m) == ford.sourceform.FortranModule]
            deplist[mod] = set(uselist)
        for mod in self.submodules:
            if type(mod.ancestor_mod) is ford.sourceform.FortranModule:
                uselist = get_deps(mod)
                uselist = [m for m in uselist if type(m) == ford.sourceform.FortranModule]
                if mod.ancestor:
                    if type(mod.ancestor) is ford.sourceform.FortranSubmodule:
                        uselist.insert(0,mod.ancestor)
                    elif self.settings['warn'].lower() == 'true':
                        print('Warning: could not identify parent SUBMODULE of SUBMODULE ' + mod.name)
                else:
                    uselist.insert(0,mod.ancestor_mod)
                deplist[mod] = set(uselist)
            elif self.settings['warn'].lower() == 'true':
                print('Warning: could not identify parent MODULE of SUBMODULE ' + mod.name)
        ranklist = toposort.toposort_flatten(deplist)
        for proc in self.procedures:
            if proc.parobj == 'sourcefile': ranklist.append(proc)
        ranklist.extend(self.programs)
        
        # Perform remaining correlations for the project
        for container in ranklist:
            if type(container) != str: container.correlate(self)
        for container in ranklist:
            if type(container) != str: container.prune()
        
        if self.settings['project_url'] == '.':
            url = '..'
        else:
            url = self.settings['project_url']
        
        for sfile in self.files:
            for module in sfile.modules:
                for function in module.functions:
                    self.procedures.append(function)
                for subroutine in module.subroutines:
                    self.procedures.append(subroutine)
                for interface in module.interfaces:
                    self.procedures.append(interface)
                for absint in module.absinterfaces:
                    self.absinterfaces.append(absint)
                for dtype in module.types:
                    self.types.append(dtype)
            
            for module in sfile.submodules:
                for function in module.functions:
                    self.procedures.append(function)
                for subroutine in module.subroutines:
                    self.procedures.append(subroutine)
                for function in module.modfunctions:
                    self.submodprocedures.append(function)
                for subroutine in module.modsubroutines:
                    self.submodprocedures.append(subroutine)
                for modproc in module.modprocedures:
                    self.submodprocedures.append(modproc)
                for interface in module.interfaces:
                    self.procedures.append(interface)
                for absint in module.absinterfaces:
                    self.absinterfaces.append(absint)
                for dtype in module.types:
                    self.types.append(dtype)

            for program in sfile.programs:
                for function in program.functions:
                    self.procedures.append(function)
                for subroutine in program.subroutines:
                    self.procedures.append(subroutine)
                for interface in program.interfaces:
                    self.procedures.append(interface)
                for absint in program.absinterfaces:
                    self.absinterfaces.append(absint)
                for dtype in program.types:
                    self.types.append(dtype)
        print()

    def markdown(self,md,base_url='..'):
        """
        Process the documentation with Markdown to produce HTML.
        """
        print("\nProcessing documentation comments...")
        ford.sourceform.set_base_url(base_url)        
        if self.settings['warn'].lower() == 'true': print()
        for src in self.files + self.extra_files:
            src.markdown(md,self)
        return

    def make_links(self,base_url='..'):
        """
        Substitute intrasite links to documentation for other parts of 
        the program.
        """
        
        ford.sourceform.set_base_url(base_url)        
        for src in self.files + self.extra_files:
            src.make_links(self)
        return



def id_mods(obj,modlist,intrinsic_mods={},submodlist=[]):
    """
    Match USE statements up with the right modules
    """
    for i in range(len(obj.uses)):
        for candidate in modlist:
            if obj.uses[i][0].lower() == candidate.name.lower():
                obj.uses[i] = [candidate, obj.uses[i][1]]
                break
        else:
            if obj.uses[i][0].lower() in intrinsic_mods:
                obj.uses[i] = [intrinsic_mods[obj.uses[i][0].lower()], obj.uses[i][1]]
                continue
    if getattr(obj,'ancestor',None):
        for submod in submodlist:
            if obj.ancestor == submod.name.lower():
                obj.ancestor = submod
                break
    if hasattr(obj,'ancestor_mod'):
        for mod in modlist:
            if obj.ancestor_mod == mod.name.lower():
                obj.ancestor_mod = mod
                break
    for modproc in getattr(obj,'modprocedures',[]):
        id_mods(modproc,modlist,intrinsic_mods)
    for func in obj.functions:
        id_mods(func,modlist,intrinsic_mods)
    for subroutine in obj.subroutines:
        id_mods(subroutine,modlist,intrinsic_mods)
    return
