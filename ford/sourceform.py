#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  sourceform.py
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
import os.path
import urllib
from pygments import highlight
from pygments.lexers import FortranLexer
from pygments.formatters import HtmlFormatter

import ford.reader

_var_type_re = re.compile("^integer|real|double\s*precision|character|complex|logical|type|class|procedure",re.IGNORECASE)
_var_kind_re = re.compile("\((.*)\)|\*\s*(\d+|\(.*\))")
_kind_re = re.compile("kind\s*=\s*",re.IGNORECASE)
_len_re = re.compile("len\s*=\s*",re.IGNORECASE)
_attribsplit_re = re.compile(",\s*(\w.*?)::\s*(.*)\s*")
_attribsplit2_re = re.compile("\s*(::)?\s*(.*)\s*")
_assign_re = re.compile("(\w+\s*(?:\([^=]*\)))\s*=(?!>)(?:\s*([^\s]+))?")
_point_re = re.compile("(\w+\s*(?:\([^=>]*\)))\s*=>(?:\s*([^\s]+))?")
_extends_re = re.compile("extends\s*\(\s*([^()\s]+)\s*\)")
_double_prec_re = re.compile("double\s+precision",re.IGNORECASE)
_quotes_re = re.compile("\"([^\"]|\"\")*\"|'([^']|'')*'",re.IGNORECASE)
_para_capture_re = re.compile("<p>.*?</p>",re.IGNORECASE|re.DOTALL)

base_url = ''

#TODO: Add ability to note EXTERNAL procedures, PARAMETER statements, and DATA statements.
class FortranBase(object):
    """
    An object containing the data common to all of the classes used to represent
    Fortran data.
    """
    _point_to_re = re.compile("\s*=>\s*",re.IGNORECASE)
    _split_re = re.compile("\s*,\s*",re.IGNORECASE)
    base_url = ''

    def __init__(self,source,first_line,parent=None,inherited_permission=None,
                 strings=[]):
        if inherited_permission:
            self.permission = inherited_permission.lower()
        else:
            self.permission = None
        self.strings = strings
        self.parent = parent
        if self.parent:
            self.parobj = self.parent.obj
        self.obj = type(self).__name__[7:].lower()
        if self.obj == 'subroutine' or self.obj == 'function':
            self.obj = 'proc'
        self._initialize(first_line)
        del self.strings
        self.doc = []
        line = source.next()
        while line[0:2] == "!!":
            self.doc.append(line[2:])
            line = source.next()
        source.pass_back(line)
        self.hierarchy = []
        cur = self.parent
        while cur:
            self.hierarchy.append(cur)
            cur = cur.parent
        self.hierarchy.reverse()
    
    def get_url(self):
        outstr = "{0}/{1}/{2}.html{3}"
        #~ and self.permission == 'public' and type(self.parent) == FortranSourceFile
        if ( (type(self) == FortranInterface and self.name) or
             (type(self) in [FortranType,FortranSourceFile,FortranProgram,FortranProgram,FortranModule]) or 
             (type(self) in [FortranFunction,FortranSubroutine]) ):
            outstr = urllib.quote(outstr.format(self.base_url,self.obj,self.name.lower().replace('/','\\'),''))
        elif ( (type(self) in [FortranFunction,FortranSubroutine]) or
               (type(self) == FortranBoundProcedure) ):
            outstr = urllib.quote(outstr.format(self.base_url,self.parobj,self.parent.name.lower().replace('/','\\'),self.name.lower().replace('/','\\')))
        else:
            outstr = None
        return outstr
    
    
    def __str__(self):
        outstr = "<a href='{0}'>{1}</a>"
        url = self.get_url()
        if url:
            outstr = outstr.format(url,self.name)
        else:
            if self.name:
                outstr = self.name
            else:
                outstr = ''
        return outstr

    
    def markdown(self,md):
        """
        Process the documentation with Markdown to produce HTML.
        """
        if len(self.doc) > 0:
            self.doc = '\n'.join(self.doc)
            self.doc = md.convert(self.doc)
            self.meta = md.Meta
        else:
            self.doc = ""
            self.meta = {}
    
        for key in self.meta:
            if len(self.meta[key]) == 1:
                self.meta[key] = self.meta[key][0]
            elif key == 'summary':
                self.meta[key] = '\n'.join(self.meta[key])
    
        if 'summary' in self.meta:
            self.meta['summary'] = md.convert(self.meta['summary'])
        elif _para_capture_re.search(self.doc):
            self.meta['summary'] = _para_capture_re.search(self.doc).group()
            
        md_list = []
        if hasattr(self,'variables'): md_list.extend(self.variables)
        if hasattr(self,'types'): md_list.extend(self.types)
        if hasattr(self,'modules'): md_list.extend(self.modules)
        if hasattr(self,'subroutines'): md_list.extend(self.subroutines)
        if hasattr(self,'functions'): md_list.extend(self.functions)
        if hasattr(self,'interfaces'): md_list.extend(self.interfaces)
        if hasattr(self,'programs'): md_list.extend(self.programs)
        if hasattr(self,'boundprocs'): md_list.extend(self.boundprocs)
        # if hasattr(self,'finalprocs'): md_list.extend(self.finalprocs)
        # if hasattr(self,'constructor') and self.constructor: md_list.append(self.constructor)
        if hasattr(self,'args'): md_list.extend(self.args)
        if hasattr(self,'retvar') and self.retvar: md_list.append(self.retvar)
        
        for item in md_list:
            if isinstance(item, FortranBase): item.markdown(md)
        
        return
    


