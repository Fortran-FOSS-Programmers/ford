#!/usr/bin/env python
# -- coding: utf-8 --
#
#  ford.py
#
#  Copyright 2014 Christopher MacMackin <cmacmackin@gmail.com>
#  This file is part of FORD.
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

from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from io import StringIO
import itertools
import sys
import argparse
import os
import pathlib
import subprocess
from datetime import date, datetime
from typing import (
    Any,
    Dict,
    Union,
    Optional,
    Tuple,
    List,
    Type,
    get_args,
    get_origin,
    get_type_hints,
)
from textwrap import dedent
import warnings
from markdown_include.include import (
    INC_SYNTAX as MD_INCLUDE_RE,
    MarkdownInclude,
    IncludePreprocessor,
)

from ford.external_project import dump_modules
import ford.fortran_project
import ford.sourceform
import ford.output
import ford.utils
from ford.pagetree import get_page_tree
from ford._markdown import MetaMarkdown
from ford.version import __version__
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]


PathLike = Union[os.PathLike, str]

__appname__ = "FORD"
__author__ = "Chris MacMackin"
__credits__ = [
    "Balint Aradi",
    "Iain Barrass",
    "Izaak Beekman",
    "Jérémie Burgalat",
    "David Dickinson",
    "Gavin Huttley",
    "Harald Klimach",
    "Nick R. Papior",
    "Marco Restelli",
    "Schildkroete23",
    "Stephen J. Turnbull",
    "Jacob Williams",
    "Stefano Zhagi",
]
__license__ = "GPLv3"
__maintainer__ = "Chris MacMackin"
__status__ = "Production"


@contextmanager
def stdout_redirector(stream):
    old_stdout = sys.stdout
    sys.stdout = stream
    try:
        yield
    finally:
        sys.stdout = old_stdout


LICENSES = {
    "by": (
        '<a rel="license" href="http://creativecommons.org/licenses/by/4.0/">'
        '<img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by/4.0/80x15.png" /></a>'
    ),
    "by-nd": (
        '<a rel="license" href="http://creativecommons.org/licenses/by-nd/4.0/">'
        '<img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nd/4.0/80x15.png" /></a>'
    ),
    "by-sa": (
        '<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/">'
        '<img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/80x15.png" /></a>'
    ),
    "by-nc": (
        '<a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/">'
        '<img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc/4.0/80x15.png" /></a>'
    ),
    "by-nc-nd": (
        '<a rel="license" href="http://creativecommons.org/licenses/by-nc-nd/4.0/">'
        '<img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-nd/4.0/80x15.png" /></a>'
    ),
    "by-nc-sa": (
        '<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/">'
        '<img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-sa/4.0/80x15.png" /></a>'
    ),
    "gfdl": '<a rel="license" href="http://www.gnu.org/licenses/old-licenses/fdl-1.2.en.html">GNU Free Documentation License</a>',
    "opl": '<a rel="license" href="http://opencontent.org/openpub/">Open Publication License</a>',
    "pdl": '<a rel="license" href="http://www.openoffice.org/licenses/PDL.html">Public Documentation License</a>',
    "bsd": '<a rel="license" href="http://www.freebsd.org/copyright/freebsd-doc-license.html">FreeBSD Documentation License</a>',
    "isc": '<a rel="license" href="https://opensource.org/licenses/ISC">ISC (Internet Systems Consortium) License</a>',
    "mit": '<a rel="license" href="https://opensource.org/licenses/MIT">MIT</a>',
    "": "",
}


def default_cpus() -> int:
    try:
        import multiprocessing

        return multiprocessing.cpu_count()
    except (ImportError, NotImplementedError):
        return 0


def is_same_type(type_in: Type, tp: Type) -> bool:
    """Returns True if ``type_in`` is the same type as either ``tp``
    or ``Optional[tp]``"""
    return (
        (type_in is tp) or (get_origin(type_in) is tp) or is_optional_type(type_in, tp)
    )


def is_optional_type(tp: Type, sub_tp: Type) -> bool:
    """Returns True if ``tp`` is ``Optional[sub_tp]``"""
    if get_origin(tp) is not Union:
        return False

    return any(tp is sub_tp for tp in get_args(tp))


