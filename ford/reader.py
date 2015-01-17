#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  reader.py
#  
#  Copyright 2014 Christopher MacMackin <cmacmackin@gmail.com>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
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
import ford.utils

#FIXME: Do I need the docbuffer variable? Could I just put that contents into the pending list?

class FortranReader(object):
    """
    An iterator which will convert a free-form Fortran source file into
    a format more conducive for analyzing. It does the following:
        - combine line continuations into one
        - remove any normal comments and any comments following an ampersand
          (line continuation)
        - keep any documentation comments and, if they are at the end of a line
          of actual code, place them on a new line
        - removes blank lines and trailing white-space
        - splits lines along semicolons
    """

    # Regexes
    COM_RE = re.compile("^([^\"'!]|(\'[^']*')|(\"[^\"]*\"))*(!.*)$")
    SC_RE = re.compile("^([^;]*);(.*)$")

    def __init__(self,filename,docmark='!'):
        self.name = filename
        self.reader = open(filename,'r')
        self.docbuffer = ""
        self.pending = []
        self.prevdoc = False
        self.doc_re = re.compile("^([^\"'!]|('[^']*')|(\"[^\"]*\"))*(!{}.*)$".format(docmark))
        
    def __iter__(self):
        return self
        
    def pass_back(self,line):
        self.pending.insert(0,line)
    
    def next(self):
        # If there are any lines waiting to be returned, return them
        if len(self.pending) != 0:
            self.prevdoc = False
            return self.pending.pop(0)
        # If there was documentation at the end of the previous line, return
        # it as the next line.
        elif len(self.docbuffer) != 0:
            tmp = self.docbuffer
            self.docbuffer = ""
            self.prevdoc = True
            return tmp
            
        # Loop through the source code until you have a complete line (including
        # all line continuations)
        done = False
        continued = False
        linebuffer = ""
        while not done:
            line = self.reader.next()
            if len(line.strip()) > 0 and line.strip()[0] == '#': continue
            # Capture any documentation comments
            match = self.doc_re.match(line)
            if match:
                self.docbuffer = match.group(4)
                line = line[0:match.start(4)]
            # Remove any regular comments
            match = self.COM_RE.match(line)
            if match:
                line = line[0:match.start(4)]
            line = line.strip()
            # If this is a blank line following previous documentation, return
            # a line of empty documentation.
            if len(line) == 0:
                if self.prevdoc and len(self.docbuffer) == 0:
                    #~ self.prevdoc = False
                    self.docbuffer = "!!"
            else:
                # Check if line is immediate continuation of previous
                if line[0] == '&':
                    if continued:
                        line = line[1:]
                    else:
                        raise Exception("Can not start a new line in Fortran with \"&\"")
                else:
                    linebuffer = linebuffer.strip()
                # Check if line will be continued
                if line[-1] == '&':
                    continued = True
                    self.docbuffer = ""
                    line = line[0:-1]
                else:
                    continued = False
                # Add this line to the buffer then check whether we're done here
            linebuffer += line
            done = (len(self.docbuffer) > 0) or ((not continued) and 
                   (len(linebuffer) > 0))

        # Split buffer with semicolons
        frags = ford.utils.quote_split(';',linebuffer)
        self.pending.extend([ s.strip() for s in frags if len(s) > 0])
        
        # Return the line
        if len(self.pending) > 0:
            self.prevdoc = False
            return self.pending.pop(0)
        else:
            tmp = self.docbuffer
            self.docbuffer = ""
            if tmp != "!!":
                self.prevdoc = True;
            return tmp


if __name__ == '__main__':
    import sys
    filename = sys.argv[1]
    for line in FortranReader(filename):
        print line
        continue


