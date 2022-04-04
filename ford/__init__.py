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
from io import StringIO
import itertools
import sys
import argparse
import markdown
import os
import pathlib
import subprocess
from datetime import date, datetime
from typing import Union
from textwrap import dedent

import ford.fortran_project
import ford.sourceform
import ford.output
import ford.utils
import ford.pagetree
from ford.md_environ import EnvironExtension

try:
    from importlib.metadata import version, PackageNotFoundError
except ModuleNotFoundError:
    from importlib_metadata import version, PackageNotFoundError
try:
    __version__ = version(__name__)
except PackageNotFoundError:
    from setuptools_scm import get_version

    __version__ = get_version(root="..", relative_to=__file__)


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


DEFAULT_SETTINGS = {
    "alias": [],
    "author": None,
    "author_description": None,
    "author_pic": None,
    "bitbucket": None,
    "coloured_edges": False,
    "copy_subdir": [],
    "creation_date": "%Y-%m-%dT%H:%M:%S.%f%z",
    "css": None,
    "dbg": True,
    "display": ["public", "protected"],
    "doc_license": "",
    "docmark": "!",
    "docmark_alt": "*",
    "email": None,
    "encoding": "utf-8",
    "exclude": [],
    "exclude_dir": [],
    "extensions": ["f90", "f95", "f03", "f08", "f15"],
    "external": [],
    "externalize": False,
    "extra_filetypes": [],
    "extra_mods": [],
    "extra_vartypes": [],
    "facebook": None,
    "favicon": "default-icon",
    "fixed_extensions": ["f", "for", "F", "FOR"],
    "fixed_length_limit": True,
    "force": False,
    "fpp_extensions": ["F90", "F95", "F03", "F08", "F15", "F", "FOR"],
    "github": None,
    "gitlab": None,
    "gitter_sidecar": None,
    "google_plus": None,
    "graph": False,
    "graph_dir": None,
    "graph_maxdepth": "10000",
    "graph_maxnodes": "1000000000",
    "hide_undoc": False,
    "incl_src": True,
    "include": [],
    "license": "",
    "linkedin": None,
    "lower": False,
    "macro": [],
    "mathjax_config": None,
    "max_frontpage_items": 10,
    "media_dir": None,
    "output_dir": "./doc",
    "page_dir": None,
    "parallel": 1,
    "predocmark": ">",
    "predocmark_alt": "|",
    "preprocess": True,
    "preprocessor": "cpp -traditional-cpp -E -D__GFORTRAN__",
    "print_creation_date": False,
    "privacy_policy_url": None,
    "proc_internals": False,
    "project": "Fortran Program",
    "project_bitbucket": None,
    "project_download": None,
    "project_github": None,
    "project_gitlab": None,
    "project_sourceforge": None,
    "project_url": "",
    "project_website": None,
    "quiet": False,
    "revision": None,
    "search": True,
    "sort": "src",
    "source": False,
    "src_dir": ["./src"],
    "summary": None,
    "terms_of_service_url": None,
    "twitter": None,
    "version": None,
    "warn": False,
    "website": None,
    "year": date.today().year,
}


def convert_to_bool(name, option):
    """Convert value 'option' to a bool, with a nice error message on
    failure. Expects a list from the markdown meta-data extension"""
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
    # and settings for generating the documentation.
    proj_docs = args.project_file.read()
    directory = os.path.dirname(args.project_file.name)

    return parse_arguments(vars(args), proj_docs, directory)


def get_command_line_arguments() -> argparse.Namespace:
    """Read the command line arguments"""

    parser = argparse.ArgumentParser(
        "ford",
        description="Document a program or library written in modern Fortran. Any command-line options over-ride those specified in the project file.",
    )
    parser.add_argument(
        "project_file",
        help="file containing the description and settings for the project",
        type=argparse.FileType("r"),
    )
    parser.add_argument(
        "-d",
        "--src_dir",
        action="append",
        help="directories containing all source files for the project",
    )
    parser.add_argument(
        "-p",
        "--page_dir",
        help="directory containing the optional page tree describing the project",
    )
    parser.add_argument(
        "-o", "--output_dir", help="directory in which to place output files"
    )
    parser.add_argument("-s", "--css", help="custom style-sheet for the output")
    parser.add_argument(
        "-r",
        "--revision",
        dest="revision",
        help="Source code revision the project to document",
    )
    parser.add_argument(
        "--exclude",
        action="append",
        help="any files which should not be included in the documentation",
    )
    parser.add_argument(
        "--exclude_dir",
        action="append",
        help="any directories whose contents should not be included in the documentation",
    )
    parser.add_argument(
        "-e",
        "--extensions",
        action="append",
        help="extensions which should be scanned for documentation (default: f90, f95, f03, f08)",
    )
    parser.add_argument(
        "-m",
        "--macro",
        action="append",
        help="preprocessor macro (and, optionally, its value) to be applied to files in need of preprocessing.",
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
        help="continue to read file if fatal errors",
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
        help="do not print any description of progress",
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version="%(prog)s version {}".format(__version__),
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
        help="any directories which should be searched for include files",
    )
    parser.add_argument(
        "--externalize",
        action="store_const",
        const="true",
        help="Provide information about Fortran objects in a json database for other FORD projects to refer to.",
    )
    parser.add_argument(
        "-L",
        "--external_links",
        dest="external",
        action="append",
        help="""External projects to link to.
        If an entity is not found in the sources, FORD will try to look it up in
        those external projects. If those have documentation generated by FORD with
        the externalize option, a link will be placed into the documentation wherever
        this entity is referred to.
        FORD will look in the provided paths for a modules.json file.
        """,
    )

    return parser.parse_args()


