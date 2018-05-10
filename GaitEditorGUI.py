# -*- coding: utf-8 -*-
"""
Created on Fri Mar 23 21:08:08 2018

@author: rdb_lab
"""

# -*- coding: utf-8 -*-
"""
Created on Tue Jan 09 14:24:15 2018

@author: adesnik-img


TO FIX COMBO: instead of having second_selected act on top of selected print,
when you enter a combo state just set selected_print to be like to_Combine_print
and turn it orange. Then clear selected print. Then you can select selected print
as usual, and combine if need be or whatever.


"""
import matplotlib as mp
mp.use('TkAgg')
#mp.use('Qt4Agg')
import matplotlib.pyplot as plt
from matplotlib.widgets import Button, Slider, RadioButtons
import matplotlib.gridspec as gspec
import matplotlib.animation as animation
import numpy as np
import matplotlib.patches as patches
import pandas as pd
from test_alt_pims import PyAVReaderIndexed
from GaitAnalyzer2 import combine_prints
import json
from matplotlib.widgets import Lasso
from matplotlib import path
import cv2
import sys
if (sys.version_info > (3, 0)):
    import tkinter as tk
    import tkinter.filedialog as tkFileDialog
    import tkinter.messagebox as tkMessageBox
else:
    import Tkinter as tk
    import tkFileDialog
    import tkMessageBox
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg, NavigationToolbar2TkAgg)
from matplotlib.figure import Figure
import os



class FigureContainer():
    """instantiates figure and axes, creates all other objects. Holds the
    animation"""
    def __init__(self):
        #because I'm using keys that matlab also uses, remove some bindings
        plt.rcParams['keymap.fullscreen'] = '{'
        plt.rcParams['keymap.yscale'] = '}'
        self.fig = plt.figure(facecolor='w')
        self.fig.set_size_inches(16, 9)
        g = gspec.GridSpec(5,2, height_ratios = [2, 6, 4, 1, 6],
                                width_ratios = [10,3])
        g.update(left=0.05, right=0.95, wspace=0.02, hspace=.04,
                 bottom = .02, top = .98)

        #add the axes in the subplot areas desired
        self.spatial_axis = self.fig.add_subplot(g[1,0])
        self.vid_axis = self.fig.add_subplot(g[4,0])
        self.temporal_axis = self.fig.add_subplot(g[2,0])
        #self.select_axis = self.fig.add_subplot(g[:,1])
        self.sel_panel = SelectPanel(self.fig, g)
        #create an axes to hold space for the buttons
        #self.fig.add_subplot(g[0,0]).set_axis_off()


        #add a slider
        slid_ax = self.fig.add_subplot(g[3,0])
        #TODO: does this actually force it to an int
        self.slide = Slider(slid_ax, 'Frame', 0, 100,
                            valinit=0, valfmt='%0.0f')

        self.print_manager = PrintManager(self.temporal_axis,
                                          self.spatial_axis, self.sel_panel,
                                          self.vid_axis, self.slide, file)
        self.sel_panel.set_print_manager(self.print_manager)
        self.set_slider_range()
        self.prev_frame = self.slide.val
        #activate pick events
        self.fig.canvas.mpl_connect('pick_event', self.print_manager.on_pick)
        self.fig.canvas.mpl_connect('key_press_event',
                                    self.print_manager.on_key_press)
        g2 = gspec.GridSpecFromSubplotSpec(1,4,
                    subplot_spec=g[0,0], wspace=0.1, hspace=0.1)
        #g2.update(left=0.05, right=0.95, wspace=0.02, hspace=.04,
        #         bottom = .2, top = .8)
        #ax=self.fig.add_subplot(g2[0,0])
        #Button(ax, 'Load File').on_clicked(
        #                            self.print_manager.initiate_split_window)
        ax=self.fig.add_subplot(g2[0,0])
        Button(ax, 'Save Changes')
        #ax=self.fig.add_subplot(g2[0,2])
        #Button(ax, 'Pause Video')
        #ax=self.fig.add_subplot(g2[0,3])
        #Button(ax, 'View Deleted')

        #and start the animation
        self.anim = animation.FuncAnimation (self.fig, self.update_func,
                                             fargs= (),  interval = 15,
                                             repeat = True)
        plt.show()

    def update_func(self, j):
        """based on the value of the slider, update the video
        """
        i = int(self.slide.val)+1
        if i > self.slide.valmax:
            i=self.slide.valmin
        self.print_manager.change_frame(self.prev_frame,i)
        #self.slide.set_val(i%len(self.left_panel.frames))
        self.slide.set_val(i)
        self.prev_frame = i
        return j

    def set_slider_range(self):
        """set the slider to range between combo_prints first frame and
        last frame"""
        self.slide.set_val(self.print_manager.combo_prints.first_frame.min())
        self.slide.valmin = self.print_manager.combo_prints.first_frame.min()
        self.slide.valmax = self.print_manager.combo_prints.last_frame.max()
        self.slide.ax.set_xlim(self.slide.valmin,self.slide.valmax)

