#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  output.py
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

from __future__ import print_function

import sys
import jinja2
import os
import shutil

import ford.sourceform
import ford.tipue_search
import ford.utils

#Python 2 or 3:
if (sys.version_info[0]>2):
    from urllib.parse import quote
else:
    from urllib import quote

def print_html(project,proj_data,proj_docs,page_tree,relative):
    def set_base_url(url):
        ford.sourceform.set_base_url(url)
        ford.pagetree.set_base_url(url)
        proj_data['project_url'] = url

    def print_pages(node):
        base_url = ''
        if relative:
            base_url = ('../'*len(node.hierarchy))[:-1]
            if node.filename == 'index':
                if len(node.hierarchy) > 0:
                    base_url = base_url + '/..'
                else:
                    base_url = '..'
            set_base_url(base_url)

        if node.filename == 'index':
            os.mkdir(os.path.join(proj_data['output_dir'],'page',node.location), 0o755)
        template = env.get_template('info_page.html')
        node.contents = ford.utils.sub_links(ford.utils.sub_macros(ford.utils.sub_notes(node.contents),base_url),project)
        html = template.render(proj_data,page=node,project=project,topnode=page_tree)
        out = open(quote(os.path.join(proj_data['output_dir'],'page',node.location,node.filename+'.html')),'wb')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'page'+node.location+'/'+node.filename+'.html')
        for item in node.files:
            try:
                shutil.copy(os.path.join(proj_data['page_dir'],node.location,item),
                            os.path.join(proj_data['output_dir'],'page',node.location))
            except Exception as e:
                print('Warning: could not copy file {}. Error: {}'.format(
                  os.path.join(proj_data['page_dir'],node.location,item),e.args[0]))
        for sub in node.subpages: 
            print_pages(sub)
            if relative: set_base_url(base_url)


    loc = os.path.dirname(__file__)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(loc, "templates")))

    try:
        if os.path.isfile(proj_data['output_dir']):
            os.remove(proj_data['output_dir'])
        elif os.path.isdir(proj_data['output_dir']):
            shutil.rmtree(proj_data['output_dir'])
        os.makedirs(proj_data['output_dir'], 0o755)
    except Exception as e:
        print('Error: Could not create output directory. {}'.format(e.args[0]))
    os.mkdir(os.path.join(proj_data['output_dir'],'lists'), 0o755)
    os.mkdir(os.path.join(proj_data['output_dir'],'sourcefile'), 0o755)
    os.mkdir(os.path.join(proj_data['output_dir'],'type'), 0o755)
    os.mkdir(os.path.join(proj_data['output_dir'],'proc'), 0o755)
    os.mkdir(os.path.join(proj_data['output_dir'],'interface'), 0o755)
    os.mkdir(os.path.join(proj_data['output_dir'],'module'), 0o755)
    os.mkdir(os.path.join(proj_data['output_dir'],'program'), 0o755)
    os.mkdir(os.path.join(proj_data['output_dir'],'src'), 0o755)
    
    shutil.copytree(os.path.join(loc,'css'), os.path.join(proj_data['output_dir'],'css'))
    shutil.copytree(os.path.join(loc,'fonts'), os.path.join(proj_data['output_dir'],'fonts'))
    shutil.copytree(os.path.join(loc,'js'),os.path.join(proj_data['output_dir'],'js'))
    shutil.copytree(os.path.join(loc,'tipuesearch'),os.path.join(proj_data['output_dir'],'tipuesearch'))
    
    if 'media_dir' in proj_data:
        try:
            shutil.copytree(proj_data['media_dir'],os.path.join(proj_data['output_dir'],'media'))
        except:
            print('Warning: error copying media directory {}'.format(proj_data['media_dir']))

    
    if 'css' in proj_data:
        shutil.copy(proj_data['css'],os.path.join(proj_data['output_dir'],'css','user.css'))
    if proj_data['favicon'] == 'default-icon':
        shutil.copy(os.path.join(loc,'favicon.png'),os.path.join(proj_data['output_dir'],'favicon.png'))
    else:
        shutil.copy(proj_data['favicon'],os.path.join(proj_data['output_dir'],'favicon.png'))
    
    if relative: set_base_url('.')
    else: set_base_url(proj_data['project_url'])        

    tipue = ford.tipue_search.Tipue_Search_JSON_Generator(proj_data['output_dir'],proj_data['project_url'])

    template = env.get_template('index.html')
    html = template.render(proj_data,proj_docs=proj_docs,project=project)
    out = open(proj_data['output_dir'] + '/index.html','wb')
    out.write(html.encode('utf8'))
    out.close()
    tipue.create_node(html,'index.html', {'category': 'home'})
    
    template = env.get_template('search.html')
    html = template.render(proj_data,project=project)
    out = open(proj_data['output_dir'] + '/search.html','wb')
    out.write(html.encode('utf8'))
    out.close()
    
    if relative: set_base_url('..')
    
    if len(project.procedures) > 0:
        template = env.get_template('proc_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(proj_data['output_dir'],'lists','procedures.html'),'wb')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'lists/procedures.html', {'category': 'list procedures'})

    if len(project.files) > 1:
        template = env.get_template('file_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(proj_data['output_dir'],'lists','files.html'),'wb')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'lists/files.html', {'category': 'list files'})
        
    if len(project.modules) > 0:
        template = env.get_template('mod_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(proj_data['output_dir'],'lists','modules.html'),'wb')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'lists/modules.html', {'category': 'list modules'})

    if len(project.programs) > 1:
        template = env.get_template('prog_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(proj_data['output_dir'],'lists','programs.html'),'wb')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'lists/programs.html', {'category': 'list programs'})
    
    if len(project.types) > 0:
        template = env.get_template('types_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(proj_data['output_dir'],'lists','types.html'),'wb')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'lists/types.html', {'category': 'list derived types'})

    if len(project.absinterfaces) > 0:
        template = env.get_template('absint_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(proj_data['output_dir'],'lists','absint.html'),'wb')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'lists/absint.html', {'category': 'list abstract interfaces'})

    for src in project.files:
        template = env.get_template('file_page.html')
        html = template.render(proj_data,src=src,project=project)
        out = open(quote(os.path.join(proj_data['output_dir'],'sourcefile',src.name.lower().replace('/','\\')+'.html')),'wb')
        out.write(html.encode('utf8'))
        out.close()
        dstdir = os.path.join(proj_data['output_dir'],'src',src.name)
        shutil.copy(src.path,dstdir)
        tipue.create_node(html,'sourcefile/'+src.name.lower().replace('/','\\')+'.html', src.meta)

    for dtype in project.types:
        template = env.get_template('type_page.html')
        html = template.render(proj_data,dtype=dtype,project=project)
        out = open(quote(os.path.join(proj_data['output_dir'],'type',dtype.name.lower().replace('/','\\')+'.html')),'wb')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'type/'+dtype.name.lower().replace('/','\\')+'.html', dtype.meta)

    for absint in project.absinterfaces:
        template = env.get_template('nongenint_page.html')
        out = open(quote(os.path.join(proj_data['output_dir'],'interface',absint.name.lower().replace('/','\\')+'.html')),'wb')
        html = template.render(proj_data,interface=absint,project=project)
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'interface/'+absint.name.lower().replace('/','\\')+'.html',absint.meta)

    for proc in project.procedures:
        if proc.obj == 'proc':
            template = env.get_template('proc_page.html')
            out = open(quote(os.path.join(proj_data['output_dir'],'proc',proc.name.lower().replace('/','\\')+'.html')),'wb')
            html = template.render(proj_data,procedure=proc,project=project)
            tipue.create_node(html,'proc/'+proc.name.lower().replace('/','\\')+'.html', proc.meta)
        else:
            if proc.generic:
                template = env.get_template('genint_page.html')
            else:
                template = env.get_template('nongenint_page.html')
            out = open(quote(os.path.join(proj_data['output_dir'],'interface',proc.name.lower().replace('/','\\')+'.html')),'wb')
            html = template.render(proj_data,interface=proc,project=project)
            tipue.create_node(html,'interface/'+proc.name.lower().replace('/','\\')+'.html', proc.meta)
        
        out.write(html.encode('utf8'))
        out.close()

    for mod in project.modules:
        template = env.get_template('mod_page.html')
        html = template.render(proj_data,module=mod,project=project)
        out = open(quote(os.path.join(proj_data['output_dir'],'module',mod.name.lower().replace('/','\\')+'.html')),'wb')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'module/'+mod.name.lower().replace('/','\\')+'.html', mod.meta)

    for prog in project.programs:
        template = env.get_template('prog_page.html')
        html = template.render(proj_data,program=prog,project=project)
        out = open(quote(os.path.join(proj_data['output_dir'],'program',prog.name.lower().replace('/','\\')+'.html')),'wb')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'program/'+prog.name.lower().replace('/','\\')+'.html', prog.meta)
    
    if page_tree: 
        print_pages(page_tree)
    
    tipue.print_output()

