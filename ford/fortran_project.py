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
import toposort
from itertools import chain
from typing import List

import ford.utils
import ford.sourceform
from ford.sourceform import (
    FortranCodeUnit,
    FortranModule,
    FortranSubmodule,
    ExternalModule,
)


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

    def warn(self, message):
        if self.settings["warn"]:
            print(f"Warning: {message}")

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
            if not item:
                continue
            try:
                name, url = item.split(":", 1)
            except ValueError:
                raise ValueError(
                    f"Could not parse 'extra_mods' item in project settings: '{item}'\n"
                    "Expected something of the form 'module_name: http://link.to/module'"
                )
            name = name.strip()
            url = url.strip().strip(r"\"'").strip()
            non_local_mods[name.lower()] = f'<a href="{url}">{name}</a>'

        self.extModules.extend(
            [ExternalModule(name, url) for name, url in non_local_mods.items()]
        )

        # load external FORD FortranModules
        ford.utils.external(self)

        # Match USE statements up with the module objects or links
        for entity in chain(
            self.modules,
            self.procedures,
            self.programs,
            self.submodules,
            self.blockdata,
        ):
            find_used_modules(entity, self.modules, self.submodules, self.extModules)

        def get_deps(item):
            uselist = [m[0] for m in item.uses]
            for procedure in item.routines:
                uselist.extend(get_deps(procedure))
            return uselist

        def filter_modules(entity) -> List[FortranModule]:
            """Return a list of `FortranModule` from the dependencies of `entity`"""
            return [dep for dep in get_deps(entity) if type(dep) is FortranModule]

        # Get the order to process other correlations with
        for mod in self.modules:
            mod.deplist = filter_modules(mod)

        for mod in self.submodules:
            if type(mod.ancestor_module) is not FortranModule:
                self.warn(
                    f"Could not identify ancestor MODULE of SUBMODULE '{mod.name}'. "
                )
                continue

            if not isinstance(mod.parent_submodule, (FortranSubmodule, type(None))):
                self.warn(
                    f"Could not identify parent SUBMODULE of SUBMODULE '{mod.name}'"
                )

            mod.deplist = [
                mod.parent_submodule or mod.ancestor_module
            ] + filter_modules(mod)

        deplist = {
            module: set(module.deplist)
            for module in chain(self.modules, self.submodules)
        }

        # Get dependencies for programs and top-level procedures as well,
        # if dependency graphs are to be produced
        if self.settings["graph"]:
            for entity in chain(self.procedures, self.programs, self.blockdata):
                entity.deplist = set(filter_modules(entity))

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

        # Mapping of various entity containers in code units to the
        # corresponding container in the project
        CONTAINERS = {
            "functions": "procedures",
            "subroutines": "procedures",
            "interfaces": "procedures",
            "absinterfaces": "absinterfaces",
            "types": "types",
            "modfunctions": "submodprocedures",
            "modsubroutines": "submodprocedures",
            "modprocedures": "submodprocedures",
        }

        # Gather all the entity containers from each code unit in each
        # file into the corresponding project container
        for sfile in self.files:
            for code_unit in chain(
                sfile.modules, sfile.submodules, sfile.programs, sfile.blockdata
            ):
                for entity_kind, container in CONTAINERS.items():
                    entities = getattr(code_unit, entity_kind, [])
                    getattr(self, container).extend(entities)

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
        Like `os.walk`, except that:

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


def find_used_modules(
    entity: FortranCodeUnit,
    modules: List[FortranModule],
    submodules: List[FortranSubmodule],
    external_modules: List[ExternalModule],
) -> None:
    """Find the module objects (or links to intrinsic/external
    module) for all of the ``USED``d names in ``entity``

    Parameters
    ----------
    entity
        A program, module, submodule or procedure
    modules
        Known Fortran modules
    intrinsic_modules
        Known intrinsic Fortran modules
    submodules
        Known Fortran submodules
    external_modules
        Known external Fortran modules

    """
    # Find the modules that this entity uses
    for dependency in entity.uses:
        dependency_name = dependency[0].lower()
        for candidate in chain(modules, external_modules):
            if dependency_name == candidate.name.lower():
                dependency[0] = candidate
                break

    # Find the ancestor of this submodule (if entity is one)
    if getattr(entity, "parent_submodule", None):
        parent_submodule_name = entity.parent_submodule.lower()
        for submod in submodules:
            if parent_submodule_name == submod.name.lower():
                entity.parent_submodule = submod
                break

    if hasattr(entity, "ancestor_module"):
        ancestor_module_name = entity.ancestor_module.lower()
        for mod in modules:
            if ancestor_module_name == mod.name.lower():
                entity.ancestor_module = mod
                break

    # Find the modules that this entity's procedures use
    for procedure in entity.routines:
        find_used_modules(procedure, modules, submodules, external_modules)
