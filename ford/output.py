# -*- coding: utf-8 -*-
#
#  output.py
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

import sys
import os
import shutil
import traceback
from itertools import chain
import pathlib

import jinja2

from tqdm import tqdm

import ford.sourceform
import ford.tipue_search
import ford.utils
from ford.graphs import graphviz_installed, GraphManager

loc = pathlib.Path(__file__).parent
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(loc / "templates"),
    trim_blocks=True,
    lstrip_blocks=True,
)
env.globals["path"] = os.path  # this lets us call path.* in templates


def is_more_than_one(collection):
    return collection > 1


env.tests["more_than_one"] = is_more_than_one

USER_WRITABLE_ONLY = 0o755


class Documentation(object):
    """
    Represents and handles the creation of the documentation files from
    a project.
    """

    def __init__(self, data, proj_docs, project, pagetree):
        # This lets us use meta data anywhere within the template.
        # Also, in future for other template, we may not need to
        # pass the data obj.
        env.globals["projectData"] = data
        self.project = project
        # Jinja2's `if` statement counts `None` as truthy, so to avoid
        # lots of refactoring and messiness in the templates, just get
        # rid of None values
        self.data = {k: v for k, v in data.items() if v is not None}
        self.lists = []
        self.docs = []
        self.njobs = int(self.data["parallel"])
        self.parallel = self.njobs > 0

        self.index = IndexPage(self.data, project, proj_docs)
        self.search = SearchPage(self.data, project)
        if not graphviz_installed and data["graph"]:
            print(
                "Warning: Will not be able to generate graphs. Graphviz not installed."
            )
        if self.data["relative"]:
            graphparent = "../"
        else:
            graphparent = ""
        print("Creating HTML documentation...")
        try:
            # Create individual entity pages
            entity_list_page_map = [
                (project.types, TypePage),
                (project.absinterfaces, AbsIntPage),
                (project.procedures, ProcPage),
                (project.submodprocedures, ProcPage),
                (project.modules, ModulePage),
                (project.submodules, ModulePage),
                (project.programs, ProgPage),
                (project.blockdata, BlockPage),
            ]
            if data["incl_src"]:
                entity_list_page_map.append((project.allfiles, FilePage))

            for entity_list, page_class in entity_list_page_map:
                for item in entity_list:
                    self.docs.append(page_class(self.data, project, item))

            # Create lists of each entity type
            if len(project.procedures) > 0:
                self.lists.append(ProcList(self.data, project))
            if data["incl_src"] and (len(project.files) + len(project.extra_files) > 1):
                self.lists.append(FileList(self.data, project))
            if len(project.modules) + len(project.submodules) > 0:
                self.lists.append(ModList(self.data, project))
            if len(project.programs) > 1:
                self.lists.append(ProgList(self.data, project))
            if len(project.types) > 0:
                self.lists.append(TypeList(self.data, project))
            if len(project.absinterfaces) > 0:
                self.lists.append(AbsIntList(self.data, project))
            if len(project.blockdata) > 1:
                self.lists.append(BlockList(self.data, project))

            # Create static pages
            self.pagetree = [
                PagetreePage(self.data, project, item) for item in (pagetree or [])
            ]
        except Exception:
            if data["dbg"]:
                traceback.print_exc()
                sys.exit("Error encountered.")
            else:
                sys.exit('Error encountered. Run with "--debug" flag for traceback.')

        self.graphs = GraphManager(
            self.data["project_url"],
            self.data["output_dir"],
            self.data.get("graph_dir", ""),
            graphparent,
            self.data["coloured_edges"],
            save_graphs=bool(self.data.get("graph_dir", False)),
        )

        if graphviz_installed and data["graph"]:
            for entity_list in [
                project.types,
                project.procedures,
                project.submodprocedures,
                project.modules,
                project.submodules,
                project.programs,
                project.files,
                project.blockdata,
            ]:
                for item in entity_list:
                    self.graphs.register(item)

            self.graphs.graph_all()
            project.callgraph = self.graphs.callgraph
            project.typegraph = self.graphs.typegraph
            project.usegraph = self.graphs.usegraph
            project.filegraph = self.graphs.filegraph
        else:
            project.callgraph = ""
            project.typegraph = ""
            project.usegraph = ""
            project.filegraph = ""

        if data["search"]:
            url = "" if data["relative"] else data["project_url"]
            self.tipue = ford.tipue_search.Tipue_Search_JSON_Generator(
                data["output_dir"], url
            )
            self.tipue.create_node(self.index.html, "index.html", {"category": "home"})
            jobs = len(self.docs) + len(self.pagetree)
            for p in tqdm(
                chain(self.docs, self.pagetree),
                total=jobs,
                unit="",
                desc="Creating search index",
            ):
                self.tipue.create_node(p.html, p.loc, p.meta)
            print("")

    def writeout(self):
        out_dir: pathlib.Path = self.data["output_dir"]
        print(f"Writing documentation to '{out_dir}'...")
        # Remove any existing file/directory. This avoids errors coming from
        # `shutils.copytree` for Python < 3.8, where we can't explicitly ignore them
        if out_dir.is_file():
            out_dir.unlink()
        else:
            shutil.rmtree(out_dir, ignore_errors=True)

        try:
            out_dir.mkdir(USER_WRITABLE_ONLY, parents=True)
        except Exception as e:
            print(f"Error: Could not create output directory. {e.args[0]}")

        for directory in [
            "lists",
            "sourcefile",
            "type",
            "proc",
            "interface",
            "module",
            "program",
            "src",
            "blockdata",
        ]:
            (out_dir / directory).mkdir(USER_WRITABLE_ONLY)

        for directory in ["css", "fonts", "js"]:
            copytree(loc / directory, out_dir / directory)

        if self.data["graph"]:
            self.graphs.output_graphs(self.njobs)
        if self.data["search"]:
            copytree(loc / "tipuesearch", out_dir / "tipuesearch")
            self.tipue.print_output()

        try:
            copytree(self.data["media_dir"], out_dir / "media")
        except OSError as e:
            print(
                f"Warning: error copying media directory {self.data['media_dir']}, {e}"
            )
        except KeyError:
            pass

        if "css" in self.data:
            shutil.copy(self.data["css"], out_dir / "css" / "user.css")

        if self.data["favicon"] == "default-icon":
            favicon_path = loc / "favicon.png"
        else:
            favicon_path = self.data["favicon"]

        shutil.copy(favicon_path, out_dir / "favicon.png")

        if self.data["incl_src"]:
            for src in self.project.allfiles:
                shutil.copy(src.path, out_dir / "src" / src.name)

        if "mathjax_config" in self.data:
            mathjax_path = out_dir / "js" / "MathJax-config"
            mathjax_path.mkdir(parents=True, exist_ok=True)
            shutil.copy(
                self.data["mathjax_config"],
                mathjax_path / os.path.basename(self.data["mathjax_config"]),
            )

        for p in chain(self.docs, self.lists, self.pagetree, [self.index, self.search]):
            p.writeout()

        print(f"\nBrowse the generated documentation: file://{out_dir}/index.html")


