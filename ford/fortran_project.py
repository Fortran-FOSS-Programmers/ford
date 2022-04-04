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

import os
import pathlib
import toposort
import ford.utils
import ford.sourceform


INTRINSIC_MODS = {
    "iso_fortran_env": '<a href="http://fortranwiki.org/fortran/show/iso_fortran_env">iso_fortran_env</a>',
    "iso_c_binding": '<a href="http://fortranwiki.org/fortran/show/iso_c_binding">iso_c_binding</a>',
    "ieee_arithmetic": '<a href="http://fortranwiki.org/fortran/show/ieee_arithmetic">ieee_arithmetic</a>',
    "ieee_exceptions": '<a href="http://fortranwiki.org/fortran/show/IEEE+arithmetic">ieee_exceptions</a>',
    "ieee_features": '<a href="http://fortranwiki.org/fortran/show/IEEE+arithmetic">ieee_features</a>',
    "openacc": '<a href="https://www.openacc.org/sites/default/files/inline-images/Specification/OpenACC.3.0.pdf#page=85">openacc</a>',
    "omp_lib": '<a href="https://www.openmp.org/spec-html/5.1/openmpch3.html#x156-1890003">omp_lib</a>',
    "mpi": '<a href="http://www.mpi-forum.org/docs/mpi-3.1/mpi31-report/node410.htm">mpi</a>',
    "mpi_f08": '<a href="http://www.mpi-forum.org/docs/mpi-3.1/mpi31-report/node409.htm">mpi_f08</a>',
}


