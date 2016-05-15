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

from __future__ import print_function
from contextlib import contextmanager
import sys
if (sys.version_info[0]>2):
    from io import StringIO
else:
    from StringIO import StringIO
import argparse
import markdown
import os
import subprocess
from datetime import date, datetime

import ford.fortran_project
import ford.sourceform
import ford.output
from ford.mdx_mathjax import MathJaxExtension
import ford.utils
import ford.pagetree

__appname__    = "FORD"
__author__     = "Chris MacMackin, Jacob Williams, Marco Restelli, Iain Barrass, Jérémie Burgalat, Stephen J. Turnbull, Balint Aradi"
__credits__    = ["Stefano Zhagi", "Izaak Beekman", "Gavin Huttley"]
__license__    = "GPLv3"
__version__    = "4.6.0"
__maintainer__ = "Chris MacMackin"
__status__     = "Production"

if sys.version_info[0] < 3:
    reload(sys)  
    sys.setdefaultencoding('utf8')

@contextmanager
def stdout_redirector(stream):
    old_stdout = sys.stdout
    sys.stdout = stream
    try:
        yield
    finally:
        sys.stdout = old_stdout

LICENSES = { 'by': '<a rel="license" href="http://creativecommons.org/licenses/by/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by/4.0/80x15.png" /></a>',
             'by-nd': '<a rel="license" href="http://creativecommons.org/licenses/by-nd/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nd/4.0/80x15.png" /></a>',
             'by-sa': '<a rel="license" href="http://creativecommons.org/licenses/by-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-sa/4.0/80x15.png" /></a>',
             'by-nc': '<a rel="license" href="http://creativecommons.org/licenses/by-nc/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc/4.0/80x15.png" /></a>',
             'by-nc-nd': '<a rel="license" href="http://creativecommons.org/licenses/by-nc-nd/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-nd/4.0/80x15.png" /></a>',
             'by-nc-sa': '<a rel="license" href="http://creativecommons.org/licenses/by-nc-sa/4.0/"><img alt="Creative Commons License" style="border-width:0" src="https://i.creativecommons.org/l/by-nc-sa/4.0/80x15.png" /></a>',
             'gfdl': '<a rel="license" href="http://www.gnu.org/licenses/old-licenses/fdl-1.2.en.html">GNU Free Documentation License</a>',
             'opl': '<a rel="license" href="http://opencontent.org/openpub/">Open Publication License</a>',
             'pdl': '<a rel="license" href="http://www.openoffice.org/licenses/PDL.html">Public Documentation License</a>',
             'bsd': '<a rel="license" href="http://www.freebsd.org/copyright/freebsd-doc-license.html">FreeBSD Documentation License</a>',
             '': ''
           }

