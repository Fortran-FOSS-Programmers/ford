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
import os.path
import json
import ford.sourceform
from urllib.request import urlopen, URLError
from urllib.parse import urljoin
import pathlib
from typing import Union


NOTE_TYPE = {
    "note": "info",
    "warning": "warning",
    "todo": "success",
    "bug": "danger",
    "history": "history",
}
NOTE_RE = [
    re.compile(
        r"@({})\s*(((?!@({})).)*?)@end\1\s*(</p>)?".format(
            note, "|".join(NOTE_TYPE.keys())
        ),
        re.IGNORECASE | re.DOTALL,
    )
    for note in NOTE_TYPE
] + [
    re.compile(r"@({})\s*(.*?)\s*</p>".format(note), re.IGNORECASE | re.DOTALL)
    for note in NOTE_TYPE
]
LINK_RE = re.compile(r"\[\[(\w+(?:\.\w+)?)(?:\((\w+)\))?(?::(\w+)(?:\((\w+)\))?)?\]\]")


# Dictionary for all macro definitions to be used in the documentation.
# Each key of the form |name| will be replaced by the value found in the
# dictionary in sub_macros.
_MACRO_DICT = {}


def sub_notes(docs):
    """
    Substitutes the special controls for notes, warnings, todos, and bugs with
    the corresponding div.
    """

    def substitute(match):
        ret = (
            '</p><div class="alert alert-{}" role="alert"><h4>{}</h4>'
            "<p>{}</p></div>".format(
                NOTE_TYPE[match.group(1).lower()],
                match.group(1).capitalize(),
                match.group(2),
            )
        )
        if len(match.groups()) >= 4 and not match.group(4):
            ret += "\n<p>"
        return ret

    for regex in NOTE_RE:
        docs = regex.sub(substitute, docs)
    return docs


def get_parens(line, retlevel=0, retblevel=0):
    """
    By default akes a string starting with an open parenthesis and returns the portion
    of the string going to the corresponding close parenthesis. If retlevel != 0 then
    will return when that level (for parentheses) is reached. Same for retblevel.
    """
    if len(line) == 0:
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
            (char.isalpha() or char == "_" or char == ":" or char == "," or char == " ")
            and level == retlevel
            and blevel == retblevel
        ):
            return parenstr
        parenstr = parenstr + char

    if level == retlevel and blevel == retblevel:
        return parenstr
    raise RuntimeError("Couldn't parse parentheses: {}".format(line))


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


def sub_links(string, project):
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
        if not match.group(2):
            for key, val in LINK_TYPES.items():
                searchlist.extend(getattr(project, val))
        else:
            if match.group(2).lower() in LINK_TYPES:
                searchlist.extend(getattr(project, LINK_TYPES[match.group(2).lower()]))
            else:
                print(
                    ERR.format(
                        match.group(),
                        'Unrecognized classification "{}".'.format(match.group(2)),
                    )
                )
                return match.group()

        for obj in searchlist:
            if match.group(1).lower() == obj.name.lower():
                url = obj.get_url()
                name = obj.name
                found = True
                item = obj
                break
        else:
            print(ERR.format(match.group(), '"{}" not found.'.format(match.group(1))))
            url = ""
            name = match.group(1)

        if found and match.group(3):
            searchlist = []
            if not match.group(4):
                for key, val in SUBLINK_TYPES.items():
                    if val == "constructor":
                        if getattr(item, "constructor", False):
                            searchlist.append(item.constructor)
                        else:
                            continue
                    else:
                        searchlist.extend(getattr(item, val, []))
            else:
                if match.group(4).lower() in SUBLINK_TYPES:
                    if hasattr(item, SUBLINK_TYPES[match.group(4).lower()]):
                        if match.group(4).lower() == "constructor":
                            if item.constructor:
                                searchlist.append(item.constructor)
                        else:
                            searchlist.extend(
                                getattr(item, SUBLINK_TYPES[match.group(4).lower()])
                            )
                    else:
                        print(
                            ERR.format(
                                match.group(),
                                '"{}" can not be contained in "{}"'.format(
                                    match.group(4), item.obj
                                ),
                            )
                        )
                        return match.group()
                else:
                    print(
                        ERR.format(
                            match.group(),
                            'Unrecognized classification "{}".'.format(match.group(2)),
                        )
                    )
                    return match.group()

            for obj in searchlist:
                if match.group(3).lower() == obj.name.lower():
                    url = url + "#" + obj.anchor
                    name = obj.name
                    item = obj
                    break
            else:
                print(
                    ERR.format(
                        match.group(),
                        '"{0}" not found in "{1}", linking to page for "{1}" instead.'.format(
                            match.group(3), name
                        ),
                    )
                )

        if found:
            return '<a href="{}">{}</a>'.format(url, name)
        else:
            return "<a>{}</a>".format(name)

    # Get information from links (need to build an RE)
    string = LINK_RE.sub(convert_link, string)
    return string


