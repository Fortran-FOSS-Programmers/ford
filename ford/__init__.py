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
import copy
from io import StringIO
import sys
import argparse
import os
import pathlib
import subprocess
from datetime import datetime
import time
from typing import Tuple, Optional
from textwrap import dedent

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib  # type: ignore[no-redef]

from ford.external_project import dump_modules
import ford.fortran_project
import ford.sourceform
import ford.output
from ford.utils import ProgressBar
from ford._typing import PathLike
from ford.pagetree import get_page_tree
from ford._markdown import MetaMarkdown
from ford.version import __version__
from ford.settings import (
    ProjectSettings,
    load_markdown_settings,
    load_toml_settings,
    convert_types_from_commandarguments,
)


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
    "gpl": (
        '<a rel="license" href="http://www.gnu.org/licenses/gpl">'
        '<img alt="GNU General Public License" style="border-width:0" src="https://www.gnu.org/graphics/gplv3-88x31.png" /></a>'
    ),
    "lgpl": (
        '<a rel="license" href="http://www.gnu.org/licenses/lgpl">'
        '<img alt="GNU Lesser General Public License" style="border-width:0" src="https://www.gnu.org/graphics/lgplv3-88x31.png" /></a>'
    ),
    "agpl": (
        '<a rel="license" href="http://www.gnu.org/licenses/agpl">'
        '<img alt="GNU Affero General Public License" style="border-width:0" src="https://www.gnu.org/graphics/agplv3-88x31.png" /></a>'
    ),
    "gfdl": '<a rel="license" href="http://www.gnu.org/licenses/old-licenses/fdl-1.2.en.html">GNU Free Documentation License</a>',
    "opl": '<a rel="license" href="http://opencontent.org/openpub/">Open Publication License</a>',
    "pdl": '<a rel="license" href="http://www.openoffice.org/licenses/PDL.html">Public Documentation License</a>',
    "bsd": '<a rel="license" href="http://www.freebsd.org/copyright/freebsd-doc-license.html">FreeBSD Documentation License</a>',
    "isc": '<a rel="license" href="https://opensource.org/licenses/ISC">ISC (Internet Systems Consortium) License</a>',
    "mit": '<a rel="license" href="https://opensource.org/licenses/MIT">MIT</a>',
    "": "",
}


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
    proj_docs, proj_data = load_settings(proj_docs, directory, args.project_file.name)

    return parse_arguments(vars(args), proj_docs, proj_data, directory)


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
        action="store_true",
        default=None,
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
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="Any other FORD options as a semicolon-separated TOML string. "
        "Options set through this have lower precedence than other command line options",
    )

    return parser.parse_args()


def load_settings(
    proj_docs: str,
    directory: PathLike = pathlib.Path("."),
    filename: Optional[str] = None,
) -> Tuple[str, ProjectSettings]:
    """Load Ford settings from ``fpm.toml`` if present, or from
    metadata in supplied project file1

    Parameters
    ----------
    proj_docs : str
        Text of project file
    directory :
        Project directory

    Returns
    -------
    proj_docs: str
        Text of project file converted from markdown
    proj_data: dict
        Project settings

    """

    proj_data = load_toml_settings(directory)

    if proj_data is None:
        proj_data, proj_docs = load_markdown_settings(directory, proj_docs, filename)

    return proj_docs, proj_data