class SelectPanel():
    """Displays radio buttons for paw classification and the current paw number.
    Alse displays information on the combination process
    """
    def __init__(self, fig, outer):
        #TODO: you may want this to not be a title, for now seems good enough
        self.title_axes = fig.add_subplot(outer[1,1])
        self.title_axes.set_axis_off()
        g = gspec.GridSpecFromSubplotSpec(1,2,
                    subplot_spec=outer[1,1], wspace=0.1, hspace=0.1)
        self.lr_axis = fig.add_subplot(g[0,1])
        self.lr_axis.set_axis_off()
        self.fh_axis = fig.add_subplot(g[0,0])
        self.fh_axis.set_axis_off()

        #button_holder = fig.add_subplot(outer[1,1])
        #button_holder.set_axis_off()
        g = gspec.GridSpecFromSubplotSpec(4,1,
                    subplot_spec=outer[2,1], wspace=0.1, hspace=0.1)
        #g.update(left=0.15, right=0.85, wspace=0.02, hspace=.04,
        #         bottom = .02, top = .98)
        ax = fig.add_subplot(g[1,0])
        Button(ax, 'Delete')
        ax = fig.add_subplot(g[2,0])
        Button(ax, 'Merge')
        ax = fig.add_subplot(g[3,0])
        Button(ax, 'Split Print')


    def set_print_manager(self, pm):
        self.print_manager = pm

    def set_selected(self, print_numb, is_right, is_hind):
        """when a paw is selected, set the radio buttons and their callbacks
        """
        self.clear_axes()
        self.title_axes.set_title('Print ' + str(print_numb))
        self.lr_but = RadioButtons(self.lr_axis, ('Left', 'Right'), active = int(is_right))
        self.fh_but = RadioButtons(self.fh_axis, ('Front', 'Hind'), active = int(is_hind))
        self.lr_but.on_clicked(self.print_manager.change_print_classification)
        self.fh_but.on_clicked(self.print_manager.change_print_classification)
        plt.draw()

    def clear_axes(self):
        self.title_axes.clear()
        self.title_axes.set_axis_off()
        self.title_axes.set_title('')
        self.lr_axis.clear()
        self.lr_axis.set_axis_off()
        self.fh_axis.clear()
        self.fh_axis.set_axis_off()
        self.lr_but = None
        self.fh_but = None
        plt.draw()

    def display_combo_text(self, print_numb):
        """Displays directions when combo state is active
        """
        self.clear_axes()
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)

        # place a text box in upper left in axes coords
        self.title_axes.text(0.05, 0.95, "Left click on another print to " +
                             "combine with print " + str(print_numb) + "\n" +
                             "Or press c again to cancel",
                             transform=self.title_axes.transAxes,
                             fontsize=24, verticalalignment='top', bbox=props)

    def display_combo_text2(self, print_numb, print_numb2):
        """Displays directions when combo state is active
        """
        self.clear_axes()
        props = dict(boxstyle='round', facecolor='wheat', alpha=0.5)

        # place a text box in upper left in axes coords
        self.title_axes.text(0.05, 0.95, "To combine print " + str(print_numb) +
                             "\n" + "and print " + str(print_numb2) + "\n" +
                             "Press enter. Or press c again to cancel",
                             transform=self.title_axes.transAxes,
                             fontsize=24, verticalalignment='top', bbox=props)



