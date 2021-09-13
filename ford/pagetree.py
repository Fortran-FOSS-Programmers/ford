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

import os


class PageNode(object):
    """
    Object representing a page in a tree of pages and subpages.
    """

    base_url = ".."

    def __init__(self, md, path, proj_copy_subdir, parent):
        print("Reading page {}".format(os.path.relpath(path)))
        with open(path, "r") as page:
            text = md.reset().convert(page.read())

        if "title" in md.Meta:
            self.title = "\n".join(md.Meta["title"])
        else:
            raise Exception("Page {} has no title metadata".format(path))
        if "author" in md.Meta:
            self.author = "\n".join(md.Meta["author"])
        else:
            self.author = None
        if "date" in md.Meta:
            self.date = "\n".join(md.Meta["date"])
        else:
            self.date = None

        if "ordered_subpage" in md.Meta:
            # index.md is the main page, it should not be added by the user in the subpage lists.
            self.ordered_subpages = [
                x for x in md.Meta["ordered_subpage"] if x != "index.md"
            ]
        else:
            self.ordered_subpages = None

        # set list of directory names that are to be copied along without
        # containing an index.md itself.
        #   first priority is the copy_dir option in the *.md file
        #   if this option is not set in the file fall back to the global
        #   project settings
        if "copy_subdir" in md.Meta:
            self.copy_subdir = md.Meta["copy_subdir"]
        else:
            self.copy_subdir = proj_copy_subdir

        self.parent = parent
        self.contents = text
        self.subpages = []
        self.files = []
        if self.parent:
            self.hierarchy = self.parent.hierarchy + [self.parent]
        else:
            self.hierarchy = []

        self.filename = os.path.split(path)[1][:-3]
        if parent:
            self.topdir = parent.topdir
            self.location = os.path.relpath(os.path.split(path)[0], self.topdir)
            self.topnode = parent.topnode
        else:
            self.topdir = os.path.split(path)[0]
            self.location = ""
            self.topnode = self

    def __str__(self):
        # ~ urlstr = "<a href='{0}/page/{1}/{2}.html'>{3}</a>"
        urlstr = "<a href='{0}'>{1}</a>"
        url = urlstr.format(
            os.path.join(self.base_url, "page", self.location, self.filename + ".html"),
            self.title,
        )
        return url

    def __iter__(self):
        retlist = [self]
        for sp in self.subpages:
            retlist.extend(list(sp.__iter__()))
        return iter(retlist)


def get_page_tree(topdir, proj_copy_subdir, md, parent=None):

    # In python 3.6 or newer, the normal dict is guaranteed to be ordered.
    # However, to keep compatibility with older versions I use OrderedDict.
    # I will use this later to remove duplicates from a list in a short way.
    from collections import OrderedDict

    # look for files within topdir
    filelist = sorted(os.listdir(topdir))
    if "index.md" not in filelist:
        print(f"Warning: No index.md file in directory {topdir}")
        return None

    # process index.md
    try:
        node = PageNode(md, os.path.join(topdir, "index.md"), proj_copy_subdir, parent)
    except Exception as e:
        print(
            "Warning: Error parsing {}.\n\t{}".format(
                os.path.relpath(os.path.join(topdir, "index.md")), e.args[0]
            )
        )
        return None
    filelist.remove("index.md")

    if node.ordered_subpages:
        # Merge user given files and all files in folder, removing duplicates.
        mergedfilelist = list(OrderedDict.fromkeys(node.ordered_subpages + filelist))
    else:
        mergedfilelist = filelist

    for name in mergedfilelist:
        if name[0] != "." and name[-1] != "~":
            if not os.path.exists(os.path.join(topdir, name)):
                raise Exception("Requested page file {} does not exist.".format(name))
            elif os.path.isdir(os.path.join(topdir, name)):
                # recurse into subdirectories
                traversedir = True
                if parent is not None:
                    traversedir = name not in parent.copy_subdir
                if traversedir:
                    subnode = get_page_tree(
                        os.path.join(topdir, name), proj_copy_subdir, md, node
                    )
                    if subnode:
                        node.subpages.append(subnode)
            elif name[-3:] == ".md":
                # process subpages
                try:
                    node.subpages.append(
                        PageNode(md, os.path.join(topdir, name), proj_copy_subdir, node)
                    )
                except Exception as e:
                    print(
                        "Warning: Error parsing {}.\n\t{}".format(
                            os.path.relpath(os.path.join(topdir, name)), e.args[0]
                        )
                    )
                    continue
            else:
                node.files.append(name)
    return node


def set_base_url(url):
    PageNode.base_url = url
