# -*- coding: utf-8 -*-
#
#  tipue_search.py
#  This file is part of FORD.
#
#  Copyright 2015 Christopher MacMackin <cmacmackin@gmail.com>
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU Affero General Public License as
#  published by the Free Software Foundation; either version 3 of the
#  License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU Affero General Public License for more details.
#
#  You should have received a copy of the GNU Affero General Public
#  License along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#


"""
Tipue Search
============

Serializes generated HTML to JSON that can be used by jQuery plugin - Tipue Search.

Adapted from the Pelican plugin by Talha Mansoor
https://github.com/getpelican/pelican-plugins/tree/master/tipue_search
"""

import os
import pathlib
import json
from bs4 import BeautifulSoup, FeatureNotFound, SoupStrainer
from codecs import open
from typing import Dict, List
from urllib.parse import urljoin

from ford.settings import EntitySettings


class Tipue_Search_JSON_Generator:
    def __init__(self, output_path: os.PathLike, project_url: str):
        self.output_path = pathlib.Path(output_path)
        self.siteurl = project_url
        self.json_nodes: List[Dict] = []
        self.only_text = SoupStrainer("div", id="text")
        self.only_title = SoupStrainer("title")

    def create_node(self, html, loc, meta: EntitySettings):
        try:
            soup = BeautifulSoup(html, "lxml", parse_only=self.only_text)
            soup_title = BeautifulSoup(html, "lxml", parse_only=self.only_title)
        except FeatureNotFound:
            soup = BeautifulSoup(html, "html.parser", parse_only=self.only_text)
            soup_title = BeautifulSoup(html, "html.parser", parse_only=self.only_title)

        page_text = (
            soup.find("div", {"id": "text"})
            .get_text(" ", strip=True)
            .replace("\\(", "")
            .replace("\\)", "")
            .replace("\\[", "")
            .replace("\\]", "")
            .replace("$$", "")
            .replace("^", "&#94;")
        )

        # What happens if there is not a title.
        if soup_title.title is not None:
            page_title = str(soup_title.title.string)
        else:
            page_title = ""

        # Should set default category?
        page_category = meta.category or ""

        if self.siteurl != "":
            page_url = urljoin(self.siteurl, loc)
        else:
            page_url = loc

        node = {
            "title": page_title,
            "text": page_text,
            "tags": page_category,
            "url": str(page_url),
        }

        self.json_nodes.append(node)

    def print_output(self):
        path = self.output_path / "search" / "search_database.json"

        root_node = {"pages": self.json_nodes}
        output = json.dumps(root_node, separators=(",", ":"), ensure_ascii=False)
        output = "var tipuesearch = " + output

        with open(path, "w", encoding="utf-8") as out:
            out.write(output)
