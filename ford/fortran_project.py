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
from itertools import chain, product
from typing import List, Optional, Union, Dict, Set
from pathlib import Path
from fnmatch import fnmatch

from ford.console import warn
from ford.external_project import load_external_modules
from ford.utils import ProgressBar
from ford.sourceform import (
    _find_in_list,
    FortranBase,
    FortranBlockData,
    FortranCodeUnit,
    FortranModule,
    FortranSubmodule,
    ExternalModule,
    FortranInterface,
    FortranType,
    FortranModuleProcedureImplementation,
    FortranCommon,
    ExternalFunction,
    ExternalSubroutine,
    FortranNamelist,
    ExternalType,
    ExternalInterface,
    ExternalVariable,
    FortranProcedure,
    FortranSourceFile,
    GenericSource,
    FortranProgram,
)
from ford.settings import ProjectSettings
from ford._typing import PathLike


LINK_TYPES = {
    "module": "modules",
    "submodule": "submodules",
    "extmodule": "extModules",
    "type": "types",
    "exttype": "extTypes",
    "procedure": "procedures",
    "extprocedure": "extProcedures",
    "subroutine": "procedures",
    "extsubroutine": "extProcedures",
    "function": "procedures",
    "extfunction": "extProcedures",
    "proc": "procedures",
    "extproc": "extProcedures",
    "file": "allfiles",
    "interface": "absinterfaces",
    "extinterface": "extInterfaces",
    "absinterface": "absinterfaces",
    "extabsinterface": "extInterfaces",
    "program": "programs",
    "block": "blockdata",
    "namelist": "namelists",
}


def find_all_files(settings: ProjectSettings) -> Set[Path]:
    """Returns a list of all selected files below a set of directories"""

    file_extensions = chain(
        settings.extensions,
        settings.fixed_extensions,
        settings.extra_filetypes.keys(),
    )

    # Get initial list of all files in all source directories
    src_files: Set[Path] = set()

    for src_dir, extension in product(settings.src_dir, file_extensions):
        src_files.update(Path(src_dir).glob(f"**/*.{extension}"))

    # Remove files under excluded directories
    for exclude_dir in settings.exclude_dir:
        src_files = {
            src for src in src_files if not fnmatch(str(src), f"{exclude_dir}/*")
        }

    bottom_level_dirs = [src_dir.name for src_dir in settings.src_dir]
    # First, let's check if the files are relative paths or not
    for i, exclude in enumerate(settings.exclude):
        exclude_path = Path(exclude)
        if (
            not exclude_path.is_file()
            and exclude_path.parent.name not in bottom_level_dirs
            and "*" not in exclude
        ):
            glob_exclude = f"**/{exclude}"
            warn(
                f"exclude file '{exclude}' is not relative to any source directories, all matching files will be excluded.\n"
                f"To suppress this warning please change it to '{glob_exclude}' in your settings file"
            )
            settings.exclude[i] = glob_exclude

    for exclude in settings.exclude:
        src_files = {
            src for src in src_files if not fnmatch(os.path.relpath(src), exclude)
        }

    return src_files