class FortranContainer(FortranBase):
    """
    A class on which any classes requiring further parsing are based.
    """
    _public_re = re.compile("^public(\s+|\s*::\s*)((\w|\s|,)+)$",re.IGNORECASE)
    _private_re = re.compile("^private(\s+|\s*::\s*)((\w|\s|,)+)$",re.IGNORECASE)
    _protected_re = re.compile("^protected(\s+|\s*::\s*)((\w|\s|,)+)$",re.IGNORECASE)
    _optional_re = re.compile("^optional(\s+|\s*::\s*)((\w|\s|,)+)$",re.IGNORECASE)
    _end_re = re.compile("^end\s*(?:(module|subroutine|function|program|type|interface)(?:\s+(\w+))?)?$",re.IGNORECASE)
    _modproc_re = re.compile("^module\s+procedure\s*(?:::|\s)?\s*(\w.*)$",re.IGNORECASE)
    _module_re = re.compile("^module(?:\s+(\w+))?$",re.IGNORECASE)
    _program_re = re.compile("^program(?:\s+(\w+))?$",re.IGNORECASE)
    _subroutine_re = re.compile("^\s*(?:(.+?)\s+)?subroutine\s+(\w+)\s*(\([^()]*\))?(\s*bind\s*\(\s*c.*\))?$",re.IGNORECASE)
    _function_re = re.compile("^(?:(.+?)\s+)?function\s+(\w+)\s*(\([^()]*\))?(?:\s*result\s*\(\s*(\w+)\s*\))?(\s*bind\s*\(\s*c.*\))?$",re.IGNORECASE)
    _type_re = re.compile("^type(?:\s+|\s*(,.*)?::\s*)((?!(?:is))\w+)\s*(\([^()]*\))?\s*$",re.IGNORECASE)
    _interface_re = re.compile("^(abstract\s+)?interface(?:\s+(\S.+))?$",re.IGNORECASE)
    _boundproc_re = re.compile("^(generic|procedure)\s*(\([^()]*\))?\s*(.*)\s*::\s*(\w.*)",re.IGNORECASE)
    _final_re = re.compile("^final\s*::\s*(\w.*)",re.IGNORECASE)
    _variable_re = re.compile("^(integer|real|double\s*precision|character|complex|logical|type(?!\s+is)|class(?!\s+is)|procedure)\s*((?:\(|\s\w|[:,*]).*)$",re.IGNORECASE)
    _use_re = re.compile("^use\s+(\w+)($|,\s*)",re.IGNORECASE)
    _call_re = re.compile("^(?:if\s*\(.*\)\s*)?call\s+(\w+)\s*(?:\(\s*(.*?)\s*\))?$",re.IGNORECASE)
    #TODO: Add the ability to recognize function calls
        
    def __init__(self,source,first_line,parent=None,inherited_permission=None,
                 strings=[]):
        if type(self) != FortranSourceFile:
            FortranBase.__init__(self,source,first_line,parent,inherited_permission,
                             strings)
        incontains = False
        permission = "public"
      
        for line in source:
            if line[0:2] == "!!": 
                self.doc.append(line[2:])
                continue

            # Temporarily replace all strings to make the parsing simpler
            self.strings = []
            search_from = 0
            while _quotes_re.search(line[search_from:]):
                self.strings.append(_quotes_re.search(line[search_from:]).group())
                line = line[0:search_from] + _quotes_re.sub("\"{}\"".format(len(self.strings)-1),line[search_from:],count=1)
                search_from += _quotes_re.search(line[search_from:]).end(0)

            # Check the various possibilities for what is on this line
            if line.lower() == "contains":
                if not incontains and type(self) in _can_have_contains:
                    incontains = True
                    if isinstance(self,FortranType): permission = "public"
                elif incontains:
                    raise Exception("Multiple CONTAINS statements present in scope")
                else:
                    raise Exception("CONTAINS statement in {}".format(type(self).__name__[7:].upper()))
            elif line.lower() == "public": permission = "public"
            elif self._public_re.match(line):
                varlist = self._split_re.split(self._public_re.match(line).group(2))
                varlist[-1] = varlist[-1].strip()
                if hasattr(self,'public_list'): 
                    self.public_list.extend(varlist)
                else:
                    raise Exception("PUBLIC declaration in {}".format(type(self).__name__[7:].upper()))
            elif line.lower() == "private": permission = "private"
            elif self._private_re.match(line):
                varlist = self._split_re.split(self._private_re.match(line).group(2))
                varlist[-1] = varlist[-1].strip()
                if hasattr(self,'private_list'): 
                    self.private_list.extend(varlist)
                else:
                    raise Exception("PRIVATE declaration in {}".format(type(self).__name__[7:].upper()))
            elif line.lower() == "protected": permission = "protected"
            elif self._protected_re.match(line):
                varlist = self._split_re.split(self._protected_re.match(line).group(2))
                varlist[-1] = varlist[-1].strip()
                if hasattr(self,'protected_list'): 
                    self._protected_list.extend(varlist)
                else:
                    raise Exception("PROTECTED declaration in {}".format(type(self).__name__[7:].upper()))
            elif line.lower() == "sequence":
                if type(self) == FortranType: self.sequence = True
            elif self._optional_re.match(line):
                varlist = self._split_re.split(self._optional_re.match(line).group(2))
                varlist[-1] = varlist[-1].strip()
                if hasattr(self,'optional_list'): 
                    self._optional_list.extend(varlist)
                else:
                    raise Exception("OPTIONAL declaration in {}".format(type(self).__name__[7:].upper()))
            elif self._end_re.match(line):
                if isinstance(self,FortranSourceFile):
                    raise Exception("END statement outside of any nesting")
                self._cleanup()
                return
            elif self._modproc_re.match(line):
                if hasattr(self,'modprocs'):
                    self.modprocs.extend(get_mod_procs(source,
                                         self._modproc_re.match(line),self))
                else:
                    raise Exception("Found module procedure in {}".format(type(self).__name__[7:].upper()))
            elif self._module_re.match(line):
                if hasattr(self,'modules'):
                    self.modules.append(FortranModule(source,
                                        self._module_re.match(line),self))
                else:
                    raise Exception("Found MODULE in {}".format(type(self).__name__[7:].upper()))
            elif self._program_re.match(line):
                if hasattr(self,'programs'):
                    self.programs.append(FortranProgram(source,
                                         self._program_re.match(line),self))
                else:
                    raise Exception("Found PROGRAM in {}".format(type(self).__name__[7:].upper()))
                if len(self.programs) > 1:
                    raise Exception("Multiple PROGRAM units in same source file.")
            elif self._subroutine_re.match(line):
                if isinstance(self,FortranCodeUnit) and not incontains: continue
                if hasattr(self,'subroutines'):
                    self.subroutines.append(FortranSubroutine(source,
                                            self._subroutine_re.match(line),self,
                                            permission))
                else:
                    raise Exception("Found SUBROUTINE in {}".format(type(self).__name__[7:].upper()))
            elif self._function_re.match(line):
                if isinstance(self,FortranCodeUnit) and not incontains: continue
                if hasattr(self,'functions'):
                    self.functions.append(FortranFunction(source,
                                          self._function_re.match(line),self,
                                          permission))
                else:
                    raise Exception("Found FUNCTION in {}".format(type(self).__name__[7:].upper()))
            elif self._type_re.match(line):
                if hasattr(self,'types'):
                    self.types.append(FortranType(source,self._type_re.match(line),
                                      self,permission))
                else:
                    raise Exception("Found derived TYPE in {}".format(type(self).__name__[7:].upper()))
            elif self._interface_re.match(line):
                if hasattr(self,'interfaces'):
                    self.interfaces.append(FortranInterface(source,
                                           self._interface_re.match(line),self,
                                           permission))
                else:
                    raise Exception("Found INTERFACE in {}".format(type(self).__name__[7:].upper()))
            elif self._boundproc_re.match(line) and incontains:
                if hasattr(self,'boundprocs'):
                    self.boundprocs.append(FortranBoundProcedure(source,
                                           self._boundproc_re.match(line),self,
                                           permission))
                else:
                    raise Exception("Found type-bound procedure in {}".format(type(self).__name__[7:].upper()))
            elif self._final_re.match(line) and incontains:
                if hasattr(self,'finalprocs'):
                    procedures = self._final_re.match(line).group(1).strip()
                    self.finalprocs.extend(self._split_re.split(procedures))
                else:
                    raise Exception("Found finalization procedure in {}".format(type(self).__name__[7:].upper()))
            elif self._variable_re.match(line):
                if hasattr(self,'variables'):
                    self.variables.extend(line_to_variables(source,line,
                                          permission,self))
                else:
                    raise Exception("Found variable in {}".format(type(self).__name__[7:].upper()))
            elif self._use_re.match(line):
                if hasattr(self,'uses'): 
                    self.uses.append(self._use_re.match(line).group(1))
                else:
                    raise Exception("Found USE statemnt in {}".format(type(self).__name__[7:].upper()))
            elif self._call_re.match(line):
                if hasattr(self,'calls'):
                    callval = self._call_re.match(line).group()
                    if self._call_re.match(line).group() not in self.calls: 
                        self.calls.append(callval)
                else:
                    raise Exception("Found procedure call in {}".format(type(self).__name__[7:].upper()))
            
        if not isinstance(self,FortranSourceFile):
            raise Exception("File ended while still nested.")
    
    def _cleanup(self):
        return
        
             
    
