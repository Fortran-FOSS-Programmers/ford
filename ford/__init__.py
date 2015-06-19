#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  ford.py
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

from __future__ import print_function

import sys
import argparse
import markdown
import os.path
from datetime import date

import ford.fortran_project
import ford.sourceform
import ford.output
from ford.mdx_mathjax import MathJaxExtension
import ford.utils
import ford.pagetree

__appname__ = "FORD"
__author__ = "Chris MacMackin, Jacob Williams, Marco Restelli"
__credits__ = ["Stefano Zhagi", "Z. Beekman", "Gavin Huttley"]
__license__ = "GPLv3"
__version__ = "2.1.0"
__maintainer__ = "Chris MacMackin"
__status__ = "Production"

def main():    
    # Setup the command-line options and parse them.
    parser = argparse.ArgumentParser(description="Document a program or library written in modern Fortran. Any command-line options over-ride those specified in the project file.")
    parser.add_argument("project_file",help="file containing the description and settings for the project",
                        type=argparse.FileType('r'))
    parser.add_argument("-d","--project_dir",action="append",help='directories containing all source files for the project')
    parser.add_argument("-o","--output_dir",help="directory in which to place output files")
    parser.add_argument("-s","--css",help="custom style-sheet for the output")
    parser.add_argument("--exclude",action="append",help="any files which should not be included in the documentation")
    parser.add_argument("-e","--extensions",action="append",help="extensions which should be scanned for documentation (default: f90, f95, f03, f08)")
    parser.add_argument("-w","--warn",dest='warn',action='store_true',
                        help="display warnings for undocumented items")
    parser.add_argument("--no-warn",dest='warn',action='store_false',
                        help="don't display warnings for undocumented items (default)")
    parser.set_defaults(warn=False)
    parser.add_argument('-V', '--version', action='version',
                        version="{}, version {}".format(__appname__,__version__))

    args = parser.parse_args()

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
    proj_docs = md.convert(proj_docs)
    proj_data = md.Meta
    md.reset()

    # Get the default options, and any over-rides, straightened out
    options = [u'project_dir',u'extensions',u'output_dir',u'css',u'exclude',
               u'project',u'author',u'author_description',u'author_pic',
               u'summary',u'github',u'bitbucket',u'facebook',u'twitter',
               u'google_plus',u'linkedin',u'email',u'website',u'project_github',
               u'project_bitbucket',u'project_website',u'project_download',
               u'project_sourceforge',u'project_url',u'display',u'version',
               u'year',u'docmark',u'predocmark',u'docmark_alt',u'predocmark_alt',
               u'media_dir',u'favicon',u'warn',u'extra_vartypes',u'page_dir',
               u'source']
    defaults = {u'project_dir':       u'./src',
                u'extensions':        [u"f90",u"f95",u"f03",u"f08",u"F90",
                                       u"F95",u"F03",u"F08"],
                u'output_dir':        u'./doc',
                u'project':           u'Fortran Program',
                u'project_url':       u'',
                u'display':           [u'public',u'protected'],
                u'year':              date.today().year,
                u'exclude':           [],
                u'docmark':           '!',
                u'docmark_alt':       '',
                u'predocmark_alt':    '',
                u'predocmark':        '',
                u'favicon':           'default-icon',
                u'extra_vartypes':    [],
                u'source':            'false',
               }
    listopts = [u'extensions',u'display',u'extra_vartypes','project_dir']
    
    for option in options:
        if hasattr(args,option) and eval("args." + option):
            proj_data[option] = eval("args." + option)
        elif option in proj_data:
            # Think if there is a safe  way to evaluate any expressions found in this list
            #proj_data[option] = proj_data[option]
            if option not in listopts:
                proj_data[option] = '\n'.join(proj_data[option])
        elif option in defaults:
           proj_data[option] = defaults[option]
    
    proj_data['display'] = [ item.lower() for item in proj_data['display'] ]
    
    # Make sure no project_dir is contained within output_dir
    for projdir in proj_data['project_dir']:
        proj_path = ford.utils.split_path(projdir)
        out_path  = ford.utils.split_path(proj_data['output_dir'])
        for directory in out_path:
            if len(proj_path) == 0: break
            if directory == proj_path[0]:
                proj_path.remove(directory)
            else:
                break
        else:
            print('Error: directory containing source-code {} a subdirectory of output directory {}.'.format(proj_data['output_dir'],projdir))
            sys.exit(1)
        
    if proj_data['docmark'] == proj_data['predocmark']:
        print('Error: docmark and predocmark are the same.')
        sys.exit(1)

    relative = (proj_data['project_url'] == '')
    if relative: proj_data['project_url'] = '.'
    if 'source' in proj_data: ford.sourceform.set_source(proj_data['source'])

    # Parse the files in your project
    warn = ('warn' in proj_data)
    project = ford.fortran_project.Project(proj_data['project'],
                proj_data['project_dir'], proj_data['extensions'], 
                proj_data['display'], proj_data['exclude'], proj_data['docmark'],
                proj_data['predocmark'], proj_data['docmark_alt'],
                proj_data['predocmark_alt'], warn, proj_data['extra_vartypes'])
    if len(project.files) < 1:
        print("Error: No source files with appropriate extension found in specified directory.")
        sys.exit(1)
    
    # Convert the documentation from Markdown to HTML. Make sure to properly
    # handle LateX and metadata.
    if relative:
        project.markdown(md,'..')
    else:
        project.markdown(md,proj_data['project_url'])
    project.correlate()
    if relative:
        project.make_links('..')
    else:
        project.make_links(proj_data['project_url'])
    
    if relative: ford.sourceform.set_base_url('.')
    if 'summary' in proj_data:
        proj_data['summary'] = md.convert(proj_data['summary'])
        proj_data['summary'] = ford.utils.sub_links(ford.utils.sub_macros(ford.utils.sub_notes(proj_data['summary']),proj_data['project_url']),project)
    if 'author_description' in proj_data:
        proj_data['author_description'] = md.convert(proj_data['author_description'])
        proj_data['author_description'] = ford.utils.sub_links(ford.utils.sub_macros(ford.utils.sub_notes(proj_data['author_description']),proj_data['project_url']),project)
    proj_docs = ford.utils.sub_links(ford.utils.sub_macros(ford.utils.sub_notes(proj_docs),proj_data['project_url']),project)
    if relative: ford.sourceform.set_base_url('..')        
    
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
    ford.output.print_html(project,proj_data,proj_docs,page_tree,relative)
    print('')
    
    return 0

if __name__ == '__main__':
    main()