class Project:
    """
    An object which collects and contains all of the information about the
    project which is to be documented.
    """

    def __init__(self, settings: ProjectSettings):
        self.settings = settings
        self.name = settings.project
        self.external = settings.external
        self.topdirs = settings.src_dir
        self.extensions = settings.extensions
        self.fixed_extensions = settings.fixed_extensions
        self.extra_filetypes = settings.extra_filetypes
        self.display = settings.display
        self.encoding = settings.encoding

        self.files: List[FortranSourceFile] = []
        self.modules: List[FortranModule] = []
        self.programs: List[FortranProgram] = []
        self.procedures: List[FortranProcedure] = []
        self.absinterfaces: List[FortranInterface] = []
        self.types: List[FortranType] = []
        self.submodules: List[FortranSubmodule] = []
        self.submodprocedures: List[FortranModuleProcedureImplementation] = []
        self.extra_files: List[GenericSource] = []
        self.blockdata: List[FortranBlockData] = []
        self.common: Dict[str, FortranCommon] = {}
        self.extModules: List[ExternalModule] = []
        self.extProcedures: List[Union[ExternalSubroutine, ExternalFunction]] = []
        self.extInterfaces: List[ExternalInterface] = []
        self.extTypes: List[ExternalType] = []
        self.extVariables: List[ExternalVariable] = []
        self.namelists: List[FortranNamelist] = []

        # Get all files within topdir, recursively

        for filename in (
            progress := ProgressBar("Parsing files", find_all_files(settings))
        ):
            relative_path = os.path.relpath(filename)
            progress.set_current(relative_path)

            extension = str(filename.suffix)[1:]  # Don't include the initial '.'
            fortran_extensions = self.extensions + self.fixed_extensions
            try:
                if extension in fortran_extensions:
                    self._fortran_file(extension, filename, settings)
                elif extension in self.extra_filetypes:
                    self.extra_files.append(GenericSource(filename, settings))
            except Exception as e:
                if not settings.dbg:
                    raise e

                warn(
                    f"Error parsing {relative_path}.\n\t{e.args if len(e.args) == 0 else e.args[0]}"
                )
                continue

    def _fortran_file(
        self, extension: str, filename: PathLike, settings: ProjectSettings
    ):
        if extension in settings.fpp_extensions:
            preprocessor = settings.preprocessor.split()
        else:
            preprocessor = None

        new_file = FortranSourceFile(
            str(filename),
            settings,
            preprocessor,
            extension in self.fixed_extensions,
            incl_src=settings.incl_src,
            encoding=self.encoding,
        )

        def namelist_check(entity):
            self.namelists.extend(getattr(entity, "namelists", []))

        for module in new_file.modules:
            self.modules.append(module)
            for routine in module.routines:
                namelist_check(routine)

        for submod in new_file.submodules:
            self.submodules.append(submod)
            for routine in submod.routines:
                namelist_check(routine)

        for function in new_file.functions:
            function.visible = True
            self.procedures.append(function)
            namelist_check(function)

        for subroutine in new_file.subroutines:
            subroutine.visible = True
            self.procedures.append(subroutine)
            namelist_check(subroutine)

        for program in new_file.programs:
            program.visible = True
            self.programs.append(program)
            namelist_check(program)
            for routine in program.routines:
                namelist_check(routine)

        for block in new_file.blockdata:
            self.blockdata.append(block)

        self.files.append(new_file)

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

        self.extModules.extend(
            [
                ExternalModule(name, url)
                for name, url in self.settings.extra_mods.items()
            ]
        )

        # load external FORD FortranModules
        load_external_modules(self)

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
            interfaceprocs = []
            for intr in getattr(item, "interfaces", []):
                if hasattr(intr, "procedure"):
                    interfaceprocs.append(intr.procedure)
            for procedure in chain(item.routines, interfaceprocs):
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
                warn(
                    f"Could not identify ancestor module ('{mod.ancestor_module}') of submodule '{mod.name}' "
                    f"(in '{mod.filename}').\n"
                    f"         This is usually because Ford hasn't found '{mod.ancestor_module}' "
                    "in any of the source directories.\n"
                )
                continue

            if not isinstance(mod.parent_submodule, (FortranSubmodule, type(None))):
                warn(
                    f"Could not identify parent submodule ('{mod.parent_submodule}') of submodule '{mod.name}' "
                    f"(in '{mod.filename}').\n"
                    f"         This is usually because Ford hasn't found '{mod.parent_submodule}' "
                    "in any of the source directories.\n"
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
        if self.settings.graph:
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
            if not isinstance(container, str):
                container.correlate(self)
        for container in ranklist:
            if not isinstance(container, str):
                container.prune()

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

    def markdown(self, md):
        """
        Process the documentation with Markdown to produce HTML.
        """
        if self.settings.warn:
            print()

        items = []
        for src in self.allfiles:
            items.extend(src.markdownable_items)

        for item in (bar := ProgressBar("Processing comments", items)):
            bar.set_current(item.name)
            item.markdown(md)

    def find(
        self,
        name: str,
        entity: Optional[str] = None,
        child_name: Optional[str] = None,
        child_entity: Optional[str] = None,
    ) -> Optional[FortranBase]:
        """Find an entity somewhere in the project

        Parameters
        ----------
        name : str
            Name of entity to look up
        entity : Optional[str]
            The class of entity (module, program, and so on)
        child_name : Optional[str]
            Name of a child of ``name`` to look up
        child_entity : Optional[str]
            The class of ``child_name``

        Returns
        -------
        Optional[FortranBase]
            Returns `None` if ``name`` not found

        """

        item = None

        if entity is not None:
            try:
                collection = getattr(self, LINK_TYPES[entity.lower()])
            except KeyError:
                raise ValueError(f"Unknown class of entity {entity!r}")
        else:
            collection = chain(
                *(getattr(self, collection) for collection in LINK_TYPES.values())
            )

        item = _find_in_list(collection, name)

        if child_name is None or item is None:
            return item

        return item.find_child(child_name, child_entity)


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
        # Can safely skip if already known
        if isinstance(dependency[0], FortranModule):
            continue
        dependency_name = dependency[0].lower()
        for candidate in chain(modules, external_modules):
            if dependency_name == candidate.name.lower():
                dependency[0] = candidate
                break

    # Find the ancestor of this submodule (if entity is one)
    if hasattr(entity, "parent_submodule") and entity.parent_submodule:
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

    # Find the modules that this entity's interfaces' procedures use
    for interface in getattr(entity, "interfaces", []):
        if hasattr(interface, "procedure"):
            find_used_modules(
                interface.procedure, modules, submodules, external_modules
            )
        else:
            for procedure in interface.routines:
                find_used_modules(procedure, modules, submodules, external_modules)