class FortranCodeUnit(FortranContainer):
    """
    A class on which programs, modules, functions, and subroutines are based.
    """
    def correlate(self,project):
        # Add procedures, interfaces and types from parent to our lists
        if hasattr(self.parent,'pub_procs'): self.pub_procs.extend(self.parent.pub_procs)
        if hasattr(self.parent,'procs'): self.procs.extend(self.parent.procs)
        #FIXME: It would be better to make the all_interfaces list contain only abstract interfaces, and to start building it during cleanup, as was done for procs
        if hasattr(self.parent,'interfaces'):
            self.all_interfaces = self.interfaces + self.parent.interfaces
        else:
            self.all_interfaces = self.interfaces + []
        if hasattr(self.parent,'all_types'):
            self.all_types = self.types + self.parent.all_types
        else:
            self.all_types = self.types + []
        
        # Add procedures and types from USED modules to our lists
        for mod in self.uses:
            if type(mod) == str: continue
            self.pub_procs.extend(mod.pub_procs)
            self.procs.extend(mod.pub_procs)
            self.all_interfaces.extend(mod.all_interfaces)
            self.all_types.extend(mod.all_types) 
        
        # Match up called procedures
        if hasattr(self,'calls'):
            for i in range(len(self.calls)):
                for proc in self.procs:
                    if self.calls[i] == proc.name:
                        self.calls[i] = proc
                        break
        
        # Recurse
        for func in self.functions:
            func.correlate(project)
        for subrtn in self.subroutines:
            subrtn.correlate(project)
        for dtype in self.types:
            dtype.correlate(project)
        for interface in self.interfaces:
            interface.correlate(project)
        for var in self.variables:
            var.correlate(project)
        if hasattr(self,'args'):
            for arg in self.args:
                #~ print arg, self.name
                arg.correlate(project)
        if hasattr(self,'retvar'):
            #~ print self.name, self.retvar, self.parent.parent.name
            #~ for var in self.variables:
                #~ print var.name
            self.retvar.correlate(project)

        # Prune anything which we don't want to be displayed
        if self.obj == 'module':
            self.functions = [ obj for obj in self.functions if obj.permission in project.display]
            self.subroutines = [ obj for obj in self.subroutines if obj.permission in project.display]
            self.types = [ obj for obj in self.types if obj.permission in project.display]
            self.interfaces = [ obj for obj in self.interfaces if obj.permission in project.display]
            self.variables = [ obj for obj in self.variables if obj.permission in project.display]
       
        