@dataclass
class Settings:
    alias: List[str] = field(default_factory=list)
    author: Optional[str] = None
    author_description: Optional[str] = None
    author_pic: Optional[str] = None
    bitbucket: Optional[str] = None
    coloured_edges: bool = False
    copy_subdir: List[str] = field(default_factory=list)
    creation_date: str = "%Y-%m-%dT%H:%M:%S.%f%z"
    css: Optional[str] = None
    dbg: bool = True
    display: List[str] = field(default_factory=lambda: ["public", "protected"])
    doc_license: str = ""
    docmark: str = "!"
    docmark_alt: str = "*"
    email: Optional[str] = None
    encoding: str = "utf-8"
    exclude: List[str] = field(default_factory=list)
    exclude_dir: List[str] = field(default_factory=list)
    extensions: List[str] = field(
        default_factory=lambda: ["f90", "f95", "f03", "f08", "f15"]
    )
    external: list = field(default_factory=list)
    externalize: bool = False
    extra_filetypes: list = field(default_factory=list)
    extra_mods: list = field(default_factory=list)
    extra_vartypes: list = field(default_factory=list)
    facebook: Optional[str] = None
    favicon: str = "default-icon"
    fixed_extensions: list = field(default_factory=lambda: ["f", "for", "F", "FOR"])
    fixed_length_limit: bool = True
    force: bool = False
    fpp_extensions: list = field(
        default_factory=lambda: ["F90", "F95", "F03", "F08", "F15", "F", "FOR"]
    )
    github: Optional[str] = None
    gitlab: Optional[str] = None
    gitter_sidecar: Optional[str] = None
    google_plus: Optional[str] = None
    graph: bool = False
    graph_dir: Optional[str] = None
    graph_maxdepth: int = 10000
    graph_maxnodes: int = 1000000000
    hide_undoc: bool = False
    incl_src: bool = True
    include: list = field(default_factory=list)
    license: str = ""
    linkedin: Optional[str] = None
    lower: bool = False
    macro: list = field(default_factory=list)
    mathjax_config: Optional[str] = None
    max_frontpage_items: int = 10
    md_extensions: list = field(default_factory=list)
    media_dir: Optional[str] = None
    output_dir: str = "./doc"
    page_dir: Optional[str] = None
    parallel: int = default_cpus()
    predocmark: str = ">"
    predocmark_alt: str = "|"
    preprocess: bool = True
    preprocessor: str = "cpp -traditional-cpp -E -D__GFORTRAN__"
    print_creation_date: bool = False
    privacy_policy_url: Optional[str] = None
    proc_internals: bool = False
    project: str = "Fortran Program"
    project_bitbucket: Optional[str] = None
    project_download: Optional[str] = None
    project_github: Optional[str] = None
    project_gitlab: Optional[str] = None
    project_sourceforge: Optional[str] = None
    project_url: str = ""
    project_website: Optional[str] = None
    quiet: bool = False
    revision: Optional[str] = None
    search: bool = True
    show_proc_parent: bool = False
    sort: str = "src"
    source: bool = False
    src_dir: list = field(default_factory=lambda: ["./src"])
    summary: Optional[str] = None
    terms_of_service_url: Optional[str] = None
    twitter: Optional[str] = None
    version: Optional[str] = None
    warn: bool = False
    website: Optional[str] = None
    year: str = str(date.today().year)

    def __post_init__(self):
        field_types = get_type_hints(self)

        for key, value in asdict(self).items():
            default_type = field_types[key]

            if is_same_type(default_type, type(value)):
                continue

            if is_same_type(default_type, list):
                setattr(self, key, [value])


def convert_to_bool(name: str, option: List[str]) -> bool:
    """Convert value 'option' to a bool, with a nice error message on
    failure. Expects a list from the markdown meta-data extension"""
    if isinstance(option, bool):
        return option

    if len(option) > 1:
        raise ValueError(
            f"Could not convert option '{name}' to bool: expected a single value but got a list ({option})"
        )
    try:
        return ford.utils.str_to_bool(option[0])
    except ValueError:
        raise ValueError(
            f"Could not convert option '{name}' to bool: expected 'true'/'false', got: {option[0]}"
        )


def initialize():
    """
    Method to parse and check configurations of FORD, get the project's
    global documentation, and create the Markdown reader.
    """
    args = get_command_line_arguments()

    # Read in the project-file. This will contain global documentation (which
    # will appear on the homepage) as well as any information about the project
    # and settings for generating the documentation

    proj_docs = args.project_file.read()
    directory = os.path.dirname(args.project_file.name)
    proj_docs, proj_data, md = load_settings(proj_docs, directory)

    return *parse_arguments(vars(args), proj_docs, proj_data, directory), md