class BasePage:
    """
    Abstract class for representation of pages in the documentation.

      data
        Dictionary containing project information (to be used when rendering)
      proj
        FortranProject object
      obj
        The object/item in the code which this page is documenting
    """

    def __init__(self, data, proj, obj=None):
        self.data = data
        self.proj = proj
        self.obj = obj
        self.meta = getattr(obj, "meta", {})
        self.out_dir = self.data["output_dir"]
        self.page_dir = self.out_dir / "page"

    @property
    def html(self):
        """Wrapper for only doing the rendering on request (drastically reduces memory)"""
        try:
            return self.render(self.data, self.proj, self.obj)
        except Exception as e:
            raise RuntimeError(
                f"Error rendering '{self.outfile.name}' for '{self.obj.name}' : {e}"
            )

    def writeout(self):
        with open(self.outfile, "wb") as out:
            out.write(self.html.encode("utf8"))

    def render(self, data, proj, obj):
        """
        Get the HTML for the page. This method must be overridden. Arguments
        are proj_data, project object, and item in the code which the
        page documents.
        """
        raise NotImplementedError("Should not instantiate BasePage type")


class ListTopPage(BasePage):
    @property
    def list_page(self):
        raise NotImplementedError("ListTopPage subclass missing 'list_page' property")

    @property
    def outfile(self):
        return self.out_dir / self.list_page

    def render(self, data, proj, obj):
        if data["relative"]:
            data["project_url"] = "."
            ford.sourceform.set_base_url(".")
            ford.pagetree.set_base_url(".")
        template = env.get_template(self.list_page)
        return template.render(data, project=proj, proj_docs=obj)


class IndexPage(ListTopPage):
    list_page = "index.html"


class SearchPage(ListTopPage):
    list_page = "search.html"


class ListPage(BasePage):
    @property
    def out_page(self):
        raise NotImplementedError("ListPage subclass missing 'out_page' property")

    @property
    def list_page(self):
        raise NotImplementedError("ListPage subclass missing 'list_page' property")

    @property
    def outfile(self):
        return self.out_dir / "lists" / self.out_page

    def render(self, data, proj, obj):
        if data["relative"]:
            data["project_url"] = ".."
            ford.sourceform.set_base_url("..")
            ford.pagetree.set_base_url("..")
        template = env.get_template(self.list_page)
        return template.render(data, project=proj)


class ProcList(ListPage):
    out_page = "procedures.html"
    list_page = "proc_list.html"