class FortranSourceFile(FortranContainer):
    """
    An object representing individual files containing Fortran code. A project
    will consist of a list of these objects. In tern, SourceFile objects will
    contains lists of all of that file's contents
    """
    def __init__(self,filepath):
        self.path = filepath.strip()
        self.name = os.path.basename(self.path)
        self.parent = None
        self.modules = []
        self.functions = []
        self.subroutines = []
        self.programs = []
        self.doc = []
        self.hierarchy = []
        self.obj = 'sourcefile'
        source = ford.reader.FortranReader(self.path)
        FortranContainer.__init__(self,source,"")
        readobj = open(self.path,'r')
        self.src = readobj.read()
        #~ self.src = highlight(self.src,FortranLexer(),HtmlFormatter(linenos=True))
        # TODO: Get line-numbers working in such a way that it will look right with Bootstrap CSS
        self.src = highlight(self.src,FortranLexer(),HtmlFormatter())



class FortranModule(FortranCodeUnit):
    """
    An object representing individual modules within your source code. These
    objects contains lists of all of the module's contents, as well as its 
    dependencies.
    """
    def _initialize(self,line):
        self.name = line.group(1)
        # TODO: Add the ability to parse ONLY directives and procedure renaming
        self.uses = []
        self.variables = []
        self.public_list = []
        self.private_list = []
        self.protected_list = []
        self.subroutines = []
        self.functions = []
        self.interfaces = []
        self.types = []

    def _cleanup(self):
        # Create list of all local procedures. Ones coming from other modules
        # will be added later, during correlation.
        self.procs = self.functions + self.subroutines
        self.pub_procs = []
        for interface in self.interfaces:
            if interface.name:
                self.procs.append(interface)
            elif not interface.abstract:
                self.procs.extend(interface.functions)
                self.procs.extend(interface.subroutines)

        for name in self.public_list:
            for var in self.variables + self.procs + self.types + self.interfaces:
                if name.lower() == var.name.lower():
                    var.permission = "public"
        for name in self.private_list:
            for var in self.variables + self.procs + self.types + self.interfaces:
                if name.lower() == var.name.lower():
                    var.permission = "private"
        for varname in self.protected_list:
            for var in self.variables:
                if varname.lower() == var.name.lower():
                    var.permission = "protected"

        for proc in self.procs:
            if proc.permission == "public": self.pub_procs.append(proc)

        del self.public_list
        del self.private_list
        del self.protected_list
        return

        
    