def get_command_line_arguments() -> argparse.Namespace:
    """Read the command line arguments"""

    parser = argparse.ArgumentParser(
        "ford",
        description="Document a program or library written in modern Fortran. "
        "Any command-line options over-ride those specified in the project file.",
    )
    parser.add_argument(
        "project_file",
        help="file containing the description and settings for the project",
        type=argparse.FileType("r", encoding="UTF-8"),
    )
    parser.add_argument(
        "-d",
        "--src_dir",
        action="append",
        help="directories containing all source files for the project (default: ``./src``)",
    )
    parser.add_argument(
        "-p",
        "--page_dir",
        help="directory containing static pages (default: None)",
    )
    parser.add_argument(
        "-o",
        "--output_dir",
        help="directory in which to place output files (default: ``./doc``)",
    )
    parser.add_argument("-s", "--css", help="custom style-sheet for the output")
    parser.add_argument(
        "-r",
        "--revision",
        dest="revision",
        help="source code version number or revision of the project to document",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        help="list of files which should not be included in the documentation",
    )
    parser.add_argument(
        "--exclude_dir",
        action="append",
        help="list of directories whose contents should not be included in the documentation",
    )
    parser.add_argument(
        "-e",
        "--extensions",
        action="append",
        help="extensions which should be scanned for documentation (default: ``f90, f95, f03, f08``)",
    )
    parser.add_argument(
        "-m",
        "--macro",
        action="append",
        help="preprocessor macros (optionally with values) to be applied to preprocessed files",
    )
    parser.add_argument(
        "-w",
        "--warn",
        dest="warn",
        action="store_true",
        default=None,
        help="display warnings for undocumented items",
    )
    parser.add_argument(
        "-f",
        "--force",
        dest="force",
        action="store_true",
        default=None,
        help="try to continue to read files even if there are fatal errors",
    )
    parser.add_argument(
        "-g",
        "--graph",
        dest="graph",
        action="store_true",
        default=None,
        help="generate graphs for documentation output",
    )
    parser.add_argument(
        "--no-search",
        dest="search",
        action="store_false",
        default=None,
        help="don't process documentation to produce a search feature",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        dest="quiet",
        action="store_true",
        default=None,
        help="suppress normal output",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s version {__version__}",
    )
    parser.add_argument(
        "--debug",
        dest="dbg",
        action="store_true",
        default=None,
        help="display traceback if fatal exception occurs and print faulty line",
    )
    parser.add_argument(
        "-I",
        "--include",
        action="append",
        help="list of directories to be searched for ``include`` files",
    )
    parser.add_argument(
        "--externalize",
        action="store_const",
        const="true",
        help="provide information about Fortran objects in a json database for "
        "other FORD projects to refer to.",
    )
    parser.add_argument(
        "-L",
        "--external_links",
        dest="external",
        action="append",
        help="""external projects to link to.
        If an entity is not found in the sources, FORD will try to look it up in
        those external projects. If those have documentation generated by FORD with
        the externalize option, a link will be placed into the documentation wherever
        this entity is referred to.
        FORD will look in the provided paths for a modules.json file.
        """,
    )

    return parser.parse_args()


def load_toml_settings(directory: Union[os.PathLike, str]) -> Optional[Settings]:
    """Load Ford settings from ``fpm.toml`` file in ``directory``

    Settings should be in ``[extra.ford]`` table
    """

    filename = Path(directory) / "fpm.toml"

    if not filename.is_file():
        return None

    with open(filename, "rb") as f:
        settings = tomllib.load(f)

    if "extra" not in settings:
        return None

    if "ford" not in settings["extra"]:
        return None

    return asdict(Settings(**settings["extra"]["ford"]))


def load_markdown_settings(directory: PathLike, proj_docs: str) -> Tuple[Dict, str]:
    proj_data, proj_docs = ford.utils.meta_preprocessor(proj_docs)
    proj_data = asdict(Settings(**proj_data))
    field_types = get_type_hints(Settings)

    for key, value in proj_data.items():
        default_type = field_types[key]

        if is_same_type(default_type, type(value)):
            continue
        if is_same_type(default_type, list):
            proj_data[key] = [value]
        elif is_same_type(default_type, bool):
            proj_data[key] = convert_to_bool(key, value)
        elif is_same_type(default_type, int):
            proj_data[key] = int(value[0])
        elif is_same_type(default_type, str) and isinstance(value, list):
            proj_data[key] = "\n".join(value)

    # Workaround for file inclusion in metadata
    for option, value in proj_data.items():
        if isinstance(value, str) and MD_INCLUDE_RE.match(value):
            warnings.warn(
                "Including other files in project file metadata is deprecated and "
                "will stop working in a future release.\n"
                f"    {option}: {value}",
                FutureWarning,
            )
            md_base_dir = proj_data.get("md_base_dir", [str(directory)])[0]
            configs = MarkdownInclude({"base_path": md_base_dir}).getConfigs()
            include_preprocessor = IncludePreprocessor(None, configs)
            proj_data[option] = "\n".join(include_preprocessor.run(value.splitlines()))

    return proj_data, proj_docs


