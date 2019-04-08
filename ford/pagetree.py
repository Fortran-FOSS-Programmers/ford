#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  pagetree.py
#  This file is part of FORD.
#  
#  Copyright 2015 Christopher MacMackin <cmacmackin@gmail.com>
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

import os
import ford.utils

class PageNode(object):
    '''
    Object representing a page in a tree of pages and subpages.
    '''
    
    base_url = '..'
    
    def __init__(self,md,path,parent,extension,pageType='normal',):
        print("Reading page {}".format(os.path.relpath(path)))
        page = open(path,'r')
        text = page.read()
        page.close()
        text = md.convert(text)
        
        if 'title' in md.Meta:
            self.title  = '\n'.join(md.Meta['title'])
        else:
            self.title  = '\n' + os.path.split(path)[1]
            #raise Exception('Page {} has no title metadata'.format(path))
        if 'author' in md.Meta:
            self.author = '\n'.join(md.Meta['author'])
        else:
            self.author = None
        if 'date' in md.Meta:
            self.date   = '\n'.join(md.Meta['date'])
        else:
            self.date = None
        
        self.parent    = parent
        self.contents  = text
        self.subpages  = []
        self.files = []
        if self.parent:
            self.hierarchy = self.parent.hierarchy + [self.parent]
        else:
            self.hierarchy = []

        if pageType == 'index':
            self.filename = 'index'
        elif pageType == 'license':
            self.filename = 'LICENSE'
        else: 
            self.filename = os.path.split(path)[1][:-3]
        self.extension = extension

        if parent:
            self.topdir   = parent.topdir
            self.location = os.path.relpath(os.path.split(path)[0],self.topdir)
            self.topnode = parent.topnode
        else:
            self.topdir   = os.path.split(path)[0]
            self.location = ''
            self.topnode = self

    def __str__(self):
        #~ urlstr = "<a href='{0}/page/{1}/{2}.html'>{3}</a>"
        urlstr = "<a href='{0}'>{1}</a>"
        url = urlstr.format(os.path.join(self.base_url,'page',self.location,self.filename+'.'+self.extension),self.title)
        return url
    
    def __iter__(self):
        retlist = [self]
        for sp in self.subpages:
            retlist.extend(list(sp.__iter__()))
        return iter(retlist)

def get_page_tree(topdir,md,data,parent=None):
    # look for files within topdir
    filelist = sorted(os.listdir(topdir))
    if data['page_index'] in filelist:
        # process index.md
        try:
            node = PageNode(md,os.path.join(topdir,data['page_index']),parent,data['page_extension'],'index')
        except Exception as e:
            print("Warning: Error parsing {}.\n\t{}".format(os.path.relpath(os.path.join(topdir,data['page_index'])),e.args[0]))
            return None
        filelist.remove(data['page_index'])
        # If page index is used, and if there is another index.md, that file will
        # not be parsed.
        if 'index.md' in filelist: filelist.remove('index.md')
    else:
        print('Warning: No '+data['page_index']+' file in directory {}'.format(topdir))
        return None

    if data['page_license'] in filelist:
        # process LICENSE
        try:
            node.subpages.append(PageNode(md,os.path.join(topdir,data['page_license']),node,data['page_extension'],'license'))
        except Exception as e:
            print("Warning: Error parsing {}.\n\t{}".format(os.path.relpath(os.path.join(topdir,data['page_license'])),e.args[0]))
        filelist.remove(data['page_license'])
        if 'LICENSE.md' in filelist: filelist.remove('LICENSE.md')
        
    for name in filelist:
        if name[0] != '.' and name[-1] != '~':
            if os.path.isdir(os.path.join(topdir,name)):
                if data['page_dir_recursive'] == True:
                    # recurse into subdirectories
                    subnode = get_page_tree(os.path.join(topdir,name),md,data,node)
                    if subnode: node.subpages.append(subnode)
            elif name[-3:] == '.md':
                # process subpages
                try:
                    node.subpages.append(PageNode(md,os.path.join(topdir,name),node,data['page_extension']))
                except Exception as e:
                    print("Warning: Error parsing {}.\n\t{}".format(os.path.relpath(os.path.join(topdir,name)),e.args[0]))
                    continue
            else:
                node.files.append(name)
    return node


def set_base_url(url):
    PageNode.base_url = url