class FortranSubroutine(FortranCodeUnit):
    """
    An object representing a Fortran subroutine and holding all of said 
    subroutine's contents.
    """
    def _initialize(self,line):
        self.proctype = 'Subroutine'
        self.name = line.group(2)
        attribstr = line.group(1)
        if not attribstr: attribstr = ""
        self.attribs = []
        if attribstr.find("pure") >= 0:
            self.attribs.append("pure")
            attribstr = attribstr.replace("pure","",1)
        if attribstr.find("elemntal") >= 0:
            self.attribs.append("elemental")
            attribstr = attribstr.replace("elemental","",1)
        if attribstr.find("recursive") >= 0:
            self.attribs.append("recursive")
            attribstr = attribstr.replace("recursive","",1)
        attribstr = re.sub(" ","",attribstr)
        self.name = line.group(2)
        self.args = []
        if line.group(3):
            if self._split_re.split(line.group(3)[1:-1]):
                for arg in self._split_re.split(line.group(3)[1:-1]):
                    if arg != '': self.args.append(arg.strip())
        self.bindC = bool(line.group(4))
        self.variables = []
        self.uses = []
        self.calls = []
        self.optional_list = []
        self.subroutines = []
        self.functions = []
        self.interfaces = []
        self.types = []

    def _cleanup(self):
        self.procs = self.functions + self.subroutines
        self.pub_procs = []
        for interface in self.interfaces:
            if interface.name:
                self.procs.append(interface)
            elif not interface.abstract:
                self.procs.extend(interface.functions)
                self.procs.extend(interface.subroutines)

        for varname in self.optional_list:
            for var in self.variables:
                if varname.lower() == var.name.lower(): 
                    var.permission = "protected"
                    break
        del self.optional_list
        for i in range(len(self.args)):
            for var in self.variables:
                if self.args[i].lower() == var.name.lower():
                    self.args[i] = var
                    self.variables.remove(var)
                    break
            if type(self.args[i]) == str:
                for intr in self.interfaces:
                    for proc in intr.subroutines + intr.functions:
                        if proc.name.lower() == self.args[i].lower():
                            self.args[i] = proc
                            if proc.proctype == 'Subroutine': intr.subroutines.remove(proc)
                            else: intr.functions.remove(proc)
                            if len(intr.subroutines + intr.functions) < 1:
                                self.interfaces.remove(intr)
                            self.args[i].parent = self
                            break

        return
    
    
class FortranFunction(FortranCodeUnit):
    """
    An object representing a Fortran function and holding all of said function's
    contents.
    """
    def _initialize(self,line):
        self.proctype = 'Function'
        self.name = line.group(2)
        attribstr = line.group(1)
        if not attribstr: attribstr = ""
        self.attribs = []
        if attribstr.find("pure") >= 0:
            self.attribs.append("pure")
            attribstr = attribstr.replace("pure","",1)
        if attribstr.find("elemntal") >= 0:
            self.attribs.append("elemental")
            attribstr = attribstr.replace("elemental","",1)
        if attribstr.find("recursive") >= 0:
            self.attribs.append("recursive")
            attribstr = attribstr.replace("recursive","",1)
        attribstr = re.sub(" ","",attribstr)
        if line.group(4):
            self.retvar = line.group(4)
        else:
            self.retvar = self.name
        if _var_type_re.search(attribstr):
            rettype, retkind, retlen, retproto, rest =  parse_type(attribstr,self.strings)
            self.retvar = FortranVariable(self.retvar,rettype,self.parent,
                                          kind=retkind,strlen=retlen,
                                          proto=retproto)
        self.args = [] # Set this in the correlation step
        
        for arg in self._split_re.split(line.group(3)[1:-1]):
            # FIXME: This is to avoid a problem whereby sometimes an empty argument list will appear to contain the argument ''. I didn't know why it would do this (especially since sometimes it works fine) and just put this in as a quick fix. However, at some point I should try to figure out the actual root of the problem.
            if arg != '': self.args.append(arg.strip())
        self.bindC = bool(line.group(5))
        self.variables = []
        self.uses = []
        self.calls = []
        self.optional_list = []
        self.subroutines = []
        self.functions = []
        self.interfaces = []
        self.types = []

    def _cleanup(self):
        self.procs = self.functions + self.subroutines
        self.pub_procs = []
        for interface in self.interfaces:
            if interface.name:
                procs.append(interface)
            elif not interface.abstract:
                procs.extend(interface.functions)
                procs.extend(interface.subroutines)

        for varname in self.optional_list:
            for var in self.variables:
                if varname.lower() == var.name.lower():
                    var.permission = "protected"
                    break
        del self.optional_list
        for i in range(len(self.args)):
            for var in self.variables:
                if self.args[i].lower() == var.name.lower():
                    self.args[i] = var
                    self.variables.remove(var)
                    break
            if type(self.args[i]) == str:
                for intr in self.interfaces:
                    for proc in intr.subroutines + intr.functions:
                        if proc.name.lower() == self.args[i].lower():
                            self.args[i] = proc
                            if proc.proctype == 'Subroutine': intr.subroutines.remove(proc)
                            else: intr.functions.remove(proc)
                            if len(intr.subroutines + intr.functions) < 1:
                                self.interfaces.remove(intr)
                            self.args[i].parent = self
                            break
        if type(self.retvar) != FortranVariable:
            for var in self.variables:
                if var.name.lower() == self.retvar.lower():
                    self.retvar = var
                    self.variables.remove(var)
                    break

        return
        
        
    