def load_settings(
    proj_docs: str, directory: PathLike = pathlib.Path.cwd()
) -> Tuple[str, Dict, MetaMarkdown]:
    """Load Ford settings from ``fpm.toml`` if present, or from
    metadata in supplied project file1

    Parameters
    ----------
    proj_docs : str
        Text of project file
    directory : Union[os.PathLike, str]
        Project directory

    Returns
    -------
    proj_docs: str
        Text of project file converted from markdown
    proj_data: dict
        Project settings
    md: MetaMarkdown
        Markdown converter

    """

    proj_data = load_toml_settings(directory)

    if proj_data is None:
        proj_data, proj_docs = load_markdown_settings(directory, proj_docs)

    # Setup Markdown object with any user-specified extensions
    md = MetaMarkdown(
        proj_data.get("md_base_dir", [str(directory)])[0],
        extensions=proj_data.get("md_extensions", []),
    )

    # Now re-read project file with all extensions loaded
    proj_docs = md.reset().convert(proj_docs)

    return proj_docs, proj_data, md


def parse_arguments(
    command_line_args: dict,
    proj_docs: str,
    proj_data: dict,
    directory: Union[os.PathLike, str] = pathlib.Path.cwd(),
):
    """Consolidates arguments from the command line and from the project
    file, and then normalises them how the rest of the code expects
    """

    # Get the default options, and any over-rides, straightened out
    proj_data.update({k: v for k, v in command_line_args.items() if v is not None})

    # Evaluate paths relative to project file location
    base_dir = pathlib.Path(directory).absolute()
    proj_data["base_dir"] = base_dir

    for var in (
        "page_dir",
        "output_dir",
        "graph_dir",
        "media_dir",
        "css",
        "mathjax_config",
        "src_dir",
        "exclude_dir",
        "include",
    ):
        if proj_data[var] is None:
            continue
        if isinstance(proj_data[var], list):
            proj_data[var] = [
                ford.utils.normalise_path(base_dir, p) for p in proj_data[var]
            ]
        else:
            proj_data[var] = ford.utils.normalise_path(base_dir, proj_data[var])

    if proj_data["favicon"].strip() != Settings.favicon:
        proj_data["favicon"] = ford.utils.normalise_path(base_dir, proj_data["favicon"])

    proj_data["display"] = [item.lower() for item in proj_data["display"]]
    proj_data["creation_date"] = datetime.now().strftime(proj_data["creation_date"])
    proj_data["relative"] = proj_data["project_url"] == ""
    proj_data["extensions"] += [
        ext for ext in proj_data["fpp_extensions"] if ext not in proj_data["extensions"]
    ]
    # Parse file extensions and comment characters for extra filetypes
    extdict = {}
    for ext in proj_data["extra_filetypes"]:
        sp = ext.split()
        if len(sp) < 2:
            continue
        if len(sp) == 2:
            extdict[sp[0]] = sp[1]  # (comment_char) only
        else:
            extdict[sp[0]] = (sp[1], sp[2])  # (comment_char and lexer_str)
    proj_data["extra_filetypes"] = extdict

    # Make sure no src_dir is contained within output_dir
    for srcdir in proj_data["src_dir"]:
        # In Python 3.9+ we can use pathlib.Path.is_relative_to
        if proj_data["output_dir"] in (srcdir, *srcdir.parents):
            raise ValueError(
                f"Source directory {srcdir} is a subdirectory of output directory {proj_data['output_dir']}."
            )

    # Check that none of the docmarks are the same
    docmarks = ["docmark", "predocmark", "docmark_alt", "predocmark_alt"]
    for first, second in itertools.combinations(docmarks, 2):
        if proj_data[first] == proj_data[second] != "":
            raise ValueError(
                f"{first} ('{proj_data[first]}') and {second} ('{proj_data[second]}') are the same"
            )

    # Add gitter sidecar if specified in metadata
    if proj_data["gitter_sidecar"] is not None:
        proj_docs += f"""
        <script>
            ((window.gitter = {{}}).chat = {{}}).options = {{
            room: '{proj_data["gitter_sidecar"].strip()}'
            }};
        </script>
        <script src="https://sidecar.gitter.im/dist/sidecar.v1.js" async defer></script>
        """
    # Handle preprocessor:
    if proj_data["preprocess"]:
        proj_data["preprocessor"] = proj_data["preprocessor"].split()
        command = proj_data["preprocessor"] + [os.devnull]
        # Check whether preprocessor works (reading nothing from stdin)
        try:
            subprocess.run(command, check=True, capture_output=True, text=True)
        except (subprocess.CalledProcessError, OSError) as ex:
            project_file = command_line_args["project_file"].name
            exit(
                dedent(
                    f"""\
                    Error: Testing preprocessor command (`{" ".join(command)}`) failed with error:
                        {ex.stderr.strip() if isinstance(ex, subprocess.CalledProcessError) else ex}

                    If you need to preprocess files, please fix the 'preprocessor' option in '{project_file}'.
                    Otherwise, please set 'preprocess: False' in '{project_file}'"""
                )
            )
    else:
        proj_data["fpp_extensions"] = []

    # Get the correct license for project license or use value as a custom license value.
    try:
        proj_data["license"] = LICENSES[proj_data["license"].lower()]
    except KeyError:
        print(
            f'Notice: license "{proj_data["license"]}" is not a recognized value, using the value as a custom license value.'
        )
    # Get the correct license for doc license(website or doc) or use value as a custom license value.
    try:
        proj_data["doc_license"] = LICENSES[proj_data["doc_license"].lower()]
    except KeyError:
        print(
            f'Notice: doc_license "{proj_data["doc_license"]}" is not a recognized value, using the value as a custom license value.'
        )

    return proj_data, proj_docs


