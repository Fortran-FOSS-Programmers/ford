#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  reader.py
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

import sys
import re
import ford.utils
import subprocess
from typing import List, Optional, Union, Sequence
from io import StringIO, TextIOWrapper

import os.path

from ford.console import warn
from ford.fixed2free2 import convertToFree
from ford._typing import PathLike


def _contains_unterminated_string(string: str) -> bool:
    """Return True if `string` contains an unterminated quote"""
    in_quote = False
    current_quote = None
    previous_char = None
    for char in string:
        # Non-quote characters don't bother us
        if char not in ("'", '"'):
            previous_char = char
            continue
        # Doubling-up a quote character doesn't make us leave a quote
        if char == previous_char:
            previous_char = char
            continue
        # If the current character is the same as the starting quote character
        # then we have left the quote (as we've dealt with doubled-quotes)
        if char == current_quote:
            in_quote = False
            current_quote = None
            previous_char = char
            continue
        # If we weren't in a quote before, we are now
        if not in_quote:
            current_quote = char
            in_quote = True
        previous_char = char
    return in_quote


def _compile_docmark(docmark: str) -> Optional[re.Pattern]:
    """Compile ``docmark`` into a regex pattern to match Fortran comments"""
    if not docmark:
        return None

    return re.compile(f"^([^\"'!]|('[^']*')|(\"[^\"]*\"))*(!{re.escape(docmark)}.*)$")


def _match_docmark(
    docmark: Optional[re.Pattern], line: str, in_quote: bool
) -> Optional[re.Match]:
    """If docmark exists, and we're not in a string literal, try to match it"""
    if in_quote:
        return None
    if not docmark:
        return None
    return docmark.match(line)


def preprocess(
    filename: str,
    preprocessor: list[str],
    macros: list[str] | None,
    encoding: str,
    inc_dirs: Sequence[PathLike],
) -> StringIO | None:
    """Run the preprocessor over the given file"""
    # Populate the macro definition and include directory path from
    # the input lists. To define a macro we prepend '-D' and for an
    # include path we prepend '-I'.  It's important that we do not
    # prepend to an empty string as 'cpp ... -D file.F90' doesn't do
    # what is desired; use filter to remove these.
    macros = ["-D" + mac.strip() for mac in filter(None, macros or [])]
    incdirs = [f"-I{d}" for d in inc_dirs]
    preprocessor = preprocessor + macros + incdirs + [filename]
    command = " ".join(preprocessor)
    print(f"Preprocessing {filename}")
    try:
        out = subprocess.run(
            preprocessor, encoding=encoding, check=True, capture_output=True
        )
        if out.stderr:
            warn(f"Warning when preprocessing {filename}:\n{command}\n{out.stderr}")
        return StringIO(out.stdout)
    except subprocess.CalledProcessError as err:
        warn(
            f"error when preprocessing {filename}:\n{command}\n{err.stderr}\n"
            "Reverting to unpreprocessed file"
        )
        return None