def initialize():
    """
    Method to parse and check configurations of FORD, get the project's 
    global documentation, and create the Markdown reader.
    """
    # Setup the command-line options and parse them.
    parser = argparse.ArgumentParser(description="Document a program or library written in modern Fortran. Any command-line options over-ride those specified in the project file.")
    parser.add_argument("project_file",help="file containing the description and settings for the project",
                        type=argparse.FileType('r'))
    parser.add_argument("-d","--project_dir",action="append",help='directories containing all source files for the project')
    parser.add_argument("-p","--page_dir",help="directory containing the optional page tree describing the project")
    parser.add_argument("-o","--output_dir",help="directory in which to place output files")
    parser.add_argument("-s","--css",help="custom style-sheet for the output")
    parser.add_argument("--exclude",action="append",help="any files which should not be included in the documentation")
    parser.add_argument("--exclude_dir",action="append",help="any directories whose contents should not be included in the documentation")
    parser.add_argument("-e","--extensions",action="append",help="extensions which should be scanned for documentation (default: f90, f95, f03, f08)")
    parser.add_argument("-m","--macro",action="append",help="preprocessor macro (and, optionally, its value) to be applied to files in need of preprocessing.")
    parser.add_argument("-w","--warn",dest='warn',action='store_true',
                        help="display warnings for undocumented items")
    parser.add_argument("--no-search",dest='search',action='store_false',
                        help="don't process documentation to produce a search feature")
    parser.add_argument("-q","--quiet",dest='quiet',action='store_true',
                        help="do not print any description of progress")
    parser.add_argument("-V", "--version", action="version",
                        version="{}, version {}".format(__appname__,__version__))
    parser.add_argument("--debug",dest="dbg",action="store_true",
                        help="display traceback if fatal exception occurs")
    # Get options from command-line
    args = parser.parse_args()
    # Set up Markdown reader
    md_ext = ['markdown.extensions.meta','markdown.extensions.codehilite',
              'markdown.extensions.extra',MathJaxExtension()]
    md = markdown.Markdown(extensions=md_ext, output_format="html5",
    extension_configs={})
    # Read in the project-file. This will contain global documentation (which
    # will appear on the homepage) as well as any information about the project
    # and settings for generating the documentation.
    proj_docs = args.project_file.read()
    md.convert(proj_docs)
    # Remake the Markdown object with settings parsed from the project_file
    if 'md_base_dir' in md.Meta: md_base = md.Meta['md_base_dir'][0] 
    else: md_base = os.path.dirname(args.project_file.name)
    md_ext.append('markdown_include.include')
    if 'md_extensions' in md.Meta: md_ext.extend(md.Meta['md_extensions'])
    md = markdown.Markdown(extensions=md_ext, output_format="html5",
            extension_configs={'markdown_include.include': {'base_path': md_base}})
    md.reset()
    # Re-read the project file
    proj_docs = md.convert(proj_docs)
    proj_data = md.Meta
    md.reset()
    # Get the default options, and any over-rides, straightened out
    options = ['project_dir','extensions','output_dir','css','exclude',
               'project','author','author_description','author_pic',
               'summary','github','bitbucket','facebook','twitter',
               'google_plus','linkedin','email','website','project_github',
               'project_bitbucket','project_website','project_download',
               'project_sourceforge','project_url','display','version',
               'year','docmark','predocmark','docmark_alt','predocmark_alt',
               'media_dir','favicon','warn','extra_vartypes','page_dir',
               'source','exclude_dir','macro','include','preprocess','quiet',
               'search','lower','sort','extra_mods','dbg','graph', 'license',
               'extra_filetypes','preprocessor','creation_date',
               'print_creation_date','proc_internals','coloured_edges',
               'graph_dir','gitter_sidecar']
    defaults = {'project_dir':         ['./src'],
                'extensions':          ['f90','f95','f03','f08','f15','F90',
                                        'F95','F03','F08','F15'],
                'output_dir':          './doc',
                'project':             'Fortran Program',
                'project_url':         '',
                'display':             ['public','protected'],
                'year':                date.today().year,
                'exclude':             [],
                'exclude_dir':         [],
                'docmark':             '!',
                'docmark_alt':         '*',
                'predocmark':          '>',
                'predocmark_alt':      '|',
                'favicon':             'default-icon',
                'extra_vartypes':      [],
                'source':              'false',
                'macro':               [],
                'include':             [],
                'preprocess':          'true',
                'preprocessor':        '',
                'proc_internals':      'true',
                'warn':                'false',
                'quiet':               'false',
                'search':              'true',
                'lower':               'false',
                'sort':                'src',
                'extra_mods':          [],
                'dbg':                 False,
                'graph':               'false',
                'license':             '',
                'extra_filetypes':     [],
                'creation_date':       '%Y-%m-%dT%H:%M:%S.%f%z',
                'print_creation_date': False,
                'coloured_edges':      'false',
                'graph_dir':           '',
               }
    listopts = ['extensions','display','extra_vartypes','project_dir',
                'exclude','exclude_dir','macro','include','extra_mods',
                'extra_filetypes']
    if args.warn:
        args.warn = 'true'
    else:
        del args.warn
    if args.quiet:
        args.quiet = 'true'
    else:
        del args.quiet
    if not args.search:
        args.search = 'false'
    else:
        del args.search
    for option in options:
        if hasattr(args,option) and getattr(args,option):
            proj_data[option] = getattr(args,option)
        elif option in proj_data:
            # Think if there is a safe  way to evaluate any expressions found in this list
            #proj_data[option] = proj_data[option]
            if option not in listopts:
                proj_data[option] = '\n'.join(proj_data[option])
        elif option in defaults:
           proj_data[option] = defaults[option]
    proj_data['display'] = [ item.lower() for item in proj_data['display'] ]
    proj_data['creation_date'] = datetime.now().strftime(proj_data['creation_date'])
    relative = (proj_data['project_url'] == '')
    proj_data['relative'] = relative
    # Parse file extensions and comment characters for extra filetypes
    extdict = {}
    for ext in proj_data['extra_filetypes']:
        sp = ext.split()
        if len(sp) < 2: continue
        extdict[sp[0]] = sp[1]
    proj_data['extra_filetypes'] = extdict
    # Make sure no project_dir is contained within output_dir
    for projdir in proj_data['project_dir']:
        proj_path = ford.utils.split_path(projdir)
        out_path  = ford.utils.split_path(proj_data['output_dir'])
        for directory in out_path:
            if len(proj_path) ==  0: break
            if directory == proj_path[0]:
                proj_path.remove(directory)
            else:
                break
        else:
            print('Error: directory containing source-code {} a subdirectory of output directory {}.'.format(proj_data['output_dir'],projdir))
            sys.exit(1)
    # Check that none of the docmarks are the same
    if proj_data['docmark'] == proj_data['predocmark'] != '':
        print('Error: docmark and predocmark are the same.')
        sys.exit(1)
    if proj_data['docmark'] == proj_data['docmark_alt'] != '':
        print('Error: docmark and docmark_alt are the same.')
        sys.exit(1)
    if proj_data['docmark'] == proj_data['predocmark_alt'] != '':
        print('Error: docmark and predocmark_alt are the same.')
        sys.exit(1)
    if proj_data['docmark_alt'] == proj_data['predocmark'] != '':
        print('Error: docmark_alt and predocmark are the same.')
        sys.exit(1)
    if proj_data['docmark_alt'] == proj_data['predocmark_alt'] != '':
        print('Error: docmark_alt and predocmark_alt are the same.')
        sys.exit(1)
    if proj_data['predocmark'] == proj_data['predocmark_alt'] != '':
        print('Error: predocmark and predocmark_alt are the same.')
        sys.exit(1)
    # Add gitter sidecar if specified in metadata
    if 'gitter_sidecar' in proj_data:
        proj_docs += '''
        <script>
            ((window.gitter = {{}}).chat = {{}}).options = {{
            room: '{}'
            }};
        </script>
        <script src="https://sidecar.gitter.im/dist/sidecar.v1.js" async defer></script>
        '''.format(proj_data['gitter_sidecar'].strip())
    
    # Handle preprocessor:
    if proj_data['preprocess'].lower() == 'true':
        if proj_data['preprocessor']:
            preprocessor = proj_data['preprocessor'].split()
        else:
            preprocessor = ['cpp','-traditional-cpp','-E']

        # Check whether preprocessor works (reading nothing from stdin)
        try:
            devnull = open(os.devnull)
            subprocess.Popen(preprocessor, stdin=devnull, stdout=devnull,
                             stderr=devnull).communicate()
        except OSError as ex:
            print('Warning: Testing preprocessor failed')
            print('  Preprocessor command: {}'.format(preprocessor))
            print('  Exception: {}'.format(ex))
            print('  -> Preprocessing turned off')
            proj_data['preprocess'] = 'false'
        else:
            proj_data['preprocess'] = 'true'
            proj_data['preprocessor'] = preprocessor
    
    # Get correct license
    try:
        proj_data['license'] = LICENSES[proj_data['license'].lower()]
    except KeyError:
        print('Warning: license "{}" not recognized.'.format(proj_data['license']))
        proj_data['license'] = ''
    # Return project data, docs, and the Markdown reader
    md.reset()
    md.Meta = {}
    return (proj_data, proj_docs, md)


