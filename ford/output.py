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



import jinja2
import os
import shutil
import urllib

import ford.sourceform
import ford.tipue_search

def print_html(project,proj_data,proj_docs,relative):
    loc = os.path.dirname(__file__)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(loc, "templates")))

    if os.path.isfile(proj_data['output_dir']):
        os.remove(proj_data['output_dir'])
    elif os.path.isdir(proj_data['output_dir']):
        shutil.rmtree(proj_data['output_dir'])

    os.makedirs(proj_data['output_dir'], 0755)
    os.mkdir(os.path.join(proj_data['output_dir'],'lists'), 0755)
    os.mkdir(os.path.join(proj_data['output_dir'],'sourcefile'), 0755)
    os.mkdir(os.path.join(proj_data['output_dir'],'type'), 0755)
    os.mkdir(os.path.join(proj_data['output_dir'],'proc'), 0755)
    os.mkdir(os.path.join(proj_data['output_dir'],'interface'), 0755)
    os.mkdir(os.path.join(proj_data['output_dir'],'module'), 0755)
    os.mkdir(os.path.join(proj_data['output_dir'],'program'), 0755)
    os.mkdir(os.path.join(proj_data['output_dir'],'src'), 0755)
    
    shutil.copytree(os.path.join(loc,'css'), os.path.join(proj_data['output_dir'],'css'))
    shutil.copytree(os.path.join(loc,'fonts'), os.path.join(proj_data['output_dir'],'fonts'))
    shutil.copytree(os.path.join(loc,'js'),os.path.join(proj_data['output_dir'],'js'))
    shutil.copytree(os.path.join(loc,'tipuesearch'),os.path.join(proj_data['output_dir'],'tipuesearch'))
    
    if 'media_dir' in proj_data:
        try:
            shutil.copytree(proj_data['media_dir'],os.path.join(proj_data['output_dir'],'media'))
        except:
            print 'Warning: error copying image directory {}'.format(proj_data['media_dir'])

    
    if 'css' in proj_data:
        shutil.copy(proj_data['css'],os.path.join(proj_data['output_dir'],'css','user.css'))
    if proj_data['favicon'] == 'default-icon':
        shutil.copy(os.path.join(loc,'favicon.png'),os.path.join(proj_data['output_dir'],'favicon.png'))
    else:
        shutil.copy(proj_data['favicon'],os.path.join(proj_data['output_dir'],'favicon.png'))
    
    if relative:
        ford.sourceform.set_base_url('.')
        proj_data['project_url'] = '.'

    tipue = ford.tipue_search.Tipue_Search_JSON_Generator(proj_data['output_dir'],proj_data['project_url'])

    template = env.get_template('index.html')
    html = template.render(proj_data,proj_docs=proj_docs,project=project)
    out = open(proj_data['output_dir'] + '/index.html','w')
    out.write(html.encode('utf8'))
    out.close()
    tipue.create_node(html,'index.html', {'category': 'home'})
    
    template = env.get_template('search.html')
    html = template.render(proj_data,project=project)
    out = open(proj_data['output_dir'] + '/search.html','w')
    out.write(html.encode('utf8'))
    out.close()
    
    if relative:
        ford.sourceform.set_base_url('..')
        proj_data['project_url'] = '..'
    
    if len(project.procedures) > 0:
        template = env.get_template('proc_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(proj_data['output_dir'],'lists','procedures.html'),'w')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'lists/procedures.html', {'category': 'list procedures'})

    if len(project.files) > 1:
        template = env.get_template('file_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(proj_data['output_dir'],'lists','files.html'),'w')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'lists/files.html', {'category': 'list files'})
        
    if len(project.modules) > 0:
        template = env.get_template('mod_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(proj_data['output_dir'],'lists','modules.html'),'w')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'lists/modules.html', {'category': 'list modules'})

    if len(project.programs) > 1:
        template = env.get_template('prog_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(proj_data['output_dir'],'lists','programs.html'),'w')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'lists/programs.html', {'category': 'list programs'})
    
    if len(project.types) > 0:
        template = env.get_template('types_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(proj_data['output_dir'],'lists','types.html'),'w')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'lists/types.html', {'category': 'list derived types'})
    
    for src in project.files:
        template = env.get_template('file_page.html')
        html = template.render(proj_data,src=src,project=project)
        out = open(urllib.quote(os.path.join(proj_data['output_dir'],'sourcefile',src.name.lower().replace('/','\\')+'.html')),'w')
        out.write(html.encode('utf8'))
        out.close()
        dstdir = os.path.join(proj_data['output_dir'],'src',src.name)
        shutil.copy(src.path,dstdir)
        tipue.create_node(html,'sourcefile/'+src.name.lower().replace('/','\\')+'.html', src.meta)
    
    for dtype in project.types:
        template = env.get_template('type_page.html')
        html = template.render(proj_data,dtype=dtype,project=project)
        out = open(urllib.quote(os.path.join(proj_data['output_dir'],'type',dtype.name.lower().replace('/','\\')+'.html')),'w')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'type/'+dtype.name.lower().replace('/','\\')+'.html', dtype.meta)
    
    for proc in project.procedures:
        if proc.obj == 'proc':
            template = env.get_template('proc_page.html')
            out = open(urllib.quote(os.path.join(proj_data['output_dir'],'proc',proc.name.lower().replace('/','\\')+'.html')),'w')
            html = template.render(proj_data,procedure=proc,project=project)
            tipue.create_node(html,'proc/'+proc.name.lower().replace('/','\\')+'.html', proc.meta)
        else:
            template = env.get_template('interface_page.html')
            out = open(urllib.quote(os.path.join(proj_data['output_dir'],'interface',proc.name.lower().replace('/','\\')+'.html')),'w')
            html = template.render(proj_data,interface=proc,project=project)
            tipue.create_node(html,'interface/'+proc.name.lower().replace('/','\\')+'.html', proc.meta)
        out.write(html.encode('utf8'))
        out.close()
    
    for mod in project.modules:
        template = env.get_template('mod_page.html')
        html = template.render(proj_data,module=mod,project=project)
        out = open(urllib.quote(os.path.join(proj_data['output_dir'],'module',mod.name.lower().replace('/','\\')+'.html')),'w')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'module/'+mod.name.lower().replace('/','\\')+'.html', mod.meta)

    for prog in project.programs:
        template = env.get_template('prog_page.html')
        html = template.render(proj_data,program=prog,project=project)
        out = open(urllib.quote(os.path.join(proj_data['output_dir'],'program',prog.name.lower().replace('/','\\')+'.html')),'w')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'program/'+prog.name.lower().replace('/','\\')+'.html', prog.meta)
    
    tipue.print_output()