def parse_arguments(
    command_line_args: dict,
    proj_docs: str,
    proj_data: ProjectSettings,
    directory: PathLike = pathlib.Path("."),
):
    """Consolidates arguments from the command line and from the project
    file, and then normalises them how the rest of the code expects
    """

    if (config := command_line_args.get("config", None)) is not None:
        toml_string = "\n".join(config.split(";"))
        for key, value in tomllib.loads(toml_string).items():
            setattr(proj_data, key, value)

    # Get the default options, and any over-rides, straightened out
    proj_data = convert_types_from_commandarguments(proj_data, command_line_args)

    proj_data.normalise_paths(directory)

    proj_data.creation_date = (
        datetime.now().astimezone().strftime(proj_data.creation_date)
    )

    # Make sure no src_dir is contained within output_dir
    for srcdir in proj_data.src_dir:
        # In Python 3.9+ we can use pathlib.Path.is_relative_to
        if proj_data.output_dir in (srcdir, *srcdir.parents):
            raise ValueError(
                f"Source directory {srcdir} is a subdirectory of output directory {proj_data.output_dir}."
            )

    # Add gitter sidecar if specified in metadata
    if proj_data.gitter_sidecar is not None:
        proj_docs += f"""
        <script>
            ((window.gitter = {{}}).chat = {{}}).options = {{
            room: '{proj_data.gitter_sidecar.strip()}'
            }};
        </script>
        <script src="https://sidecar.gitter.im/dist/sidecar.v1.js" async defer></script>
        """

    # Handle preprocessor:
    if proj_data.preprocess:
        command = proj_data.preprocessor.split() + [os.devnull]
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
        proj_data.fpp_extensions = []

    # Get the correct license for project license or use value as a custom license value.
    try:
        proj_data.license = LICENSES[proj_data.license.lower()]
    except KeyError:
        print(
            f'Notice: license "{proj_data.license}" is not a recognized value, using the value as a custom license value.'
        )
    # Get the correct license for doc license(website or doc) or use value as a custom license value.
    try:
        proj_data.doc_license = LICENSES[proj_data.doc_license.lower()]
    except KeyError:
        print(
            f'Notice: doc_license "{proj_data.doc_license}" is not a recognized value, using the value as a custom license value.'
        )

    return proj_data, proj_docs


def main(proj_data: ProjectSettings, proj_docs: str):
    """
    Main driver of FORD.
    """

    # Parse the files in your project
    project = ford.fortran_project.Project(proj_data)
    if len(project.files) < 1:
        print(
            "Error: No source files with appropriate extension found in specified directory."
        )
        sys.exit(1)

    print("  Correlating information from different parts of your project...")
    correlate_time_start = time.time()
    project.correlate()
    correlate_time_end = time.time()
    print(f"  ...done in {correlate_time_end - correlate_time_start:5.3f}s")

    # Setup Markdown object with any user-specified extensions
    aliases = copy.copy(proj_data.alias)
    aliases.update(proj_data.external)
    url_path = pathlib.Path(proj_data.project_url)
    aliases.update(
        {
            "url": str(url_path),
            "media": str(url_path / "media"),
            "page": str(url_path / "page"),
        }
    )

    md = MetaMarkdown(
        proj_data.md_base_dir,
        base_url=proj_data.project_url,
        extensions=proj_data.md_extensions,
        aliases=aliases,
        project=project,
    )

    # Convert the documentation from Markdown to HTML
    proj_docs = md.reset().convert(proj_docs, path=proj_data.project_url)
    project.markdown(md)

    # Convert summaries and descriptions to HTML
    if proj_data.summary is not None:
        proj_data.summary = md.convert(proj_data.summary)
    if proj_data.author_description is not None:
        proj_data.author_description = md.convert(proj_data.author_description)

    # Process any pages
    if proj_data.page_dir is not None:
        total_files = len(list(proj_data.page_dir.glob("**/*.md")))
        with ProgressBar("Processing pages", total=total_files) as progress:
            page_tree = get_page_tree(
                proj_data.page_dir,
                proj_data.copy_subdir,
                proj_data.output_dir,
                md,
                encoding=proj_data.encoding,
                progress=progress,
            )
    else:
        page_tree = None

    # Produce the documentation using Jinja2. Output it to the desired location
    # and copy any files that are needed (CSS, JS, images, fonts, source files,
    # etc.)

    docs = ford.output.Documentation(proj_data, proj_docs, project, page_tree)
    docs.writeout()

    if proj_data.externalize:
        # save FortranModules to a JSON file which then can be used
        # for external modules
        dump_modules(project, path=proj_data.output_dir)

    return 0


def run():
    proj_data, proj_docs = initialize()

    f = StringIO() if proj_data.quiet else sys.stdout
    with stdout_redirector(f):
        main(proj_data, proj_docs)


if __name__ == "__main__":
    run()
