#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  project.py
#  
#  Copyright 2014 Christopher MacMackin <cmacmackin@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
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

#FIXME: Need to add .lower() to all equality tests between strings

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
        self.display = settings['display']

        fpp_ext = []
        if settings['preprocess'].lower() == 'true':
            for ext in self.extensions:
                if ext == ext.upper() and ext != ext.lower(): fpp_ext.append(ext)        
        
        self.files = []
        self.modules = []
        self.programs = []
        self.procedures = []
        self.absinterfaces = []
        self.types = []
                
        # Get all files within topdir, recursively
        srctree = []
        for topdir in self.topdirs:
            srctree = os.walk(topdir)
            for srcdir in srctree:
                if os.path.split(srcdir[0])[1] in settings['exclude_dir']:
                    continue
                curdir = srcdir[0]
                for item in srcdir[2]:
                    if item.split('.')[-1] in self.extensions and not item in settings['exclude']:
                        # Get contents of the file
                        print("Reading file {}".format(os.path.relpath(os.path.join(curdir,item))))
                        fpp = item.split('.')[-1] in fpp_ext
                        #~ self.files.append(ford.sourceform.FortranSourceFile(os.path.join(curdir,item),settings,fpp))
                        try:
                            self.files.append(ford.sourceform.FortranSourceFile(os.path.join(curdir,item),settings,fpp))
                        except Exception as e:
                            print("Warning: Error parsing {}.\n\t{}".format(os.path.relpath(os.path.join(curdir,item)),e.args[0]))
                            continue
                        
                        for module in self.files[-1].modules:
                            self.modules.append(module)
                        
                        for function in self.files[-1].functions:
                            self.procedures.append(function)
                        for subroutine in self.files[-1].subroutines:
                            self.procedures.append(subroutine)
                        for program in self.files[-1].programs:
                            self.programs.append(program)


    def __str__(self):
        return self.name
    
    def correlate(self):
        """
        Associates various constructs with each other.
        """

        print("\nCorrelating information from different parts of your project...\n")
                        
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
        for srcfile in self.files:
            containers = srcfile.modules + srcfile.functions + srcfile.subroutines + srcfile.programs
            for container in containers:
                id_mods(container,self.modules,non_local_mods)
            
        # Get the order to process other correlations with
        deplist = {}
        for mod in self.modules:
            uselist = mod.uses
            for proc in mod.subroutines:
                uselist.extend(proc.uses)
            for proc in mod.functions:
                uselist.extend(proc.uses)
            uselist = [m for m in uselist if type(m) == ford.sourceform.FortranModule]
            deplist[mod] = set(uselist)
        ranklist = toposort.toposort_flatten(deplist)
        for proc in self.procedures:
            if proc.parobj == 'sourcefile': ranklist.append(proc)
        ranklist.extend(self.programs)
        
        # Perform remaining correlations for the project
        for container in ranklist:
            if type(container) != str: container.correlate(self)
        for container in ranklist:
            if type(container) != str: container.prune()
        
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

            for program in sfile.programs:
                for function in program.functions:
                    self.procedures.append(function)
                for subroutine in program.subroutines:
                    self.procedures.append(subroutine)
                for interface in program.interfaces:
                    self.procedures.append(interfaces)
                for absint in program.absinterfaces:
                    self.absinterfaces.append(absint)
                for dtype in program.types:
                    self.types.append(dtype)

    def markdown(self,md,base_url='..'):
        """
        Process the documentation with Markdown to produce HTML.
        """
        
        ford.sourceform.set_base_url(base_url)        
        if self.settings['warn'].lower() == 'true': print()
        for src in self.files:
            src.markdown(md,self)
        return

    def make_links(self,base_url='..'):
        """
        Substitute intrasite links to documentation for other parts of 
        the program.
        """
        
        ford.sourceform.set_base_url(base_url)        
        for src in self.files:
            src.make_links(self)
        return



def id_mods(obj,modlist,intrinsic_mods={}):
    """
    Match USE statements up with the right modules
    """
    for i in range(len(obj.uses)):
        if obj.uses[i].lower() in intrinsic_mods:
            obj.uses[i] = intrinsic_mods[obj.uses[i].lower()]
            continue
        for candidate in modlist:
            if obj.uses[i].lower() == candidate.name.lower():
                obj.uses[i] = candidate
                break
    for func in obj.functions:
        id_mods(func,modlist)
    for subroutine in obj.subroutines:
        id_mods(subroutine,modlist)
    return