class FileList(ListPage):
    out_page = "files.html"
    list_page = "file_list.html"


class ModList(ListPage):
    out_page = "modules.html"
    list_page = "mod_list.html"


class ProgList(ListPage):
    out_page = "programs.html"
    list_page = "prog_list.html"


class TypeList(ListPage):
    out_page = "types.html"
    list_page = "types_list.html"


class AbsIntList(ListPage):
    out_page = "absint.html"
    list_page = "absint_list.html"


class BlockList(ListPage):
    out_page = "blockdata.html"
    list_page = "block_list.html"


class DocPage(BasePage):
    """
    Abstract class to be inherited by all pages for items in the code.
    """

    @property
    def page_path(self):
        raise NotImplementedError("DocPage subclass missing 'page_path'")

    @property
    def payload_key(self):
        raise NotImplementedError("DocPage subclass missing 'payload_key'")

    @property
    def object_page(self):
        return self.obj.ident + ".html"

    @property
    def loc(self):
        return pathlib.Path(self.obj.get_dir()) / self.object_page

    @property
    def outfile(self):
        return self.out_dir / self.obj.get_dir() / self.object_page

    def render(self, data, project, object):
        if data["relative"]:
            data["project_url"] = ".."
            ford.sourceform.set_base_url("..")
            ford.pagetree.set_base_url("..")
        template = env.get_template(self.page_path)
        try:
            return template.render(data, project=project, **{self.payload_key: object})
        except jinja2.exceptions.TemplateError:
            print(f"Error rendering page '{self.outfile}'")
            raise


class FilePage(DocPage):
    page_path = "file_page.html"
    payload_key = "src"


class TypePage(DocPage):
    page_path = "type_page.html"
    payload_key = "dtype"


class AbsIntPage(DocPage):
    page_path = "nongenint_page.html"
    payload_key = "interface"


class ModulePage(DocPage):
    page_path = "mod_page.html"
    payload_key = "module"


class ProgPage(DocPage):
    page_path = "prog_page.html"
    payload_key = "program"


class BlockPage(DocPage):
    page_path = "block_page.html"
    payload_key = "blockdat"


class ProcedurePage(DocPage):
    page_path = "proc_page.html"
    payload_key = "procedure"


class GenericInterfacePage(DocPage):
    page_path = "genint_page.html"
    payload_key = "interface"


class InterfacePage(DocPage):
    page_path = "nongenint_page.html"
    payload_key = "interface"


def ProcPage(data, proj, obj):
    """Factory function for creating procedure or interface pages"""
    if obj.obj == "proc":
        return ProcedurePage(data, proj, obj)
    if obj.generic:
        return GenericInterfacePage(data, proj, obj)
    return InterfacePage(data, proj, obj)


class PagetreePage(BasePage):
    @property
    def object_page(self):
        return self.obj.filename + ".html"

    @property
    def loc(self):
        return pathlib.Path("page") / self.obj.location / self.object_page

    @property
    def outfile(self):
        return self.page_dir / self.obj.location / self.object_page

    def render(self, data, proj, obj):
        if data["relative"]:
            base_url = ("../" * len(obj.hierarchy))[:-1]
            if obj.filename == "index":
                if len(obj.hierarchy) > 0:
                    base_url = base_url + "/.."
                else:
                    base_url = ".."
            ford.sourceform.set_base_url(base_url)
            ford.pagetree.set_base_url(base_url)
            data["project_url"] = base_url
        template = env.get_template("info_page.html")
        obj.contents = ford.utils.sub_links(
            ford.utils.sub_macros(ford.utils.sub_notes(obj.contents)), proj
        )
        return template.render(data, page=obj, project=proj, topnode=obj.topnode)

    def writeout(self):
        if self.obj.filename == "index":
            (self.page_dir / self.obj.location).mkdir(USER_WRITABLE_ONLY, exist_ok=True)
        super(PagetreePage, self).writeout()

        for item in self.obj.copy_subdir:
            item_path = self.data["page_dir"] / self.obj.location / item
            try:
                copytree(item_path, self.page_dir / self.obj.location / item)
            except Exception as e:
                print(
                    f"Warning: could not copy directory '{item_path}'. Error: {e.args[0]}"
                )

        for item in self.obj.files:
            item_path = self.data["page_dir"] / self.obj.location / item
            try:
                shutil.copy(item_path, self.page_dir / self.obj.location)
            except Exception as e:
                print(f"Warning: could not copy file '{item_path}'. Error: {e.args[0]}")


def copytree(src: pathlib.Path, dst: pathlib.Path) -> None:
    """Wrapper around `shutil.copytree` that:
    a) doesn't try to set xattrs; and
    b) ensures modification time is time of current FORD run
    """
    shutil.copytree(src, dst, copy_function=shutil.copy)
    for file in dst.rglob("*"):
        file.touch()