class PrintManager():
    def __init__(self, temporal_axis, spatial_axis, select_panel, vid_axis,
                 slider, file):
        
        self.temporal_axis = temporal_axis
        self.spatial_axis = spatial_axis
        self.select_panel = select_panel
        self.combo_prints = pd.read_csv(file.replace('.mp4', ' combo df.csv'),
                                        index_col = 0)
        self.hulls_df = pd.read_pickle(file.replace('.mp4', 'hull.p'))
        #add paw_id to combo_prints for color and other purposes
        self.combo_prints.is_hind = self.combo_prints.is_hind.astype('bool')
        self.combo_prints.is_right = self.combo_prints.is_right.astype('bool')
        self.assign_paw_ids()
        self.colors = ['c','g','b','m']
        self.slide = slider

        self.vid_panel = VideoPanel(vid_axis, self.combo_prints, self.hulls_df,
                                    self.colors, file)

        self.selected_print = None
        self.in_combo_state = False
        self.second_selected = None #used when in combo state to hold the other print

        self.artist_dict = {}
        self.print_dict = {}
        for print_numb in self.combo_prints.index.values:
            self.print_dict[print_numb] = []

        self.display_paws_temporal()
        self.display_paws_spatial()

    def assign_paw_ids(self):
        """add paw_id to combo_prints to color and locate prints"""
        self.combo_prints.loc[~self.combo_prints.is_right, 'paw_id'] = 0
        self.combo_prints.loc[(~self.combo_prints.is_right) &
                            ~self.combo_prints.is_hind, 'paw_id'] = 1
        self.combo_prints.loc[self.combo_prints.is_right, 'paw_id'] = 2
        self.combo_prints.loc[(self.combo_prints.is_right)
                            & ~self.combo_prints.is_hind, 'paw_id'] = 3

    def display_paws_temporal(self):
        """plots matplotlib rects to make a hildebrand plot for the gait"""
        self.temporal_axis.clear()
        for print_numb, print_ in self.combo_prints.iterrows():
            patch = patches.Rectangle((print_.first_frame, print_.paw_id),
                                      print_.last_frame-print_.first_frame, 1,
                                      facecolor=self.colors[int(print_.paw_id)],
                                      picker = 2, linewidth = 3)
            self.temporal_axis.add_patch(patch)
            self.artist_dict[patch] = print_numb
            self.print_dict[print_numb].append(patch)
        self.temporal_axis.set_xlim(self.combo_prints.first_frame.min(),
                                    self.combo_prints.last_frame.max())
        self.temporal_axis.set_ylim(0, 4)
        self.temporal_axis.set_axis_off()

    def plot_hull_row_spatial(self, row):
        """plot a single row of the hulls_df in the spatial axis"""
        paw_id = int(self.combo_prints.paw_id[row.print_numb].values[0])
        hull = row.hull.values[0]
        artist = self.spatial_axis.plot(hull[:,0,0], hull[:,0,1], linewidth=4,
                                        c=self.colors[paw_id], picker=5,
                                        alpha=.8)
        artist = artist[0]
        self.artist_dict[artist] = row.print_numb.values[0]
        self.print_dict[row.print_numb.values[0]].append(artist)
        for cnt in row.contours.values[0]:
            artist = self.spatial_axis.plot(cnt[:,0,0], cnt[:,0,1], c='k',
                                   linewidth=1, zorder=1)
            self.print_dict[row.print_numb.values[0]].append(artist[0])

    def display_paws_spatial(self, invert_axes = True, minimal = True):
        if minimal:
            for idx, print_ in self.combo_prints.iterrows():
                row = self.hulls_df.loc[(self.hulls_df.print_numb == idx) &
                                        (self.hulls_df.frame ==
                                         print_.frame_max_a)]
                self.plot_hull_row_spatial(row)
        else:
            for idx, row in self.hulls_df[self.hulls_df.is_kept].iterrows():
                self.plot_hull_row_spatial(row)
        self.spatial_axis.set_ylim(self.combo_prints.Y.min()-30,
                                       self.combo_prints.Y.max()+30)
        if invert_axes:
            self.spatial_axis.set_xlim(self.combo_prints.X.max()+30,
                                       self.combo_prints.X.min()-30)
        else:
            self.spatial_axis.set_xlim(self.combo_prints.X.min()-30,
                                       self.combo_prints.X.max()+30)
        self.spatial_axis.set_axis_off()

    def on_pick(self, event):
        """when a print is selected, color it to indicate that and set up
        the select panel. If in a combo state, prepare to combine that
        and the other print.
        """
        print_numb = self.artist_dict[event.artist]
        if ~self.in_combo_state:
            if event.mouseevent.button == 1: #if left click
                if self.selected_print != print_numb:
                    if self.selected_print is not None:
                        self.recolor(self.selected_print)
                    self.color_selected(print_numb)
                    self.selected_print = print_numb
                    self.select_panel.set_selected(
                            self.selected_print,
                            self.combo_prints.is_right[self.selected_print],
                            self.combo_prints.is_hind[self.selected_print])
                    self.slide.set_val(
                            self.combo_prints.first_frame[print_numb] - 2)
                plt.draw()
            elif event.mouseevent.button == 3: #if right click
                print('hey ho a pirates life for me')
        else:
            if event.mouseevent.button == 1: #if left click
                if self.selected_print != print_numb:
                    self.color_selected(print_numb)
                    self.second_selected = print_numb
                    self.select_panel.display_combo_text2(self.selected_print,
                                                          print_numb)
                plt.draw()

    def on_key_press(self, event):
        """handles each of the different key events.
        l,r,h, and f change the print classification of selected print
        d deletes the print, and has a helper method to do it.
        c and enter
        """
        if self.selected_print is not None:
            #if its a keypress to set one of the paw id props
            if event.key in ['l','r','h','f']:
                self.change_print_classification(event.key)
            elif event.key == 'd':
                self.delete_print(self.selected_print)
            elif event.key == 'c':
                self.in_combo_state = ~self.in_combo_state
                if self.in_combo_state:
                    self.select_panel.display_combo_text(self.selected_print)
                else:
                    if self.second_selected is not None:
                        self.recolor(self.second_selected)
                        self.second_selected = None
                    self.select_panel.set_selected(self.selected_print,
                                    self.combo_prints.is_right[self.selected_print],
                                    self.combo_prints.is_hind[self.selected_print])
            elif event.key == 'enter':
                if self.in_combo_state and self.second_selected is not None:
                    #the prints have to have the same front and side class
                    if (self.combo_prints.is_right[self.second_selected] == \
                        self.combo_prints.is_right[self.selected_print] and
                        self.combo_prints.is_hind[self.second_selected] == \
                        self.combo_prints.is_hind[self.selected_print]):
                            #TODO: a temporary hack
                            self.combo_prints['print_numb'] = self.combo_prints.index.values
                            combine_prints(self.combo_prints, self.selected_print,
                                           self.second_selected,
                                           hulls_df=self.hulls_df)
                            self.handle_combine_graphics(self.selected_print,
                                                         self.second_selected)
                            self.in_combo_state = False
                            self.second_selected = None
                            self.selected_print = None
                    else:
                        #TODO: display this onscreen somehow
                        print("PAWS MUST MATCH")
                        self.in_combo_state = False
                        self.recolor(self.second_selected)
                        self.second_selected = None
                        self.select_panel.set_selected(
                            self.selected_print,
                            self.combo_prints.is_right[self.selected_print],
                            self.combo_prints.is_hind[self.selected_print])
            #TODO: TEMPORARY
            elif event.key == 'm':
                self.initiate_split_window()


    def initiate_split_window(self):
        if self.selected_print is not None:
            SplitPrintWindow(self, self.combo_prints, self.hulls_df,
                              self.selected_print, self.vid_panel)

    def change_print_classification(self, label):
        """when radio buttons are clicked, or the correct key is pressed,
        l,r,h, and f change the print classification of selected print,
        resets selected print to None, and then adjusts the plots
        """
        if label == 'Left' or 'l':
            self.combo_prints.loc[self.selected_print, 'is_right'] = False
        if label == 'Right' or 'r':
            self.combo_prints.loc[self.selected_print, 'is_right'] = True
        if label == 'Hind' or 'h':
            self.combo_prints.loc[self.selected_print, 'is_hind'] = True
        if label == 'Front' or 'f':
            self.combo_prints.loc[self.selected_print, 'is_hind'] = False
        self.assign_paw_ids()
        self.recolor(self.selected_print)
        self.adjust_temporal(self.selected_print)
        self.select_panel.clear_axes()
        self.selected_print = None


    def delete_print(self, print_numb):
        """handles the nuts and bolts of removing a print graphically and
        in the data structures
        """
        #remove all artists from fig
        for artist in self.print_dict[print_numb]:
            self.artist_dict.pop(artist, None)
            artist.remove()
        self.print_dict.pop(print_numb, None)
        self.combo_prints.drop(print_numb)
        self.hulls_df.loc[self.hulls_df.print_numb == print_numb, 'is_kept'] = False
        self.select_panel.clear_axes()
        self.selected_print = None
        self.vid_panel.delete_print(print_numb)
        plt.draw()

    def handle_combine_graphics(self, print_numb1, print_numb2):
        """handles fixing up graphics after two prints are combined"""
        keep = max(print_numb1, print_numb2)
        del_ = min(print_numb1, print_numb2)
        self.print_dict[keep] = self.print_dict[keep]+self.print_dict[del_]
        for artist in self.print_dict[del_]:
            #a roundabout way of checking if its a rectangle
            if len(artist.findobj(patches.Rectangle)) > 0:
                self.artist_dict.pop(artist, None)
                self.print_dict[keep].remove(artist)
                artist.remove()
            else:
                self.artist_dict[artist] = keep
        self.vid_panel.handle_combine_graphics(print_numb1, print_numb2)
        self.print_dict.pop(del_, None)
        self.adjust_temporal(keep)
        self.recolor(keep)

    def recolor(self, print_numb):
        """set print artists to correct color based on print number"""
        pid = self.combo_prints.paw_id[print_numb]
        color = self.colors[int(pid)]
        for artist in self.print_dict[print_numb]:
            try:
                artist.set_edgecolor('k')
                artist.set_facecolor(color)
            except AttributeError:
                if artist.get_color() != 'k': #ignore the drawn contours
                    artist.set_color(color)
        self.vid_panel.recolor(print_numb)
        plt.draw()

    def color_selected(self, print_numb):
        """make print artists red, for when the print is selected"""
        for artist in self.print_dict[print_numb]:
            try:
                artist.set_edgecolor('r')
            except AttributeError:
                if artist.get_color() != 'k': #ignore the drawn contours
                    artist.set_color('r')

    def adjust_temporal(self, print_numb):
        """change the location of the frame range rectangle to reflect the
        properties of the print classification"""
        #TODO: make less janky
        rect = self.print_dict[print_numb][0]
        paw_id = self.combo_prints.paw_id[print_numb]
        rect.set_y(paw_id)
        rect.set_x(self.combo_prints.first_frame[print_numb])
        rect.set_width(self.combo_prints.last_frame[print_numb]-
                self.combo_prints.first_frame[print_numb])
        plt.draw()

    def change_frame(self, prev, new):
        self.vid_panel.change_frame(prev,new)

    #TODO: make this also work for GaitAnalyzer2?
    def add_hull_to_df(self, contours, frame, to_keep, print_numb=None):
        """given a collection of contours, the frame they occured at,
        and whether or not to keep them, find the hull, extract the
        summary info, and then add them to the hulls_df
        """
        hull = cv2.convexHull(contours)
        M = cv2.moments(hull)
        #must have nonzero area to be added
        if M['m00'] > 0:
            row_dict = {'frame': frame,
                        'hull': [hull],
                        'contours': [[contours]],
                        'area': M['m00'],
                        'X': int(M['m10'] / M['m00']),
                        'Y': int(M['m01'] / M['m00']),
                        'is_kept': to_keep}
            if print_numb is not None:
                row_dict['print_numb'] = print_numb
            new_df = pd.DataFrame(row_dict)
            #this is not an in place operation, so the change must be given to vid panel
            self.hulls_df = self.hulls_df.append(new_df, ignore_index=True)
            self.vid_panel.set_hulls_df(self.hulls_df)

    def add_print_to_combo_prints(self, print_numb, is_right, is_hind):
        """based on the info from hulls df, add the given print with given
        classification to the combo_prints df"""
        these_hulls = self.hulls_df.loc[self.hulls_df.print_numb == print_numb]
        imax = these_hulls.area.idxmax()
        #each value must be in a list to make pandas process correctly
        row_dict = {
            'print_numb': [print_numb], 'max_area': [these_hulls.area.max()],
            'X': [these_hulls.X[imax]], 'Y': [these_hulls.Y[imax]],
            'frame_max_a': [these_hulls.frame[imax]],
            'first_frame': [these_hulls.frame.min()],
            'last_frame': [these_hulls.frame.max()], 'is_right': [is_right],
            'is_hind': [is_hind], 'paw_id': [-1]}
        #convert all but bools to int
        for k, v in row_dict.iteritems():
            if k not in ['is_right', 'is_hind']:
                row_dict[k] = [int(num) for num in v]
        new_df = pd.DataFrame.from_dict(row_dict)
        new_df.set_index('print_numb', inplace=True)
        #this is not an in place operation, so the change must be given to vid panel
        self.combo_prints = self.combo_prints.append(new_df, verify_integrity=True)
        self.vid_panel.set_combo_prints(self.combo_prints)
        self.assign_paw_ids()

    def split_print(self, new_hull_points, old_hull_points, frame, orig_print):
        """given the new and old hull points from the SplitPrintWindow,
        update hulls df, combo prints and the displays to reflect the new split
        """
        #first, replace all of the old, wrong information in hulls_df for orig print
        for idx, points in enumerate(old_hull_points):
            points = points.reshape(points.shape[0],1,2)
            del_idx = self.hulls_df.index[(self.hulls_df.frame == frame[idx][0]) &
                                          (self.hulls_df.print_numb == orig_print)]
            print(del_idx)
            self.hulls_df.drop(del_idx, inplace=True)
            self.add_hull_to_df(points, frame[idx], True, print_numb = orig_print)

        #then add the new information for the second paw
        new_print_numb = self.combo_prints.sort_index().index.\
                            values[len(self.combo_prints) - 1] + 1
        for idx, points in enumerate(new_hull_points):
            points = points.reshape(points.shape[0],1,2)
            self.add_hull_to_df(points, frame[idx], True, print_numb = new_print_numb)

        #then, using the classification of the old print, add them to combo_prints
        is_right = self.combo_prints.is_right[orig_print]
        is_hind = self.combo_prints.is_hind[orig_print]
        self.combo_prints.drop(orig_print, inplace=True)
        self.add_print_to_combo_prints(orig_print, is_right, is_hind)
        self.add_print_to_combo_prints(new_print_numb, is_right, is_hind)

        #then wipe and recreate graphics.
        self.wipe_graphics()
        self.assign_paw_ids()
        self.display_paws_temporal()
        self.display_paws_spatial()
        self.vid_panel.wipe_and_redraw_graphics()
        plt.draw()

    def wipe_graphics(self):
        """resets graphics and the variables associated with ui control
        to initial state
        """
        self.spatial_axis.clear()
        self.temporal_axis.clear()
        self.selected_print = None
        self.in_combo_state = False
        self.second_selected = None
        self.artist_dict = {}
        self.print_dict = {}
        for print_numb in self.combo_prints.index.values:
            self.print_dict[print_numb] = []



