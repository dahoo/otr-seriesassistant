# -*- coding: utf-8 -*-
"""
@author: Daniel Hoffmann
"""

import gtk, os

def assure_path_exists(path):
        dir = os.path.dirname(path)
        if not os.path.exists(dir):
                os.makedirs(dir)

def getNodeText(element, tagName):
    elements = element.getElementsByTagName(tagName)
    if len(elements) > 0 and elements[0].firstChild:
        return elements[0].firstChild.nodeValue
    return ''

def add_cell_renderer(control, col_no=0, renderer=None, attr='text'):
    if renderer is None:
        renderer = gtk.CellRendererText()
    control.pack_start(renderer, True)
    control.add_attribute(renderer, attr, col_no)
    

def create_treeview_column(widget, title, col_no, renderer=None,
                           attr='text'):
    column = gtk.TreeViewColumn(title)
    widget.append_column(column)
    add_cell_renderer(column, col_no, renderer,  attr)