class Project(object):
    """
    An object which collects and contains all of the information about the
    project which is to be documented.
    """

    def __init__(self, settings):
        self.settings = settings
        self.name = settings["project"]
        self.external = settings["external"]
        self.topdirs = settings["src_dir"]
        self.extensions = settings["extensions"]
        self.fixed_extensions = settings["fixed_extensions"]
        self.extra_filetypes = settings["extra_filetypes"]
        self.display = settings["display"]
        self.encoding = settings["encoding"]

        html_incl_src = settings.get("incl_src", True)

        self.files = []
        self.modules = []
        self.programs = []
        self.procedures = []
        self.absinterfaces = []
        self.types = []
        self.submodules = []
        self.submodprocedures = []
        self.extra_files = []
        self.blockdata = []
        self.common = {}
        self.extModules = []
        self.extProcedures = []
        self.extInterfaces = []
        self.extTypes = []
        self.extVariables = []

        # Get all files within topdir, recursively
        srcdir_list = self.make_srcdir_list(settings["exclude_dir"])
        for curdir in srcdir_list:
            for item in [f for f in curdir.iterdir() if f.is_file()]:
                if item.name in settings["exclude"]:
                    continue

                filename = curdir / item
                relative_path = os.path.relpath(filename)
                extension = str(item.suffix)[1:]  # Don't include the initial '.'
                if extension in self.extensions or extension in self.fixed_extensions:
                    # Get contents of the file
                    print(f"Reading file {relative_path}")
                    if extension in settings["fpp_extensions"]:
                        preprocessor = settings["preprocessor"]
                    else:
                        preprocessor = None
                    try:
                        self.files.append(
                            ford.sourceform.FortranSourceFile(
                                str(filename),
                                settings,
                                preprocessor,
                                extension in self.fixed_extensions,
                                incl_src=html_incl_src,
                                encoding=self.encoding,
                            )
                        )
                    except Exception as e:
                        if not settings["dbg"]:
                            raise e

                        print(f"Warning: Error parsing {relative_path}.\n\t{e.args[0]}")
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
                    for block in self.files[-1].blockdata:
                        self.blockdata.append(block)
                elif extension in self.extra_filetypes:
                    print(f"Reading file {relative_path}")
                    try:
                        self.extra_files.append(
                            ford.sourceform.GenericSource(str(filename), settings)
                        )
                    except Exception as e:
                        if not settings["dbg"]:
                            raise e

                        print(f"Warning: Error parsing {relative_path}.\n\t{e.args[0]}")
                        continue

    @property
    def allfiles(self):
        """Instead of duplicating files, it is much more efficient to create the itterator on the fly"""
        for f in self.files:
            yield f
        for f in self.extra_files:
            yield f

    def __str__(self):
        return self.name

    def correlate(self):
        """
        Associates various constructs with each other.
        """

        print("Correlating information from different parts of your project...")

        non_local_mods = INTRINSIC_MODS.copy()
        for item in self.settings["extra_mods"]:
            try:
                i = item.index(":")
            except ValueError:
                print('Warning: could not parse extra modules "{}"'.format(item))
                continue
            name = item[:i].strip()
            url = item[i + 1 :].strip()
            non_local_mods[name.lower()] = '<a href="{}">{}</a>'.format(url, name)

        # load external FORD FortranModules
        ford.utils.external(self)

        # Match USE statements up with the right modules
        for s in self.modules:
            id_mods(s, self.modules, non_local_mods, self.submodules, self.extModules)
        for s in self.procedures:
            id_mods(s, self.modules, non_local_mods, self.submodules, self.extModules)
        for s in self.programs:
            id_mods(s, self.modules, non_local_mods, self.submodules, self.extModules)
        for s in self.submodules:
            id_mods(s, self.modules, non_local_mods, self.submodules, self.extModules)
        for s in self.blockdata:
            id_mods(s, self.modules, non_local_mods, self.submodules, self.extModules)
        # Get the order to process other correlations with
        deplist = {}

        def get_deps(item):
            uselist = [m[0] for m in item.uses]
            for proc in getattr(item, "subroutines", []):
                uselist.extend(get_deps(proc))
            for proc in getattr(item, "functions", []):
                uselist.extend(get_deps(proc))
            for proc in getattr(item, "modprocedures", []):
                uselist.extend(get_deps(proc))
            return uselist

        for mod in self.modules:
            uselist = get_deps(mod)
            uselist = [m for m in uselist if type(m) == ford.sourceform.FortranModule]
            deplist[mod] = set(uselist)
            mod.deplist = uselist
        for mod in self.submodules:
            if type(mod.ancestor_mod) is ford.sourceform.FortranModule:
                uselist = get_deps(mod)
                uselist = [
                    m for m in uselist if type(m) == ford.sourceform.FortranModule
                ]
                if mod.ancestor:
                    if type(mod.ancestor) is ford.sourceform.FortranSubmodule:
                        uselist.insert(0, mod.ancestor)
                    elif self.settings["warn"]:
                        print(
                            "Warning: could not identify parent SUBMODULE of SUBMODULE "
                            + mod.name
                        )
                else:
                    uselist.insert(0, mod.ancestor_mod)
                mod.deplist = uselist
                deplist[mod] = set(uselist)
            elif self.settings["warn"]:
                print(
                    "Warning: could not identify parent MODULE of SUBMODULE " + mod.name
                )
        # Get dependencies for programs and top-level procedures as well,
        # if dependency graphs are to be produced
        if self.settings["graph"]:
            for proc in self.procedures:
                proc.deplist = set(
                    [
                        m
                        for m in get_deps(proc)
                        if type(m) == ford.sourceform.FortranModule
                    ]
                )
            for prog in self.programs:
                prog.deplist = set(
                    [
                        m
                        for m in get_deps(prog)
                        if type(m) == ford.sourceform.FortranModule
                    ]
                )
            for block in self.blockdata:
                block.deplist = set(
                    [
                        m
                        for m in get_deps(block)
                        if type(m) == ford.sourceform.FortranModule
                    ]
                )
        ranklist = toposort.toposort_flatten(deplist)
        for proc in self.procedures:
            if proc.parobj == "sourcefile":
                ranklist.append(proc)
        ranklist.extend(self.programs)
        ranklist.extend(self.blockdata)

        # Perform remaining correlations for the project
        for container in ranklist:
            if type(container) != str:
                container.correlate(self)
        for container in ranklist:
            if type(container) != str:
                container.prune()

        if self.settings["project_url"] == ".":
            url = ".."
        else:
            url = self.settings["project_url"]

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

            for block in sfile.blockdata:
                for dtype in block.types:
                    self.types.append(dtype)

        def sum_lines(*argv, **kwargs):
            """Wrapper for minimizing memory consumption"""
            routine = kwargs.get("func", "num_lines")
            n = 0
            for arg in argv:
                for item in arg:
                    n += getattr(item, routine)
            return n

        self.mod_lines = sum_lines(self.modules, self.submodules)
        self.proc_lines = sum_lines(self.procedures)
        self.file_lines = sum_lines(self.files)
        self.type_lines = sum_lines(self.types)
        self.type_lines_all = sum_lines(self.types, func="num_lines_all")
        self.absint_lines = sum_lines(self.absinterfaces)
        self.prog_lines = sum_lines(self.programs)
        self.block_lines = sum_lines(self.blockdata)
        print()

    def markdown(self, md, base_url=".."):
        """
        Process the documentation with Markdown to produce HTML.
        """
        print("\nProcessing documentation comments...")
        ford.sourceform.set_base_url(base_url)
        if self.settings["warn"]:
            print()
        for src in self.allfiles:
            src.markdown(md, self)

    def make_links(self, base_url=".."):
        """
        Substitute intrasite links to documentation for other parts of
        the program.
        """
        ford.sourceform.set_base_url(base_url)
        for src in self.allfiles:
            src.make_links(self)

    def make_srcdir_list(self, exclude_dirs):
        """
        Like os.walk, except that:
        a) directories listed in exclude_dir are excluded with all
          their subdirectories
        b) absolute paths are returned
        """
        srcdir_list = []
        for topdir in self.topdirs:
            srcdir_list.append(topdir)
            srcdir_list += self.recursive_dir_list(topdir, exclude_dirs)
        return srcdir_list

    def recursive_dir_list(self, topdir, skip):
        dir_list = []
        for entry in os.listdir(topdir):
            abs_entry = ford.utils.normalise_path(topdir, entry)
            if abs_entry.is_dir() and (abs_entry not in skip):
                dir_list.append(abs_entry)
                dir_list += self.recursive_dir_list(abs_entry, skip)
        return dir_list


def id_mods(obj, modlist, intrinsic_mods={}, submodlist=[], extMods=[]):
    """
    Match USE statements up with the right modules
    """
    for i in range(len(obj.uses)):
        for candidate in modlist + extMods:
            if obj.uses[i][0].lower() == candidate.name.lower():
                obj.uses[i] = [candidate, obj.uses[i][1]]
                break
        else:
            if obj.uses[i][0].lower() in intrinsic_mods:
                obj.uses[i] = [intrinsic_mods[obj.uses[i][0].lower()], obj.uses[i][1]]
                continue
    if getattr(obj, "ancestor", None):
        for submod in submodlist:
            if obj.ancestor.lower() == submod.name.lower():
                obj.ancestor = submod
                break
    if hasattr(obj, "ancestor_mod"):
        for mod in modlist:
            if obj.ancestor_mod.lower() == mod.name.lower():
                obj.ancestor_mod = mod
                break
    for modproc in getattr(obj, "modprocedures", []):
        id_mods(modproc, modlist, intrinsic_mods, extMods)
    for func in getattr(obj, "functions", []):
        id_mods(func, modlist, intrinsic_mods, extMods)
    for subroutine in getattr(obj, "subroutines", []):
        id_mods(subroutine, modlist, intrinsic_mods, extMods)
