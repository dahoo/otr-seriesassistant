#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Daniel Hoffmann
"""

import helpers
import gtk, requests
from xml.dom.minidom import parseString

class ChooseSeriesDialog(object):
    def __init__(self):
        self.builder = gtk.Builder()
        self.builder.add_from_file("seriesChooserDialog.ui")
        self.builder.connect_signals(self)
        
        helpers.create_treeview_column(self.obj('tv_results'), 'Name', 0,
                               gtk.CellRendererSpin())

        helpers.create_treeview_column(self.obj('tv_results'), 'ID',  1,
                               gtk.CellRendererText())       
        
        window = self.builder.get_object("dialog1")
        window.show_all()

    def obj(self, name):
        """
        returns glade object 'name'
        """
        return self.builder.get_object(name)        
        
    def on_bt_search_clicked(self, action, *args):
        name = self.obj('en_name').get_text()
        language = ''
        if self.obj('rb_german').get_active():
            language = '&language=de'
        elif self.obj('rb_all').get_active():
            language = '&language=all'
        response = requests.get('http://www.thetvdb.com/api/GetSeries.php?seriesname=' + name + language)
        
        if response.status_code == 200:
            xmlFile = parseString(response.content)
            for element in xmlFile.getElementsByTagName('Series'):
                self.obj('ls_series').append((helpers.getNodeText(element, 'SeriesName'),
                         helpers.getNodeText(element, 'seriesid')))
            self.obj('tv_results').set_cursor(0)
            
    def on_bt_ok_clicked(self, action, *args):
        path = self.obj('tv_results').get_cursor()[0]
        if path is not None:
            row = self.obj('ls_series')[path]
            self.response = (row[0], row[1])
            self.quit()
            
    def run(self):
        try:
            gtk.main()
        except KeyboardInterrupt:
            pass
        
    def quit(self):
        gtk.main_quit()
 
def getDialogText():
    dialog = ChooseSeriesDialog()
    dialog.run()
    response = dialog.response
    dialog.builder.get_object("dialog1").destroy()
    return response
    
if __name__ == '__main__':
    print "Selected: %s" % getDialogText()[0]
    gtk.main()
