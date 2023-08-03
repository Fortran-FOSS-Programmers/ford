# -*- coding: utf-8 -*-
#
#  utils.py
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

import re
import os.path
import pathlib
from typing import Dict, Union, TYPE_CHECKING, List, Any, Tuple
from io import StringIO
import itertools
from collections import defaultdict

if TYPE_CHECKING:
    from ford.fortran_project import Project

LINK_RE = re.compile(
    r"""\[\[
    (?P<name>\w+(?:\.\w+)?)
    (?:\((?P<entity>\w+)\))?
    (?::(?P<child_name>\w+)
    (?:\((?P<child_entity>\w+)\))?)?
    \]\]""",
    re.VERBOSE,
)


def get_parens(line: str, retlevel: int = 0, retblevel: int = 0) -> str:
    """
    By default takes a string starting with an open parenthesis and returns the portion
    of the string going to the corresponding close parenthesis. If retlevel != 0 then
    will return when that level (for parentheses) is reached. Same for retblevel.
    """
    if not line:
        return line
    parenstr = ""
    level = 0
    blevel = 0
    for char in line:
        if char == "(":
            level += 1
        elif char == ")":
            level -= 1
        elif char == "[":
            blevel += 1
        elif char == "]":
            blevel -= 1
        elif (
            (char.isalpha() or char in ("_", ":", ",", " "))
            and level == retlevel
            and blevel == retblevel
        ):
            return parenstr
        parenstr = parenstr + char

    if level == retlevel and blevel == retblevel:
        return parenstr
    raise RuntimeError(f"Couldn't parse parentheses: {line}")


def strip_paren(line: str, retlevel: int = 0) -> list:
    """
    Takes a string with parentheses and removes any of the contents inside or outside
    of the retlevel of parentheses. Additionally, whenever a scope of the retlevel is
    left, the string is split.

    e.g. strip_paren("foo(bar(quz) + faz) + baz(buz(cas))", 1) -> ["(bar() + faz)", "(buz())"]
    """
    retstrs = []
    curstr = StringIO()
    level = 0
    for char in line:
        if char == "(":
            if level == retlevel or level + 1 == retlevel:
                curstr.write(char)
            level += 1
        elif char == ")":
            if level == retlevel or level - 1 == retlevel:
                curstr.write(char)
            if level == retlevel:
                # We are leaving a scope of the desired level,
                # and should split to indicate as such.
                retstrs.append(curstr.getvalue())
                curstr = StringIO()
            level -= 1
        elif level == retlevel:
            curstr.write(char)

    if curstr.getvalue() != "":
        retstrs.append(curstr.getvalue())
    return retstrs


def paren_split(sep, string):
    """
    Splits the string into pieces divided by sep, when sep is outside of parentheses.
    """
    if len(sep) != 1:
        raise ValueError("Separation string must be one character long")
    retlist = []
    level = 0
    blevel = 0
    left = 0
    for i in range(len(string)):
        if string[i] == "(":
            level += 1
        elif string[i] == ")":
            level -= 1
        elif string[i] == "[":
            blevel += 1
        elif string[i] == "]":
            blevel -= 1
        elif string[i] == sep and level == 0 and blevel == 0:
            retlist.append(string[left:i])
            left = i + 1
    retlist.append(string[left:])
    return retlist


def quote_split(sep, string):
    """
    Splits the strings into pieces divided by sep, when sep in not inside quotes.
    """
    if len(sep) != 1:
        raise ValueError("Separation string must be one character long")
    retlist = []
    squote = False
    dquote = False
    left = 0
    i = 0
    while i < len(string):
        if string[i] == '"' and not dquote:
            if not squote:
                squote = True
            elif (i + 1) < len(string) and string[i + 1] == '"':
                i += 1
            else:
                squote = False
        elif string[i] == "'" and not squote:
            if not dquote:
                dquote = True
            elif (i + 1) < len(string) and string[i + 1] == "'":
                i += 1
            else:
                dquote = False
        elif string[i] == sep and not dquote and not squote:
            retlist.append(string[left:i])
            left = i + 1
        i += 1
    retlist.append(string[left:])
    return retlist


