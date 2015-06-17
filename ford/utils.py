#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  utils.py
#  
#  Copyright 2015 Christopher MacMackin <cmacmackin@gmail.com>
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

NOTE_RE = re.compile("@note\s*(.*?)\s*</p>",re.IGNORECASE|re.DOTALL)
WARNING_RE = re.compile("@warning\s*(.*?)\s*</p>",re.IGNORECASE|re.DOTALL)
TODO_RE = re.compile("@todo\s*(.*?)\s*</p>",re.IGNORECASE|re.DOTALL)
BUG_RE = re.compile("@bug\s*(.*?)\s*</p>",re.IGNORECASE|re.DOTALL)
LINK_RE = re.compile("\[\[(\w+)(?:\((\w+)\))?(?::(\w+)(?:\((\w+)\))?)?\]\]")


def sub_notes(docs):
    """
    Substitutes the special controls for notes, warnings, todos, and bugs with
    the corresponding div.
    """
    while NOTE_RE.search(docs):
        docs = NOTE_RE.sub("<div class=\"alert alert-info\" role=\"alert\"><h4>Note</h4>\g<1></div></p>",docs)
        
    while WARNING_RE.search(docs):
        docs = WARNING_RE.sub("<div class=\"alert alert-warning\" role=\"alert\"><h4>Warning</h4>\g<1></div></p>",docs)
    
    while TODO_RE.search(docs):
        docs = TODO_RE.sub("<div class=\"alert alert-success\" role=\"alert\"><h4>ToDo</h4>\g<1></div></p>",docs)
    
    while BUG_RE.search(docs):
        docs = BUG_RE.sub("<div class=\"alert alert-danger\" role=\"alert\"><h4>Bug</h4>\g<1></div></p>",docs)

    return docs



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
    blevel = 0
    left = 0
    for i in range(len(string)):
        if string[i] == "(": level += 1
        elif string[i] == ")": level -= 1
        elif string[i] == "[": blevel += 1
        elif string[i] == "]": blevel -= 1
        elif string[i] == sep and level == 0 and blevel == 0:
            retlist.append(string[left:i])
            left = i+1
    retlist.append(string[left:])
    return retlist



def quote_split(sep,string):
    """
    Splits the strings into pieces divided by sep, when sep in not inside quotes.
    """
    if len(sep) != 1: raise Exception("Separation string must be one character long")
    retlist = []
    squote = False
    dquote = False
    left = 0
    i = 0
    while i < len(string):
        if string[i] == '"' and not dquote:
            if not squote:
                squote = True
            elif (i+1) < len(string) and string[i+1] == '"':
                i += 1
            else:
                squote = False
        elif string[i] == "'" and not squote:
            if not dquote:
                dquote = True
            elif (i+1) < len(string) and string[i+1] == "'":
                i += 1
            else:
                dquote = False            
        elif string[i] == sep and not dquote and not squote:
            retlist.append(string[left:i])
            left = i + 1
        i += 1
    retlist.append(string[left:])
    return retlist


def split_path(path):
    '''
    Splits the argument into its constituent directories and returns them as
    a list.
    '''
    def recurse_path(path,retlist):
        if len(retlist) > 10: exit(0)
        head, tail = os.path.split(path)
        if len(tail) > 0:
            retlist.insert(0,tail)
            recurse_path(head,retlist)
        elif len(head) > 1:
            recurse_path(head,retlist)
        else:
            return

    retlist = []
    path = os.path.realpath(os.path.normpath(path))
    drive, path = os.path.splitdrive(path)
    if len(drive) > 0: retlist.append(drive)
    recurse_path(path,retlist)
    return retlist