class FortranReader:
    """
    An iterator which will convert a free-form Fortran source file into
    a format more conducive for analyzing. It does the following:

    - combine line continuations into one
    - remove any normal comments and any comments following an ampersand
      (line continuation)
    - if there are documentation comments preceding a piece of code, buffer
      them and return them after the code, but before any documentation
      following it
    - keep any documentation comments and, if they are at the end of a line
      of actual code, place them on a new line
    - removes blank lines and trailing white-space
    - split lines along semicolons
    """

    # Regexes
    COM_RE = re.compile("^([^\"'!]|('[^']*')|(\"[^\"]*\"))*(!.*)$")
    SC_RE = re.compile("^([^;]*);(.*)$")

    def __init__(
        self,
        filename: str,
        docmark: str = "!",
        predocmark: str = "",
        docmark_alt: str = "",
        predocmark_alt: str = "",
        fixed: bool = False,
        length_limit: bool = True,
        preprocessor: Optional[List[str]] = None,
        macros: Optional[List[str]] = None,
        inc_dirs: Optional[Sequence[PathLike]] = None,
        encoding: str = "utf-8",
    ):
        # Check that none of the docmarks are the same
        if docmark == predocmark != "":
            raise ValueError("Error: docmark and predocmark are the same.")
        if docmark == docmark_alt != "":
            raise ValueError("Error: docmark and docmark_alt are the same.")
        if docmark == predocmark_alt != "":
            raise ValueError("Error: docmark and predocmark_alt are the same.")
        if docmark_alt == predocmark != "":
            raise ValueError("Error: docmark_alt and predocmark are the same.")
        if docmark_alt == predocmark_alt != "":
            raise ValueError("Error: docmark_alt and predocmark_alt are the same.")
        if predocmark == predocmark_alt != "":
            raise ValueError("Error: predocmark and predocmark_alt are the same.")

        self.name = filename
        self.fixed = fixed
        self.length_limit = length_limit
        self.inc_dirs = inc_dirs or []
        self.docbuffer: List[str] = []
        self.pending: List[str] = []
        self.prevdoc = False
        self.reading_alt = 0
        self.encoding = encoding

        self.docmark = docmark
        self.doc_re = _compile_docmark(docmark)
        self.predocmark = predocmark
        self.predoc_re = _compile_docmark(predocmark)
        self.docmark_alt = docmark_alt
        self.doc_alt_re = _compile_docmark(docmark_alt)
        self.predocmark_alt = predocmark_alt
        self.predoc_alt_re = _compile_docmark(predocmark_alt)

        self.line_number = 0

        self.reader: Union[StringIO, TextIOWrapper]

        if preprocessor and (
            reader := preprocess(
                filename, preprocessor, macros, encoding, self.inc_dirs
            )
        ):
            self.reader = reader
        else:
            self.reader = open(filename, "r", encoding=encoding)

        if fixed:
            self.reader = convertToFree(self.reader, length_limit)

    def __iter__(self):
        return self

    def pass_back(self, line: str):
        self.pending.insert(0, line)

    def __next__(self):
        # If there are any lines waiting to be returned, return them
        if len(self.pending) != 0:
            self.include()
            self.prevdoc = False
            return self.pending.pop(0)
        # If there are any documentation lines waiting to be returned, return them.
        # This can happen for inline and preceding docs
        elif len(self.docbuffer) != 0:
            self.prevdoc = True
            return self.docbuffer.pop(0)

        # Loop through the source code until you have a complete line (including
        # all line continuations), or a complete preceding doc block
        done = False
        continued = False
        reading_predoc = False
        reading_predoc_alt = 0
        linebuffer = ""

        while not done:
            line = next(self.reader)

            self.line_number += 1

            in_quote = _contains_unterminated_string(linebuffer)

            if len(line.strip()) > 0 and line.strip()[0] == "#":
                continue

            # Capture any preceding documentation comments
            match = _match_docmark(self.predoc_re, line, in_quote)
            if match:
                # Switch to predoc: following comment lines are predoc until the end of the block
                reading_predoc = True
                self.reading_alt = 0
                reading_predoc_alt = 0
                # Substitute predocmark with docmark
                tmp = match.group(4)
                tmp = tmp[:1] + self.docmark + tmp[1 + len(self.predocmark) :]
                self.docbuffer.append(tmp)
                if len(line[0 : match.start(4)].strip()) > 0:
                    raise ValueError(
                        f"Preceding documentation lines can not be inline: {line}"
                    )

            # Check for alternate preceding documentation
            match = _match_docmark(self.predoc_alt_re, line, in_quote)
            if match:
                # Switch to doc_alt: following comment lines are documentation until end of the block
                reading_predoc_alt = 1
                self.reading_alt = 0
                reading_predoc = False
                # Substitute predocmark_alt with docmark
                tmp = match.group(4)
                tmp = tmp[:1] + self.docmark + tmp[1 + len(self.predocmark_alt) :]
                self.docbuffer.append(tmp)
                if len(line[0 : match.start(4)].strip()) > 0:
                    raise RuntimeError(
                        f"In file {self.name}\n{self.line_number}|  {line.strip()}\n"
                        f"{'^':>{len(str(self.line_number)) + match.start(4) + 4}}\n"
                        f"Preceding alternate documentation lines can not be inline\n"
                        f"Use the docmark '!{self.docmark}' instead"
                    )

            # Check for alternate succeeding documentation
            match = _match_docmark(self.doc_alt_re, line, in_quote)
            if match:
                # Switch to doc_alt: following comment lines are documentation until end of the block
                self.reading_alt = 1
                reading_predoc = False
                reading_predoc_alt = 0
                # Substitute predocmark_alt with docmark
                tmp = match.group(4)
                tmp = tmp[:1] + self.docmark + tmp[1 + len(self.docmark_alt) :]
                self.docbuffer.append(tmp)
                if len(line[0 : match.start(4)].strip()) > 0:
                    raise ValueError(
                        f"Alternate documentation lines can not be inline: {line}"
                    )

            # Capture any documentation comments
            match = _match_docmark(self.doc_re, line, in_quote)
            if match:
                self.reading_alt = 0
                reading_predoc_alt = 0
                self.docbuffer.append(match.group(4))
                line = line[0 : match.start(4)]

            if len(line.strip()) == 0 or line.strip()[0] != "!":
                self.reading_alt = 0

            if len(line.strip()) != 0 and line.strip()[0] != "!":
                reading_predoc_alt = 0

            # Remove any regular comments, unless following an alternative (pre)docmark
            match = _match_docmark(self.COM_RE, line, in_quote)
            if match:
                if (reading_predoc_alt > 1 or self.reading_alt > 1) and len(
                    line[0 : match.start(4)].strip()
                ) == 0:
                    tmp = match.group(4)
                    tmp = tmp[:1] + self.docmark + tmp[1:]
                    self.docbuffer.append(tmp)
                line = line[0 : match.start(4)]
            line = line.strip()

            # If this is a blank line following previous documentation, return
            # a line of empty documentation.
            if len(line) == 0:
                if self.prevdoc and len(self.docbuffer) == 0:
                    # ~ self.prevdoc = False
                    self.docbuffer.append("!" + self.docmark)
            else:
                reading_predoc = False
                reading_predoc_alt = 0
                self.reading_alt = 0
                # Check if line is immediate continuation of previous
                if line[0] == "&":
                    if continued:
                        line = line[1:]
                        if len(line.strip()) == 0:
                            # If the line contained only an "&" and `continued==True` then
                            # we keep going.
                            continue
                    elif len(line.strip()) == 1:
                        continue
                    else:
                        raise ValueError(
                            f"Can not start a new line in Fortran with '&': {line}"
                        )
                else:
                    linebuffer = linebuffer.strip() + " "
                # Check if line will be continued
                if line[-1] == "&":
                    continued = True
                    line = line[0:-1]
                else:
                    continued = False

            if self.reading_alt > 0:
                self.reading_alt += 1

            if reading_predoc_alt > 0:
                reading_predoc_alt += 1

            # Add this line to the buffer then check whether we're done here
            linebuffer += line
            # ~ print(((len(self.docbuffer) > 0) or (len(linebuffer) > 0)), not continued, not reading_predoc, (reading_predoc_alt == 0))
            done = (
                ((len(self.docbuffer) > 0) or (len(linebuffer) > 0))
                and not continued
                and not reading_predoc
                and (reading_predoc_alt == 0)
            )

        # Split buffer with semicolons
        # ~ print(count,linebuffer,len(linebuffer))
        frags = ford.utils.quote_split(";", linebuffer)
        self.pending.extend([s.strip() for s in frags if len(s) > 0])

        # Return the line
        if len(self.pending) > 0:
            self.include()
            self.prevdoc = False
            return self.pending.pop(0)
        else:
            tmp = self.docbuffer.pop(0)
            if tmp != "!" + self.docmark:
                self.prevdoc = True
            return tmp

    def include(self):
        """
        If the next line is an include statement, inserts the contents
        of the included file into the pending buffer.
        """
        if len(self.pending) == 0 or not self.pending[0].lower().startswith("include "):
            return
        curpending = self.pending.pop(0)
        name = curpending[8:].strip()[1:-1]
        for b in [os.path.dirname(self.name)] + self.inc_dirs:
            pname = os.path.abspath(os.path.expanduser(os.path.join(b, name)))
            if os.path.isfile(pname):
                name = pname
                break
        else:
            msg = f'Can not find include file "{name}"'
            if name.endswith(".h"):
                warn(msg)
                # undo pop and return
                self.pending = [curpending] + self.pending
                return
            raise FileNotFoundError(msg)
        self.pending = (
            list(
                FortranReader(
                    name,
                    self.docmark,
                    self.predocmark,
                    self.docmark_alt,
                    self.predocmark_alt,
                    self.fixed,
                    self.length_limit,
                    inc_dirs=self.inc_dirs,
                    encoding=self.encoding,
                )
            )
            + self.pending
        )


if __name__ == "__main__":
    filename = sys.argv[1]
    for line in FortranReader(
        filename,
        docmark="!",
        predocmark=">",
        docmark_alt="#",
        predocmark_alt="<",
    ):
        print(line)
