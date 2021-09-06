# -*- coding: utf-8 -*-
#
#  sourceform.py
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
import os.path
import copy

# Python 2 or 3:
if sys.version_info[0] > 2:
    from urllib.parse import quote
else:
    from urllib import quote

import toposort
from pygments import highlight
from pygments.lexers import FortranLexer, FortranFixedLexer, guess_lexer_for_filename
from pygments.formatters import HtmlFormatter

import ford.reader
import ford.utils

VAR_TYPE_STRING = r"^integer|real|double\s*precision|character|complex|double\s*complex|logical|type|class|procedure|enumerator"
VARKIND_RE = re.compile(r"\((.*)\)|\*\s*(\d+|\(.*\))")
KIND_RE = re.compile(r"kind\s*=\s*", re.IGNORECASE)
LEN_RE = re.compile(r"len\s*=\s*", re.IGNORECASE)
ATTRIBSPLIT_RE = re.compile(r",\s*(\w.*?)::\s*(.*)\s*")
ATTRIBSPLIT2_RE = re.compile(r"\s*(::)?\s*(.*)\s*")
ASSIGN_RE = re.compile(r"(\w+\s*(?:\([^=]*\)))\s*=(?!>)(?:\s*([^\s]+))?")
POINT_RE = re.compile(r"(\w+\s*(?:\([^=>]*\)))\s*=>(?:\s*([^\s]+))?")
EXTENDS_RE = re.compile(r"extends\s*\(\s*([^()\s]+)\s*\)", re.IGNORECASE)
DOUBLE_PREC_RE = re.compile(r"double\s+precision", re.IGNORECASE)
DOUBLE_CMPLX_RE = re.compile(r"double\s+complex", re.IGNORECASE)
QUOTES_RE = re.compile(r"\"([^\"]|\"\")*\"|'([^']|'')*'", re.IGNORECASE)
PARA_CAPTURE_RE = re.compile(r"<p>.*?</p>", re.IGNORECASE | re.DOTALL)
COMMA_RE = re.compile(r",(?!\s)")
NBSP_RE = re.compile(r" (?= )|(?<= ) ")
DIM_RE = re.compile(r"^\w+\s*(\(.*\))\s*$")

INTRINSICS = [
    "abort",
    "abs",
    "abstract",
    "access",
    "achar",
    "acos",
    "acosh",
    "adjustl",
    "adjustr",
    "aimag",
    "aint",
    "alarm",
    "all",
    "allocatable",
    "allocate",
    "allocated",
    "and",
    "anint",
    "any",
    "asin",
    "asinh",
    "assign",
    "associate",
    "associated",
    "asynchronous",
    "atan",
    "atan2",
    "atanh",
    "atomic_add",
    "atomic_and",
    "atomic_cas",
    "atomic_define",
    "atomic_fetch_add",
    "atomic_fetch_and",
    "atomic_fetch_or",
    "atomic_fetch_xor",
    "atomic_or",
    "atomic_ref",
    "atomic_xor",
    "backtrace",
    "backspace",
    "bessel_j0",
    "bessel_j1",
    "bessel_jn",
    "bessel_y0",
    "bessel_y1",
    "bessel_yn",
    "bge",
    "bgt",
    "bind",
    "bit_size",
    "ble",
    "block",
    "block data",
    "blt",
    "btest",
    "c_associated",
    "c_f_pointer",
    "c_f_procpointer",
    "c_funloc",
    "c_loc",
    "c_sizeof",
    "cabs",
    "call",
    "case",
    "case default",
    "cdabs",
    "ceiling",
    "char",
    "character",
    "chdir",
    "chmod",
    "class",
    "close",
    "cmplx",
    "codimension",
    "co_broadcast",
    "co_max",
    "co_min",
    "co_reduce",
    "co_sum",
    "command_argument_count",
    "common",
    "compiler_options",
    "compiler_version",
    "complex",
    "concurrent",
    "conjg",
    "contains",
    "contiguous",
    "continue",
    "cos",
    "cosh",
    "count",
    "cpu_time",
    "critical",
    "cshift",
    "cycle",
    "data",
    "ctime",
    "dabs",
    "date_and_time",
    "dble",
    "dcmplx",
    "deallocate",
    "deferred",
    "digits",
    "dim",
    "dimension",
    "do",
    "dlog",
    "dlog10",
    "dmax1",
    "dmin1",
    "dot_product",
    "double complex",
    "double precision",
    "dprod",
    "dreal",
    "dshiftl",
    "dshiftr",
    "dsqrt",
    "dtime",
    "elemental",
    "else",
    "else if",
    "elseif",
    "elsewhere",
    "end",
    "end associate",
    "end block",
    "end block data",
    "end critical",
    "end do",
    "end enum",
    "end forall",
    "end function",
    "end if",
    "end interface",
    "end module",
    "end program",
    "end select",
    "end submodule",
    "end subroutine",
    "end type",
    "end where",
    "endfile",
    "endif",
    "entry",
    "enum",
    "enumerator",
    "eoshift",
    "epsilon",
    "equivalence",
    "erf",
    "erfc",
    "erfc_scaled",
    "etime",
    "error stop",
    "execute_command_line",
    "exit",
    "exp",
    "exponent",
    "extends",
    "extends_type_of",
    "external",
    "fget",
    "fgetc",
    "final",
    "findloc",
    "fdate",
    "floor",
    "flush",
    "fnum",
    "forall",
    "format",
    "fput",
    "fputc",
    "fraction",
    "function",
    "free",
    "fseek",
    "fstat",
    "ftell",
    "gamma",
    "generic",
    "gerror",
    "getarg",
    "get_command",
    "get_command_argument",
    "getcwd",
    "getenv",
    "get_environment_variable",
    "go to",
    "goto",
    "getgid",
    "getlog",
    "getpid",
    "getuid",
    "gmtime",
    "hostnm",
    "huge",
    "hypot",
    "iabs",
    "iachar",
    "iall",
    "iand",
    "iany",
    "iargc",
    "ibclr",
    "ibits",
    "ibset",
    "ichar",
    "idate",
    "ieee_class",
    "ieee_copy_sign",
    "ieee_get_flag",
    "ieee_get_halting_mode",
    "ieee_get_rounding_mode",
    "ieee_get_status",
    "ieee_get_underflow_mode",
    "ieee_is_finite",
    "ieee_is_nan",
    "ieee_is_negative",
    "ieee_is_normal",
    "ieee_logb",
    "ieee_next_after",
    "ieee_rem",
    "ieee_rint",
    "ieee_scalb",
    "ieee_selected_real_kind",
    "ieee_set_flag",
    "ieee_set_halting_mode",
    "ieee_set_rounding_mode",
    "ieee_set_status",
    "ieee_support_datatype",
    "ieee_support_denormal",
    "ieee_support_divide",
    "ieee_support_flag",
    "ieee_support_halting",
    "ieee_support_inf",
    "ieee_support_io",
    "ieee_support_nan",
    "ieee_support_rounding",
    "ieee_support_sqrt",
    "ieee_support_standard",
    "ieee_support_underflow_control",
    "ieee_unordered",
    "ieee_value",
    "ieor",
    "ierrno",
    "if",
    "imag",
    "image_index",
    "implicit",
    "implicit none",
    "import",
    "include",
    "index",
    "inquire",
    "int",
    "integer",
    "intent",
    "interface",
    "intrinsic",
    "int2",
    "int8",
    "ior",
    "iparity",
    "irand",
    "is",
    "is_contiguous",
    "is_iostat_end",
    "is_iostat_eor",
    "isatty",
    "ishft",
    "ishftc",
    "isnan",
    "itime",
    "kill",
    "kind",
    "lbound",
    "lcobound",
    "leadz",
    "len",
    "len_trim",
    "lge",
    "lgt",
    "link",
    "lle",
    "llt",
    "lock",
    "lnblnk",
    "loc",
    "log",
    "log_gamma",
    "log10",
    "logical",
    "long",
    "lshift",
    "lstat",
    "ltime",
    "malloc",
    "maskl",
    "maskr",
    "matmul",
    "max",
    "max0",
    "maxexponent",
    "maxloc",
    "maxval",
    "mclock",
    "mclock8",
    "merge",
    "merge_bits",
    "min",
    "min0",
    "minexponent",
    "minloc",
    "minval",
    "mod",
    "module",
    "module procedure",
    "modulo",
    "move_alloc",
    "mvbits",
    "namelist",
    "nearest",
    "new_line",
    "nint",
    "non_overridable",
    "none",
    "nopass",
    "norm2",
    "not",
    "null",
    "nullify",
    "num_images",
    "only",
    "open",
    "or",
    "operator",
    "optional",
    "pack",
    "parameter",
    "parity",
    "pass",
    "pause",
    "pointer",
    "perror",
    "popcnt",
    "poppar",
    "precision",
    "present",
    "print",
    "private",
    "procedure",
    "product",
    "program",
    "protected",
    "public",
    "pure",
    "radix",
    "ran",
    "rand",
    "random_number",
    "random_seed",
    "range",
    "rank",
    "read",
    "real",
    "recursive",
    "rename",
    "repeat",
    "reshape",
    "result",
    "return",
    "rewind",
    "rewrite",
    "rrspacing",
    "rshift",
    "same_type_as",
    "save",
    "scale",
    "scan",
    "secnds",
    "second",
    "select",
    "select case",
    "select type",
    "selected_char_kind",
    "selected_int_kind",
    "selected_real_kind",
    "sequence",
    "set_exponent",
    "shape",
    "shifta",
    "shiftl",
    "shiftr",
    "sign",
    "signal",
    "sin",
    "sinh",
    "size",
    "sizeof",
    "sleep",
    "spacing",
    "spread",
    "sqrt",
    "srand",
    "stat",
    "stop",
    "storage_size",
    "submodule",
    "subroutine",
    "sum",
    "sync all",
    "sync images",
    "sync memory",
    "symlnk",
    "system",
    "system_clock",
    "tan",
    "tanh",
    "target",
    "then",
    "this_image",
    "time",
    "time8",
    "tiny",
    "trailz",
    "transfer",
    "transpose",
    "trim",
    "ttynam",
    "type",
    "type_as",
    "ubound",
    "ucobound",
    "umask",
    "unlock",
    "unlink",
    "unpack",
    "use",
    "value",
    "verify",
    "volatile",
    "wait",
    "where",
    "while",
    "write",
    "xor",
    "zabs",
]

base_url = ""