class FortranProgram(FortranCodeUnit):
    """
    An object representing the main Fortran program.
    """
    def _initialize(self,line):
        self.name = line.group(1)
        self.variables = []
        self.subroutines = []
        self.functions = []
        self.interfaces = []
        self.types = []
        self.uses = []
        self.calls = []
    
    def _cleanup(self):
        self.procs = self.functions + self.subroutines
        self.pub_procs = []
        for interface in self.interfaces:
            if interface.name:
                procs.append(interface)
            elif not interface.abstract:
                procs.extend(interface.functions)
                procs.extend(interface.subroutines)

    
    
class FortranType(FortranContainer):
    """
    An object representing a Fortran derived type and holding all of said type's
    components and type-bound procedures. It also contains information on the
    type's inheritance.
    """
    def _initialize(self,line):
        self.name = line.group(2)
        self.extends = None
        self.attributes = []
        if line.group(1):
            attribstr = line.group(1)[1:].strip()
            attriblist = self._split_re.split(attribstr.strip())
            for attrib in attriblist:
                if _extends_re.search(attrib):
                    self.extends = _extends_re.search(attrib).group(1)
                elif attrib.strip().lower() == "public":
                    self.permission = "public"
                elif attrib.strip().lower() == "private":
                    self.permission = "private"
                else:
                    self.attributes.append(attrib.strip())
        if line.group(3):
            paramstr = line.group(3).strip()
            self.parameters = self._split_re(paramstr)
        else:
            self.parameters = []
        self.sequence = False
        self.variables = []
        self.boundprocs = []
        self.finalprocs = []
        self.constructor = None
        
        
    def _cleanup(self):
        # Match parameters with variables
        for i in range(len(self.parameters)):
            for var in self.variables:
                if self.parameters[i].lower() == var.name.lower():
                    self.parameters[i] = var
                    self.variables.remove(var)
                    break

        
    def correlate(self,project):
        self.all_interfaces = self.parent.all_interfaces
        self.all_types = self.parent.all_types
        self.procs = self.parent.procs
        # Get type of extension
        if self.extends:
            for dtype in self.all_types:
                if dtype.name.lower() == self.extends.lower():
                    self.extends = dtype
                    break
        # Match variables as needed (recurse)
        for i in range(len(self.variables)-1,-1,-1):
            if self.variables[i].permission in project.display:
                self.variables[i].correlate(project)
            else:
                del self.variables[i]
        # Match boundprocs with procedures
        for proc in self.boundprocs:
            if proc.permission in project.display:
                proc.correlate(project)
            else:
                self.boundprocs.remove(proc)
        # Match finalprocs
        for i in range(len(self.finalprocs)):
            for proc in self.procs:
                if proc.name.lower() == self.finalprocs[i].lower():
                    self.finalprocs[i] = proc
                    break
        # Find a constructor, if one exists
        for proc in self.procs:
            if proc.name.lower() == self.name.lower():
                self.constructor = proc
                break
        
    
class FortranInterface(FortranContainer):
    """
    An object representing a Fortran interface.
    """
    def _initialize(self,line):
        self.proctype = 'Interface'
        self.abstract = bool(line.group(1))
        self.name = line.group(2)
        self.hasname = bool(self.name)
        self.subroutines = []
        self.functions = []
        self.modprocs = []

    def correlate(self,project):
        if self.abstract: return
        self.all_interfaces = self.parent.all_interfaces
        self.all_types = self.parent.all_types
        self.procs = self.parent.procs
        if not self.hasname:
            contents = self.subroutines + self.functions
            self.name = contents[0].name
        for modproc in self.modprocs:
            for proc in self.procs:
                if modproc.name.lower() == proc.name.lower():
                    modproc.procedure = proc
                    break
        for subrtn in self.subroutines:
            subrtn.correlate(project)
            #~ for proc in self.parent.procs:
                #~ if subrtn.name.lower() == proc.name.lower():
                    #~ subrtn.procedure = proc
                    #~ break
        for func in self.functions:
            func.correlate(project)
            #~ for proc in self.parent.procs:
                #~ if func.name.lower() == proc.name.lower():
                    #~ func.procedure = proc
                    #~ break
                    
    
    
