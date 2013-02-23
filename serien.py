#!/usr/bin/env python
#-*- coding: utf-8-*-
"""
@author: Daniel Hoffmann
"""

import helpers, inputDialog
import gtk, requests, zipfile, StringIO, os, shelve
from xml.dom.minidom import parseString
from collections import namedtuple
from os.path import join, expanduser

Episode = namedtuple("Episode", "season number name image plot id")

class SeriesAssistant(object):
    def __init__(self):

        self.bannerDirectory = join(expanduser('~'), '.config', 
                                    'OTR-Serien-Assistent', 'banners')
        self.seriesDirectory = join(expanduser('~'), '.config', 
                                    'OTR-Serien-Assistent', 'series')
        helpers.assure_path_exists(self.bannerDirectory)    
        helpers.assure_path_exists(self.seriesDirectory)    
        
        self.builder = gtk.Builder()
        self.builder.add_from_file("main.ui")
        self.builder.connect_signals(self)
        
        self.actions = shelve.open(join(expanduser('~'), '.config', 
                                    'OTR-Serien-Assistent', 'config.db'))
        self.series = shelve.open(join(expanduser('~'), '.config', 
                                    'OTR-Serien-Assistent', 'series.db'))
        images = ['record.png', 'download.png', 'seen.png']                
        self.list_pixbufs = [gtk.gdk.Pixbuf(gtk.gdk.COLORSPACE_RGB, True, 8, 16, 16).fill(0x00000000)]
        for image in images:
            f = join('images', image)
            pixbuf = gtk.gdk.pixbuf_new_from_file(f)
            self.list_pixbufs.append(pixbuf)

        helpers.create_treeview_column(self.obj('tv_episodes'), '', 0,
                               gtk.CellRendererPixbuf(), 'pixbuf')        
        
        helpers.create_treeview_column(self.obj('tv_episodes'), 'Staffel', 1,
                               gtk.CellRendererText())

        helpers.create_treeview_column(self.obj('tv_episodes'), 'Episode',  2,
                               gtk.CellRendererText())

        helpers.create_treeview_column(self.obj('tv_episodes'), 'Name',  3,
                               gtk.CellRendererText())
                            
        helpers.add_cell_renderer(self.obj('cb_series')) 
        
        self.loadSeries()        
        
        self.obj('tv_episodes').set_cursor(0)
    
        window = self.builder.get_object("window1")
        window.show_all()


    def obj(self, name):
    	"""
	returns glade object 'name'
	"""
        return self.builder.get_object(name)
        

    def run(self):
        try:
            gtk.main()
        except KeyboardInterrupt:
            pass
    

    def quit(self):
        gtk.main_quit()

    def loadSeries(self):
        for value in self.series:
            self.obj('ls_series').append((self.series[value], value))
        self.obj('cb_series').set_active(0)

    def retrieveEpisodeNames(self, seriesId):
        # Please don't use this API key, apply for your own on 
        # http://thetvdb.com/?tab=apiregister
        apiKey = '572F11950DF860B6'
    
        path = 'http://thetvdb.com/api/'+ apiKey + '/series/' \
            + seriesId + '/all'
    
        filepath = self.seriesDirectory
        filepath += os.sep.join(path.split('/series')[1:])
        
        helpers.assure_path_exists(filepath)

        content = ''

        try:
           with open(os.path.join(filepath, 'de.xml')) as file:              
               content = file.read()
               file.close()
        except IOError:
            response = requests.get(path + '/de.zip')
            if response.status_code == 200:
                zip = zipfile.ZipFile(StringIO.StringIO(response.content))
                zip.extract('de.xml', filepath)
                with open(os.path.join(filepath, 'de.xml')) as file: 
                   content = file.read()
                   file.close() 

        
        xmlFile = parseString(content)
        
        episodesXML = xmlFile.getElementsByTagName('Episode')
        episodes = []
        for episodeElem in episodesXML:
            season = int(helpers.getNodeText(episodeElem, 'Combined_season'))
            if season > 0:
                name = helpers.getNodeText(episodeElem, 'EpisodeName')
                number = helpers.getNodeText(episodeElem, 'Combined_episodenumber')
                season = int(helpers.getNodeText(episodeElem, 'Combined_season'))
                image = 'http://www.thetvdb.com/banners/' + helpers.getNodeText(episodeElem, 'filename')
                plot = helpers.getNodeText(episodeElem, 'Overview')
                episodeId = helpers.getNodeText(episodeElem, 'id')
                
                episode = Episode(season, int(number.split('.')[0]), name, image, plot, episodeId)
                episodes.append(episode)
        return episodes
    
    def set_image(self, path):
        image = self.builder.get_object("im_episode")
        filepath = self.bannerDirectory
        filepath += os.sep.join(path.split('/banners')[1:])
        
        helpers.assure_path_exists(filepath)

        try:
           with open(filepath) as file: 
               image.set_from_file(filepath)
               file.close()
        except IOError:
            try:
                response = requests.get(path)
                if response.status_code == 200:
                    try:
                        with open(filepath, 'wb') as f:
                            for chunk in response.iter_content():
                                f.write(chunk)
                            f.close()
                        with open(filepath) as file: 
                           image.set_from_file(filepath)
                           file.close()
                    except IOError:
                        image.clear()
            except requests.exceptions.ConnectionError:
                print 'No Internet connection!'

    def set_values(self, values):
        self.set_image(values[4]);
        self.obj('scroll_plot').get_vadjustment().set_value(0)
        textBuffer = self.obj('txt_plot').get_buffer()
        textBuffer.set_text(values[5])
        
        episodeId = self.get_current_episode()[6]
        seriesId = self.get_current_series()[1]
        action = self.actions.setdefault(seriesId + episodeId, 0)
        
        if action == 0:
            self.obj('rb_no_action').set_active(True)
        elif action == 1:
            self.obj('rb_recorded').set_active(True)
        elif action == 2:
            self.obj('rb_downloaded').set_active(True)
        elif action == 3:
            self.obj('rb_seen').set_active(True)
            
        self.actions.sync()

    def get_icon_pixbuf(self, stock):
        return self.obj('tv_episodes').render_icon(stock_id=getattr(gtk, stock),
                                size=gtk.ICON_SIZE_MENU,
                                detail=None)
                                
    def get_current_series(self):
        tree_iter = self.obj('cb_series').get_active_iter()
        if tree_iter != None:
            model = self.obj('cb_series').get_model()
            name = model[tree_iter][0]
            row_id = model[tree_iter][1]
            return (name, row_id)
    
    def get_current_episode(self):
        path = self.obj('tv_episodes').get_cursor()[0]
        if path is not None:
            return self.obj('ls_episodes')[path]
            
    def set_current_episode_pixbuf(self, pixbuf):
        tree_iter = self.obj('tv_episodes').get_cursor()[0]
        if tree_iter != None:
            model = self.obj('tv_episodes').get_model()
            model[tree_iter][0] = pixbuf
            return len(model)
        
    def update_status_bar(self, seen, number):
        fraction = min(1.0, seen / number)
        self.obj('pg_series').set_fraction(fraction)
        self.obj('pg_series').set_text('{0:n}/{1:n}'.format(seen, number))

