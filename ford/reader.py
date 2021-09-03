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

if sys.version_info[0] > 2:
    from io import StringIO
else:
    from StringIO import StringIO
import os.path

from ford.fixed2free2 import convertToFree


class FortranReader(object):
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
        filename,
        docmark="!",
        predocmark="",
        docmark_alt="",
        predocmark_alt="",
        fixed=False,
        length_limit=True,
        preprocessor=None,
        macros=[],
        inc_dirs=[],
        encoding="utf-8",
    ):
        self.name = filename

        # Check that none of the docmarks are the same
        if docmark == predocmark != "":
            raise Exception("Error: docmark and predocmark are the same.")
        if docmark == docmark_alt != "":
            raise Exception("Error: docmark and docmark_alt are the same.")
        if docmark == predocmark_alt != "":
            raise Exception("Error: docmark and predocmark_alt are the same.")
        if docmark_alt == predocmark != "":
            raise Exception("Error: docmark_alt and predocmark are the same.")
        if docmark_alt == predocmark_alt != "":
            raise Exception("Error: docmark_alt and predocmark_alt are the same.")
        if predocmark == predocmark_alt != "":
            raise Exception("Error: predocmark and predocmark_alt are the same.")

        if preprocessor:
            # Populate the macro definition and include directory path from
            # the input lists.  To define a macro we prepend '-D' and for an
            # include path we prepend '-I'.  It's important that we do not
            # prepend to an empty string as 'cpp ... -D file.F90' doesn't do
            # what is desired; use filter to remove these.
            macros = ["-D" + mac.strip() for mac in filter(None, macros)]
            incdirs = ["-I" + d.strip() for d in filter(None, inc_dirs)]
            preprocessor = preprocessor + macros + incdirs + [filename]
            fpp = subprocess.Popen(
                preprocessor,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                encoding=encoding,
            )
            (out, err) = fpp.communicate()

            if len(err) > 0:
                print("Warning: error preprocessing " + filename)
                print(err)
                self.reader = open(filename, "r", encoding=encoding)
            else:
                self.reader = StringIO(out)
        else:
            self.reader = open(filename, "r", encoding=encoding)

        if fixed:
            self.reader = convertToFree(self.reader, length_limit)

        self.fixed = fixed
        self.length_limit = length_limit
        self.inc_dirs = inc_dirs
        self.docbuffer = []
        self.pending = []
        self.prevdoc = False
        self.reading_alt = 0
        self.docmark = docmark
        self.doc_re = re.compile(
            "^([^\"'!]|('[^']*')|(\"[^\"]*\"))*(!{}.*)$".format(re.escape(docmark))
        )
        self.predocmark = predocmark
        self.encoding = encoding
        if len(self.predocmark) != 0:
            self.predoc_re = re.compile(
                "^([^\"'!]|('[^']*')|(\"[^\"]*\"))*(!{}.*)$".format(
                    re.escape(predocmark)
                )
            )
        else:
            self.predoc_re = None
        self.docmark_alt = docmark_alt
        if len(self.docmark_alt) != 0:
            self.doc_alt_re = re.compile(
                "^([^\"'!]|('[^']*')|(\"[^\"]*\"))*(!{}.*)$".format(
                    re.escape(docmark_alt)
                )
            )
        else:
            self.doc_alt_re = None
        self.predocmark_alt = predocmark_alt
        if len(self.predocmark_alt) != 0:
            self.predoc_alt_re = re.compile(
                "^([^\"'!]|('[^']*')|(\"[^\"]*\"))*(!{}.*)$".format(
                    re.escape(predocmark_alt)
                )
            )
        else:
            self.predoc_alt_re = None

        self.line_number = 0

    def __iter__(self):
        return self

    def pass_back(self, line):
        self.pending.insert(0, line)

    # for Python 2:
    def next(self):
        return self.__next__()

    def __next__(self):  # Python 3
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

            if sys.version_info[0] > 2:
                line = self.reader.__next__()
            else:  # Python 2
                line = self.reader.next()

            self.line_number += 1

            if len(line.strip()) > 0 and line.strip()[0] == "#":
                continue

            # Capture any preceding documenation comments
            if self.predoc_re:
                match = self.predoc_re.match(line)
            else:
                match = False
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
                    raise Exception(
                        "Preceding documentation lines can not be inline: {}".format(
                            line
                        )
                    )

            # Check for alternate preceding documentation
            if self.predoc_alt_re:
                match = self.predoc_alt_re.match(line)
            else:
                match = False
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
            if self.doc_alt_re:
                match = self.doc_alt_re.match(line)
            else:
                match = False
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
                    raise Exception(
                        "Alternate documentation lines can not be inline: {}".format(
                            line
                        )
                    )

            # Capture any documentation comments
            match = self.doc_re.match(line)
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
            match = self.COM_RE.match(line)
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
                        raise Exception(
                            'Can not start a new line in Fortran with "&": {}'.format(
                                line
                            )
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
            msg = 'Can not find include file "{}".'.format(name)
            if name.endswith(".h"):
                print("WARNING:", msg)
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
        continue