class VideoPanel():
    """handles the video display. Contains the video object, and then
    has dicts that allow prints to be updated based on changes to combo_prints,
    and also has a frame dict that controls setting artists visible and
    invisible based on the current frame display"""
    def __init__(self, axis, combo_prints, hulls_df, colors, file):
        self.spatial_axis = axis
        self.spatial_axis.set_axis_off()
        self.combo_prints = combo_prints
        self.hulls_df = hulls_df
        self.video_path = file
        with open(os.path.join(os.path.split(file)[0], 'SettingsData.txt'), 'rb') as f:
            settings = json.load(f)
        self.roi = settings['roi']
        self.video = PyAVReaderIndexed(self.video_path)
        self.im_artist = self.spatial_axis.imshow(self.video[0][self.roi[1]:self.roi[3], self.roi[0]:self.roi[2]],
                                          interpolation='nearest', zorder=1)
        self.colors = colors
        self.print_dict = {}
        for print_numb in self.combo_prints.index.values:
            self.print_dict[print_numb] = []
        self.frame_dict = {}
        for frame in range(int(self.combo_prints.first_frame.min()),
                           int(self.combo_prints.last_frame.max())+1):
            self.frame_dict[frame] = []

        self.display_paws_spatial()

    def set_combo_prints(self, combo_prints):
        self.combo_prints = combo_prints

    def set_hulls_df(self, hulls_df):
        self.hulls_df = hulls_df

    #TODO: do inheritance
    def wipe_and_redraw_graphics(self):
        #TODO: temp
        self.combo_prints.to_pickle('testing split in vid panel combo.p')
        self.hulls_df.to_pickle('testing split in vid panel hull.p')
        self.spatial_axis.clear()
        self.print_dict = {}
        for print_numb in self.combo_prints.index.values:
            self.print_dict[print_numb] = []
        self.frame_dict = {}
        for frame in range(int(self.combo_prints.first_frame.min()),
                           int(self.combo_prints.last_frame.max())+1):
            self.frame_dict[frame] = []
        self.im_artist = self.spatial_axis.imshow(self.video[0][self.roi[1]:self.roi[3], self.roi[0]:self.roi[2]],
                                          interpolation='nearest', zorder=1)
        self.display_paws_spatial()

    #TODO: DO INHERITANCE
    def display_paws_spatial(self, invert_axes = True, do_edges = False):
        for idx, row_ in self.hulls_df[self.hulls_df.is_kept].iterrows():
            #get paw id from combo prints
            paw_id = self.combo_prints.paw_id[row_.print_numb]
            #TODO: make these closed
            artist = self.spatial_axis.plot(row_.hull[:,0,0], row_.hull[:,0,1],
                                            c = self.colors[int(paw_id)],
                                            visible=False)
            artist = artist[0]
            self.print_dict[row_.print_numb].append(artist)
            self.frame_dict[row_.frame].append(artist)

            if do_edges:
                for cnt in row_.contours:
                    artist = self.spatial_axis.plot(
                                cnt[:,0,0], cnt[:,0,1], c='k', linewidth=.5,
                                zorder=2, visible=False)
                    self.print_dict[row_.print_numb].append(artist[0])
                    self.frame_dict[row_.frame].append(artist[0])
        self.spatial_axis.set_ylim(self.combo_prints.Y.min()-30,
                                   self.combo_prints.Y.max()+30)
        if invert_axes:
            self.spatial_axis.set_xlim(self.combo_prints.X.max()+30,
                                       self.combo_prints.X.min()-30)
        else:
            self.spatial_axis.set_xlim(self.combo_prints.X.min()-30,
                                       self.combo_prints.X.max()+30)
        self.spatial_axis.set_axis_off()

    def recolor(self, print_numb):
        pid = self.combo_prints.paw_id[print_numb]
        color = self.colors[int(pid)]
        for artist in self.print_dict[print_numb]:
            try:
                artist.set_edgecolor('k')
                artist.set_facecolor(color)
            except AttributeError:
                if artist.get_color() != 'k':
                    artist.set_color(color)
        plt.draw()

    def handle_combine_graphics(self, print_numb1, print_numb2):
        keep = max(print_numb1, print_numb2)
        del_ = min(print_numb1, print_numb2)
        self.print_dict[keep] = self.print_dict[keep]+self.print_dict[del_]

    def delete_print(self, print_numb):
        #remove all artists from fig
        for artist in self.print_dict[print_numb]:
            #TODO: do this better
            for frame in range(self.combo_prints.first_frame[print_numb],
                               self.combo_prints.last_frame[print_numb]+1):
                self.frame_dict[frame].remove(artist)
            artist.remove()
        self.print_dict.pop(print_numb, None)
        plt.draw()

    def change_frame(self, prev_frame, new_frame):
        #print('starting frame change')
        #s=time.time()
        for artist in self.frame_dict[prev_frame]:
            artist.set_visible(False)
        #print(time.time()-s)
        for artist in self.frame_dict[new_frame]:
            artist.set_visible(True)
        #print(time.time()-s)
        #The frames in the dfs start at frame 1, but video is zero indexed
        self.im_artist.set_data(self.get_frame(new_frame))
        #print(time.time()-s)
        plt.draw()
        #print(time.time()-s)

    def get_frame(self, frame):
        #The frames in the dfs start at frame 1, but video is zero indexed
        return self.video[frame-1][self.roi[1]:self.roi[3], self.roi[0]:self.roi[2]]