def sub_links(string: str, project: Project) -> str:
    """
    Replace links to different parts of the program, formatted as
    [[name]] or [[name(object-type)]] with the appropriate URL. Can also
    link to an item's entry in another's page with the syntax
    [[parent-name:name]]. The object type can be placed in parentheses
    for either or both of these parts.
    """
    LINK_TYPES = {
        "module": "modules",
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

    SUBLINK_TYPES = {
        "variable": "variables",
        "type": "types",
        "constructor": "constructor",
        "interface": "interfaces",
        "absinterface": "absinterfaces",
        "subroutine": "subroutines",
        "function": "functions",
        "final": "finalprocs",
        "bound": "boundprocs",
        "modproc": "modprocs",
        "common": "common",
    }

    def convert_link(match):
        ERR = "Warning: Could not substitute link {}. {}"
        url = ""
        name = ""
        found = False
        searchlist = []
        item = None
        # [name,obj,subname,subobj]
        if not match["entity"]:
            for key, val in LINK_TYPES.items():
                searchlist.extend(getattr(project, val))
        else:
            if match["entity"].lower() in LINK_TYPES:
                searchlist.extend(getattr(project, LINK_TYPES[match["entity"].lower()]))
            else:
                print(
                    ERR.format(
                        match.group(),
                        f'Unrecognized classification "{match["entity"]}"',
                    )
                )
                return match.group()

        for obj in searchlist:
            if match["name"].lower() == obj.name.lower():
                url = obj.get_url()
                name = obj.name
                found = True
                item = obj
                break
        else:
            print(ERR.format(match.group(), f'"{match["name"]}" not found.'))
            url = ""
            name = match["name"]

        if found and match["child_name"]:
            searchlist = []
            if not match["child_entity"]:
                for key, val in SUBLINK_TYPES.items():
                    if val == "constructor":
                        if getattr(item, "constructor", False):
                            searchlist.append(item.constructor)
                        else:
                            continue
                    else:
                        searchlist.extend(getattr(item, val, []))
            else:
                if match["child_entity"].lower() in SUBLINK_TYPES:
                    if hasattr(item, SUBLINK_TYPES[match["child_entity"].lower()]):
                        if match["child_entity"].lower() == "constructor":
                            if item.constructor:
                                searchlist.append(item.constructor)
                        else:
                            searchlist.extend(
                                getattr(
                                    item, SUBLINK_TYPES[match["child_entity"].lower()]
                                )
                            )
                    else:
                        print(
                            ERR.format(
                                match.group(),
                                f'"{match["child_entity"]}" can not be contained in "{item.obj}"',
                            )
                        )
                        return match.group()
                else:
                    print(
                        ERR.format(
                            match.group(),
                            f'Unrecognized classification "{match["entity"]}".',
                        )
                    )
                    return match.group()

            for obj in searchlist:
                if match["child_name"].lower() == obj.name.lower():
                    url = str(url) + "#" + obj.anchor
                    name = obj.name
                    item = obj
                    break
            else:
                print(
                    ERR.format(
                        match.group(),
                        f'"{match["child_name"]}" not found in "{name}", linking to page for "{name}" instead.',
                    )
                )

        if found:
            return f'<a href="{url}">{name}</a>'
        return f"<a>{name}</a>"

    # Get information from links (need to build an RE)
    string = LINK_RE.sub(convert_link, string)
    return string


def str_to_bool(text):
    """Convert string to bool. Only takes 'true'/'false', ignoring case"""
    if isinstance(text, bool):
        return text
    if text.capitalize() == "True":
        return True
    if text.capitalize() == "False":
        return False
    raise ValueError(
        f"Could not convert string to bool: expected 'true'/'false', got '{text}'"
    )


def normalise_path(
    base_dir: pathlib.Path, path: Union[str, pathlib.Path]
) -> pathlib.Path:
    """Tidy up path, making it absolute, relative to base_dir"""
    return (base_dir / os.path.expandvars(path)).absolute()


def traverse(root, attrs) -> list:
    """Traverse a tree of objects, returning a list of all objects found
    within the attributes attrs"""
    nodes = []
    for obj in itertools.chain(*[getattr(root, attr, []) for attr in attrs]):
        nodes.append(obj)
        nodes.extend(traverse(obj, attrs))
    return nodes


# Global Vars
META_RE = re.compile(r"^[ ]{0,3}(?P<key>[A-Za-z0-9_-]+):\s*(?P<value>.*)")
META_MORE_RE = re.compile(r"^[ ]{4,}(?P<value>.*)")
BEGIN_RE = re.compile(r"^-{3}(\s.*)?")
END_RE = re.compile(r"^(-{3}|\.{3})(\s.*)?")


def meta_preprocessor(lines: Union[str, List[str]]) -> Tuple[Dict[str, Any], List[str]]:
    """Extract metadata from start of ``lines``

    This is modified from the `Meta-Data Python Markdown extension`_
    and uses the same syntax

    Arguments
    ---------
    lines:
        Text to process

    Returns
    -------
    meta:
        Dictionary of metadata, with lowercase keys
    lines:
        Original text with metadata lines removed as list

    Notes
    -----

    Original code copyright 2007-2008 `Waylan Limberg
    <http://achinghead.com>`_

    Changes copyright 2008-2014 `The Python Markdown Project
    <https://python-markdown.github.io>`_

    Further changes copyright 2023 Ford authors

    License: `BSD <https://opensource.org/licenses/bsd-license.php>`_

    .. _Meta-Data Python Markdown extension:
      https://python-markdown.github.io/extensions/meta_data/

    """

    if isinstance(lines, str):
        lines = lines.splitlines()

    if lines and BEGIN_RE.match(lines[0]):
        lines.pop(0)
    meta = defaultdict(list)
    key = None
    while lines:
        line = lines.pop(0)
        if line.strip() == "" or END_RE.match(line):
            break  # blank line or end of YAML header - done
        if m1 := META_RE.match(line):
            key = m1.group("key").lower().strip()
            value = m1.group("value").strip()
            meta[key].append(value)
        else:
            if (m2 := META_MORE_RE.match(line)) and key:
                # Add another line to existing key
                meta[key].append(m2.group("value").strip())
            else:
                lines.insert(0, line)
                break  # no meta data - done
    return meta, lines