def parse_arguments(
    command_line_args: dict,
    proj_docs: str,
    directory: Union[os.PathLike, str] = os.getcwd(),
):
    """Consolidates arguments from the command line and from the project
    file, and then normalises them how the rest of the code expects
    """

    try:
        import multiprocessing

        ncpus = "{0}".format(multiprocessing.cpu_count())
    except (ImportError, NotImplementedError):
        ncpus = "0"

    DEFAULT_SETTINGS["parallel"] = ncpus

    # Set up Markdown reader
    md_ext = [
        "markdown.extensions.meta",
        "markdown.extensions.codehilite",
        "markdown.extensions.extra",
        "mdx_math",
        EnvironExtension(),
    ]
    md = markdown.Markdown(
        extensions=md_ext, output_format="html5", extension_configs={}
    )

    md.convert(proj_docs)
    # Remake the Markdown object with settings parsed from the project_file
    if "md_base_dir" in md.Meta:
        md_base = md.Meta["md_base_dir"][0]
    else:
        md_base = directory
    md_ext.append("markdown_include.include")
    if "md_extensions" in md.Meta:
        md_ext.extend(md.Meta["md_extensions"])
    md = markdown.Markdown(
        extensions=md_ext,
        output_format="html5",
        extension_configs={"markdown_include.include": {"base_path": md_base}},
    )

    # Re-read the project file
    proj_docs = md.reset().convert(proj_docs)
    proj_data = md.Meta

    # Get the default options, and any over-rides, straightened out
    for option, default in DEFAULT_SETTINGS.items():
        args_option = command_line_args.get(option, None)
        if args_option is not None:
            proj_data[option] = args_option
        elif option in proj_data:
            # Think if there is a safe  way to evaluate any expressions found in this list
            default_type = DEFAULT_SETTINGS.get(option, None)
            if isinstance(default_type, bool):
                proj_data[option] = convert_to_bool(option, proj_data[option])
            elif not isinstance(default_type, list):
                # If it's not supposed to be a list, then it's
                # probably supposed to be a single big block of text,
                # like a description
                proj_data[option] = "\n".join(proj_data[option])
        else:
            proj_data[option] = default

    # Evaluate paths relative to project file location
    base_dir = pathlib.Path(directory).absolute()
    proj_data["base_dir"] = base_dir

    for var in [
        "page_dir",
        "output_dir",
        "graph_dir",
        "media_dir",
        "css",
        "mathjax_config",
        "src_dir",
        "exclude_dir",
        "include",
    ]:
        if proj_data[var] is None:
            continue
        if isinstance(proj_data[var], list):
            proj_data[var] = [
                ford.utils.normalise_path(base_dir, p) for p in proj_data[var]
            ]
        else:
            proj_data[var] = ford.utils.normalise_path(base_dir, proj_data[var])

    if proj_data["favicon"].strip() != DEFAULT_SETTINGS["favicon"]:
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
        proj_docs += """
        <script>
            ((window.gitter = {{}}).chat = {{}}).options = {{
            room: '{}'
            }};
        </script>
        <script src="https://sidecar.gitter.im/dist/sidecar.v1.js" async defer></script>
        """.format(
            proj_data["gitter_sidecar"].strip()
        )
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
            'Notice: license "{}" is not a recognized value, using the value as a custom license value.'.format(
                proj_data["license"]
            )
        )
    # Get the correct license for doc license(website or doc) or use value as a custom license value.
    try:
        proj_data["doc_license"] = LICENSES[proj_data["doc_license"].lower()]
    except KeyError:
        print(
            'Notice: doc_license "{}" is not a recognized value, using the value as a custom license value.'.format(
                proj_data["doc_license"]
            )
        )

    # Return project data, docs, and the Markdown reader
    md.reset()
    return (proj_data, proj_docs, md)


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
    ford.utils.register_macro("url = {0}".format(proj_data["project_url"]))
    ford.utils.register_macro(
        "media = {0}".format(os.path.join(proj_data["project_url"], "media"))
    )
    ford.utils.register_macro(
        "page = {0}".format(os.path.join(proj_data["project_url"], "page"))
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
            ford.utils.sub_macros(ford.utils.sub_notes(proj_data["summary"])), project
        )
    if proj_data["author_description"] is not None:
        proj_data["author_description"] = md.convert(proj_data["author_description"])
        proj_data["author_description"] = ford.utils.sub_links(
            ford.utils.sub_macros(
                ford.utils.sub_notes(proj_data["author_description"])
            ),
            project,
        )
    proj_docs_ = ford.utils.sub_links(
        ford.utils.sub_macros(ford.utils.sub_notes(proj_docs)), project
    )
    # Process any pages
    if proj_data["page_dir"] is not None:
        page_tree = ford.pagetree.get_page_tree(
            os.path.normpath(proj_data["page_dir"]), proj_data["copy_subdir"], md
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
        ford.utils.external(project, make=True, path=proj_data["output_dir"])

    print("")
    return 0


def run():
    proj_data, proj_docs, md = initialize()

    f = StringIO() if proj_data["quiet"] else sys.stdout
    with stdout_redirector(f):
        main(proj_data, proj_docs, md)


if __name__ == "__main__":
    run()