###############################
## signal handling
###############################

#################
## main window

    def on_window1_delete_event(self, *args):
        self.actions.close()
        self.series.close()
        self.quit()

#############
## actions

    def on_tv_episodes_cursor_changed(self, action, *args):
        path = self.obj('tv_episodes').get_cursor()[0]
        if path is not None:
            row = self.obj('ls_episodes')[path]
            self.set_values(row)
        
    def on_cb_series_changed(self, action, *args):
        name, seriesId = self.get_current_series()
        self.obj('ls_episodes').clear()
        episodes = self.retrieveEpisodeNames(seriesId)     

        fraction = 0.0
        for episode in episodes:
            episodeId = episode[5]
            action = self.actions.setdefault(str(int(seriesId + episodeId)), 0)
            if action == 3:
                fraction += 1
            pixbuf = self.list_pixbufs[action]            
            self.obj('ls_episodes').append((pixbuf, episode[0], episode[1], episode[2],
                                             episode[3], episode[4], episode[5]))
        self.obj('tv_episodes').set_cursor(0)
        self.update_status_bar(fraction, len(episodes))
                                         
    def on_bt_new_clicked(self, action, *args):
        new = inputDialog.getDialogText()
        self.obj('ls_series').append((new[0], new[1]))
        self.obj('cb_series').set_active(len(self.obj('ls_series')) - 1)
        self.series[new[1]] = new[0]
        self.series.sync()

    def on_radiobuttons_group_changed(self, action, *args):
        try:
            episodeId = self.get_current_episode()[6]
            seriesId = self.get_current_series()[1]           
            
            buttons = action.get_group()
            preAction = self.actions[seriesId + episodeId]
            for button in buttons:
                if button.get_active():
                    name = gtk.Buildable.get_name(button)
                    if name == 'rb_no_action':
                        self.actions[seriesId + episodeId] = 0
                    elif name == 'rb_recorded':
                        self.actions[seriesId + episodeId] = 1
                    elif name == 'rb_downloaded':
                        self.actions[seriesId + episodeId] = 2
                    elif name == 'rb_seen':
                        self.actions[seriesId + episodeId] = 3
                    self.actions.sync()
                    number = self.set_current_episode_pixbuf(
                        self.list_pixbufs[self.actions[seriesId + episodeId]])
            
            if not preAction == self.actions[seriesId + episodeId]:
                update = 1.0
                if (preAction == 3 and not self.actions[seriesId + episodeId] == 3):
                    update *= -1
                oldFraction = self.obj('pg_series').get_fraction()
                print oldFraction * number + update
                self.update_status_bar((oldFraction * number) + update, number)
        except TypeError:
            pass


if __name__ == '__main__':
    app = SeriesAssistant()
    app.run()