class FortranVariable(FortranBase):
    """
    An object representing a variable within Fortran.
    """
    def __init__(self,name,vartype,parent,attribs=[],intent="inout",
                 optional=False,permission="public",parameter=False,kind=None,
                 strlen=None,proto=None,doc=[],points=False,initial=None):
        self.name = name
        self.vartype = vartype.lower()
        self.parent = parent
        if self.parent:
            self.parobj = self.parent.obj
        self.obj = type(self).__name__[7:].lower()
        self.attribs = attribs
        self.intent = intent
        self.optional = optional
        self.kind = kind
        self.strlen = strlen
        self.proto = proto
        self.doc = doc
        self.permission = permission
        self.points = points
        self.parameter = parameter
        self.doc = []
        self.initial = initial
        self.dimension = ''
        index = self.name.find('(')
        if index > 0 :
            self.dimension = self.name[index:]
            self.name = self.name[0:index]

    def correlate(self,project):
        if self.proto and self.proto[0] == '*': self.proto[0] = '*'
        if (self.vartype == "type" or self.vartype == "class") and self.proto and self.proto[0] != '*':
            for dtype in self.parent.all_types:
                if dtype.name.lower() == self.proto[0].lower(): 
                    self.proto[0] = dtype
                    break
        elif self.vartype == "procedure" and self.proto:
            for proc in self.parent.procs:
                if proc.name.lower() == self.proto.lower():
                    self.proto = proc
                    break
            if type(self.proto) == str:
                for interface in self.parent.all_interfaces:
                    if interface.abstract:
                        for proc in interface.subroutines + interface.functions:
                            if proc.name.lower() == self.proto.lower():
                                self.proto = interface
                                break
            


class FortranBoundProcedure(FortranBase):
    """
    An object representing a type-bound procedure, possibly overloaded.
    """
    def _initialize(self,line):
        attribstr = line.group(3)
        self.attribs = []
        if attribstr:
            tmp_attribs = paren_split(",",attribstr[1:])
            for i in range(len(tmp_attribs)):
                tmp_attribs[i] = tmp_attribs[i].strip()
                if tmp_attribs[i].lower() == "public": self.permission = "public"
                elif tmp_attribs[i].lower() == "private": self.permission = "private"
                else: self.attribs.append(tmp_attribs[i])
        rest = line.group(4)
        split = self._point_to_re.split(rest)
        self.name = split[0]
        self.generic = (line.group(1).lower() == "generic")
        self.bindings = []
        if len(split) > 1:
            binds = self._split_re.split(split[1])
            for bind in binds:
                self.bindings.append(bind.strip())
        else:
            self.bindings.append(self.name)
        if line.group(2):
            self.prototype = line.group(2)[1:-1]
        else:
            self.prototype = None

    def correlate(self,project):
        self.procs = self.parent.procs
        for i in range(len(self.bindings)):
            for proc in self.procs:
                if proc.name.lower() == self.bindings[i].lower():
                    self.bindings[i] = proc
                    break
        
        

class FortranModuleProcedure(FortranBase):
    """
    An object representing a module procedure procedure.
    """
    def __init__(self,name,parent=None,inherited_permission=None):
        if inherited_permission:
            self.permission = inherited_permission.lower()
        else:
            self.permission = None
        self.parent = parent
        if self.parent:
            self.parobj = self.parent.obj
        self.obj = 'moduleprocedure'
        self.name = name
        self.procedure = None
        self.doc = []
        self.hierarchy = []
        cur = self.parent
        while cur:
            self.hierarchy.append(cur)
            cur = cur.parent
        self.hierarchy.reverse()
                

_can_have_contains = [FortranModule,FortranProgram,FortranFunction,
                      FortranSubroutine,FortranType]
        
def line_to_variables(source, line, inherit_permission, parent):
    """
    Returns a list of variables declared in the provided line of code. The
    line of code should be provided as a string.
    """
    vartype, kind, strlen, proto, rest = parse_type(line,parent.strings)
    attribs = []
    intent = "inout"
    optional = False
    permission = inherit_permission
    parameter = False
    
    attribmatch = _attribsplit_re.match(rest)
    if attribmatch:
        attribstr = attribmatch.group(1).strip()
        declarestr = attribmatch.group(2).strip()
        tmp_attribs = paren_split(",",attribstr)
        for i in range(len(tmp_attribs)):
            tmp_attribs[i] = tmp_attribs[i].strip()
            if tmp_attribs[i].lower() == "public": permission = "public"
            elif tmp_attribs[i].lower() == "private": permission = "private"
            elif tmp_attribs[i].lower() == "protected": permission = "protected"
            elif tmp_attribs[i].lower() == "optional": optional = True
            elif tmp_attribs[i].lower() == "parameter": parameter = True
            elif tmp_attribs[i].lower().replace(' ','') == "intent(in)":
                intent = 'in'
            elif tmp_attribs[i].lower().replace(' ','') == "intent(out)":
                intent = 'out'
            elif tmp_attribs[i].lower().replace(' ','') == "intent(inout)":
                pass
            else: attribs.append(tmp_attribs[i])
    else:
        declarestr = _attribsplit2_re.match(rest).group(2)
    declarations = paren_split(",",declarestr)

    varlist = []
    for dec in declarations:
        dec = re.sub(" ","",dec)
        split = paren_split('=',dec)
        if len(split) > 1:
            if split[1][0] == '>':
                name = split[0]
                initial = split[1][1:]
                points = True
            else:
                name = split[0]
                initial = split[1]
                points = False
        else:
            name = dec.strip()
            initial = None
            points = False
            
        if initial and vartype == "character":
            match = _quotes_re.search(initial)
            if match:
                num = int(match.group()[1:-1])
                initial = _quotes_re.sub(parent.strings[num],initial)
            
        if proto:
            varlist.append(FortranVariable(name,vartype,parent,attribs,intent,
                           optional,permission,parameter,kind,strlen,list(proto),
                           [],points,initial))
        else:
            varlist.append(FortranVariable(name,vartype,parent,attribs,intent,
                           optional,permission,parameter,kind,strlen,proto,
                           [],points,initial))
        
    doc = []
    docline = source.next()
    while docline[0:2] == "!!":
        doc.append(docline[2:])
        docline = source.next()
    source.pass_back(docline)
    varlist[-1].doc = doc
    return varlist
    
    

