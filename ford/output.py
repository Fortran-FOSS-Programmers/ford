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
import ford.sourceform

def print_html(project,proj_data,proj_docs,relative):
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(os.path.dirname(__file__), "templates")))

    if os.path.isfile(proj_data['output_dir']):
        os.remove(proj_data['output_dir'])
    elif os.path.isdir(proj_data['output_dir']):
        shutil.rmtree(proj_data['output_dir'])

    os.mkdir(proj_data['output_dir'], 0755)
    os.mkdir(os.path.join(proj_data['output_dir'],'lists'), 0755)
    os.mkdir(os.path.join(proj_data['output_dir'],'sourcefile'), 0755)
    os.mkdir(os.path.join(proj_data['output_dir'],'type'), 0755)
    os.mkdir(os.path.join(proj_data['output_dir'],'proc'), 0755)
    os.mkdir(os.path.join(proj_data['output_dir'],'interface'), 0755)
    os.mkdir(os.path.join(proj_data['output_dir'],'module'), 0755)
    os.mkdir(os.path.join(proj_data['output_dir'],'program'), 0755)
    os.mkdir(os.path.join(proj_data['output_dir'],'src'), 0755)
    
    loc = os.path.dirname(__file__)
    shutil.copytree(os.path.join(loc,'css'), os.path.join(proj_data['output_dir'],'css'))
    shutil.copytree(os.path.join(loc,'fonts'), os.path.join(proj_data['output_dir'],'fonts'))
    shutil.copytree(os.path.join(loc,'js'),os.path.join(proj_data['output_dir'],'js'))
    
    if relative:
        ford.sourceform.set_base_url('.')
        proj_data['project_url'] = '.'

    template = env.get_template('index.html')
    html = template.render(proj_data,proj_docs=proj_docs,project=project)
    out = open(proj_data['output_dir'] + '/index.html','w')
    out.write(html)
    out.close()
    
    if relative:
        ford.sourceform.set_base_url('..')
        proj_data['project_url'] = '..'
        
    if len(project.procedures) > 0:
        template = env.get_template('proc_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(proj_data['output_dir'],'lists','procedures.html'),'w')
        out.write(html)
        out.close()

    if len(project.files) > 1:
        template = env.get_template('file_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(proj_data['output_dir'],'lists','files.html'),'w')
        out.write(html)
        out.close()
        
    if len(project.modules) > 0:
        template = env.get_template('mod_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(proj_data['output_dir'],'lists','modules.html'),'w')
        out.write(html)
        out.close()

    if len(project.programs) > 1:
        template = env.get_template('prog_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(proj_data['output_dir'],'lists','programs.html'),'w')
        out.write(html)
        out.close()
    
    if len(project.types) > 0:
        template = env.get_template('types_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(proj_data['output_dir'],'lists','types.html'),'w')
        out.write(html)
        out.close()
    
    for src in project.files:
        template = env.get_template('file_page.html')
        html = template.render(proj_data,src=src,project=project)
        out = open(os.path.join(proj_data['output_dir'],'sourcefile',src.name+'.html'),'w')
        out.write(html)
        out.close()
        dstdir = os.path.join(proj_data['output_dir'],'src',src.name)
        shutil.copy(src.path,dstdir)
    
    for dtype in project.types:
        template = env.get_template('type_page.html')
        html = template.render(proj_data,dtype=dtype[1],project=project)
        out = open(os.path.join(proj_data['output_dir'],'type',dtype[1].name) + '.html','w')
        out.write(html)
        out.close()
    
    for proc in project.procedures:
        if proc[1].obj == 'proc':
            template = env.get_template('proc_page.html')
            out = open(os.path.join(proj_data['output_dir'],'proc',proc[1].name+'.html'),'w')
            html = template.render(proj_data,procedure=proc[1],project=project)
        else:
            template = env.get_template('interface_page.html')
            out = open(os.path.join(proj_data['output_dir'],'interface',proc[1].name+'.html'),'w')
            html = template.render(proj_data,interface=proc[1],project=project)
        out.write(html)
        out.close()
    
    for mod in project.modules:
        template = env.get_template('mod_page.html')
        html = template.render(proj_data,module=mod,project=project)
        out = open(os.path.join(proj_data['output_dir'],'module',mod.name+'.html'),'w')
        out.write(html)
        out.close()

    for prog in project.programs:
        template = env.get_template('prog_page.html')
        html = template.render(proj_data,program=prog,project=project)
        out = open(os.path.join(proj_data['output_dir'],'program',prog.name+'.html'),'w')
        out.write(html)
        out.close()


if __name__ == '__main__':
	main()

