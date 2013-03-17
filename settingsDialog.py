#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@author: Daniel Hoffmann
"""

import gtk
from os.path import join, expanduser

class SettingsDialog(object):
    def __init__(self, videoPath, archivePath, videoPlayer):
        self.builder = gtk.Builder()
        self.builder.add_from_file("settingsDialog.ui")
        self.builder.connect_signals(self)
        
        self.videoPath = videoPath
        self.archivePath = archivePath
        self.videoPlayer = videoPlayer
        
        if len(videoPath) > 0:
            self.obj('fcbVideos').set_current_folder(self.videoPath)
            
        if len(archivePath) > 0:
            self.obj('fcbVideosArchive').set_current_folder(self.archivePath)
        
        if len(videoPlayer) > 0:
            self.obj('fcbPlayer').set_filename(self.videoPlayer)
            
        self.obj('fcbVideosArchive').connect('current-folder-changed', self.file_selected)
        
        window = self.builder.get_object("dialog1")
        window.show_all()

    def obj(self, name):
        """
        returns glade object 'name'
        """
        return self.builder.get_object(name)     
            
    def file_selected(self, widget):
        name = gtk.Buildable.get_name(widget)
        if name == 'fcbVideos':
            self.videoPath = widget.get_filename()
        elif name == 'fcbVideosArchive':
            self.archivePath = widget.get_filename()
        elif name == 'fcbPlayer':
            self.videoPlayer = widget.get_filename()
            
    def on_ac_ok_clicked_activate(self, action, *args):
        self.response = (self.videoPath, self.archivePath, self.videoPlayer)
        self.quit()
        
    def on_ac_cancel_clicked_activate(self, action, *args):
        self.response = None
        self.quit()
            
    def run(self):
        try:
            gtk.main()
        except KeyboardInterrupt:
            pass
        
    def quit(self):
        gtk.main_quit()
 
def getDialogResponse(videoPath, archivePath, videoPlayer):
    dialog = SettingsDialog(videoPath, archivePath, videoPlayer)
    dialog.run()
    response = dialog.response
    dialog.builder.get_object("dialog1").destroy()
    return response
    
if __name__ == '__main__':
    videoPath = join(expanduser('~'), 'Videos')
    archivePath = join(expanduser('~'), 'Videos', 'archiv')
    videoPlayer = join('/', 'usr', 'bin', 'totem')
    print getDialogResponse(videoPath, archivePath, videoPlayer)
    gtk.main()