def parse_type(string,capture_strings):
    """
    Gets variable type, kind, length, and/or derived-type attributes from a 
    variable declaration.
    """
    match = _var_type_re.match(string)
    if not match: raise Exception("Invalid variable declaration: {}".format(string))
    
    vartype = match.group().lower()
    if _double_prec_re.match(vartype): vartype = "double precision"
    rest = string[match.end():].strip()
    kindstr = get_parens(rest)
    rest = rest[len(kindstr):].strip()

    # FIXME: This won't work for old-fashioned REAL*8 type notations
    if len(kindstr) < 3 and vartype != "type" and vartype != "class":
        return (vartype, None, None, None, rest)
    match = _var_kind_re.search(kindstr)
    if match:
        if match.group(1):
            star = False
            args = match.group(1).strip()
        else:
            star = True
            args = match.group(2).strip()

        args = re.sub("\s","",args)
        if vartype == "type" or vartype == "class" or vartype == "procedure":
            _proto_re = re.compile("(\*|\w+)\s*(?:\((.*)\))?")
            try:
                proto = list(_proto_re.match(args).groups())
                if not proto[1]: proto[1] = ''
            except:
                raise Exception("Bad type, class, or procedure prototype specification: {}".format(args))
            return (vartype, None, None, proto, rest)
        elif vartype == "character":
            if star:
                return (vartype, None, args[1], None, rest)
            else:
                kind = None
                length = None
                if _kind_re.search(args):
                    kind = _kind_re.sub("",args)
                    try:
                        match = _quotes_re.search(kind)
                        num = int(match.group()[1:-1])
                        kind = _quotes_re.sub(captured_strings[num],kind)
                    except:
                        pass
                elif _len_re.search(args):
                    length = _len_re.sub("",args)
                else:
                    length = args
                return (vartype, kind, length, None, rest)
        else: 
            kind = _kind_re.sub("",args)
            return (vartype, kind, None, None, rest)

    raise Exception("Bad declaration of variable type {}: {}".format(vartype,string))
    
    
    
def get_parens(line):
    """
    Takes a string starting with an open parenthesis and returns the portion
    of the string going to the corresponding close parenthesis.
    """
    if len(line) == 0: return line
    parenstr = ''
    level = 0
    blevel = 0
    for char in line:
        if char == '(':
            level += 1
        elif char == ')':
            level -= 1
        elif char == '[':
            blevel += 1
        elif char == ']':
            blevel -= 1
        elif (char.isalpha() or char == '_' or char == ':' or char == ',' 
          or char == ' ') and level == 0 and blevel == 0:
            return parenstr
        parenstr = parenstr + char
    
    if level == 0 and blevel == 0: return parenstr    
    raise Exception("Couldn't parse parentheses: {}".format(line))



def paren_split(sep,string):
    """
    Splits the string into pieces divided by sep, when sep is outside of parentheses.
    """
    if len(sep) != 1: raise Exception("Separation string must be one character long")
    retlist = []
    level = 0
    left = 0
    for i in range(len(string)):
        if string[i] == "(": level += 1
        elif string[i] == ")": level -= 1
        elif string[i] == sep and level == 0:
            retlist.append(string[left:i])
            left = i+1
    retlist.append(string[left:])
    return retlist


def set_base_url(url):
    FortranBase.base_url = url

def get_mod_procs(source,line,parent):
    inherit_permission = parent.permission
    retlist = []
    _split_re = re.compile("\s*,\s*",re.IGNORECASE)
    splitlist = _split_re.split(line.group(1))
    if splitlist and len(splitlist) > 0:
        for item in splitlist:
            retlist.append(FortranModuleProcedure(item,parent,inherit_permission))
    else:
        retlist.append(FortranModuleProcedure(line.group(1),parent,inherit_permission))
    
    doc = []
    docline = source.next()
    while docline[0:2] == "!!":
        doc.append(docline[2:])
        docline = source.next()
    source.pass_back(docline)
    retlist[-1].doc = doc
    
    return retlist