def main(proj_data, proj_docs, md):
    """
    Main driver of FORD.
    """
    if proj_data["relative"]:
        proj_data["project_url"] = "."
    # Parse the files in your project
    project = ford.fortran_project.Project(proj_data)
    if len(project.files) < 1:
        print(
            "Error: No source files with appropriate extension found in specified directory."
        )
        sys.exit(1)

    # Define core macros:
    ford.utils.register_macro(f"url = {proj_data['project_url']}")
    ford.utils.register_macro(
        f'media = {os.path.join(proj_data["project_url"], "media")}'
    )
    ford.utils.register_macro(
        f'page = {os.path.join(proj_data["project_url"], "page")}'
    )

    # Register the user defined aliases:
    for alias in proj_data["alias"]:
        ford.utils.register_macro(alias)

    # Convert the documentation from Markdown to HTML. Make sure to properly
    # handle LateX and metadata.
    base_url = ".." if proj_data["relative"] else proj_data["project_url"]
    project.markdown(md, base_url)
    project.correlate()
    project.make_links(base_url)

    # Convert summaries and descriptions to HTML
    if proj_data["relative"]:
        ford.sourceform.set_base_url(".")
    if proj_data["summary"] is not None:
        proj_data["summary"] = md.convert(proj_data["summary"])
        proj_data["summary"] = ford.utils.sub_links(
            ford.utils.sub_macros(proj_data["summary"]), project
        )
    if proj_data["author_description"] is not None:
        proj_data["author_description"] = md.convert(proj_data["author_description"])
        proj_data["author_description"] = ford.utils.sub_links(
            ford.utils.sub_macros(proj_data["author_description"]),
            project,
        )
    proj_docs_ = ford.utils.sub_links(ford.utils.sub_macros(proj_docs), project)
    # Process any pages
    if proj_data["page_dir"] is not None:
        page_tree = get_page_tree(
            pathlib.Path(proj_data["page_dir"]),
            proj_data["copy_subdir"],
            md,
            encoding=proj_data["encoding"],
        )
        print()
    else:
        page_tree = None
    proj_data["pages"] = page_tree

    # Produce the documentation using Jinja2. Output it to the desired location
    # and copy any files that are needed (CSS, JS, images, fonts, source files,
    # etc.)

    docs = ford.output.Documentation(proj_data, proj_docs_, project, page_tree)
    docs.writeout()

    if proj_data["externalize"]:
        # save FortranModules to a JSON file which then can be used
        # for external modules
        dump_modules(project, path=proj_data["output_dir"])

    return 0


def run():
    proj_data, proj_docs, md = initialize()

    f = StringIO() if proj_data["quiet"] else sys.stdout
    with stdout_redirector(f):
        main(proj_data, proj_docs, md)


if __name__ == "__main__":
    run()