class FortranBase(object):
    """
    An object containing the data common to all of the classes used to represent
    Fortran data.
    """

    IS_SPOOF = False

    POINTS_TO_RE = re.compile(r"\s*=>\s*", re.IGNORECASE)
    SPLIT_RE = re.compile(r"\s*,\s*", re.IGNORECASE)
    SRC_CAPTURE_STR = r"^[ \t]*([\w(),*: \t]+?[ \t]+)?{0}([\w(),*: \t]+?)?[ \t]+{1}[ \t\n,(].*?end[ \t]*{0}[ \t]+{1}[ \t]*?(!.*?)?$"

    # ~ this regex is not working for the LINK and DOUBLE_LINK types

    base_url = ""
    pretty_obj = {
        "proc": "procedures",
        "type": "derived types",
        "sourcefile": "source files",
        "program": "programs",
        "module": "modules and submodules",
        "submodule": "modules and submodules",
        "interface": "abstract interfaces",
        "blockdata": "block data units",
    }

    def __init__(
        self, source, first_line, parent=None, inherited_permission=None, strings=[]
    ):
        self.visible = False
        if inherited_permission is not None:
            self.permission = inherited_permission.lower()
        else:
            self.permission = None
        self.strings = strings
        self.parent = parent
        if self.parent:
            self.parobj = self.parent.obj
            self.display = self.parent.display
            self.settings = self.parent.settings
        else:
            self.parobj = None
            self.display = None
            self.settings = None
        self.obj = type(self).__name__[7:].lower()
        if (
            self.obj == "subroutine"
            or self.obj == "function"
            or self.obj == "submoduleprocedure"
        ):
            self.obj = "proc"
        self._initialize(first_line)
        del self.strings
        self.doc = []
        line = source.__next__()
        while line[0:2] == "!" + self.settings["docmark"]:
            self.doc.append(line[2:])
            line = source.__next__()
        source.pass_back(line)
        self.hierarchy = []
        cur = self.parent
        while cur:
            self.hierarchy.append(cur)
            cur = cur.parent
        self.hierarchy.reverse()

    def get_dir(self):
        if (
            type(self)
            in [
                FortranSubroutine,
                ExternalSubroutine,
                FortranFunction,
                ExternalFunction,
            ]
            and type(self.parent) in [FortranInterface, ExternalInterface]
            and not self.parent.generic
        ):
            return "interface"
        elif type(self) is FortranSubmodule:
            return "module"
        elif type(self) in [
            FortranSourceFile,
            FortranProgram,
            FortranModule,
            GenericSource,
            FortranBlockData,
            ExternalModule,
        ] or (
            type(self)
            in [
                FortranType,
                ExternalType,
                FortranInterface,
                ExternalInterface,
                FortranFunction,
                ExternalFunction,
                FortranSubroutine,
                ExternalSubroutine,
                FortranSubmoduleProcedure,
            ]
            and type(self.parent)
            in [
                FortranSourceFile,
                FortranProgram,
                FortranModule,
                FortranSubmodule,
                FortranBlockData,
                ExternalModule,
            ]
        ):
            return self.obj
        else:
            return None

    def get_url(self):
        if hasattr(self, "external_url"):
            return self.external_url
        outstr = "{0}/{1}/{2}.html"
        loc = self.get_dir()
        if loc:
            return outstr.format(self.base_url, loc, quote(self.ident))
        elif (
            isinstance(self, (FortranBoundProcedure, FortranCommon))
            or isinstance(self, FortranVariable)
            and isinstance(self.parent, FortranType)
        ):
            parent_url = self.parent.get_url()
            if parent_url:
                return parent_url + "#" + self.anchor
            else:
                return None
        else:
            return None

    def lines_description(self, total, total_all=0, obj=None):
        if not obj:
            obj = self.obj
        description = "{:4.1f}% of total for {}.".format(
            float(self.num_lines) / total * 100, self.pretty_obj[obj]
        )
        if total_all:
            description = (
                "<p>"
                + description
                + "</p>Including implementation: {} statements, {:4.1f}% of total for {}.".format(
                    self.num_lines_all,
                    float(self.num_lines_all) / total_all * 100,
                    self.pretty_obj[obj],
                )
            )
        return description

    @property
    def ident(self):
        if (
            type(self) in [FortranSubroutine, FortranFunction]
            and type(self.parent) == FortranInterface
            and not self.parent.generic
        ):
            return namelist.get_name(self.parent)
        else:
            return namelist.get_name(self)

    @property
    def anchor(self):
        return self.obj + "-" + quote(self.ident)

    def __str__(self):
        outstr = "<a href='{0}'>{1}</a>"
        url = self.get_url()
        if url and getattr(self, "visible", True):
            if self.name:
                name = self.name
            else:
                name = "<em>unnamed</em>"
            return outstr.format(url, name)
        elif self.name:
            return self.name
        else:
            return ""

    @property
    def contents_size(self):
        """
        Returns the number of different categories to be shown in the
        contents side-bar in the HTML documentation.
        """
        count = 0
        if hasattr(self, "variables"):
            count += 1
        if hasattr(self, "types"):
            count += 1
        if hasattr(self, "modules"):
            count += 1
        if hasattr(self, "submodules"):
            count += 1
        if hasattr(self, "subroutines"):
            count += 1
        if hasattr(self, "modprocedures"):
            count += 1
        if hasattr(self, "functions"):
            count += 1
        if hasattr(self, "interfaces"):
            count += 1
        if hasattr(self, "absinterfaces"):
            count += 1
        if hasattr(self, "programs"):
            count += 1
        if hasattr(self, "boundprocs"):
            count += 1
        if hasattr(self, "finalprocs"):
            count += 1
        if hasattr(self, "enums"):
            count += 1
        if hasattr(self, "procedure"):
            count += 1
        if hasattr(self, "constructor"):
            count += 1
        if hasattr(self, "modfunctions"):
            count += 1
        if hasattr(self, "modsubroutines"):
            count += 1
        if hasattr(self, "modprocs"):
            count += 1
        if getattr(self, "src", None):
            count += 1
        return count

    def __lt__(self, other):
        """
        Compare two Fortran objects. Needed to make toposort work.
        """
        return self.ident < other.ident

    def markdown(self, md, project):
        """
        Process the documentation with Markdown to produce HTML.
        """
        if len(self.doc) > 0:
            if len(self.doc) == 1 and ":" in self.doc[0]:
                words = self.doc[0].split(":")[0].strip()
                if words.lower() not in [
                    "author",
                    "date",
                    "license",
                    "version",
                    "category",
                    "summary",
                    "deprecated",
                    "display",
                    "graph",
                ]:
                    self.doc.insert(0, "")
                self.doc.append("")
            self.doc = "\n".join(self.doc)
            self.doc = md.convert(self.doc)
            self.meta = md.Meta
            md.reset()
            md.Meta = {}
        else:
            if (
                self.settings["warn"].lower() == "true"
                and self.obj != "sourcefile"
                and self.obj != "genericsource"
            ):
                # TODO: Add ability to print line number where this item is in file
                print(
                    "Warning: Undocumented {} {} in file {}".format(
                        self.obj, self.name, self.hierarchy[0].name
                    )
                )
            self.doc = ""
            self.meta = {}

        if self.parent:
            self.display = self.parent.display

        # ~ print (self.meta)
        for key in self.meta:
            # ~ print(key, self.meta[key])
            if key == "display":
                tmp = [item.lower() for item in self.meta[key]]
                if type(self) == FortranSourceFile:
                    while "none" in tmp:
                        tmp.remove("none")
                if len(tmp) == 0:
                    pass
                elif "none" in tmp:
                    self.display = []
                elif (
                    "public" not in tmp
                    and "private" not in tmp
                    and "protected" not in tmp
                ):
                    pass
                else:
                    self.display = tmp
            elif len(self.meta[key]) == 1:
                self.meta[key] = self.meta[key][0]
            elif key == "summary":
                self.meta[key] = "\n".join(self.meta[key])
        if hasattr(self, "num_lines"):
            self.meta["num_lines"] = self.num_lines

        self.doc = ford.utils.sub_macros(ford.utils.sub_notes(self.doc))

        if "summary" in self.meta:
            self.meta["summary"] = md.convert(self.meta["summary"])
            self.meta["summary"] = ford.utils.sub_macros(
                ford.utils.sub_notes(self.meta["summary"])
            )
        elif PARA_CAPTURE_RE.search(self.doc):
            if self.get_url() is None:
                # There is no stand-alone webpage for this item (e.g.,
                # an internal routine in a routine, so make the whole
                # doc blob appear, without the link to "more..."
                self.meta["summary"] = self.doc
            else:
                self.meta["summary"] = PARA_CAPTURE_RE.search(self.doc).group()
        else:
            self.meta["summary"] = ""
        if self.meta["summary"].strip() != self.doc.strip():
            self.meta[
                "summary"
            ] += '<a href="{}" class="pull-right"><emph>Read more&hellip;</emph></a>'.format(
                self.get_url()
            )
        if "graph" not in self.meta:
            self.meta["graph"] = self.settings["graph"]
        else:
            self.meta["graph"] = self.meta["graph"].lower()
        if "graph_maxdepth" not in self.meta:
            self.meta["graph_maxdepth"] = self.settings["graph_maxdepth"]
        if "graph_maxnodes" not in self.meta:
            self.meta["graph_maxnodes"] = self.settings["graph_maxnodes"]

        if self.obj == "proc" or self.obj == "type" or self.obj == "program":
            if "source" not in self.meta:
                self.meta["source"] = self.settings["source"].lower()
            else:
                self.meta["source"] = self.meta["source"].lower()
            if self.meta["source"] == "true":
                if self.obj == "proc":
                    obj = self.proctype.lower()
                else:
                    obj = self.obj
                regex = re.compile(
                    self.SRC_CAPTURE_STR.format(obj, self.name),
                    re.IGNORECASE | re.DOTALL | re.MULTILINE,
                )
                match = regex.search(self.hierarchy[0].raw_src)
                if match:
                    self.src = highlight(match.group(), FortranLexer(), HtmlFormatter())
                else:
                    self.src = ""
                    if self.settings["warn"].lower() == "true":
                        print(
                            "Warning: Could not extract source code for {} {} in file {}".format(
                                self.obj, self.name, self.hierarchy[0].name
                            )
                        )

        if self.obj == "proc":
            if "proc_internals" not in self.meta:
                self.meta["proc_internals"] = self.settings["proc_internals"].lower()
            else:
                self.meta["proc_internals"] = self.meta["proc_internals"].lower()

        # Create Markdown
        for item in self.iterator(
            "variables",
            "modules",
            "submodules",
            "common",
            "subroutines",
            "modprocedures",
            "functions",
            "interfaces",
            "absinterfaces",
            "types",
            "programs",
            "blockdata",
            "boundprocs",
            "finalprocs",
            "args",
            "enums",
        ):
            if isinstance(item, FortranBase):
                item.markdown(md, project)
        if hasattr(self, "retvar"):
            if self.retvar:
                if isinstance(self.retvar, FortranBase):
                    self.retvar.markdown(md, project)
        if hasattr(self, "procedure"):
            if isinstance(self.procedure, FortranBase):
                self.procedure.markdown(md, project)
        return

    def sort(self):
        """
        Sorts components of the object.
        """
        if hasattr(self, "variables"):
            sort_items(self, self.variables)
        if hasattr(self, "modules"):
            sort_items(self, self.modules)
        if hasattr(self, "submodules"):
            sort_items(self, self.submodules)
        if hasattr(self, "common"):
            sort_items(self, self.common)
        if hasattr(self, "subroutines"):
            sort_items(self, self.subroutines)
        if hasattr(self, "modprocedures"):
            sort_items(self, self.modprocedures)
        if hasattr(self, "functions"):
            sort_items(self, self.functions)
        if hasattr(self, "interfaces"):
            sort_items(self, self.interfaces)
        if hasattr(self, "absinterfaces"):
            sort_items(self, self.absinterfaces)
        if hasattr(self, "types"):
            sort_items(self, self.types)
        if hasattr(self, "programs"):
            sort_items(self, self.programs)
        if hasattr(self, "blockdata"):
            sort_items(self, self.blockdata)
        if hasattr(self, "boundprocs"):
            sort_items(self, self.boundprocs)
        if hasattr(self, "finalprocs"):
            sort_items(self, self.finalprocs)
        if hasattr(self, "args"):
            # sort_items(self.args,args=True)
            pass

    def make_links(self, project):
        """
        Process intra-site links to documentation of other parts of the program.
        """
        self.doc = ford.utils.sub_links(self.doc, project)
        if "summary" in self.meta:
            self.meta["summary"] = ford.utils.sub_links(self.meta["summary"], project)

        # Create links in the project
        for item in self.iterator(
            "variables",
            "types",
            "enums",
            "modules",
            "submodules",
            "subroutines",
            "functions",
            "interfaces",
            "absinterfaces",
            "programs",
            "boundprocs",
            "args",
            "bindings",
        ):
            if isinstance(item, FortranBase):
                item.make_links(project)
        if hasattr(self, "retvar"):
            if self.retvar:
                if isinstance(self.retvar, FortranBase):
                    self.retvar.make_links(project)
        if hasattr(self, "procedure"):
            if isinstance(self.procedure, FortranBase):
                self.procedure.make_links(project)

        # if hasattr(self,'finalprocs'): recurse_list.extend(self.finalprocs)
        # if hasattr(self,'constructor') and self.constructor: recurse_list.append(self.constructor)

    @property
    def routines(self):
        """Iterator returning *both* functions and subroutines, in that order"""
        for item in self.iterator("functions", "subroutines"):
            yield item

    def iterator(self, *argv):
        """Iterator returning any list of elements via attribute lookup in `self`

        This iterator retains the order of the arguments"""
        for arg in argv:
            if hasattr(self, arg):
                for item in getattr(self, arg):
                    yield item


