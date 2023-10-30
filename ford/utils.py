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

import re
import os
import os.path
import pathlib
from types import TracebackType
from typing import Dict, Union, List, Any, Tuple, Optional, Iterable, cast, Sized, Type
from io import StringIO
import itertools
from collections import defaultdict
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    SpinnerColumn,
    MofNCompleteColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TaskProgressColumn,
)

from ford.console import console


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
    return (base_dir / os.path.expandvars(path)).absolute().resolve()


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


class ProgressBar:
    """Progress bar that can be used to wrap an iterable and include
    the current item in the bar, or used as a context manager if not
    using a simple iterable

    An example::

        for item in (bar := ProgressBar("Processing items", items)):
            bar.set_current(item.name)
            item.do_work()

    Arguments
    ---------
    description:
        Description of task
    iterable:
        Collection to iterate over
    total:
        Can be used if length of iterable is not known at start

    """

    def __init__(
        self,
        description: str,
        iterable: Optional[Iterable] = None,
        total: Optional[int] = None,
    ):
        if total is None and hasattr(iterable, "__len__"):
            self._total: Optional[int] = len(cast(Sized, iterable))
        else:
            self._total = total

        # rich `Progress` breaks `pdb` and `breakpoint`, see:
        # - https://github.com/Textualize/rich/issues/1053
        # - https://github.com/Textualize/rich/issues/1465
        # and maintainer seems uninterested in fixing. So, workaround
        # by setting an env var to disable progress bar entirely
        disable: bool = bool(os.environ.get("FORD_DEBUGGING", False))

        self._iterable = iterable
        self._progress = Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description:21}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            TimeElapsedColumn(),
            TextColumn("{task.fields[current]}"),
            console=console,
            disable=disable,
        )

        self._progress.start()
        self._main_task = self._progress.add_task(
            description, total=self._total, current="--"
        )

    def set_current(self, current: str):
        """Set name of current item"""
        self._progress.update(self._main_task, advance=1, current=current)

    def __iter__(self):
        try:
            for item in self._iterable:
                yield item
        finally:
            self._progress.__exit__(None, None, None)

    def __enter__(self):
        self._progress.__enter__()
        return self

    def __exit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> None:
        self._progress.__exit__(exc_type, exc_val, exc_tb)