class SplitPrintWindow():
    def __init__(self, print_manager, combo_prints, hulls_df, print_numb,
                 vid_panel, invert_axes = True):
        print('init split print window')

        self.root = tk.Tk()
        self.root.wm_title("Embedding in Tk")

        self.fig = Figure(figsize=(5, 4), dpi=100)
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)  # A tk.DrawingArea.
        self.canvas.draw()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        self.toolbar = NavigationToolbar2TkAgg(self.canvas, self.root)
        self.toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)
        self.print_manager = print_manager
        self.combo_prints = combo_prints
        self.print_numb = print_numb
        self.first_frame = self.combo_prints.first_frame[print_numb]
        n_frames = (self.combo_prints.last_frame[print_numb] -
                    self.first_frame) + 1
        grid_size = int(np.ceil(np.sqrt(n_frames)))
        self.axes=[]
        self.fig.set_size_inches(16, 9)
        button_axes = self.fig.add_axes([.01, .01, .05, .05])
        self.button = Button(button_axes, 'Split')
        self.button.on_clicked(self.create_new_hulls)

        these_hulls = hulls_df[hulls_df.print_numb==print_numb]
        self.collections = {}
        self.xyes = {}
        for i in range(0, n_frames):
            ax=self.fig.add_subplot(grid_size,grid_size,i+1)
            self.axes.append(ax)
            ax.set_axis_off()
            frame = vid_panel.get_frame(self.first_frame+i)
            X = self.combo_prints.X[print_numb]
            Y = self.combo_prints.Y[print_numb]
            ax.imshow(frame)
            xes = []
            yes = []
            for c in (these_hulls.contours[these_hulls.frame ==
                                           self.first_frame+i].values[0]):
                #add all to a single list to make one collection
                xes = xes + list(c[:,0,0])
                yes = yes + list(c[:,0,1])
            self.collections[ax] = ax.scatter(xes, yes)
            self.xyes[ax] = self.collections[ax].get_offsets()
            #set it to have list of facecolors so that selection works
            facecolors = self.collections[ax].get_facecolors()
            npts = len(self.xyes[ax])
            facecolors = np.tile(facecolors, npts).reshape(npts, -1)
            self.collections[ax].set_facecolor(facecolors)

            if invert_axes:
                ax.set_xlim(X+50,X-50)
            else:
                ax.set_xlim(X-50,X+50)
            ax.set_ylim(Y-50,Y+50)
            ax.set_title('Frame ' + str(self.first_frame+i))
        self.axes = np.asarray(self.axes)
        self.cid = self.canvas.mpl_connect('button_press_event', self.onpress)
        self.canvas.draw()
        tk.mainloop()

    def create_new_hulls(self, event):
        new_hull_points = []
        old_hull_points = []
        frame = []
        for ax, collection in self.collections.iteritems():
            #make np array of bools with whether color matches the selection color for each point
            inds = np.asarray([True if np.array_equal(i, [.4,.4,.9, 1.0])
                    else False for i in collection.get_facecolors()])
            #use np bool indexing to get x,y values for selected and unselected
            new_hull_points.append(self.xyes[ax][inds])
            old_hull_points.append(self.xyes[ax][~inds])
            frame.append(self.first_frame + np.where(self.axes==ax)[0])
        self.print_manager.split_print(new_hull_points, old_hull_points,
                                       frame, self.print_numb)
        self.root.destroy()

    def callback(self, verts):
        facecolors = self.collections[self.current_axes].get_facecolors()
        p = path.Path(verts)
        ind = p.contains_points(self.xyes[self.current_axes])
        for i in range(len(self.xyes[self.current_axes])):
            if ind[i]:
                facecolors[i] = [.4,.4,.9, 1.0]
            else:
                facecolors[i] = [.4,.4,.2, .5]
        self.collections[self.current_axes].set_facecolor(facecolors)
        self.fig.canvas.draw_idle()
        self.fig.canvas.widgetlock.release(self.lasso)
        del self.lasso

    #TODO: troubleshoot widget locks
    def onpress(self, event):
        print('hey a press')
        if self.fig.canvas.widgetlock.locked(): return
        print('passed widget lock')
        if event.inaxes is None: return
        print('passed axes')
        self.current_axes = event.inaxes
        self.lasso = Lasso(event.inaxes, (event.xdata, event.ydata), self.callback)
        # acquire a lock on the widget drawing
        self.fig.canvas.widgetlock(self.lasso)

file = tkFileDialog.askopenfilename(message = "choose the video file")
FigureContainer(file)