def sub_links(string,project):
    '''
    Replace links to different parts of the program, formatted as
    [[name]] or [[name(object-type)]] with the appropriate URL. Can also
    link to an item's entry in another's page with the syntax
    [[parent-name:name]]. The object type can be placed in parentheses
    for either or both of these parts.
    '''
    LINK_TYPES    = { 'module': 'modules',
                      'type': 'types',
                      'procedure': 'procedures',
                      'subroutine': 'procedures',
                      'function': 'procedures',
                      'proc': 'procedures',
                      'file': 'files',
                      'interface': 'absinterfaces',
                      'absinterface': 'absinterfaces',
                      'program': 'programs' }
        
    SUBLINK_TYPES = { 'variable': 'variables',
                      'type': 'types',
                      'constructor': 'constructor',
                      'interface': 'interfaces',
                      'absinterface': 'absinterfaces',
                      'subroutine': 'subroutines',
                      'function': 'functions',
                      'final': 'finalprocs',
                      'bound': 'boundprocs',
                      'modproc': 'modprocs' }
    SUBLINK_ABBR  = { 'variable': 'var',
                      'constructor': 'intr',
                      'interface': 'intr',
                      'absinterface': 'intr',
                      'type': 'type',
                      'subroutine': 'proc',
                      'function': 'proc',
                      'final': 'fp',
                      'bound': 'bp',
                      'modproc': 'proc' }
    
    
    def get_abbr(obj,parobj):
        if obj == getattr(parobj,'constructor',None):
            return SUBLINK_ABBR['constructor']
        for key, val in SUBLINK_TYPES.items():
            if val != 'constructor' and obj in getattr(parobj,val,[]):
                return SUBLINK_ABBR[key]
        
    
    def convert_link(match):
        ERR = 'Warning: Could not substitute link {}. {}'
        url = ''
        name = ''
        found = False
        searchlist = []
        item = None
        
        #[name,obj,subname,subobj]
        if not match.group(2):
            for key, val in LINK_TYPES.items():
                searchlist.extend(getattr(project,val))
        else:
            if match.group(2).lower() in LINK_TYPES:
                searchlist.extend(getattr(project,LINK_TYPES[match.group(2).lower()]))
            else:
                print(ERR.format(match.group(),'Unrecognized classification "{}".'.format(match.group(2))))
                return match.group()
        
        for obj in searchlist:
            if match.group(1).lower() == obj.name.lower():
                url = obj.get_url()
                name = obj.name
                found = True
                item = obj
                break
        else:
            print(ERR.format(match.group(),'"{}" not found.'.format(match.group(1))))
        
        if found and match.group(3):
            searchlist = []
            # TODO: Need to add code to check that item actually has these attributes. In particular, the default behaviour WILL NOT be safe.
            if not match.group(4):
                for key, val in SUBLINK_TYPES.items():
                    if val == 'constructor':
                        if hasattr(item,'constructor'):
                            searchlist.append(item.constructor)
                        else:
                            continue
                    else:
                        searchlist.extend(getattr(item,val,[]))
            else:
                if match.group(4).lower() in SUBLINK_TYPES:
                    if hasattr(item,SUBLINK_TYPES[match.group(4).lower()]):
                        if match.group(4).lower == 'constructor':
                            searchlist.append(item.constructor)
                        else:
                            searchlist.extend(getattr(item,SUBLINK_TYPES[match.group(4).lower()]))
                    else:
                        print(ERR.format(match.group(),'"{}" can not be contained in "{}"'.format(match.group(4),item.obj)))
                        return match.group()
                else:
                    print(ERR.format(match.group(),'Unrecognized classification "{}".'.format(match.group(2))))
                    return match.group()
        
            
            for obj in searchlist:
                if match.group(3).lower() == obj.name.lower():
                    url = url + '#' + get_abbr(obj,item) + '-' + obj.name
                    name = obj.name
                    item = obj
                    break
            else:
                print(ERR.format(match.group(),'"{0}" not found in "{1}", linking to page for "{1}" instead.'.format(match.group(3),name)))
        
        if found:
            return '<a href="{}">{}</a>'.format(url,name)
        else:
            return match.group()

    # Get information from links (need to build an RE)
    string = LINK_RE.sub(convert_link,string)
    return string


def sub_macros(string,base_url):
    '''
    Replaces macros in documentation with their appropriate values. These macros
    are used for things like providing URLs.
    '''
    macros = { '|url|': base_url,
               '|media|': os.path.join(base_url,'media'),
               '|page|': os.path.join(base_url,'page')
             }
    for key, val in macros.items():
        string = string.replace(key,val)
    return string