def register_macro(string):
    """
    Register a new macro definition of the form 'key = value'.
    In the documentation |key| can then be used to represent value.
    If key is already defined in the list of macros an RuntimeError
    will be raised.
    The function returns a tuple of the form (value, key), where
    key is None if no key definition is found in the string.
    """

    if "=" not in string:
        raise RuntimeError("Error, no alias name provided for {0}".format(string))

    chunks = string.split("=", 1)
    key = "|{0}|".format(chunks[0].strip())
    val = chunks[1].strip()

    if key in _MACRO_DICT:
        # The macro is already defined. Do not overwrite it!
        # Can be ignored if the definition is the same...
        if val != _MACRO_DICT[key]:
            raise RuntimeError(
                'Could not register macro "{0}" as "{1}" because it is already defined as "{2}".'.format(
                    key, val, _MACRO_DICT[key]
                )
            )

    # Everything OK, add the macro definition to the dict.
    _MACRO_DICT[key] = val

    return (val, key)


def sub_macros(string):
    """
    Replaces macros in documentation with their appropriate values. These macros
    are used for things like providing URLs.
    """
    for key, val in _MACRO_DICT.items():
        string = string.replace(key, val)
    return string


def external(project, make=False, path="."):
    """
    Reads and writes the information needed for processing external modules.
    """
    from ford.sourceform import (
        ExternalModule,
        ExternalFunction,
        ExternalSubroutine,
        ExternalInterface,
        ExternalType,
        ExternalVariable,
    )

    # attributes of a module object needed for further processing
    ATTRIBUTES = [
        "pub_procs",
        "pub_absints",
        "pub_types",
        "pub_vars",
        "functions",
        "subroutines",
        "interfaces",
        "absinterfaces",
        "types",
        "variables",
    ]

    # Mapping between entity name and its type
    ENTITIES = {
        "module": ExternalModule,
        "interface": ExternalInterface,
        "type": ExternalType,
        "variable": ExternalVariable,
        "function": ExternalFunction,
        "subroutine": ExternalSubroutine,
    }

    def obj2dict(intObj):
        """
        Converts an object to a dictionary.
        """
        extDict = {
            "name": intObj.name,
            "external_url": intObj.get_url(),
            "obj": intObj.obj,
        }
        if hasattr(intObj, "proctype"):
            extDict["proctype"] = intObj.proctype
        if hasattr(intObj, "extends"):
            if isinstance(intObj.extends, ford.sourceform.FortranType):
                extDict["extends"] = obj2dict(intObj.extends)
            else:
                extDict["extends"] = intObj.extends
        for attrib in ATTRIBUTES:
            if not hasattr(intObj, attrib):
                continue

            attribute = getattr(intObj, attrib)

            if isinstance(attribute, str):
                extDict[attrib] = attribute
            elif isinstance(attribute, list):
                extDict[attrib] = [obj2dict(item) for item in attribute]
            elif isinstance(attribute, dict):
                extDict[attrib] = {key: obj2dict(val) for key, val in attribute.items()}
        return extDict

    def modules_from_local(url: pathlib.Path):
        """
        Get module information from an external project but on the
        local file system.
        Uses the io module to work in both, Python 2 and 3.
        """
        from io import open

        with open(url / "modules.json", mode="r", encoding="utf-8") as extfile:
            return json.loads(extfile.read())

    def dict2obj(extDict, url, parent=None, remote: bool = False) -> None:
        """
        Converts a dictionary to an object and immediately adds it to the project
        """
        name = extDict["name"]
        if extDict["external_url"]:
            extDict["external_url"] = extDict["external_url"].split("/", 1)[-1]
            if remote:
                external_url = urljoin(url, extDict["external_url"])
            else:
                external_url = url / extDict["external_url"]
        else:
            external_url = extDict["external_url"]

        # Look up what type of entity this is
        obj_type = extDict.get("proctype", extDict["obj"]).lower()
        # Construct the entity
        extObj: FortranBase = ENTITIES[obj_type](name, external_url, parent)
        # Now add it to the correct project list
        project_list = getattr(project, extObj._project_list)
        project_list.append(extObj)

        if obj_type == "interface":
            extObj.proctype = extDict["proctype"]
        elif obj_type == "type":
            extObj.extends = extDict["extends"]

        for key in ATTRIBUTES:
            if key not in extDict:
                continue
            if isinstance(extDict[key], str):
                setattr(extObj, key, extDict[key])
            elif isinstance(extDict[key], list):
                tmpLs = [dict2obj(item, url, extObj, remote) for item in extDict[key]]
                setattr(extObj, key, tmpLs)
            elif isinstance(extDict[key], dict):
                tmpDict = {
                    key2: dict2obj(item, url, extObj, remote)
                    for key2, item in extDict[key].items()
                }
                setattr(extObj, key, tmpDict)

    if make:
        # convert internal module object to a JSON database
        extModules = [obj2dict(module) for module in project.modules]
        with open(os.path.join(path, "modules.json"), "w") as modFile:
            modFile.write(json.dumps(extModules))
    else:
        # get the external modules from the external URLs
        for urldef in project.external:
            # get the external modules from the external URL
            url, short = register_macro(urldef)
            remote = re.match("https?://", url)
            try:
                if remote:
                    # Ensure the URL ends with '/' to have urljoin work as
                    # intentend.
                    if url[-1] != "/":
                        url = url + "/"
                    extModules = json.loads(
                        urlopen(urljoin(url, "modules.json")).read().decode("utf8")
                    )
                else:
                    url = pathlib.Path(url).resolve()
                    extModules = modules_from_local(url)
            except (URLError, json.JSONDecodeError) as error:
                extModules = []
                print("Could not open external URL '{}', reason: {}".format(url, error))
            # convert modules defined in the JSON database to module objects
            for extModule in extModules:
                dict2obj(extModule, url, remote=remote)


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
