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
import os
import shutil
import time

import jinja2

import ford.sourceform
import ford.tipue_search
import ford.utils

#Python 2 or 3:
if (sys.version_info[0]>2):
    from urllib.parse import quote
else:
    from urllib import quote

def print_html(project,proj_data,proj_docs,page_tree,relative):
    out_dir = quote(proj_data['output_dir'])
    
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
            os.mkdir(os.path.join(out_dir,'page',node.location), 0o755)
        template = env.get_template('info_page.html')
        node.contents = ford.utils.sub_links(ford.utils.sub_macros(ford.utils.sub_notes(node.contents),base_url),project)
        html = template.render(proj_data,page=node,project=project,topnode=page_tree)
        out = open(os.path.join(out_dir,'page',node.location,quote(node.filename)+'.html'),'wb')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'page'+node.location+'/'+node.filename+'.html')
        for item in node.files:
            try:
                shutil.copy(os.path.join(proj_data['page_dir'],node.location,item),
                            os.path.join(out_dir,'page',node.location))
            except Exception as e:
                print('Warning: could not copy file {}. Error: {}'.format(
                  os.path.join(proj_data['page_dir'],node.location,item),e.args[0]))
        for sub in node.subpages: 
            print_pages(sub)
            if relative: set_base_url(base_url)


    loc = os.path.dirname(__file__)
    env = jinja2.Environment(loader=jinja2.FileSystemLoader(os.path.join(loc, "templates")))

    try:
        if os.path.isfile(out_dir):
            os.remove(out_dir)
        elif os.path.isdir(out_dir):
            shutil.rmtree(out_dir)
        os.makedirs(out_dir, 0o755)
    except Exception as e:
        print('Error: Could not create output directory. {}'.format(e.args[0]))
    os.mkdir(os.path.join(out_dir,'lists'), 0o755)
    os.mkdir(os.path.join(out_dir,'sourcefile'), 0o755)
    os.mkdir(os.path.join(out_dir,'type'), 0o755)
    os.mkdir(os.path.join(out_dir,'proc'), 0o755)
    os.mkdir(os.path.join(out_dir,'interface'), 0o755)
    os.mkdir(os.path.join(out_dir,'module'), 0o755)
    os.mkdir(os.path.join(out_dir,'program'), 0o755)
    os.mkdir(os.path.join(out_dir,'src'), 0o755)
    
    copytree(os.path.join(loc,'css'), os.path.join(out_dir,'css'))
    copytree(os.path.join(loc,'fonts'), os.path.join(out_dir,'fonts'))
    copytree(os.path.join(loc,'js'),os.path.join(out_dir,'js'))
    copytree(os.path.join(loc,'tipuesearch'),os.path.join(out_dir,'tipuesearch'))
    
    if 'media_dir' in proj_data:
        try:
            copytree(proj_data['media_dir'],os.path.join(out_dir,'media'))
        except:
            print('Warning: error copying media directory {}'.format(proj_data['media_dir']))

    
    if 'css' in proj_data:
        shutil.copy(proj_data['css'],os.path.join(out_dir,'css','user.css'))
    if proj_data['favicon'] == 'default-icon':
        shutil.copy(os.path.join(loc,'favicon.png'),os.path.join(out_dir,'favicon.png'))
    else:
        shutil.copy(proj_data['favicon'],os.path.join(out_dir,'favicon.png'))
    
    if relative: set_base_url('.')
    else: set_base_url(proj_data['project_url'])        

    tipue = ford.tipue_search.Tipue_Search_JSON_Generator(out_dir,proj_data['project_url'])

    template = env.get_template('index.html')
    html = template.render(proj_data,proj_docs=proj_docs,project=project)
    out = open(os.path.join(out_dir,'index.html'),'wb')
    out.write(html.encode('utf8'))
    out.close()
    tipue.create_node(html,'index.html', {'category': 'home'})
    
    template = env.get_template('search.html')
    html = template.render(proj_data,project=project)
    out = open(os.path.join(out_dir,'search.html'),'wb')
    out.write(html.encode('utf8'))
    out.close()
    
    if relative: set_base_url('..')
    
    if len(project.procedures) > 0:
        template = env.get_template('proc_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(out_dir,'lists','procedures.html'),'wb')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'lists/procedures.html', {'category': 'list procedures'})

    if len(project.files) > 1:
        template = env.get_template('file_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(out_dir,'lists','files.html'),'wb')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'lists/files.html', {'category': 'list files'})
        
    if len(project.modules) > 0:
        template = env.get_template('mod_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(out_dir,'lists','modules.html'),'wb')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'lists/modules.html', {'category': 'list modules'})

    if len(project.programs) > 1:
        template = env.get_template('prog_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(out_dir,'lists','programs.html'),'wb')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'lists/programs.html', {'category': 'list programs'})
    
    if len(project.types) > 0:
        template = env.get_template('types_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(out_dir,'lists','types.html'),'wb')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'lists/types.html', {'category': 'list derived types'})

    if len(project.absinterfaces) > 0:
        template = env.get_template('absint_list.html')
        html = template.render(proj_data,project=project)
        out = open(os.path.join(out_dir,'lists','absint.html'),'wb')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'lists/absint.html', {'category': 'list abstract interfaces'})

    for src in project.files:
        template = env.get_template('file_page.html')
        html = template.render(proj_data,src=src,project=project)
        out = open(os.path.join(out_dir,'sourcefile',quote(src.name.lower().replace('/','slash'))+'.html'),'wb')
        out.write(html.encode('utf8'))
        out.close()
        dstdir = os.path.join(out_dir,'src',src.name)
        shutil.copy(src.path,dstdir)
        tipue.create_node(html,'sourcefile/'+src.name.lower().replace('/','slash')+'.html', src.meta)

    for dtype in project.types:
        template = env.get_template('type_page.html')
        html = template.render(proj_data,dtype=dtype,project=project)
        out = open(os.path.join(out_dir,'type',quote(dtype.name.lower().replace('/','slash'))+'.html'),'wb')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'type/'+dtype.name.lower().replace('/','slash')+'.html', dtype.meta)

    for absint in project.absinterfaces:
        template = env.get_template('nongenint_page.html')
        out = open(os.path.join(out_dir,'interface',quote(absint.name.lower().replace('/','slash'))+'.html'),'wb')
        html = template.render(proj_data,interface=absint,project=project)
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'interface/'+absint.name.lower().replace('/','slash')+'.html',absint.meta)

    for proc in project.procedures:
        if proc.obj == 'proc':
            template = env.get_template('proc_page.html')
            out = open(os.path.join(out_dir,'proc',quote(proc.name.lower().replace('/','slash'))+'.html'),'wb')
            html = template.render(proj_data,procedure=proc,project=project)
            tipue.create_node(html,'proc/'+proc.name.lower().replace('/','slash')+'.html', proc.meta)
        else:
            if proc.generic:
                template = env.get_template('genint_page.html')
            else:
                template = env.get_template('nongenint_page.html')
            out = open(os.path.join(out_dir,'interface',quote(proc.name.lower().replace('/','slash'))+'.html'),'wb')
            html = template.render(proj_data,interface=proc,project=project)
            tipue.create_node(html,'interface/'+proc.name.lower().replace('/','slash')+'.html', proc.meta)
        
        out.write(html.encode('utf8'))
        out.close()

    for mod in project.modules:
        template = env.get_template('mod_page.html')
        html = template.render(proj_data,module=mod,project=project)
        out = open(os.path.join(out_dir,'module',quote(mod.name.lower().replace('/','slash'))+'.html'),'wb')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'module/'+mod.name.lower().replace('/','slash')+'.html', mod.meta)

    for prog in project.programs:
        template = env.get_template('prog_page.html')
        html = template.render(proj_data,program=prog,project=project)
        out = open(os.path.join(out_dir,'program',quote(prog.name.lower().replace('/','slash'))+'.html'),'wb')
        out.write(html.encode('utf8'))
        out.close()
        tipue.create_node(html,'program/'+prog.name.lower().replace('/','slash')+'.html', prog.meta)
    
    if page_tree: 
        print_pages(page_tree)
    
    tipue.print_output()


def copytree(src, dst, symlinks=False, ignore=None):
    """
    A version of shutil.copystat() modified so that it won't copy over
    date metadata.
    """
    try:
        WindowsError
    except NameError:
        WindowsError = None
    
    def touch(path):
        now = time.time()
        try:
            # assume it's there
            os.utime(path, (now, now))
        except os.error:
            # if it isn't, try creating the directory,
            # a file with that name
            os.makedirs(os.path.dirname(path))
            open(path, "w").close()
            os.utime(path, (now, now))

    names = os.listdir(src)
    if ignore is not None:
        ignored_names = ignore(src, names)
    else:
        ignored_names = set()

    os.makedirs(dst)
    errors = []
    for name in names:
        if name in ignored_names:
            continue
        srcname = os.path.join(src, name)
        dstname = os.path.join(dst, name)
        try:
            if symlinks and os.path.islink(srcname):
                linkto = os.readlink(srcname)
                os.symlink(linkto, dstname)
            elif os.path.isdir(srcname):
                copytree(srcname, dstname, symlinks, ignore)
            else:
                shutil.copy2(srcname, dstname)
                touch(dstname)                
            # XXX What about devices, sockets etc.?
        except (IOError, os.error) as why:
            errors.append((srcname, dstname, str(why)))
        # catch the Error from the recursive copytree so that we can
        # continue with other files
        except Error as err:
            errors.extend(err.args[0])
    try:
        shutil.copystat(src, dst)
    except WindowsError:
        # can't copy file access times on Windows
        pass
    except OSError as why:
        errors.extend((src, dst, str(why)))
    touch(dst)
    if errors:
        raise Error(errors)