class FortranContainer(FortranBase):
    """
    A class on which any classes requiring further parsing are based.
    """

    ATTRIB_RE = re.compile(
        r"^(asynchronous|allocatable|bind\s*\(.*\)|data|dimension|external|intent\s*\(\s*\w+\s*\)|optional|parameter|"
        r"pointer|private|protected|public|save|target|value|volatile)(?:\s+|\s*::\s*)((/|\(|\w).*?)\s*$",
        re.IGNORECASE,
    )
    END_RE = re.compile(
        r"^end\s*(?:(module|submodule|subroutine|function|procedure|program|type|interface|enum|block\sdata|block|associate)(?:\s+(\w.*))?)?$",
        re.IGNORECASE,
    )
    BLOCK_RE = re.compile(r"^(\w+\s*:)?\s*block\s*$", re.IGNORECASE)
    BLOCK_DATA_RE = re.compile(r"^block\s*data\s*(\w+)?\s*$", re.IGNORECASE)
    ASSOCIATE_RE = re.compile(r"^(\w+\s*:)?\s*associate\s*\((.+)\)\s*$", re.IGNORECASE)
    ENUM_RE = re.compile(r"^enum\s*,\s*bind\s*\(.*\)\s*$", re.IGNORECASE)
    MODPROC_RE = re.compile(
        r"^(module\s+)?procedure\s*(?:::|\s)\s*(\w.*)$", re.IGNORECASE
    )
    MODULE_RE = re.compile(r"^module(?:\s+(\w+))?$", re.IGNORECASE)
    SUBMODULE_RE = re.compile(
        r"^submodule\s*\(\s*(\w+)\s*(?::\s*(\w+))?\s*\)\s*(?:::|\s)\s*(\w+)$",
        re.IGNORECASE,
    )
    PROGRAM_RE = re.compile(r"^program(?:\s+(\w+))?$", re.IGNORECASE)
    SUBROUTINE_RE = re.compile(
        r"^\s*(?:(.+?)\s+)?subroutine\s+(\w+)\s*(\([^()]*\))?(?:\s*bind\s*\(\s*(.*)\s*\))?$",
        re.IGNORECASE,
    )
    FUNCTION_RE = re.compile(
        r"^(?:(.+?)\s+)?function\s+(\w+)\s*(\([^()]*\))?(?=(?:.*result\s*\(\s*(\w+)\s*\))?)(?=(?:.*bind\s*\(\s*(.*)\s*\))?).*$",
        re.IGNORECASE,
    )
    TYPE_RE = re.compile(
        r"^type(?:\s+|\s*(,.*)?::\s*)((?!(?:is\s*\())\w+)\s*(\([^()]*\))?\s*$",
        re.IGNORECASE,
    )
    INTERFACE_RE = re.compile(r"^(abstract\s+)?interface(?:\s+(\S.+))?$", re.IGNORECASE)
    # ~ ABS_INTERFACE_RE = re.compile(r"^abstract\s+interface(?:\s+(\S.+))?$",re.IGNORECASE)
    BOUNDPROC_RE = re.compile(
        r"^(generic|procedure)\s*(\([^()]*\))?\s*(.*)\s*::\s*(\w.*)", re.IGNORECASE
    )
    COMMON_RE = re.compile(r"^common(?:\s*/\s*(\w+)\s*/\s*|\s+)(\w+.*)", re.IGNORECASE)
    COMMON_SPLIT_RE = re.compile(r"\s*(/\s*\w+\s*/)\s*", re.IGNORECASE)
    FINAL_RE = re.compile(r"^final\s*::\s*(\w.*)", re.IGNORECASE)
    USE_RE = re.compile(
        r"^use(?:\s*(?:,\s*(?:non_)?intrinsic\s*)?::\s*|\s+)(\w+)\s*($|,.*)",
        re.IGNORECASE,
    )
    ARITH_GOTO_RE = re.compile(r"go\s*to\s*\([0-9,\s]+\)", re.IGNORECASE)
    CALL_RE = re.compile(
        r"(?:^|[^a-zA-Z0-9_% ]\s*)(\w+)(?=\s*\(\s*(?:.*?)\s*\))", re.IGNORECASE
    )
    SUBCALL_RE = re.compile(
        r"^(?:if\s*\(.*\)\s*)?call\s+(\w+)\s*(?:\(\s*(.*?)\s*\))?$", re.IGNORECASE
    )
    FORMAT_RE = re.compile(r"^[0-9]+\s+format\s+\(.*\)", re.IGNORECASE)

    VARIABLE_STRING = (
        r"^(integer|real|double\s*precision|character|complex|double\s*complex|logical|type(?!\s+is)|class(?!\s+is|\s+default)|"
        r"procedure|enumerator{})\s*((?:\(|\s\w|[:,*]).*)$"
    )

    def __init__(
        self, source, first_line, parent=None, inherited_permission=None, strings=[]
    ):
        self.num_lines = 0
        if not isinstance(self, FortranSourceFile):
            self.num_lines += 1
        if type(self) != FortranSourceFile:
            FortranBase.__init__(
                self, source, first_line, parent, inherited_permission, strings
            )
        incontains = False
        if type(self) is FortranSubmodule:
            permission = "private"
        else:
            permission = "public"

        typestr = ""
        for vtype in self.settings["extra_vartypes"]:
            typestr = typestr + "|" + vtype
        self.VARIABLE_RE = re.compile(
            self.VARIABLE_STRING.format(typestr), re.IGNORECASE
        )

        blocklevel = 0
        associatelevel = 0
        for line in source:
            if line[0:2] == "!" + self.settings["docmark"]:
                self.doc.append(line[2:])
                continue
            if line.strip() != "":
                self.num_lines += 1

            # Temporarily replace all strings to make the parsing simpler
            self.strings = []
            search_from = 0
            while QUOTES_RE.search(line[search_from:]):
                self.strings.append(QUOTES_RE.search(line[search_from:]).group())
                line = line[0:search_from] + QUOTES_RE.sub(
                    '"{}"'.format(len(self.strings) - 1), line[search_from:], count=1
                )
                search_from += QUOTES_RE.search(line[search_from:]).end(0)

            # Check the various possibilities for what is on this line
            if self.settings["lower"].lower() == "true":
                line = line.lower()
            if line.lower() == "contains":
                if not incontains and type(self) in _can_have_contains:
                    incontains = True
                    if isinstance(self, FortranType):
                        permission = "public"
                elif incontains:
                    self.print_error(
                        line, "Multiple CONTAINS statements present in scope"
                    )
                else:
                    self.print_error(
                        line,
                        "CONTAINS statement in {}".format(
                            type(self).__name__[7:].upper()
                        ),
                    )
            elif line.lower() == "public":
                permission = "public"
            elif line.lower() == "private":
                permission = "private"
            elif line.lower() == "protected":
                permission = "protected"
            elif line.lower() == "sequence":
                if type(self) == FortranType:
                    self.sequence = True
            elif self.FORMAT_RE.match(line):
                # There's nothing interesting for us in a format statement
                continue
            elif self.ATTRIB_RE.match(line) and blocklevel == 0:
                match = self.ATTRIB_RE.match(line)
                attr = match.group(1).lower().replace(" ", "")
                if len(attr) >= 4 and attr[0:4].lower() == "bind":
                    attr = attr.replace(",", ", ")
                if hasattr(self, "attr_dict"):
                    if attr == "data":
                        pass
                    elif (
                        attr == "dimension"
                        or attr == "allocatable"
                        or attr == "pointer"
                    ):
                        names = ford.utils.paren_split(",", match.group(2))
                        for name in names:
                            name = name.strip().lower()
                            i = name.index("(")
                            n = name[:i]
                            sh = name[i:]
                            if n in self.attr_dict:
                                self.attr_dict[n].append(attr + sh)
                            else:
                                self.attr_dict[n] = [attr + sh]
                    else:
                        stmnt = match.group(2)
                        if attr == "parameter":
                            stmnt = stmnt[1:-1].strip()
                        names = ford.utils.paren_split(",", stmnt)
                        search_from = 0
                        while QUOTES_RE.search(attr[search_from:]):
                            num = int(
                                QUOTES_RE.search(attr[search_from:]).group()[1:-1]
                            )
                            attr = attr[0:search_from] + QUOTES_RE.sub(
                                self.strings[num], attr[search_from:], count=1
                            )
                            search_from += QUOTES_RE.search(attr[search_from:]).end(0)
                        for name in names:
                            if attr == "parameter":
                                split = ford.utils.paren_split("=", name)
                                name = split[0].strip().lower()
                                self.param_dict[name] = split[1]
                            name = name.strip().lower()
                            if name in self.attr_dict:
                                self.attr_dict[name].append(attr)
                            else:
                                self.attr_dict[name] = [attr]
                elif attr.lower() == "data" and self.obj == "sourcefile":
                    # TODO: This is just a fix to keep FORD from crashing on
                    # encountering a block data structure. At some point I
                    # should actually implement support for them.
                    continue
                else:
                    self.print_error(
                        line,
                        "Found {} statement in {}".format(
                            attr.upper(), type(self).__name__[7:].upper()
                        ),
                    )
            elif self.END_RE.match(line):
                if isinstance(self, FortranSourceFile):
                    self.print_error(line, "END statement outside of any nesting")
                endtype = self.END_RE.match(line).group(1)
                if endtype and endtype.lower() == "block":
                    blocklevel -= 1
                elif endtype and endtype.lower() == "associate":
                    associatelevel -= 1
                else:
                    self._cleanup()
                    return
            elif self.MODPROC_RE.match(line) and (
                self.MODPROC_RE.match(line).group(1) or type(self) is FortranInterface
            ):
                if hasattr(self, "modprocs"):
                    # Module procedure in an INTERFACE
                    self.modprocs.extend(
                        get_mod_procs(source, self.MODPROC_RE.match(line), self)
                    )
                elif hasattr(self, "modprocedures"):
                    # Module procedure implementing an interface in a SUBMODULE
                    self.modprocedures.append(
                        FortranSubmoduleProcedure(
                            source, self.MODPROC_RE.match(line), self, permission
                        )
                    )
                    self.num_lines += self.modprocedures[-1].num_lines - 1
                else:
                    self.print_error(
                        line,
                        "Found module procedure in {}".format(
                            type(self).__name__[7:].upper()
                        ),
                    )
            elif self.BLOCK_DATA_RE.match(line):
                if hasattr(self, "blockdata"):
                    self.blockdata.append(
                        FortranBlockData(source, self.BLOCK_DATA_RE.match(line), self)
                    )
                    self.num_lines += self.blockdata[-1].num_lines - 1
                else:
                    self.print_error(
                        line,
                        "Found BLOCK DATA in {}".format(
                            type(self).__name__[7:].upper()
                        ),
                    )
            elif self.BLOCK_RE.match(line):
                blocklevel += 1
            elif self.ASSOCIATE_RE.match(line):
                associatelevel += 1
            elif self.MODULE_RE.match(line):
                if hasattr(self, "modules"):
                    self.modules.append(
                        FortranModule(source, self.MODULE_RE.match(line), self)
                    )
                    self.num_lines += self.modules[-1].num_lines - 1
                else:
                    self.print_error(
                        line,
                        "Found MODULE in {}".format(type(self).__name__[7:].upper()),
                    )
            elif self.SUBMODULE_RE.match(line):
                if hasattr(self, "submodules"):
                    self.submodules.append(
                        FortranSubmodule(source, self.SUBMODULE_RE.match(line), self)
                    )
                    self.num_lines += self.submodules[-1].num_lines - 1
                else:
                    self.print_error(
                        line,
                        "Found SUBMODULE in {}".format(type(self).__name__[7:].upper()),
                    )
            elif self.PROGRAM_RE.match(line):
                if hasattr(self, "programs"):
                    self.programs.append(
                        FortranProgram(source, self.PROGRAM_RE.match(line), self)
                    )
                    self.num_lines += self.programs[-1].num_lines - 1
                else:
                    self.print_error(
                        line,
                        "Found PROGRAM in {}".format(type(self).__name__[7:].upper()),
                    )
                if len(self.programs) > 1:
                    raise Exception("Multiple PROGRAM units in same source file.")
            elif self.SUBROUTINE_RE.match(line):
                if isinstance(self, FortranCodeUnit) and not incontains:
                    continue
                if hasattr(self, "subroutines"):
                    self.subroutines.append(
                        FortranSubroutine(
                            source, self.SUBROUTINE_RE.match(line), self, permission
                        )
                    )
                    self.num_lines += self.subroutines[-1].num_lines - 1
                else:
                    self.print_error(
                        line,
                        "Found SUBROUTINE in {}".format(
                            type(self).__name__[7:].upper()
                        ),
                    )
            elif self.FUNCTION_RE.match(line):
                if isinstance(self, FortranCodeUnit) and not incontains:
                    continue
                if hasattr(self, "functions"):
                    self.functions.append(
                        FortranFunction(
                            source, self.FUNCTION_RE.match(line), self, permission
                        )
                    )
                    self.num_lines += self.functions[-1].num_lines - 1
                else:
                    self.print_error(
                        line,
                        "Found FUNCTION in {}".format(type(self).__name__[7:].upper()),
                    )
            elif self.TYPE_RE.match(line) and blocklevel == 0:
                if hasattr(self, "types"):
                    self.types.append(
                        FortranType(source, self.TYPE_RE.match(line), self, permission)
                    )
                    self.num_lines += self.types[-1].num_lines - 1
                else:
                    self.print_error(
                        line,
                        "Found derived TYPE in {}".format(
                            type(self).__name__[7:].upper()
                        ),
                    )
            elif self.INTERFACE_RE.match(line) and blocklevel == 0:
                if hasattr(self, "interfaces"):
                    intr = FortranInterface(
                        source, self.INTERFACE_RE.match(line), self, permission
                    )
                    self.num_lines += intr.num_lines - 1
                    if intr.abstract:
                        self.absinterfaces.extend(intr.contents)
                    elif intr.generic:
                        self.interfaces.append(intr)
                    else:
                        self.interfaces.extend(intr.contents)
                else:
                    self.print_error(
                        line,
                        "Found INTERFACE in {}".format(type(self).__name__[7:].upper()),
                    )
            elif self.ENUM_RE.match(line) and blocklevel == 0:
                if hasattr(self, "enums"):
                    self.enums.append(
                        FortranEnum(source, self.ENUM_RE.match(line), self, permission)
                    )
                    self.num_lines += self.enums[-1].num_lines - 1
                else:
                    self.print_error(
                        line, "Found ENUM in {}".format(type(self).__name__[7:].upper())
                    )
            elif self.BOUNDPROC_RE.match(line) and incontains:
                if hasattr(self, "boundprocs"):
                    match = self.BOUNDPROC_RE.match(line)
                    split = match.group(4).split(",")
                    split.reverse()
                    if match.group(1).lower() == "generic" or len(split) == 1:
                        self.boundprocs.append(
                            FortranBoundProcedure(
                                source, self.BOUNDPROC_RE.match(line), self, permission
                            )
                        )
                    else:
                        for bind in split:
                            pseudo_line = line[: match.start(4)] + bind
                            self.boundprocs.append(
                                FortranBoundProcedure(
                                    source,
                                    self.BOUNDPROC_RE.match(pseudo_line),
                                    self,
                                    permission,
                                )
                            )
                else:
                    self.print_error(
                        line,
                        "Found type-bound procedure in {}".format(
                            type(self).__name__[7:].upper()
                        ),
                    )
            elif self.COMMON_RE.match(line):
                if hasattr(self, "common"):
                    split = self.COMMON_SPLIT_RE.split(line)
                    if len(split) > 1:
                        for i in range(len(split) // 2):
                            pseudo_line = (
                                split[0]
                                + " "
                                + split[2 * i + 1]
                                + " "
                                + split[2 * i + 2].strip()
                            )
                            if pseudo_line[-1] == ",":
                                pseudo_line = pseudo_line[:-1]
                            self.common.append(
                                FortranCommon(
                                    source,
                                    self.COMMON_RE.match(pseudo_line),
                                    self,
                                    "public",
                                )
                            )
                        for i in range(len(split) // 2):
                            self.common[-i - 1].doc = self.common[
                                -len(split) // 2 + 1
                            ].doc
                    else:
                        self.common.append(
                            FortranCommon(
                                source, self.COMMON_RE.match(line), self, "public"
                            )
                        )
                else:
                    self.print_error(
                        line,
                        "Found common statement in {}".format(
                            type(self).__name__[7:].upper()
                        ),
                    )
            elif self.FINAL_RE.match(line) and incontains:
                if hasattr(self, "finalprocs"):
                    procedures = self.SPLIT_RE.split(
                        self.FINAL_RE.match(line).group(1).strip()
                    )
                    finprocs = [
                        FortranFinalProc(proc, self) for proc in procedures[:-1]
                    ]
                    finprocs.append(FortranFinalProc(procedures[-1], self, source))
                    self.finalprocs.extend(finprocs)
                else:
                    self.print_error(
                        line,
                        "Found finalization procedure in {}".format(
                            type(self).__name__[7:].upper()
                        ),
                    )
            elif self.VARIABLE_RE.match(line) and blocklevel == 0:
                if hasattr(self, "variables"):
                    self.variables.extend(
                        line_to_variables(source, line, permission, self)
                    )
                else:
                    self.print_error(
                        line,
                        "Found variable in {}".format(type(self).__name__[7:].upper()),
                    )
            elif self.USE_RE.match(line):
                if hasattr(self, "uses"):
                    self.uses.append(self.USE_RE.match(line).groups())
                else:
                    self.print_error(
                        line,
                        "Found USE statemnt in {}".format(
                            type(self).__name__[7:].upper()
                        ),
                    )
            else:
                if self.CALL_RE.search(line):
                    if hasattr(self, "calls"):
                        # Arithmetic GOTOs looks little like function references:
                        # "goto (1, 2, 3) i".  But even in free-form source we're
                        # allowed to use a space: "go to (1, 2, 3) i".  Our CALL_RE
                        # expression doesn't catch that so we first rule such a
                        # GOTO out.
                        if not self.ARITH_GOTO_RE.search(line):
                            callvals = self.CALL_RE.findall(line)
                            for val in callvals:
                                if (
                                    val.lower() not in self.calls
                                    and val.lower() not in INTRINSICS
                                ):
                                    self.calls.append(val.lower())
                    else:
                        pass
                        # Not raising an error here as too much possibility that something
                        # has been misidentified as a function call
                        # ~ raise Exception("Found procedure call in {}".format(type(self).__name__[7:].upper()))
                if self.SUBCALL_RE.match(line):
                    # Need this to catch any subroutines called without argument lists
                    if hasattr(self, "calls"):
                        callval = self.SUBCALL_RE.match(line).group(1)
                        if (
                            callval.lower() not in self.calls
                            and callval.lower() not in INTRINSICS
                        ):
                            self.calls.append(callval.lower())
                    else:
                        self.print_error(
                            line,
                            "Found procedure call in {}".format(
                                type(self).__name__[7:].upper()
                            ),
                        )

        if not isinstance(self, FortranSourceFile):
            raise Exception("File ended while still nested.")

    def _cleanup(self):
        raise NotImplementedError()

    def print_error(self, line, msg, dbg=None, force=None):
        if dbg is None:
            dbg = self.settings["dbg"]
        if force is None:
            force = self.settings["force"]
        if dbg:
            print(f"{line}: {msg}")
        else:
            if force:
                return
            raise ValueError(msg)


class FortranCodeUnit(FortranContainer):
    """
    A class on which programs, modules, functions, and subroutines are based.
    """

    def correlate(self, project):
        # Add procedures, interfaces and types from parent to our lists
        if hasattr(self.parent, "all_procs"):
            self.all_procs.update(self.parent.all_procs)
        self.all_absinterfaces = getattr(self.parent, "all_absinterfaces", {})
        for ai in self.absinterfaces:
            self.all_absinterfaces[ai.name.lower()] = ai
        self.all_types = getattr(self.parent, "all_types", {})
        for dt in self.types:
            self.all_types[dt.name.lower()] = dt
        self.all_vars = getattr(self.parent, "all_vars", {})
        for var in self.variables:
            self.all_vars[var.name.lower()] = var

        if type(getattr(self, "ancestor", "")) not in [str, type(None)]:
            self.ancestor.descendants.append(self)
            self.all_procs.update(self.ancestor.all_procs)
            self.all_absinterfaces.update(self.ancestor.all_absinterfaces)
            self.all_types.update(self.ancestor.all_types)
        elif type(getattr(self, "ancestor_mod", "")) not in [str, type(None)]:
            self.ancestor_mod.descendants.append(self)
            self.all_procs.update(self.ancestor_mod.all_procs)
            self.all_absinterfaces.update(self.ancestor_mod.all_absinterfaces)
            self.all_types.update(self.ancestor_mod.all_types)

        if isinstance(self, FortranSubmodule):
            for proc in self.routines:
                if proc.module and proc.name.lower() in self.all_procs:
                    intr = self.all_procs[proc.name.lower()]
                    if (
                        intr.proctype.lower() == "interface"
                        and not intr.generic
                        and not intr.abstract
                        and intr.procedure.module is True
                    ):
                        proc.module = intr
                        intr.procedure.module = proc

        if hasattr(self, "modprocedures"):
            for proc in self.modprocedures:
                if proc.name.lower() in self.all_procs:
                    intr = self.all_procs[proc.name.lower()]
                    # Don't think I need these checks...
                    if (
                        intr.proctype.lower() == "interface"
                        and not intr.generic
                        and not intr.abstract
                        and intr.procedure.module is True
                    ):
                        proc.attribs = intr.procedure.attribs
                        proc.args = intr.procedure.args
                        if hasattr(intr.procedure, "retvar"):
                            proc.retvar = intr.procedure.retvar
                        proc.proctype = intr.procedure.proctype
                        proc.module = intr
                        intr.procedure.module = proc

        # Add procedures and types from USED modules to our lists
        for mod, extra in self.uses:
            if type(mod) is str:
                continue
            procs, absints, types, variables = mod.get_used_entities(extra)
            if self.obj == "module":
                self.pub_procs.update(
                    [
                        (name, proc)
                        for name, proc in procs.items()
                        if name in self.public_list
                    ]
                )
                self.pub_absints.update(
                    [
                        (name, absint)
                        for name, absint in absints.items()
                        if name in self.public_list
                    ]
                )
                self.pub_types.update(
                    [
                        (name, dtype)
                        for name, dtype in types.items()
                        if name in self.public_list
                    ]
                )
                self.pub_vars.update(
                    [
                        (name, var)
                        for name, var in variables.items()
                        if name in self.public_list
                    ]
                )
            self.all_procs.update(procs)
            self.all_absinterfaces.update(absints)
            self.all_types.update(types)
            self.all_vars.update(variables)
        self.uses = set([m[0] for m in self.uses])

        typelist = {}
        for dtype in self.types:
            if dtype.extends and dtype.extends.lower() in self.all_types:
                dtype.extends = self.all_types[dtype.extends.lower()]
                typelist[dtype] = set([dtype.extends])
            else:
                typelist[dtype] = set([])
        typeorder = toposort.toposort_flatten(typelist)

        # Match up called procedures
        if hasattr(self, "calls"):
            tmplst = []
            for call in self.calls:
                argname = False
                for a in getattr(self, "args", []):
                    # Consider allowing procedures passed as arguments to be included in callgraphs
                    argname = argname or call.lower() == a.name.lower()
                if hasattr(self, "retvar"):
                    argname = argname or call.lower() == self.retvar.name.lower()
                if (
                    call.lower() not in self.all_vars
                    and (
                        call.lower() not in self.all_types
                        or call.lower() in self.all_procs
                    )
                    and not argname
                ):
                    tmplst.append(call)
            self.calls = tmplst
            fileprocs = {}
            if self.parobj == "sourcefile":
                for proc in self.parent.subroutines + self.parent.functions:
                    fileprocs[proc.name.lower()] = proc
            for i in range(len(self.calls)):
                if self.calls[i].lower() in self.all_procs:
                    self.calls[i] = self.all_procs[self.calls[i].lower()]
                elif self.calls[i].lower() in fileprocs:
                    self.calls[i] = fileprocs[self.calls[i].lower()]
                else:
                    for proc in project.procedures:
                        if self.calls[i] == proc.name.lower():
                            self.calls[i] = proc
                            break

        if self.obj == "submodule":
            self.ancestry = []
            item = self
            while item.ancestor:
                item = item.ancestor
                self.ancestry.insert(0, item)
            self.ancestry.insert(0, item.ancestor_mod)

        # Recurse
        for dtype in typeorder:
            if dtype in self.types:
                dtype.correlate(project)
        for func in self.functions:
            func.correlate(project)
        for subrtn in self.subroutines:
            subrtn.correlate(project)
        for interface in self.interfaces:
            interface.correlate(project)
        for absint in self.absinterfaces:
            absint.correlate(project)
        for var in self.variables:
            var.correlate(project)
        for com in self.common:
            com.correlate(project)
        if hasattr(self, "modprocedures"):
            for mp in self.modprocedures:
                mp.correlate(project)
        if hasattr(self, "args") and not getattr(self, "mp", False):
            for arg in self.args:
                arg.correlate(project)
        if hasattr(self, "retvar") and not getattr(self, "mp", False):
            self.retvar.correlate(project)

        # Sort content
        self.sort()

        # Separate module subroutines/functions from normal ones
        if self.obj == "submodule":
            self.modfunctions = [func for func in self.functions if func.module]
            self.functions = [func for func in self.functions if not func.module]
            self.modsubroutines = [sub for sub in self.subroutines if sub.module]
            self.subroutines = [sub for sub in self.subroutines if not sub.module]

        del self.public_list

    def process_attribs(self):
        # IMPORTANT: Make sure types processed before interfaces--import when
        # determining permissions of derived types and overridden constructors
        for item in self.iterator(
            "functions", "subroutines", "types", "interfaces", "absinterfaces"
        ):
            for attr in self.attr_dict.get(item.name.lower(), []):
                if attr == "public" or attr == "private" or attr == "protected":
                    item.permission = attr
                elif attr[0:4] == "bind":
                    if hasattr(item, "bindC"):
                        item.bindC = attr[5:-1]
                    elif getattr(item, "procedure", None):
                        item.procedure.bindC = attr[5:-1]
                    else:
                        item.attribs.append(attr)
                else:
                    item.attribs.append(attr)
            try:
                del self.attr_dict[item.name.lower()]
            except KeyError:
                pass
        for var in self.variables:
            for attr in self.attr_dict.get(var.name.lower(), []):
                if attr == "public" or attr == "private" or attr == "protected":
                    var.permission = attr
                elif attr[0:6] == "intent":
                    var.intent = attr[7:-1]
                elif DIM_RE.match(attr) and (
                    "pointer" in attr or "allocatable" in attr
                ):
                    i = attr.index("(")
                    var.attribs.append(attr[0:i])
                    var.dimension = attr[i:]
                elif attr == "parameter":
                    var.attribs.append(attr)
                    var.initial = self.param_dict[var.name.lower()]
                else:
                    var.attribs.append(attr)
            try:
                del self.attr_dict[var.name.lower()]
            except KeyError:
                pass
        self.public_list = []
        for item, attrs in self.attr_dict.items():
            if "public" in attrs:
                self.public_list.append(item)
        del self.attr_dict

    def prune(self):
        """
        Remove anything which shouldn't be displayed.
        """

        def to_include(obj):
            inc = obj.permission in self.display
            if self.settings["hide_undoc"].lower() == "true" and not obj.doc:
                inc = False
            return inc

        if self.obj == "proc" and self.meta["proc_internals"] == "false":
            self.functions = []
            self.subroutines = []
            self.types = []
            self.interfaces = []
            self.absinterfaces = []
            self.variables = []
        else:
            self.functions = [obj for obj in self.functions if to_include(obj)]
            self.subroutines = [obj for obj in self.subroutines if to_include(obj)]
            self.types = [obj for obj in self.types if to_include(obj)]
            self.interfaces = [obj for obj in self.interfaces if to_include(obj)]
            self.absinterfaces = [obj for obj in self.absinterfaces if to_include(obj)]
            self.variables = [obj for obj in self.variables if to_include(obj)]
            if hasattr(self, "modprocedures"):
                self.modprocedures = [
                    obj for obj in self.modprocedures if to_include(obj)
                ]
            if hasattr(self, "modsubroutines"):
                self.modsubroutines = [
                    obj for obj in self.modsubroutines if to_include(obj)
                ]
            if hasattr(self, "modfunctions"):
                self.modfunctions = [
                    obj for obj in self.modfunctions if to_include(obj)
                ]
        # Recurse
        for obj in self.absinterfaces:
            obj.visible = True
        for obj in self.iterator(
            "functions",
            "subroutines",
            "types",
            "interfaces",
            "modprocedures",
            "modfunctions",
            "modsubroutines",
        ):
            obj.visible = True
        for obj in self.iterator(
            "functions",
            "subroutines",
            "types",
            "modprocedures",
            "modfunctions",
            "modsubroutines",
        ):
            obj.prune()


class FortranSourceFile(FortranContainer):
    """
    An object representing individual files containing Fortran code. A project
    will consist of a list of these objects. In turn, SourceFile objects will
    contains lists of all of that file's contents
    """

    def __init__(self, filepath, settings, preprocessor=None, fixed=False, **kwargs):
        # Hack to prevent FortranBase.__str__ to generate an anchor link to the source file in HTML output.
        self.visible = kwargs.get("incl_src", True)
        self.path = filepath.strip()
        self.name = os.path.basename(self.path)
        self.settings = settings
        self.fixed = fixed
        self.parent = None
        self.modules = []
        self.submodules = []
        self.functions = []
        self.subroutines = []
        self.programs = []
        self.blockdata = []
        self.doc = []
        self.hierarchy = []
        self.obj = "sourcefile"
        self.display = settings["display"]
        self.encoding = kwargs.get("encoding", True)

        source = ford.reader.FortranReader(
            self.path,
            settings["docmark"],
            settings["predocmark"],
            settings["docmark_alt"],
            settings["predocmark_alt"],
            fixed,
            settings["fixed_length_limit"].lower() == "true",
            preprocessor,
            settings["macro"],
            settings["include"],
            settings["encoding"],
        )

        FortranContainer.__init__(self, source, "")
        readobj = open(self.path, "r", encoding=settings["encoding"])
        self.raw_src = readobj.read()
        if self.fixed:
            self.src = highlight(
                self.raw_src,
                FortranFixedLexer(),
                HtmlFormatter(lineanchors="ln", cssclass="hl"),
            )
        else:
            self.src = highlight(
                self.raw_src,
                FortranLexer(),
                HtmlFormatter(lineanchors="ln", cssclass="hl"),
            )


class FortranModule(FortranCodeUnit):
    """
    An object representing individual modules within your source code. These
    objects contains lists of all of the module's contents, as well as its
    dependencies.
    """

    ONLY_RE = re.compile(r"^\s*,\s*only\s*:\s*(?=[^,])", re.IGNORECASE)
    RENAME_RE = re.compile(r"(\w+)\s*=>\s*(\w+)", re.IGNORECASE)

    def _initialize(self, line):
        self.name = line.group(1)
        self.uses = []
        self.variables = []
        self.enums = []
        self.public_list = []
        self.private_list = []
        self.protected_list = []
        self.subroutines = []
        self.functions = []
        self.interfaces = []
        self.absinterfaces = []
        self.types = []
        self.descendants = []
        self.common = []
        self.visible = True
        self.attr_dict = dict()
        self.param_dict = dict()

    def _cleanup(self):
        # Create list of all local procedures. Ones coming from other modules
        # will be added later, during correlation.
        self.all_procs = {}
        for p in self.routines:
            self.all_procs[p.name.lower()] = p
        for interface in self.interfaces:
            if not interface.abstract:
                self.all_procs[interface.name.lower()] = interface
            if interface.generic:
                for proc in interface.iterator("subroutines", "functions"):
                    self.all_procs[proc.name.lower()] = proc
        self.process_attribs()
        self.variables = [v for v in self.variables if "external" not in v.attribs]
        self.pub_procs = {}
        for p, proc in self.all_procs.items():
            if proc.permission == "public":
                self.pub_procs[p] = proc
        self.pub_vars = {}
        for var in self.variables:
            if var.permission == "public" or var.permission == "protected":
                self.pub_vars[var.name] = var
        self.pub_types = {}
        for dt in self.types:
            if dt.permission == "public":
                self.pub_types[dt.name] = dt
        self.pub_absints = {}
        for ai in self.absinterfaces:
            if ai.permission == "public":
                self.pub_absints[ai.name] = ai

    def get_used_entities(self, use_specs):
        """
        Returns the entities which are imported by a use statement. These
        are contained in dicts.
        """
        if len(use_specs.strip()) == 0:
            return (self.pub_procs, self.pub_absints, self.pub_types, self.pub_vars)

        only = bool(self.ONLY_RE.match(use_specs))
        use_specs = self.ONLY_RE.sub("", use_specs)
        # The used names after possible renaming
        used_names = {}
        for item in map(str.strip, use_specs.split(",")):
            match = self.RENAME_RE.search(item)
            if match:
                used_names[match.group(2).lower()] = match.group(1)
            else:
                used_names[item.lower()] = item

        def used_objects(object_type: str, only: bool) -> dict:
            """Get the objects that are actually used"""
            result = {}
            object_collection = getattr(self, object_type)
            for name, obj in object_collection.items():
                name = name.lower()
                if only:
                    if name in used_names:
                        result[used_names[name]] = obj
                else:
                    result[name] = obj
            return result

        ret_procs = used_objects("pub_procs", only)
        ret_absints = used_objects("pub_absints", only)
        ret_types = used_objects("pub_types", only)
        ret_vars = used_objects("pub_vars", only)
        return (ret_procs, ret_absints, ret_types, ret_vars)


class FortranSubmodule(FortranModule):
    def _initialize(self, line):
        FortranModule._initialize(self, line)
        self.name = line.group(3)
        self.ancestor = line.group(2)
        self.ancestor_mod = line.group(1)
        self.modprocedures = []
        del self.public_list
        del self.private_list
        del self.protected_list

    def _cleanup(self):
        # Create list of all local procedures. Ones coming from other modules
        # will be added later, during correlation.
        self.process_attribs()
        self.variables = [v for v in self.variables if "external" not in v.attribs]
        self.all_procs = {}
        for p in self.routines:
            self.all_procs[p.name.lower()] = p
        for interface in self.interfaces:
            if not interface.abstract:
                self.all_procs[interface.name.lower()] = interface
            if interface.generic:
                for proc in interface.iterator("subroutines", "functions"):
                    self.all_procs[proc.name.lower()] = proc


class FortranSubroutine(FortranCodeUnit):
    """
    An object representing a Fortran subroutine and holding all of said
    subroutine's contents.
    """

    def _initialize(self, line):
        self.proctype = "Subroutine"
        self.name = line.group(2)
        attribstr = line.group(1)
        self.module = False
        self.mp = False
        if not attribstr:
            attribstr = ""
        self.attribs = []
        if attribstr.find("impure") >= 0:
            self.attribs.append("impure")
            attribstr = attribstr.replace("impure", "", 1)
        if attribstr.find("pure") >= 0:
            self.attribs.append("pure")
            attribstr = attribstr.replace("pure", "", 1)
        if attribstr.find("elemental") >= 0:
            self.attribs.append("elemental")
            attribstr = attribstr.replace("elemental", "", 1)
        if attribstr.find("non_recursive") >= 0:
            self.attribs.append("non_recursive")
            attribstr = attribstr.replace("non_recursive", "", 1)
        if attribstr.find("recursive") >= 0:
            self.attribs.append("recursive")
            attribstr = attribstr.replace("recursive", "", 1)
        if attribstr.find("module") >= 0:
            self.module = True
            attribstr = attribstr.replace("module", "", 1)
        attribstr = re.sub(" ", "", attribstr)
        # ~ self.name = line.group(2)
        self.args = []
        if line.group(3):
            if self.SPLIT_RE.split(line.group(3)[1:-1]):
                for arg in self.SPLIT_RE.split(line.group(3)[1:-1]):
                    if arg.strip() != "":
                        self.args.append(arg.strip())
        self.bindC = line.group(4)
        self.variables = []
        self.enums = []
        self.uses = []
        self.calls = []
        self.optional_list = []
        self.subroutines = []
        self.functions = []
        self.interfaces = []
        self.absinterfaces = []
        self.types = []
        self.common = []
        self.attr_dict = dict()
        self.param_dict = dict()
        self.associate_blocks = []

    def set_permission(self, value):
        self._permission = value

    def get_permission(self):
        if type(self.parent) == FortranInterface and not self.parent.generic:
            return self.parent.permission
        else:
            return self._permission

    permission = property(get_permission, set_permission)

    def _cleanup(self):
        self.all_procs = {}
        for p in self.routines:
            self.all_procs[p.name.lower()] = p
        for interface in self.interfaces:
            if not interface.abstract:
                self.all_procs[interface.name.lower()] = interface
            if interface.generic:
                for proc in interface.iterator("subroutines", "functions"):
                    self.all_procs[proc.name.lower()] = proc
        for i in range(len(self.args)):
            for var in self.variables:
                if self.args[i].lower() == var.name.lower():
                    self.args[i] = var
                    self.variables.remove(var)
                    break
            if type(self.args[i]) == str:
                for intr in self.interfaces:
                    if not (intr.abstract or intr.generic):
                        proc = intr.procedure
                        if proc.name.lower() == self.args[i].lower():
                            self.args[i] = proc
                            self.interfaces.remove(intr)
                            self.args[i].parent = self
                            break
            if type(self.args[i]) == str:
                if self.args[i][0].lower() in "ijklmn":
                    vartype = "integer"
                else:
                    vartype = "real"
                self.args[i] = FortranVariable(self.args[i], vartype, self)
                self.args[i].doc = ""
        self.process_attribs()
        self.variables = [v for v in self.variables if "external" not in v.attribs]


class FortranFunction(FortranCodeUnit):
    """
    An object representing a Fortran function and holding all of said function's
    contents.
    """

    def _initialize(self, line):
        self.proctype = "Function"
        self.name = line.group(2)
        attribstr = line.group(1)
        self.module = False
        self.mp = False
        if not attribstr:
            attribstr = ""
        self.attribs = []
        if attribstr.lower().find("impure") >= 0:
            self.attribs.append("impure")
            attribstr = re.sub("impure", "", attribstr, 0, re.IGNORECASE)
        if attribstr.lower().find("pure") >= 0:
            self.attribs.append("pure")
            attribstr = re.sub("pure", "", attribstr, 0, re.IGNORECASE)
        if attribstr.lower().find("elemental") >= 0:
            self.attribs.append("elemental")
            attribstr = re.sub("elemental", "", attribstr, 0, re.IGNORECASE)
        if attribstr.lower().find("non_recursive") >= 0:
            self.attribs.append("non_recursive")
            attribstr = re.sub("non_recursive", "", attribstr, 0, re.IGNORECASE)
        if attribstr.lower().find("recursive") >= 0:
            self.attribs.append("recursive")
            attribstr = re.sub("recursive", "", attribstr, 0, re.IGNORECASE)
        if attribstr.lower().find("module") >= 0:
            self.module = True
            attribstr = re.sub("module", "", attribstr, 0, re.IGNORECASE)
        attribstr = re.sub(" ", "", attribstr)
        if line.group(4):
            self.retvar = line.group(4)
        else:
            self.retvar = self.name

        typestr = ""
        for vtype in self.settings["extra_vartypes"]:
            typestr = typestr + "|" + vtype
        var_type_re = re.compile(VAR_TYPE_STRING + typestr, re.IGNORECASE)
        if var_type_re.search(attribstr):
            rettype, retkind, retlen, retproto, rest = parse_type(
                attribstr, self.strings, self.settings
            )
            self.retvar = FortranVariable(
                self.retvar, rettype, self, kind=retkind, strlen=retlen, proto=retproto
            )
        self.args = []  # Set this in the correlation step

        for arg in self.SPLIT_RE.split(line.group(3)[1:-1]):
            # FIXME: This is to avoid a problem whereby sometimes an empty
            # argument list will appear to contain the argument ''. I didn't
            # know why it would do this (especially since sometimes it works
            # fine) and just put this in as a quick fix. However, at some point
            # I should try to figure out the actual root of the problem.
            if arg.strip() != "":
                self.args.append(arg.strip())
        try:
            self.bindC = ford.utils.get_parens(line.group(5), -1)[0:-1]
        except (RuntimeError, TypeError):
            self.bindC = line.group(5)
        if self.bindC:
            search_from = 0
            while QUOTES_RE.search(self.bindC[search_from:]):
                num = int(QUOTES_RE.search(self.bindC[search_from:]).group()[1:-1])
                self.bindC = self.bindC[0:search_from] + QUOTES_RE.sub(
                    self.parent.strings[num], self.bindC[search_from:], count=1
                )
                search_from += QUOTES_RE.search(self.bindC[search_from:]).end(0)
        self.variables = []
        self.enums = []
        self.uses = []
        self.calls = []
        self.optional_list = []
        self.subroutines = []
        self.functions = []
        self.interfaces = []
        self.absinterfaces = []
        self.types = []
        self.common = []
        self.attr_dict = dict()
        self.param_dict = dict()
        self.associate_blocks = []

    def set_permission(self, value):
        self._permission = value

    def get_permission(self):
        if type(self.parent) == FortranInterface and not self.parent.generic:
            return self.parent.permission
        else:
            return self._permission

    permission = property(get_permission, set_permission)

    def _cleanup(self):
        self.all_procs = {}
        for p in self.routines:
            self.all_procs[p.name.lower()] = p
        for interface in self.interfaces:
            if not interface.abstract:
                self.all_procs[interface.name.lower()] = interface
            if interface.generic:
                for proc in interface.iterator("subroutines", "functions"):
                    self.all_procs[proc.name.lower()] = proc
        for i in range(len(self.args)):
            for var in self.variables:
                if self.args[i].lower() == var.name.lower():
                    self.args[i] = var
                    self.variables.remove(var)
                    break
            if type(self.args[i]) == str:
                for intr in self.interfaces:
                    if not (intr.abstract or intr.generic):
                        proc = intr.procedure
                        if proc.name.lower() == self.args[i].lower():
                            self.args[i] = proc
                            self.interfaces.remove(intr)
                            self.args[i].parent = self
                            break
            if type(self.args[i]) == str:
                if self.args[i][0].lower() in "ijklmn":
                    vartype = "integer"
                else:
                    vartype = "real"
                self.args[i] = FortranVariable(self.args[i], vartype, self)
                self.args[i].doc = ""
        if type(self.retvar) != FortranVariable:
            for var in self.variables:
                if var.name.lower() == self.retvar.lower():
                    self.retvar = var
                    self.variables.remove(var)
                    break
            else:
                if self.retvar[0].lower() in "ijklmn":
                    vartype = "integer"
                else:
                    vartype = "real"
                self.retvar = FortranVariable(self.retvar, vartype, self)
        self.process_attribs()
        self.variables = [v for v in self.variables if "external" not in v.attribs]


class FortranSubmoduleProcedure(FortranCodeUnit):
    """
    An object representing a the implementation of a Module Function or
    Module Subroutine in a sumbmodule.
    """

    def _initialize(self, line):
        self.proctype = "Module Procedure"
        self.name = line.group(2)
        self.variables = []
        self.enums = []
        self.uses = []
        self.calls = []
        self.subroutines = []
        self.functions = []
        self.interfaces = []
        self.absinterfaces = []
        self.types = []
        self.attr_dict = dict()
        self.mp = True
        self.param_dict = dict()
        self.associate_blocks = []
        self.common = []

    def _cleanup(self):
        self.process_attribs()
        self.all_procs = {}
        for p in self.routines:
            self.all_procs[p.name.lower()] = p
        for interface in self.interfaces:
            if not interface.abstract:
                self.all_procs[interface.name.lower()] = interface
            if interface.generic:
                for proc in interface.iterator("subroutines", "functions"):
                    self.all_procs[proc.name.lower()] = proc
        self.variables = [v for v in self.variables if "external" not in v.attribs]


class FortranProgram(FortranCodeUnit):
    """
    An object representing the main Fortran program.
    """

    def _initialize(self, line):
        self.name = line.group(1)
        if self.name is None:
            self.name = ""
        self.variables = []
        self.enums = []
        self.subroutines = []
        self.functions = []
        self.interfaces = []
        self.types = []
        self.uses = []
        self.calls = []
        self.absinterfaces = []
        self.attr_dict = dict()
        self.param_dict = dict()
        self.associate_blocks = []
        self.common = []

    def _cleanup(self):
        self.all_procs = {}
        for p in self.routines:
            self.all_procs[p.name.lower()] = p
        for interface in self.interfaces:
            if not interface.abstract:
                self.all_procs[interface.name.lower()] = interface
            if interface.generic:
                for proc in interface.iterator("subroutines", "functions"):
                    self.all_procs[proc.name.lower()] = proc
        self.process_attribs()
        self.variables = [v for v in self.variables if "external" not in v.attribs]


class FortranType(FortranContainer):
    """
    An object representing a Fortran derived type and holding all of said type's
    components and type-bound procedures. It also contains information on the
    type's inheritance.
    """

    def _initialize(self, line):
        self.name = line.group(2)
        self.extends = None
        self.attributes = []
        if line.group(1):
            attribstr = line.group(1)[1:].strip()
            attriblist = self.SPLIT_RE.split(attribstr.strip())
            for attrib in attriblist:
                if EXTENDS_RE.search(attrib):
                    self.extends = EXTENDS_RE.search(attrib).group(1)
                elif attrib.strip().lower() == "public":
                    self.permission = "public"
                elif attrib.strip().lower() == "private":
                    self.permission = "private"
                elif attrib.strip().lower() == "external":
                    self.attributes.append("external")
                else:
                    self.attributes.append(attrib.strip())
        if line.group(3):
            paramstr = line.group(3).strip()
            self.parameters = self.SPLIT_RE.split(paramstr)
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

    def correlate(self, project):
        self.all_absinterfaces = self.parent.all_absinterfaces
        self.all_types = self.parent.all_types
        self.all_procs = self.parent.all_procs
        self.num_lines_all = self.num_lines

        # Match variables as needed (recurse)
        # ~ for i in range(len(self.variables)-1,-1,-1):
        # ~ self.variables[i].correlate(project)
        for v in self.variables:
            v.correlate(project)
        # Get inherited public components
        inherited = [
            var
            for var in getattr(self.extends, "variables", [])
            if var.permission == "public"
        ]
        self.local_variables = self.variables
        self.variables = inherited + self.variables

        # Match boundprocs with procedures
        # FIXME: This is not at all modular because must process non-generic bound procs first--could there be a better way to do it
        for proc in self.boundprocs:
            if not proc.generic:
                proc.correlate(project)
        # Identify inherited type-bound procedures which are not overridden
        inherited = []
        inherited_generic = []
        if self.extends and type(self.extends) is not str:
            for bp in self.extends.boundprocs:
                if bp.permission == "private":
                    continue
                if all([bp.name.lower() != b.name.lower() for b in self.boundprocs]):
                    if bp.generic:
                        gen = copy.copy(bp)
                        gen.parent = self
                        inherited.append(gen)
                    else:
                        inherited.append(bp)
                elif bp.generic:
                    gen = copy.copy(bp)
                    gen.parent = self
                    inherited_generic.append(gen)
        self.boundprocs = inherited + self.boundprocs
        # Match up generic type-bound procedures to their particular bindings
        for proc in self.boundprocs:
            for bp in inherited_generic:
                if bp.name.lower() == proc.name.lower():
                    proc.bindings = bp.bindings + proc.bindings
                    break
            if proc.generic:
                proc.correlate(project)
        # Match finalprocs
        for fp in self.finalprocs:
            fp.correlate(project)
        # Find a constructor, if one exists
        if self.name.lower() in self.all_procs:
            self.constructor = self.all_procs[self.name.lower()]
            self.constructor.permission = self.permission
            self.num_lines += getattr(
                self.constructor, "num_lines_all", self.constructor.num_lines
            )
        # Sort content
        self.sort()
        # Get total num_lines, including implementations
        for proc in self.finalprocs:
            self.num_lines_all += proc.procedure.num_lines
        for proc in self.boundprocs:
            for bind in proc.bindings:
                if isinstance(bind, (FortranFunction, FortranSubroutine)):
                    self.num_lines_all += bind.num_lines
                elif isinstance(bind, FortranBoundProcedure):
                    for b in bind.bindings:
                        if isinstance(b, (FortranFunction, FortranSubroutine)):
                            self.num_lines_all += b.num_lines

    def prune(self):
        """
        Remove anything which shouldn't be displayed.
        """
        self.boundprocs = [
            obj for obj in self.boundprocs if obj.permission in self.display
        ]
        self.variables = [
            obj for obj in self.variables if obj.permission in self.display
        ]
        for obj in self.boundprocs + self.variables:
            obj.visible = True


class FortranEnum(FortranContainer):
    """
    An object representing a Fortran enumeration. Contains the individual
    enumerators as variables.
    """

    def _initialize(self, line):
        self.variables = []

    def _cleanup(self):
        prev_val = -1
        for var in self.variables:
            if not var.initial:
                var.initial = prev_val + 1
            try:
                prev_val = int(var.initial)
            except ValueError:
                raise Exception("Non-integer assigned to enumerator.")


class FortranInterface(FortranContainer):
    """
    An object representing a Fortran interface.
    """

    def _initialize(self, line):
        self.proctype = "Interface"
        self.name = line.group(2)
        self.subroutines = []
        self.functions = []
        self.modprocs = []
        self.generic = bool(self.name)
        self.abstract = bool(line.group(1))
        if self.generic and self.abstract:
            raise Exception(
                "Generic interface {} can not be abstract".format(self.name)
            )

    def correlate(self, project):
        self.all_absinterfaces = self.parent.all_absinterfaces
        self.all_types = self.parent.all_types
        self.all_procs = self.parent.all_procs
        self.num_lines_all = self.num_lines
        if self.generic:
            for modproc in self.modprocs:
                if modproc.name.lower() not in self.all_procs:
                    raise RuntimeError(
                        f"Could not find interface procedure '{modproc.name}' in '{self.parent.name}'. "
                        f"Known procedures are: {list(self.all_procs.keys())}"
                    )
                modproc.procedure = self.all_procs[modproc.name.lower()]
                self.num_lines_all += modproc.procedure.num_lines
            for subrtn in self.subroutines:
                subrtn.correlate(project)
            for func in self.functions:
                func.correlate(project)
        else:
            self.procedure.correlate(project)
        # Sort content
        self.sort()

    def _cleanup(self):
        if self.abstract:
            contents = []
            for proc in self.routines:
                proc.visible = False
                item = copy.copy(self)
                item.procedure = proc
                item.procedure.parent = item
                del item.functions
                del item.modprocs
                del item.subroutines
                item.name = proc.name
                item.permission = proc.permission
                contents.append(item)
            self.contents = contents
        elif not self.generic:
            contents = []
            for proc in self.routines:
                proc.visible = False
                item = copy.copy(self)
                item.procedure = proc
                item.procedure.parent = item
                del item.functions
                del item.modprocs
                del item.subroutines
                item.name = proc.name
                item.permission = proc.permission
                contents.append(item)
            self.contents = contents


class FortranFinalProc(FortranBase):
    """
    An object representing a finalization procedure for a derived type
    within Fortran.
    """

    def __init__(self, name, parent, source=None):
        self.name = name
        self.parent = parent
        self.procedure = None
        self.obj = "finalproc"
        self.parobj = self.parent.obj
        self.display = self.parent.display
        self.settings = self.parent.settings
        self.doc = []
        if source:
            line = source.__next__()
            while line[0:2] == "!" + self.settings["docmark"]:
                self.doc.append(line[2:])
                line = source.__next__()
            source.pass_back(line)
        self.hierarchy = []
        cur = self.parent
        while cur:
            self.hierarchy.append(cur)
            cur = cur.parent
        self.hierarchy.reverse()

    def correlate(self, project):
        self.all_procs = self.parent.all_procs
        if self.name.lower() in self.all_procs:
            self.procedure = self.all_procs[self.name.lower()]


class FortranVariable(FortranBase):
    """
    An object representing a variable within Fortran.
    """

    def __init__(
        self,
        name,
        vartype,
        parent,
        attribs=[],
        intent="",
        optional=False,
        permission="public",
        parameter=False,
        kind=None,
        strlen=None,
        proto=None,
        doc=[],
        points=False,
        initial=None,
    ):
        self.name = name
        self.vartype = vartype.lower()
        self.parent = parent
        if self.parent:
            self.parobj = self.parent.obj
            self.settings = self.parent.settings
        else:
            self.parobj = None
            self.settings = None
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
        self.dimension = ""
        self.meta = {}
        self.visible = False

        indexlist = []
        indexparen = self.name.find("(")
        if indexparen > 0:
            indexlist.append(indexparen)
        indexbrack = self.name.find("[")
        if indexbrack > 0:
            indexlist.append(indexbrack)
        indexstar = self.name.find("*")
        if indexstar > 0:
            indexlist.append(indexstar)

        if len(indexlist) > 0:
            self.dimension = self.name[min(indexlist) :]
            self.name = self.name[0 : min(indexlist)]

        self.hierarchy = []
        cur = self.parent
        while cur:
            self.hierarchy.append(cur)
            cur = cur.parent
        self.hierarchy.reverse()

    def correlate(self, project):
        if (
            (self.vartype == "type" or self.vartype == "class")
            and self.proto
            and self.proto[0] != "*"
        ):
            if self.proto[0].lower() in self.parent.all_types:
                self.proto[0] = self.parent.all_types[self.proto[0].lower()]
        elif self.vartype == "procedure" and self.proto and self.proto[0] != "*":
            if self.proto[0].lower() in self.parent.all_procs:
                self.proto[0] = self.parent.all_procs[self.proto[0].lower()]
            elif self.proto[0].lower() in self.parent.all_absinterfaces:
                self.proto[0] = self.parent.all_absinterfaces[self.proto[0].lower()]


class FortranBoundProcedure(FortranBase):
    """
    An object representing a type-bound procedure, possibly overloaded.
    """

    def _initialize(self, line):
        attribstr = line.group(3)
        self.attribs = []
        self.deferred = False
        if attribstr:
            tmp_attribs = ford.utils.paren_split(",", attribstr[1:])
            for i in range(len(tmp_attribs)):
                tmp_attribs[i] = tmp_attribs[i].strip()
                if tmp_attribs[i].lower() == "public":
                    self.permission = "public"
                elif tmp_attribs[i].lower() == "private":
                    self.permission = "private"
                elif tmp_attribs[i].lower() == "deferred":
                    self.deferred = True
                else:
                    self.attribs.append(tmp_attribs[i])
        rest = line.group(4)
        split = self.POINTS_TO_RE.split(rest)
        self.name = split[0].strip()
        self.generic = line.group(1).lower() == "generic"
        self.proto = line.group(2)
        if self.proto:
            self.proto = self.proto[1:-1].strip()
        self.bindings = []
        if len(split) > 1:
            binds = self.SPLIT_RE.split(split[1])
            for bind in binds:
                self.bindings.append(bind.strip())
        else:
            self.bindings.append(self.name)
        if line.group(2):
            self.prototype = line.group(2)[1:-1]
        else:
            self.prototype = None

    def correlate(self, project):
        self.all_procs = self.parent.all_procs
        self.protomatch = False
        if self.proto:
            if self.proto.lower() in self.all_procs:
                self.proto = self.all_procs[self.proto.lower()]
                self.protomatch = True
            elif self.proto.lower() in self.parent.all_absinterfaces:
                self.proto = self.parent.all_absinterfaces[self.proto.lower()]
                self.protomatch = True
            # else:
            #    self.proto = FortranSpoof(self.proto, self, 'INTERFACE')
            #    self.protomatch = True
        if self.generic:
            for i in range(len(self.bindings)):
                for proc in self.parent.boundprocs:
                    if type(self.bindings[i]) is str:
                        if proc.name and proc.name.lower() == self.bindings[i].lower():
                            self.bindings[i] = proc
                            break
                    else:
                        if (
                            proc.name
                            and proc.name.lower() == self.bindings[i].name.lower()
                        ):
                            self.bindings[i] = proc
                            break
                # else:
                #    self.bindings[i] = FortranSpoof(self.bindings[i], self.parent, 'BOUNDPROC')
        elif not self.deferred:
            for i in range(len(self.bindings)):
                if self.bindings[i].lower() in self.all_procs:
                    self.bindings[i] = self.all_procs[self.bindings[i].lower()]
                    break
            # else:
            #    self.bindings[i] = FortranSpoof(self.bindings[i], self.parent, 'BOUNDPROC')
        # Sort content
        self.sort()


class FortranModuleProcedure(FortranBase):
    """
    An object representing a module procedure in an interface. Not to be
    confused with type of module procedure which is the implementation of
    a module function or module subroutine in a submodule.
    """

    def __init__(self, name, parent=None, inherited_permission=None):
        if inherited_permission is not None:
            self.permission = inherited_permission.lower()
        else:
            self.permission = None
        self.parent = parent
        if self.parent:
            self.parobj = self.parent.obj
            self.settings = self.parent.settings
        else:
            self.parobj = None
            self.settings = None
        self.obj = "moduleprocedure"
        self.name = name
        self.procedure = None
        self.doc = []
        self.hierarchy = []
        cur = self.parent
        while cur:
            self.hierarchy.append(cur)
            cur = cur.parent
        self.hierarchy.reverse()


class FortranBlockData(FortranContainer):
    """
    An object representing a block-data unit. Now obsolete due to modules,
    block data units allowed variables held in common blocks to be initialized
    outside of an executing program unit.
    """

    def _initialize(self, line):
        self.name = line.group(1)
        if not self.name:
            self.name = "<em>unnamed</em>"
        self.uses = []
        self.variables = []
        self.types = []
        self.common = []
        self.visible = True
        self.attr_dict = dict()
        self.param_dict = dict()

    def correlate(self, project):
        # Add procedures, interfaces and types from parent to our lists
        self.all_types = {}
        for dt in self.types:
            self.all_types[dt.name.lower()] = dt
        self.all_vars = {}
        for var in self.variables:
            self.all_vars[var.name.lower()] = var
        self.all_absinterfaces = {}
        self.all_procs = {}

        # Add procedures and types from USED modules to our lists
        for mod, extra in self.uses:
            if type(mod) is str:
                continue
            procs, absints, types, variables = mod.get_used_entities(extra)
            self.all_procs.update(procs)
            self.all_absinterfaces.update(absints)
            self.all_types.update(types)
            self.all_vars.update(variables)
        self.uses = [m[0] for m in self.uses]

        typelist = {}
        for dtype in self.types:
            if dtype.extends and dtype.extends.lower() in self.all_types:
                dtype.extends = self.all_types[dtype.extends.lower()]
                typelist[dtype] = set([dtype.extends])
            else:
                typelist[dtype] = set([])
        typeorder = toposort.toposort_flatten(typelist)

        for dtype in typeorder:
            dtype.visible = True
            if dtype in self.types:
                dtype.correlate(project)
        for var in self.variables:
            var.correlate(project)
        for com in self.common:
            com.correlate(project)
        # Sort content
        self.sort()

    def prune(self):
        self.types = [obj for obj in self.types if obj.permission in self.display]
        self.variables = [
            obj for obj in self.variables if obj.permission in self.display
        ]
        for dtype in self.types:
            dtype.visible = True
        for dtype in self.types:
            dtype.prune()

    def _cleanup(self):
        self.process_attribs()

    def process_attribs(self):
        for item in self.types:
            for attr in self.attr_dict.get(item.name.lower(), []):
                if "public" in self.attr_dict[item.name.lower()]:
                    item.permission = "public"
                elif "private" in self.attr_dict[item.name.lower()]:
                    item.permission = "private"
                elif attr[0:4] == "bind":
                    if hasattr(item, "bindC"):
                        item.bindC = attr[5:-1]
                    elif getattr(item, "procedure", None):
                        item.procedure.bindC = attr[5:-1]
                    else:
                        item.attribs.append(attr[5:-1])
        for var in self.variables:
            for attr in self.attr_dict.get(var.name.lower(), []):
                if attr == "public" or attr == "private" or attr == "protected":
                    var.permission = attr
                elif attr[0:6] == "intent":
                    var.intent = attr[7:-1]
                elif DIM_RE.match(attr) and (
                    "pointer" in attr or "allocatable" in attr
                ):
                    i = attr.index("(")
                    var.attribs.append(attr[0:i])
                    var.dimension = attr[i:]
                elif attr == "parameter":
                    var.attribs.append(attr)
                    var.initial = self.param_dict[var.name.lower()]
                else:
                    var.attribs.append(attr)
        del self.attr_dict


class FortranCommon(FortranBase):
    """
    An object representing a common block. This is a legacy feature.
    """

    def _initialize(self, line):
        self.name = line.group(1)
        if not self.name:
            self.name = ""
        self.other_uses = []
        self.variables = [v.strip() for v in ford.utils.paren_split(",", line.group(2))]
        self.visible = True

    def correlate(self, project):
        for i in range(len(self.variables)):
            if self.variables[i] in self.parent.all_vars:
                self.variables[i] = self.parent.all_vars[self.variables[i]]
                try:
                    self.parent.variables.remove(self.variables[i])
                except ValueError:
                    pass
            else:
                if self.variables[i][0].lower() in "ijklmn":
                    vartype = "integer"
                else:
                    vartype = "real"
                self.variables[i] = FortranVariable(self.variables[i], vartype, self)
                self.variables[i].doc = ""

        if self.name in project.common:
            self.other_uses = project.common[self.name]
            self.other_uses.append(self)
        else:
            lst = [
                self,
            ]
            project.common[self.name] = lst
            self.other_uses = lst
        # Sort content
        self.sort()


class FortranSpoof(object):
    """
    A dummy-type which is used to represent arguments, interfaces, type-bound
    procedures, etc. which lack a corresponding variable or implementation.
    """

    IS_SPOOF = True

    def __init__(self, name, parent=None, obj="ITEM"):
        self.name = name
        self.parent = parent
        self.obj = obj
        if self.parent.settings["warn"]:
            print(
                "Warning: {} {} in {} {} could not be matched to "
                "corresponding item in code (file {}).".format(
                    self.obj.upper(),
                    self.name,
                    self.parent.obj.upper(),
                    self.parent.name,
                    self.parent.hierarchy[0].name,
                )
            )

    def __getitem__(self, key):
        return []

    def __len__(self):
        return 0

    def __contains__(self, item):
        return False

    def __getattr__(self, name):
        return []

    def __str__(self):
        return self.name


class GenericSource(FortranBase):
    """
    Represent a non-Fortran source file. The contents of the file will
    not be analyzed, but documentation can be extracted.
    """

    def __init__(self, filename, settings):
        self.obj = "sourcefile"
        self.parobj = None
        self.parent = None
        self.hierarchy = []
        self.settings = settings
        self.num_lines = 0
        extra_filetypes = settings["extra_filetypes"][filename.split(".")[-1]]
        comchar = extra_filetypes[0]
        if len(extra_filetypes) > 1:
            self.lexer_str = extra_filetypes[1]
        else:
            self.lexer_str = None
        docmark = settings["docmark"]
        predocmark = settings["predocmark"]
        docmark_alt = settings["docmark_alt"]
        predocmark_alt = settings["predocmark_alt"]
        self.path = filename.strip()
        self.name = os.path.basename(self.path)
        with open(filename, "r", encoding=settings["encoding"]) as r:
            self.raw_src = r.read()
        # TODO: Get line numbers to display properly
        if self.lexer_str is None:
            lexer = guess_lexer_for_filename(self.name, self.raw_src)
        else:
            import pygments.lexers

            lexer = getattr(pygments.lexers, self.lexer_str)
        self.src = highlight(
            self.raw_src, lexer, HtmlFormatter(lineanchors="ln", cssclass="hl")
        )
        com_re = re.compile(
            r"^((?!{0}|[\"']).|(\'[^']*')|(\"[^\"]*\"))*({0}.*)$".format(
                re.escape(comchar)
            )
        )
        if docmark == docmark_alt != "":
            raise Exception("Error: docmark and docmark_alt are the same.")
        if docmark == predocmark_alt != "":
            raise Exception("Error: docmark and predocmark_alt are the same.")
        if docmark_alt == predocmark != "":
            raise Exception("Error: docmark_alt and predocmark are the same.")
        if predocmark == predocmark_alt != "":
            raise Exception("Error: predocmark and predocmark_alt are the same.")
        if len(predocmark) != 0:
            doc_re = re.compile(
                r"^((?!{0}|[\"']).|('[^']*')|(\"[^\"]*\"))*({0}(?:{1}|{2}).*)$".format(
                    re.escape(comchar), re.escape(docmark), re.escape(predocmark)
                )
            )
        else:
            doc_re = re.compile(
                r"^((?!{0}|[\"']).|('[^']*')|(\"[^\"]*\"))*({0}{1}.*)$".format(
                    re.escape(comchar), re.escape(docmark)
                )
            )
        if len(docmark_alt) != 0 and len(predocmark_alt) != 0:
            doc_alt_re = re.compile(
                r"^((?!{0}|[\"']).|('[^']*')|(\"[^\"]*\"))*({0}(?:{1}|{2}).*)$".format(
                    re.escape(comchar),
                    re.escape(docmark_alt),
                    re.escape(predocmark_alt),
                )
            )
        elif len(docmark_alt) != 0:
            doc_alt_re = re.compile(
                r"^((?!{0}|[\"']).|('[^']*')|(\"[^\"]*\"))*({0}{1}.*)$".format(
                    re.escape(comchar), re.escape(docmark_alt)
                )
            )
        elif len(predocmark_alt) != 0:
            doc_alt_re = re.compile(
                r"^((?!{0}|[\"']).|('[^']*')|(\"[^\"]*\"))*({0}{1}.*)$".format(
                    re.escape(comchar), re.escape(predocmark_alt)
                )
            )
        else:
            doc_alt_re = None
        self.doc = []
        prevdoc = False
        docalt = False
        for line in open(filename, "r", encoding=settings["encoding"]):
            line = line.strip()
            if doc_alt_re:
                match = doc_alt_re.match(line)
            else:
                match = False
            if match:
                prevdoc = True
                docalt = True
                doc = match.group(4)
                if doc.startswith(comchar + docmark_alt):
                    doc = doc[len(comchar + docmark_alt) :].strip()
                else:
                    doc = doc[len(comchar + predocmark_alt) :].strip()
                self.doc.append(doc)
                continue
            match = doc_re.match(line)
            if match:
                prevdoc = True
                if docalt:
                    docalt = False
                doc = match.group(4)
                if doc.startswith(comchar + docmark):
                    doc = doc[len(comchar + docmark) :].strip()
                else:
                    doc = doc[len(comchar + predocmark) :].strip()
                self.doc.append(doc)
                continue
            match = com_re.match(line)
            if match:
                if docalt:
                    if match.start(4) == 0:
                        doc = match.group(4)
                        doc = doc[len(comchar) :].strip()
                        self.doc.append(doc)
                    else:
                        docalt = False
                elif prevdoc:
                    prevdoc = False
                    self.doc.append("")
                continue
            # if not including any comment...
            if prevdoc:
                self.doc.append("")
                prevdoc = False
            docalt = False

    def lines_description(self, total, total_all=0):
        return ""


_can_have_contains = [
    FortranModule,
    FortranProgram,
    FortranFunction,
    FortranSubroutine,
    FortranType,
    FortranSubmodule,
    FortranSubmoduleProcedure,
]


def line_to_variables(source, line, inherit_permission, parent):
    """
    Returns a list of variables declared in the provided line of code. The
    line of code should be provided as a string.
    """
    vartype, kind, strlen, proto, rest = parse_type(
        line, parent.strings, parent.settings
    )
    attribs = []
    intent = ""
    optional = False
    permission = inherit_permission
    parameter = False

    attribmatch = ATTRIBSPLIT_RE.match(rest)
    if attribmatch:
        attribstr = attribmatch.group(1).strip()
        declarestr = attribmatch.group(2).strip()
        tmp_attribs = ford.utils.paren_split(",", attribstr)
        for i in range(len(tmp_attribs)):
            tmp_attribs[i] = tmp_attribs[i].strip()
            if tmp_attribs[i].lower() == "public":
                permission = "public"
            elif tmp_attribs[i].lower() == "private":
                permission = "private"
            elif tmp_attribs[i].lower() == "protected":
                permission = "protected"
            elif tmp_attribs[i].lower() == "optional":
                optional = True
            elif tmp_attribs[i].lower() == "parameter":
                parameter = True
            elif tmp_attribs[i].lower().replace(" ", "") == "intent(in)":
                intent = "in"
            elif tmp_attribs[i].lower().replace(" ", "") == "intent(out)":
                intent = "out"
            elif tmp_attribs[i].lower().replace(" ", "") == "intent(inout)":
                intent = "inout"
            else:
                attribs.append(tmp_attribs[i])
    else:
        declarestr = ATTRIBSPLIT2_RE.match(rest).group(2)
    declarations = ford.utils.paren_split(",", declarestr)

    varlist = []
    for dec in declarations:
        dec = re.sub(" ", "", dec)
        split = ford.utils.paren_split("=", dec)
        if len(split) > 1:
            name = split[0]
            if split[1][0] == ">":
                initial = split[1][1:]
                points = True
            else:
                initial = split[1]
                points = False
        else:
            name = dec.strip()
            initial = None
            points = False

        if initial:
            initial = COMMA_RE.sub(", ", initial)
            search_from = 0
            while QUOTES_RE.search(initial[search_from:]):
                num = int(QUOTES_RE.search(initial[search_from:]).group()[1:-1])
                string = NBSP_RE.sub("&nbsp;", parent.strings[num])
                string = string.replace("\\", "\\\\")
                initial = initial[0:search_from] + QUOTES_RE.sub(
                    string, initial[search_from:], count=1
                )
                search_from += QUOTES_RE.search(initial[search_from:]).end(0)

        if proto:
            varlist.append(
                FortranVariable(
                    name,
                    vartype,
                    parent,
                    copy.copy(attribs),
                    intent,
                    optional,
                    permission,
                    parameter,
                    kind,
                    strlen,
                    list(proto),
                    [],
                    points,
                    initial,
                )
            )
        else:
            varlist.append(
                FortranVariable(
                    name,
                    vartype,
                    parent,
                    copy.copy(attribs),
                    intent,
                    optional,
                    permission,
                    parameter,
                    kind,
                    strlen,
                    proto,
                    [],
                    points,
                    initial,
                )
            )

    doc = []
    docline = source.__next__()
    while docline[0:2] == "!" + parent.settings["docmark"]:
        doc.append(docline[2:])
        docline = source.__next__()
    source.pass_back(docline)
    for var in varlist:
        var.doc = doc
    return varlist


def parse_type(string, capture_strings, settings):
    """
    Gets variable type, kind, length, and/or derived-type attributes from a
    variable declaration.
    """
    typestr = ""
    for vtype in settings["extra_vartypes"]:
        typestr = typestr + "|" + vtype
    var_type_re = re.compile(VAR_TYPE_STRING + typestr, re.IGNORECASE)
    match = var_type_re.match(string)
    if not match:
        raise Exception("Invalid variable declaration: {}".format(string))

    vartype = match.group().lower()
    if DOUBLE_PREC_RE.match(vartype):
        vartype = "double precision"
    if DOUBLE_CMPLX_RE.match(vartype):
        vartype = "double complex"
    rest = string[match.end() :].strip()
    kindstr = ford.utils.get_parens(rest)
    rest = rest[len(kindstr) :].strip()

    if (
        len(kindstr) < 3
        and vartype != "type"
        and vartype != "class"
        and not kindstr.startswith("*")
    ):
        return (vartype, None, None, None, rest)
    match = VARKIND_RE.search(kindstr)
    if match:
        if match.group(1):
            star = False
            args = match.group(1).strip()
        else:
            star = True
            args = match.group(2).strip()
            if args.startswith("("):
                args = args[1:-1].strip()

        args = re.sub(r"\s", "", args)
        if vartype == "type" or vartype == "class" or vartype == "procedure":
            PROTO_RE = re.compile(r"(\*|\w+)\s*(?:\((.*)\))?")
            try:
                proto = list(PROTO_RE.match(args).groups())
                if not proto[1]:
                    proto[1] = ""
            except AttributeError:
                raise Exception(
                    "Bad type, class, or procedure prototype specification: {}".format(
                        args
                    )
                )
            return (vartype, None, None, proto, rest)
        elif vartype == "character":
            if star:
                return (vartype, None, args, None, rest)
            else:
                kind = None
                length = None
                if KIND_RE.search(args):
                    kind = KIND_RE.sub("", args)
                    try:
                        match = QUOTES_RE.search(kind)
                        num = int(match.group()[1:-1])
                        kind = QUOTES_RE.sub(capture_strings[num], kind)
                    except AttributeError:
                        pass
                elif LEN_RE.search(args):
                    length = LEN_RE.sub("", args)
                else:
                    length = args
                return (vartype, kind, length, None, rest)
        else:
            kind = KIND_RE.sub("", args)
            return (vartype, kind, None, None, rest)

    raise Exception("Bad declaration of variable type {}: {}".format(vartype, string))


def set_base_url(url):
    FortranBase.base_url = url


def get_mod_procs(source, line, parent):
    inherit_permission = parent.permission
    retlist = []
    SPLIT_RE = re.compile(r"\s*,\s*", re.IGNORECASE)
    splitlist = SPLIT_RE.split(line.group(2))
    if splitlist and len(splitlist) > 0:
        for item in splitlist:
            retlist.append(FortranModuleProcedure(item, parent, inherit_permission))
    else:
        retlist.append(
            FortranModuleProcedure(line.group(1), parent, inherit_permission)
        )

    doc = []
    docline = source.__next__()
    while docline[0:2] == "!" + parent.settings["docmark"]:
        doc.append(docline[2:])
        docline = source.__next__()
    source.pass_back(docline)
    retlist[-1].doc = doc

    return retlist


def sort_items(self, items, args=False):
    """
    Sort the `self`'s contents, as contained in the list `items` as
    specified in `self`'s meta-data.
    """
    if self.settings["sort"].lower() == "src":
        return

    def alpha(i):
        return i.name

    def permission(i):
        if args:
            if i.intent == "in":
                return "b"
            if i.intent == "inout":
                return "c"
            if i.intent == "out":
                return "d"
            if i.intent == "":
                return "e"
        perm = getattr(i, "permission", "")
        if perm == "public":
            return "b"
        if perm == "protected":
            return "c"
        if perm == "private":
            return "d"
        return "a"

    def permission_alpha(i):
        return permission(i) + "-" + i.name

    def itype(i):
        if i.obj == "variable":
            retstr = i.vartype
            if retstr == "class":
                retstr = "type"
            if i.kind:
                retstr = retstr + "-" + str(i.kind)
            if i.strlen:
                retstr = retstr + "-" + str(i.strlen)
            if i.proto:
                retstr = retstr + "-" + i.proto[0]
            return retstr
        elif i.obj == "proc":
            if i.proctype != "Function":
                return i.proctype.lower()
            else:
                return i.proctype.lower() + "-" + itype(i.retvar)
        else:
            return i.obj

    def itype_alpha(i):
        return itype(i) + "-" + i.name

    if self.settings["sort"].lower() == "alpha":
        items.sort(key=alpha)
    elif self.settings["sort"].lower() == "permission":
        items.sort(key=permission)
    elif self.settings["sort"].lower() == "permission-alpha":
        items.sort(key=permission_alpha)
    elif self.settings["sort"].lower() == "type":
        items.sort(key=itype)
    elif self.settings["sort"].lower() == "type-alpha":
        items.sort(key=itype_alpha)


class NameSelector(object):
    """
    Object which tracks what names have been provided for different
    entities in Fortran code. It will provide an identifier which is
    guaranteed to be unique. This identifier can then me used as a
    filename for the documentation of that entity.
    """

    def __init__(self):
        self._items = {}
        self._counts = {}

    def get_name(self, item):
        """
        Return the name for this item registered with this NameSelector.
        If no name has previously been registered, then generate a new
        one.
        """
        if not isinstance(item, ford.sourceform.FortranBase):
            raise Exception(
                "{} is not of a type derived from FortranBase".format(str(item))
            )

        if item in self._items:
            return self._items[item]
        else:
            if item.get_dir() not in self._counts:
                self._counts[item.get_dir()] = {}
            if item.name in self._counts[item.get_dir()]:
                num = self._counts[item.get_dir()][item.name] + 1
            else:
                num = 1
            self._counts[item.get_dir()][item.name] = num
            name = item.name.lower().replace("<", "lt")
            # name is already lower
            name = name.replace(">", "gt")
            name = name.replace("/", "SLASH")
            if name == "":
                name = "__unnamed__"
            if num > 1:
                name = name + "~" + str(num)
            self._items[item] = name
            return name


namelist = NameSelector()


class ExternalModule(FortranModule):
    def __init__(self):
        self.name = ""
        self.uses = []
        self.pub_procs = {}
        self.pub_absints = {}
        self.pub_types = {}
        self.pub_vars = {}
        self.external_url = ""


class ExternalFunction(FortranFunction):
    def __init__(self):
        self.name = ""
        self.external_url = ""


class ExternalSubroutine(FortranSubroutine):
    def __init__(self):
        self.name = ""
        self.external_url = ""


class ExternalInterface(FortranInterface):
    def __init__(self):
        self.name = ""
        self.external_url = ""


class ExternalType(FortranType):
    def __init__(self):
        self.name = ""
        self.external_url = ""


class ExternalVariable(FortranVariable):
    def __init__(self):
        self.name = ""
        self.external_url = ""