def main(proj_data,proj_docs,md):
    """
    Main driver of FORD.
    """
    if proj_data['relative']: proj_data['project_url'] = '.'
    # Parse the files in your project
    project = ford.fortran_project.Project(proj_data)
    if len(project.files) < 1:
        print("Error: No source files with appropriate extension found in specified directory.")
        sys.exit(1)        
    # Convert the documentation from Markdown to HTML. Make sure to properly
    # handle LateX and metadata.
    if proj_data['relative']:
        project.markdown(md,'..')
    else:
        project.markdown(md,proj_data['project_url'])
    project.correlate()
    if proj_data['relative']:
        project.make_links('..')
    else:
        project.make_links(proj_data['project_url'])
    # Convert summaries and descriptions to HTML
    if proj_data['relative']: ford.sourceform.set_base_url('.')
    if 'summary' in proj_data:
        proj_data['summary'] = md.convert(proj_data['summary'])
        proj_data['summary'] = ford.utils.sub_links(ford.utils.sub_macros(ford.utils.sub_notes(proj_data['summary']),proj_data['project_url']),project)
    if 'author_description' in proj_data:
        proj_data['author_description'] = md.convert(proj_data['author_description'])
        proj_data['author_description'] = ford.utils.sub_links(ford.utils.sub_macros(ford.utils.sub_notes(proj_data['author_description']),proj_data['project_url']),project)
    proj_docs_ = ford.utils.sub_links(ford.utils.sub_macros(ford.utils.sub_notes(proj_docs),proj_data['project_url']),project)
    # Process any pages
    if 'page_dir' in proj_data:
        page_tree = ford.pagetree.get_page_tree(os.path.normpath(proj_data['page_dir']),md)
        print()
    else:
        page_tree = None
    proj_data['pages'] = page_tree
    # Produce the documentation using Jinja2. Output it to the desired location
    # and copy any files that are needed (CSS, JS, images, fonts, source files,
    # etc.)
    print("Creating HTML documentation...")
    docs = ford.output.Documentation(proj_data,proj_docs_,project,page_tree)
    docs.writeout()
    print('')
    return 0


def run():
    proj_data, proj_docs, md = initialize()
    if proj_data['quiet'].lower() == 'true':
        f = StringIO()
        with stdout_redirector(f):
            main(proj_data,proj_docs,md)
    else:
        main(proj_data,proj_docs,md)


if __name__ == '__main__':
    run()
