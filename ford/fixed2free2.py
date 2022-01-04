#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# fixed2free2.py: Conversion of Fortran code from fixed to free
#                 source form.
#
# Copyright (C) 2012    Elias Rabel
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
Script that converts fixed form Fortran code to free form
Usage: file name as first command line parameter

python fixed2free2.py file.f > file.f90
"""

# author: Elias Rabel, 2012
# Let me know if you find this script useful:
# ylikx.0 at gmail
# https://www.github.com/ylikx/

# TODO:
# *) Improve command line usage

import sys


class FortranLine:
    def __init__(self, line, length_limit=True):
        self.line = line
        self.line_conv = line
        self.isComment = False
        self.isContinuation = False
        self.length_limit = length_limit
        self.__analyse()

    def __repr__(self):
        return self.line_conv

    def continueLine(self):
        """Insert line continuation symbol at end of line."""

        if not (self.isLong and self.is_regular):
            self.line_conv = self.line_conv.rstrip() + " &\n"
        else:
            temp = self.line_conv[:72].rstrip() + " &"
            self.line_conv = temp.ljust(72) + self.excess_line

    def __analyse(self):
        line = self.line
        firstchar = line[0] if len(line) > 0 else ""
        self.label = line[0:5].strip().lower() + " " if len(line) > 1 else ""
        cont_char = line[5] if len(line) >= 6 else ""
        fivechars = line[1:5] if len(line) > 1 else ""
        self.isShort = len(line) <= 6
        self.isLong = len(line) > 73 and self.length_limit

        self.isComment = firstchar in "cC*!"
        self.isNewComment = "!" in fivechars and not self.isComment
        self.isOMP = self.isComment and fivechars.lower() == "$omp"
        if self.isOMP:
            self.isComment = False
            self.label = ""
        self.isCppLine = firstchar == "#"
        self.is_regular = not (
            self.isComment or self.isNewComment or self.isCppLine or self.isShort
        )
        self.isContinuation = (
            not (cont_char.isspace() or cont_char == "0") and self.is_regular
        )

        if self.isLong and self.is_regular:
            self.excess_line = "!" + line[72:]
            line = line[:72] + "\n"
        else:
            self.excess_line = ""

        self.line = line
        self.__convert()

    def __convert(self):
        line = self.line
        self.code = line[6:] if len(line) > 6 else "\n"

        if self.isComment:
            self.line_conv = "!" + line[1:]
        elif self.isNewComment or self.isCppLine:
            self.line_conv = line
        elif self.isOMP:
            self.line_conv = "!" + line[1:5] + " " + self.code
        elif not self.label.isspace():
            self.line_conv = self.label + self.code
        else:
            self.line_conv = self.code

        if self.isLong and self.is_regular:
            self.line_conv = self.line_conv.rstrip().ljust(72) + self.excess_line


def convertToFree(stream, length_limit=True):
    """Convert stream from fixed source form to free source form."""
    linestack = []

    for line in stream:
        convline = FortranLine(line, length_limit)

        if convline.is_regular:
            if convline.isContinuation and linestack:
                linestack[0].continueLine()
            for line_ in linestack:
                yield str(line_)
            linestack = []

        linestack.append(convline)

    for line in linestack:
        yield str(line)


if __name__ == "__main__":

    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as infile:
            for line in convertToFree(infile):
                print(line)

    else:
        print(__doc__)
