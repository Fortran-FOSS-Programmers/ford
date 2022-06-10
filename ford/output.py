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

import errno
import sys
import os
import shutil
import time
import traceback
from itertools import chain
import pathlib

import jinja2

from tqdm import tqdm

import ford.sourceform
import ford.tipue_search
import ford.utils
from ford.graphmanager import GraphManager
from ford.graphs import graphviz_installed

loc = pathlib.Path(__file__).parent
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(loc / "templates"),
    trim_blocks=True,
    lstrip_blocks=True,
)
env.globals["path"] = os.path  # this lets us call path.* in templates

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
        self.pagetree = []
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
            if data["incl_src"]:
                for item in project.allfiles:
                    self.docs.append(FilePage(self.data, project, item))
            for item in project.types:
                self.docs.append(TypePage(self.data, project, item))
            for item in project.absinterfaces:
                self.docs.append(AbsIntPage(self.data, project, item))
            for item in project.procedures:
                self.docs.append(ProcPage(self.data, project, item))
            for item in project.submodprocedures:
                self.docs.append(ProcPage(self.data, project, item))
            for item in project.modules:
                self.docs.append(ModulePage(self.data, project, item))
            for item in project.submodules:
                self.docs.append(ModulePage(self.data, project, item))
            for item in project.programs:
                self.docs.append(ProgPage(self.data, project, item))
            for item in project.blockdata:
                self.docs.append(BlockPage(self.data, project, item))
            if len(project.procedures) > 0:
                self.lists.append(ProcList(self.data, project))
            if data["incl_src"]:
                if len(project.files) + len(project.extra_files) > 1:
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
            if pagetree:
                for item in pagetree:
                    self.pagetree.append(PagetreePage(self.data, project, item))
        except Exception:
            if data["dbg"]:
                traceback.print_exc()
                sys.exit("Error encountered.")
            else:
                sys.exit('Error encountered. Run with "--debug" flag for traceback.')
        if graphviz_installed and data["graph"]:
            print("Generating graphs...")
            self.graphs = GraphManager(
                self.data["project_url"],
                self.data["output_dir"],
                self.data.get("graph_dir", ""),
                graphparent,
                self.data["coloured_edges"],
            )
            for item in project.types:
                self.graphs.register(item)
            for item in project.procedures:
                self.graphs.register(item)
            for item in project.submodprocedures:
                self.graphs.register(item)
            for item in project.modules:
                self.graphs.register(item)
            for item in project.submodules:
                self.graphs.register(item)
            for item in project.programs:
                self.graphs.register(item)
            for item in project.files:
                self.graphs.register(item)
            for item in project.blockdata:
                self.graphs.register(item)
            self.graphs.graph_all()
            project.callgraph = self.graphs.callgraph
            project.typegraph = self.graphs.typegraph
            project.usegraph = self.graphs.usegraph
            project.filegraph = self.graphs.filegraph
        else:
            self.graphs = GraphManager(
                self.data["project_url"],
                self.data["output_dir"],
                self.data.get("graph_dir", ""),
                graphparent,
                self.data["coloured_edges"],
            )
            project.callgraph = ""
            project.typegraph = ""
            project.usegraph = ""
            project.filegraph = ""
        if data["search"]:
            print("Creating search index...")
            if data["relative"]:
                self.tipue = ford.tipue_search.Tipue_Search_JSON_Generator(
                    data["output_dir"], ""
                )
            else:
                self.tipue = ford.tipue_search.Tipue_Search_JSON_Generator(
                    data["output_dir"], data["project_url"]
                )
            self.tipue.create_node(self.index.html, "index.html", {"category": "home"})
            jobs = len(self.docs) + len(self.pagetree)
            progbar = tqdm(
                chain(iter(self.docs), iter(self.pagetree)),
                total=jobs,
                unit="",
                file=sys.stdout,
            )
            for i, p in enumerate(progbar):
                self.tipue.create_node(p.html, p.loc, p.meta)
            print("")

    def writeout(self):
        print("Writing resulting documentation.")
        out_dir: pathlib.Path = self.data["output_dir"]
        # Remove any existing file/directory
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
        except OSError:
            print(
                "Warning: error copying media directory {}".format(
                    self.data["media_dir"]
                )
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

        # By doing this we omit a duplication of data.
        for p in self.docs:
            p.writeout()
        for p in self.lists:
            p.writeout()
        for p in self.pagetree:
            p.writeout()
        self.index.writeout()
        self.search.writeout()


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
        return self.render(self.data, self.proj, self.obj)

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


class IndexPage(BasePage):
    @property
    def outfile(self):
        return self.out_dir / "index.html"

    def render(self, data, proj, obj):
        if data["relative"]:
            data["project_url"] = "."
            ford.sourceform.set_base_url(".")
            ford.pagetree.set_base_url(".")
        template = env.get_template("index.html")
        return template.render(data, project=proj, proj_docs=obj)


class SearchPage(BasePage):
    @property
    def outfile(self):
        return self.out_dir / "search.html"

    def render(self, data, proj, obj):
        if data["relative"]:
            data["project_url"] = "."
            ford.sourceform.set_base_url(".")
            ford.pagetree.set_base_url(".")
        template = env.get_template("search.html")
        return template.render(data, project=proj)


class ProcList(BasePage):
    @property
    def outfile(self):
        return self.out_dir / "lists" / "procedures.html"

    def render(self, data, proj, obj):
        if data["relative"]:
            data["project_url"] = ".."
            ford.sourceform.set_base_url("..")
            ford.pagetree.set_base_url("..")
        template = env.get_template("proc_list.html")
        return template.render(data, project=proj)


class FileList(BasePage):
    @property
    def outfile(self):
        return self.out_dir / "lists" / "files.html"

    def render(self, data, proj, obj):
        if data["relative"]:
            data["project_url"] = ".."
            ford.sourceform.set_base_url("..")
            ford.pagetree.set_base_url("..")
        template = env.get_template("file_list.html")
        return template.render(data, project=proj)


class ModList(BasePage):
    @property
    def outfile(self):
        return self.out_dir / "lists" / "modules.html"

    def render(self, data, proj, obj):
        if data["relative"]:
            data["project_url"] = ".."
            ford.sourceform.set_base_url("..")
            ford.pagetree.set_base_url("..")
        template = env.get_template("mod_list.html")
        return template.render(data, project=proj)


class ProgList(BasePage):
    @property
    def outfile(self):
        return self.out_dir / "lists" / "programs.html"

    def render(self, data, proj, obj):
        if data["relative"]:
            data["project_url"] = ".."
            ford.sourceform.set_base_url("..")
            ford.pagetree.set_base_url("..")
        template = env.get_template("prog_list.html")
        return template.render(data, project=proj)


class TypeList(BasePage):
    @property
    def outfile(self):
        return self.out_dir / "lists" / "types.html"

    def render(self, data, proj, obj):
        if data["relative"]:
            data["project_url"] = ".."
            ford.sourceform.set_base_url("..")
            ford.pagetree.set_base_url("..")
        template = env.get_template("types_list.html")
        return template.render(data, project=proj)


class AbsIntList(BasePage):
    @property
    def outfile(self):
        return self.out_dir / "lists" / "absint.html"

    def render(self, data, proj, obj):
        if data["relative"]:
            data["project_url"] = ".."
            ford.sourceform.set_base_url("..")
            ford.pagetree.set_base_url("..")
        template = env.get_template("absint_list.html")
        return template.render(data, project=proj)


class BlockList(BasePage):
    @property
    def outfile(self):
        return self.out_dir / "lists" / "blockdata.html"

    def render(self, data, proj, obj):
        if data["relative"]:
            data["project_url"] = ".."
            ford.sourceform.set_base_url("..")
            ford.pagetree.set_base_url("..")
        template = env.get_template("block_list.html")
        return template.render(data, project=proj)


class DocPage(BasePage):
    """
    Abstract class to be inherited by all pages for items in the code.
    """

    @property
    def object_page(self):
        return self.obj.ident + ".html"

    @property
    def loc(self):
        return pathlib.Path(self.obj.get_dir()) / self.object_page

    @property
    def outfile(self):
        return self.out_dir / self.obj.get_dir() / self.object_page


class FilePage(DocPage):
    def render(self, data, proj, obj):
        if data["relative"]:
            data["project_url"] = ".."
            ford.sourceform.set_base_url("..")
            ford.pagetree.set_base_url("..")
        template = env.get_template("file_page.html")
        return template.render(data, src=obj, project=proj)


class TypePage(DocPage):
    def render(self, data, proj, obj):
        if data["relative"]:
            data["project_url"] = ".."
            ford.sourceform.set_base_url("..")
            ford.pagetree.set_base_url("..")
        template = env.get_template("type_page.html")
        return template.render(data, dtype=obj, project=proj)


class AbsIntPage(DocPage):
    def render(self, data, proj, obj):
        if data["relative"]:
            data["project_url"] = ".."
            ford.sourceform.set_base_url("..")
            ford.pagetree.set_base_url("..")
        template = env.get_template("nongenint_page.html")
        return template.render(data, interface=obj, project=proj)


class ProcPage(DocPage):
    def render(self, data, proj, obj):
        if data["relative"]:
            data["project_url"] = ".."
            ford.sourceform.set_base_url("..")
            ford.pagetree.set_base_url("..")
        if obj.obj == "proc":
            template = env.get_template("proc_page.html")
            return template.render(data, procedure=obj, project=proj)
        else:
            if obj.generic:
                template = env.get_template("genint_page.html")
            else:
                template = env.get_template("nongenint_page.html")
            return template.render(data, interface=obj, project=proj)


class ModulePage(DocPage):
    def render(self, data, proj, obj):
        if data["relative"]:
            data["project_url"] = ".."
            ford.sourceform.set_base_url("..")
            ford.pagetree.set_base_url("..")
        template = env.get_template("mod_page.html")
        return template.render(data, module=obj, project=proj)


class ProgPage(DocPage):
    def render(self, data, proj, obj):
        if data["relative"]:
            data["project_url"] = ".."
            ford.sourceform.set_base_url("..")
            ford.pagetree.set_base_url("..")
        template = env.get_template("prog_page.html")
        return template.render(data, program=obj, project=proj)


class BlockPage(DocPage):
    def render(self, data, proj, obj):
        if data["relative"]:
            data["project_url"] = ".."
            ford.sourceform.set_base_url("..")
            ford.pagetree.set_base_url("..")
        template = env.get_template("block_page.html")
        return template.render(data, blockdat=obj, project=proj)


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


def copytree(src, dst):
    """Replaces shutil.copytree to avoid problems on certain file systems.

    shutil.copytree() and shutil.copystat() invoke os.setxattr(), which seems
    to fail when called for directories on at least one NFS file system.
    The current routine is a simple replacement, which should be good enough for
    Ford.
    """

    def touch(path):
        now = time.time()
        try:
            # assume it's there
            os.utime(path, (now, now))
        except os.error:
            # if it isn't, try creating the directory,
            # a file with that name
            os.makedirs(os.path.dirname(path))
            open(path, "w").close()
            os.utime(path, (now, now))

    for root, dirs, files in os.walk(src):
        relsrcdir = os.path.relpath(root, src)
        dstdir = os.path.join(dst, relsrcdir)
        if not os.path.exists(dstdir):
            try:
                os.makedirs(dstdir)
            except OSError as ex:
                if ex.errno != errno.EEXIST:
                    raise
        for ff in files:
            shutil.copy(os.path.join(root, ff), os.path.join(dstdir, ff))
            touch(os.path.join(dstdir, ff))


def truncate(string, width):
    """
    Truncates/pads the string to be the the specified length,
    including ellipsis dots if truncation occurs.
    """
    if len(string) > width:
        return string[: width - 3] + "..."
    else:
        return string.ljust(width)
