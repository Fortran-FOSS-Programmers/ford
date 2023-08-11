# -*- coding: utf-8 -*-
#
#  pagetree.py
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

from __future__ import annotations

import os
from pathlib import Path
from typing import List, Optional, Sequence
from textwrap import dedent
from ford.utils import meta_preprocessor


class PageNode:
    """
    Object representing a page in a tree of pages and subpages.
    """

    base_url = Path("..")

    def __init__(
        self,
        md,
        path: Path,
        proj_copy_subdir: Sequence[os.PathLike],
        parent: Optional[PageNode],
        encoding: str = "utf-8",
    ):
        print(f"Reading page {os.path.relpath(path)}")
        self.meta, text = meta_preprocessor(dedent(Path(path).read_text(encoding)))

        if "title" not in self.meta:
            raise ValueError(f"Page '{path}' has no title metadata")

        self.title = "\n".join(self.meta["title"])
        self.author = "\n".join(self.meta.get("author", []))
        self.date = "\n".join(self.meta.get("date", []))

        # index.md is the main page, it should not be added by the user in the subpage lists.
        self.ordered_subpages = [
            x for x in self.meta.get("ordered_subpage", []) if x != "index.md"
        ]

        # set list of directory names that are to be copied along without
        # containing an index.md itself.
        #   first priority is the copy_dir option in the *.md file
        #   if this option is not set in the file fall back to the global
        #   project settings
        self.copy_subdir = self.meta.get("copy_subdir", proj_copy_subdir)
        self.parent = parent
        self.contents = md.reset().convert(text)
        self.subpages: List[PageNode] = []
        self.files: List[os.PathLike] = []
        self.filename = Path(path.stem)
        if self.parent:
            self.hierarchy: List[PageNode] = self.parent.hierarchy + [self.parent]
            self.topdir: Path = self.parent.topdir
            self.location = Path(os.path.relpath(path.parent, self.topdir))
            self.topnode: PageNode = self.parent.topnode
        else:
            self.hierarchy = []
            self.topdir = path.parent
            self.location = Path()
            self.topnode = self

    @property
    def path(self):
        return self.location / self.filename.with_suffix(".html")

    def __str__(self):
        return f"<a href='{self.base_url / 'page' / self.path}'>{self.title}</a>"

    def __iter__(self):
        retlist = [self]
        for sp in self.subpages:
            retlist.extend(list(sp.__iter__()))
        return iter(retlist)


def get_page_tree(
    topdir: os.PathLike,
    proj_copy_subdir: Sequence[os.PathLike],
    md,
    parent=None,
    encoding: str = "utf-8",
):
    # In python 3.6 or newer, the normal dict is guaranteed to be ordered.
    # However, to keep compatibility with older versions I use OrderedDict.
    # I will use this later to remove duplicates from a list in a short way.
    from collections import OrderedDict

    topdir = Path(topdir)

    # look for files within topdir
    index_file = topdir / "index.md"

    if not index_file.exists():
        print(f"Warning: '{index_file}' does not exist")
        return None

    # process index.md
    try:
        node = PageNode(md, index_file, proj_copy_subdir, parent, encoding)
    except Exception as e:
        print(f"Warning: Error parsing {index_file.relative_to('.')}.\n\t{e.args[0]}")
        return None

    filelist = sorted(os.listdir(topdir))
    filelist.remove("index.md")

    if node.ordered_subpages:
        # Merge user given files and all files in folder, removing duplicates.
        mergedfilelist = list(OrderedDict.fromkeys(node.ordered_subpages + filelist))
    else:
        mergedfilelist = filelist

    for name in mergedfilelist:
        if name[0] == ".":
            continue
        if name[-1] == "~":
            continue

        filename = topdir / name

        if not filename.exists():
            raise ValueError(f"Requested page file '{filename}' does not exist")

        if filename.is_dir():
            # recurse into subdirectories
            if parent and name in parent.copy_subdir:
                continue

            if subnode := get_page_tree(filename, proj_copy_subdir, md, node, encoding):
                node.subpages.append(subnode)
        elif filename.suffix == ".md":
            # process subpages
            try:
                node.subpages.append(
                    PageNode(md, filename, proj_copy_subdir, node, encoding)
                )
            except ValueError as e:
                print(f"Warning: Error parsing '{filename}'.\n\t{e.args[0]}")
                continue
        else:
            node.files.append(name)

    return node


def set_base_url(url):
    PageNode.base_url = Path(url)
