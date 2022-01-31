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

import jinja2

if sys.version_info[0] > 2:
    jinja2.utils.Cycler.next = jinja2.utils.Cycler.__next__
from tqdm import tqdm

import ford.sourceform
import ford.tipue_search
import ford.utils
from ford.graphmanager import GraphManager
from ford.graphs import graphviz_installed

loc = os.path.dirname(__file__)
env = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.join(loc, "templates")),
    trim_blocks=True,
    lstrip_blocks=True,
)
env.globals["path"] = os.path  # this lets us call path.* in templates


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
        out_dir = self.data["output_dir"]
        try:
            if os.path.isfile(out_dir):
                os.remove(out_dir)
            elif os.path.isdir(out_dir):
                shutil.rmtree(out_dir)
            os.makedirs(out_dir, 0o755)
        except Exception as e:
            print("Error: Could not create output directory. {}".format(e.args[0]))
        os.mkdir(os.path.join(out_dir, "lists"), 0o755)
        os.mkdir(os.path.join(out_dir, "sourcefile"), 0o755)
        os.mkdir(os.path.join(out_dir, "type"), 0o755)
        os.mkdir(os.path.join(out_dir, "proc"), 0o755)
        os.mkdir(os.path.join(out_dir, "interface"), 0o755)
        os.mkdir(os.path.join(out_dir, "module"), 0o755)
        os.mkdir(os.path.join(out_dir, "program"), 0o755)
        os.mkdir(os.path.join(out_dir, "src"), 0o755)
        os.mkdir(os.path.join(out_dir, "blockdata"), 0o755)
        copytree(os.path.join(loc, "css"), os.path.join(out_dir, "css"))
        copytree(os.path.join(loc, "fonts"), os.path.join(out_dir, "fonts"))
        copytree(os.path.join(loc, "js"), os.path.join(out_dir, "js"))
        if self.data["graph"]:
            self.graphs.output_graphs(self.njobs)
        if self.data["search"]:
            copytree(
                os.path.join(loc, "tipuesearch"), os.path.join(out_dir, "tipuesearch")
            )
            self.tipue.print_output()

        try:
            copytree(self.data["media_dir"], os.path.join(out_dir, "media"))
        except OSError:
            print(
                "Warning: error copying media directory {}".format(
                    self.data["media_dir"]
                )
            )
        except KeyError:
            pass

        if "css" in self.data:
            shutil.copy(self.data["css"], os.path.join(out_dir, "css", "user.css"))

        if self.data["favicon"] == "default-icon":
            shutil.copy(
                os.path.join(loc, "favicon.png"), os.path.join(out_dir, "favicon.png")
            )
        else:
            shutil.copy(self.data["favicon"], os.path.join(out_dir, "favicon.png"))

        if self.data["incl_src"]:
            for src in self.project.allfiles:
                shutil.copy(src.path, os.path.join(out_dir, "src", src.name))

        if "mathjax_config" in self.data:
            os.mkdir(os.path.join(out_dir, "js", "MathJax-config"))
            shutil.copy(
                self.data["mathjax_config"],
                os.path.join(
                    out_dir,
                    "js",
                    "MathJax-config",
                    os.path.basename(self.data["mathjax_config"]),
                ),
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


class BasePage(object):
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

    @property
    def out_dir(self):
        """Returns the output directory of the project"""
        return self.data["output_dir"]

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
        return os.path.join(self.out_dir, "index.html")

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
        return os.path.join(self.out_dir, "search.html")

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
        return os.path.join(self.out_dir, "lists", "procedures.html")

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
        return os.path.join(self.out_dir, "lists", "files.html")

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
        return os.path.join(self.out_dir, "lists", "modules.html")

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
        return os.path.join(self.out_dir, "lists", "programs.html")

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
        return os.path.join(self.out_dir, "lists", "types.html")

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
        return os.path.join(self.out_dir, "lists", "absint.html")

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
        return os.path.join(self.out_dir, "lists", "blockdata.html")

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
    def loc(self):
        return self.obj.get_dir() + "/" + self.obj.ident + ".html"

    @property
    def outfile(self):
        return os.path.join(self.out_dir, self.obj.get_dir(), self.obj.ident + ".html")


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
    def loc(self):
        return "page/" + self.obj.location + "/" + self.obj.filename + ".html"

    @property
    def outfile(self):
        return os.path.join(
            self.out_dir, "page", self.obj.location, self.obj.filename + ".html"
        )

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
            os.mkdir(os.path.join(self.out_dir, "page", self.obj.location), 0o755)
        super(PagetreePage, self).writeout()

        for item in self.obj.copy_subdir:
            try:
                copytree(
                    os.path.join(self.data["page_dir"], self.obj.location, item),
                    os.path.join(self.out_dir, "page", self.obj.location, item),
                )
            except Exception as e:
                print(
                    "Warning: could not copy directory {}. Error: {}".format(
                        os.path.join(self.data["page_dir"], self.obj.location, item),
                        e.args[0],
                    )
                )

        for item in self.obj.files:
            try:
                shutil.copy(
                    os.path.join(self.data["page_dir"], self.obj.location, item),
                    os.path.join(self.out_dir, "page", self.obj.location),
                )
            except Exception as e:
                print(
                    "Warning: could not copy file {}. Error: {}".format(
                        os.path.join(self.data["page_dir"], self.obj.location, item),
                        e.args[0],
                    )
                )


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
