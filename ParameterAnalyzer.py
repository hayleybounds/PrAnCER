# -*- coding: utf-8 -*-
"""
Created on Thu Jun 16 12:41:53 2016

@author: Hayley Bounds

04/06:
Changing speed calcs to be done from ff to ff

04/09:
Adding some new variables

05/16/17:
Adding GUI.
"""
import sys
if (sys.version_info > (3, 0)):
    import tkinter as tk
    import tkinter.filedialog as tkFileDialog
    import tkinter.messagebox as tkMessageBox
else:
    import Tkinter as tk
    import tkFileDialog
    import tkMessageBox
import os.path
import math
import glob
import numpy as np
import pandas as pd

#global variable that sets how many prints will be analyzed
hind_prints_to_analyze = 0


"""allows the user to set parameters
"""
class StartupMenu():
    def __init__(self):
        self.root = tk.Tk()
        self.root.update()
        self.folder = ""

        tk.Label(self.root,
                 text="Number of Hind Prints to Analyze:").grid(row=0, sticky=tk.W)
        self.numb_prints = tk.IntVar()
        tk.Entry(self.root, width=15,
                 textvariable=self.numb_prints).grid(row=0, column=1)
        self.numb_prints.set(4)


        fold_but = tk.Button(self.root, text="Choose Folder:",
                             command = self.get_folder)
        self.fold_lab = tk.Label(self.root, text=self.folder)
        quit_but = tk.Button(self.root, text="Continue", command = self.close)

        fold_but.grid(row=1)
        self.fold_lab.grid(row=3, column=1)
        quit_but.grid(row=1, column=0, columnspan=2)

        self.root.mainloop()

    def close(self):
        global hind_prints_to_analyze
        #TODO: this is bad form
        if self.folder == "":
            self.root.destroy()
            self.root.quit()
            raise Exception("No Folder Selected")

        try:
            self.numb_prints.get()
        except ValueError:
            raise ValueError("Input to Number of Prints must be integers")

         
        if self.numb_prints.get() < 4:
            raise ValueError("Number Prints to Analyze must be >=4")

        hind_prints_to_analyze = self.numb_prints.get()
        do_all(self.folder)
        self.root.destroy()
        self.root.quit()

    def get_folder(self):
        self.folder = tkFileDialog.askdirectory(title='Choose a Folder')
        self.fold_lab.configure(text = self.folder)


def make_file_path(inputfolder, filetype='.csv'):
    #splits the filepath into directory + the files name
    splitpath = os.path.split(inputfolder)
    newpath = inputfolder + '/' + splitpath[1] + ' gait parameters' + filetype

    #if this file already exists append numbers to it until it doesn't exist anymore
    counter = 1
    while os.path.exists(newpath):
        counter += 1
        temp = splitpath[1].split('.')[0] + ' gait parameters' + ' (' + str(counter) + ')' + filetype
        newpath = inputfolder + '/' + temp

    return newpath


"""Gets the avg base of support for a trial.
Only takes in filename so it can throw errors
TODO: make it actually throw an error, remove partial prints
"""
def get_avg_bos(prints_df, name):
    numbPrints = hind_prints_to_analyze
    #first, delete all non back paws
    df = prints_df[prints_df.is_hind]
    df = df.reset_index(drop=True)
    #first make sure everything is in order
    [print('WARNING: for ' + name + ' paws out of order') for i in range(1, numbPrints) if df.is_right[i]==df.is_right[i-1]]
    #then return bos
    return np.mean([abs(df.Y[i] - df.Y[i-1]) for i in range(1, numbPrints)])

"""gets the avg stride length for a trial.
Uses absolute distance, not just x distance.
"""
def get_avg_stride(prints_df, name):
    numbPrints = hind_prints_to_analyze
    
    #first, delete all non back paws
    df = prints_df[prints_df.is_hind]
    df = df.reset_index(drop=True)
    #first make sure everything is in order
    [print('WARNING: for ' + name + ' paws out of order') for i in range(2, numbPrints) if df.is_right[i]!=df.is_right[i-2]]
    #then return stride
    xy = df.loc[:,['X','Y']].values
    return np.mean([np.linalg.norm(xy[i,:] - xy[i-2,:]) for i in range(2, numbPrints)])


"""gets the avg step length for a trial.
"""
def get_avg_step(prints_df, name):
    numbPrints = hind_prints_to_analyze
    #first, delete all non back paws
    df = prints_df[prints_df.is_hind]
    df = df.reset_index(drop=True)
    #first make sure everything is in order
    [print('WARNING: for ' + name + ' paws out of order') for i in range(1, numbPrints) if df.is_right[i]==df.is_right[i-1]]
    #then return stride
    return np.mean([abs(df.X[i] - df.X[i-1]) for i in range(1, numbPrints)])


def get_avg_frame(prints_df, name):
    numbPrints = hind_prints_to_analyze
    #first, delete all non back paws
    df = prints_df[prints_df.is_hind]
    df = df.reset_index(drop=True)
    #make a duration column
    df.loc[:,'duration'] = df.last_frame-df.first_frame
    return df.duration[0:numbPrints].mean()


"""Finds the speed the animal travelled for a single stride.
"""
def get_speed_by_stride(prints_df, name, which_stride):
    numbPrints = hind_prints_to_analyze
     #first, delete all non back paws
    backs_df = prints_df[prints_df.is_hind]
    df = backs_df.reset_index(drop=True);
    #bc for now I'm getting several stride speeds
    if len(backs_df.is_hind) < (which_stride + 2):
        return
    
    #first make sure everything is in order
    [print('WARNING: for ' + name + ' paws out of order') for i in range(1, numbPrints) if df.is_right[i]==df.is_right[i-1]]
    
    #get the speed for only the selected stride
    i = which_stride + 1
    xy = df.loc[:,['X','Y']].values
    length = np.linalg.norm(xy[i,:]-xy[i-2,:])
    frames = df.first_frame[i] - df.first_frame[i-2]

    return (float(length)/frames)

"""
Gets the stance to swing ratio for the right and left hind paws separately
"""
def get_stance_swing(prints_df, RorL):
    numbPrints = hind_prints_to_analyze
    #first, delete all non back paws
    backs_df = prints_df[prints_df.is_hind]
    if RorL=='l':        
        rights_df = backs_df[~backs_df.is_right]
    else:
        rights_df = backs_df[backs_df.is_right]
    df = rights_df.reset_index(drop=True)
    #make a duration column
    df.loc[:,'duration'] = df.last_frame-df.first_frame
    print('size of rights df', rights_df, 'setting is', RorL)
    return np.mean([df.duration[i-1]/(df.first_frame[i]-df.last_frame[i-1]) for i in range(1, int(numbPrints/2))])
                   
"""
Gets the duty factor for right and left paws separately
"""
def get_duty_factor(prints_df, RorL):
    numbPrints = hind_prints_to_analyze
    #first, delete all non back paws
    backs_df = prints_df[prints_df.is_hind]
    if RorL=='l':        
        rights_df = backs_df[~backs_df.is_right]
    else:
        rights_df = backs_df[backs_df.is_right]
    df = rights_df.reset_index(drop=True)
    #make a duration column
    df.loc[:,'duration'] = df.last_frame-df.first_frame
    
    return np.mean([df.duration[i-1]/(df.first_frame[i]-df.last_frame[i-1]+df.duration[i-1]) for i in range(1, int(numbPrints/2))])


"""gets average of max contact area for all back paws
"""
def get_avg_area(prints_df):
    numbPrints = hind_prints_to_analyze
    backs_df = prints_df[prints_df.is_hind]
    return np.mean(backs_df.loc[:,'max_area'].iloc[range(numbPrints)])

                   
"""Finds the relative positions of pairs of ipsilateral front and hind paws.

Returns all the distance values for all pairs in the absolute (x+y) dimensions

Now assuming correct positions and correct removal of bad prints
"""
def get_h_f_positions(prints_df, name):
    numbPrints = hind_prints_to_analyze
    abs_positions=[]
    final_matches=[]
    fronts_df = prints_df[~prints_df.is_hind]
    backs_df = prints_df[prints_df.is_hind]
    backs_df = backs_df.reset_index(drop=True)
    #for numb hind prints to analyze, find the front print of the same side that's closest to it
    #and get the difference in position of it
    for i in range(0, numbPrints):
        this_bp = backs_df.loc[i,:]
        matching_fronts = fronts_df.loc[(fronts_df.is_right==this_bp.is_right),:]
        matches = []
        xy = this_bp[['X','Y']].values        
        for indx, paw in matching_fronts.iterrows():
            dist = np.linalg.norm(xy-paw[['X','Y']].values)
            if dist < 200 and paw.first_frame < this_bp.first_frame:
                #then need to make sure that this bp is the closest thing to the fp that is in acceptable time range
                min_bprint = 0
                min_dist = 60000
                candidate_backs = backs_df[backs_df.first_frame > paw.first_frame]
                for bindx, cb in candidate_backs.iterrows():
                    dist = np.linalg.norm(cb[['X','Y']].values-
                                          paw[['X','Y']].values)
                    if dist<min_dist:
                        min_bprint = cb.print_numb
                        min_dist = dist

                if min_bprint == this_bp.print_numb:
                    matches.append(paw.print_numb)
        #if there's more than one match
        if len(matches)>1:
            #store what the min one has been so far
            min_print = 0
            min_dist = 60000
            for k in matches:
                xval = xy[0]
                yval = xy[1]
                dist_to = math.sqrt((xval -
                        fronts_df[fronts_df.print_numb==k].X.iloc[0])**2 +
                        (yval -
                        fronts_df[fronts_df.print_numb==k].Y.iloc[0])**2)
                if dist_to<min_dist:
                    min_dist = dist_to
                    min_print = k
            matches = [min_print]
        if len(matches) == 1:
            p = matches[0]
            abs_positions.append(math.sqrt((this_bp.X -
                        fronts_df[fronts_df.print_numb==p].X.iloc[0])**2 +
                        (this_bp.Y -
                        fronts_df[fronts_df.print_numb==p].Y.iloc[0])**2))

            final_matches.append(p)
            #elif len(matches)==0:
               # print" "
                #print "no matches for" + name + " " + str(prints_df.print_numb.iloc[i])

    #check for paws matched multiple times
    if len(set([x for x in final_matches if final_matches.count(x) > 1])) > 0:
        print ("for " + name)
        print (set([x for x in final_matches if final_matches.count(x) > 1]))
                   
    return abs_positions


"""The following three methods use the output of get_h_f_positions to find the
mean, coefficient of variation, and standard deviation for a run, respectively
"""
def get_h_f_mean(prints_df, name):
    poses = get_h_f_positions(prints_df, name)
    return np.mean(poses)

def get_h_f_cv(prints_df, name):
    poses = get_h_f_positions(prints_df, name)
    return np.std(poses)/np.mean(poses)

def get_h_f_sd(prints_df, name):
    poses = get_h_f_positions(prints_df, name)
    return np.std(poses)


def make_day_file(subfolder):
    #find all .csv  in that folder
    file_paths = glob.glob(subfolder + '/*' + '.csv')

    #get rid of csvs that don't contain 'analyzed'
    file_paths = [path for path in file_paths if 'combo df' in path]

    #then get rid of ones that don't say corrected
    #file_paths = [path for path in file_paths if 'corrected' in path]

    #read everything to panda dataframes
    dfs = []
    for path in file_paths:
        df = pd.read_csv(path)
        df.is_hind = df.is_hind.astype('bool')
        df.is_right = df.is_right.astype('bool')
        dfs.append(df)

    #a list of just the file name w/o path info
    file_names = [os.path.split(path)[1].split('.')[0] for path in file_paths]

    avg_boses = [get_avg_bos(dfs[i], file_names[i]) for i in range(len(dfs))]

    avg_strides = [get_avg_stride(dfs[i], file_names[i]) for i in range(len(dfs))]

    avg_steps = [get_avg_step(dfs[i], file_names[i]) for i in range(len(dfs))]

    avg_frames = [get_avg_frame(dfs[i], file_names[i]) for i in range(len(dfs))]

    avg_as = [get_avg_area(dfs[i]) for i in range(len(dfs))]

    stride_speed_one = [get_speed_by_stride(dfs[i], file_names[i], 1) for i in range(len(dfs))]
    stride_speed_two = [get_speed_by_stride(dfs[i], file_names[i], 2) for i in range(len(dfs))]
    stride_speed_three = [get_speed_by_stride(dfs[i], file_names[i], 3) for i in range(len(dfs))]

    r_stance_swing = [get_stance_swing(dfs[i], 'r') for i in range(len(dfs))]
    l_stance_swing = [get_stance_swing(dfs[i], 'l') for i in range(len(dfs))]

    r_duty = [get_duty_factor(dfs[i], 'r') for i in range(len(dfs))]
    l_duty = [get_duty_factor(dfs[i], 'l') for i in range(len(dfs))]

    h_f_abs_mean = [get_h_f_mean(dfs[i], file_names[i]) for i in range(len(dfs))]
    h_f_abs_cv = [get_h_f_cv(dfs[i], file_names[i]) for i in range(len(dfs))]
    h_f_abs_sd = [get_h_f_sd(dfs[i], file_names[i]) for i in range(len(dfs))]


    newpath = make_file_path(subfolder)

    #put everything together to a panda df
    zz = pd.DataFrame( {'filename':file_names, 'Base of Support':avg_boses, 'Stride Length':avg_strides,
        'Step Length':avg_steps, 'Stance Duration': avg_frames, 
        'Average of Maximum Areas': avg_as,
        'Stride Speed First Stride': stride_speed_one, 'Stride Speed Second Stride': stride_speed_two,
        'Stride Speed Third Stride': stride_speed_three,
        'Right Limb Stance to Swing Ratio': r_stance_swing,
        'Left Limb Stance to Swing Ratio': l_stance_swing,
        'Right Limb Duty Factor': r_duty, 'Left Limb Duty Factor': l_duty,
        'Mean Absolute Interlimb Distance': h_f_abs_mean,
        'CV of Absolute Interlimb Distance':h_f_abs_cv,
        'SD of Absolute Interlimb Distance': h_f_abs_sd})
    output = zz[['filename', 
                 'Base of Support', 'Stride Length', 'Step Length',
                 'Stance Duration', 'Average of Maximum Areas',
                 'Stride Speed First Stride', 'Stride Speed Second Stride',
                 'Stride Speed Third Stride', 'Right Limb Stance to Swing Ratio',
                 'Left Limb Stance to Swing Ratio', 'Right Limb Duty Factor',
                 'Left Limb Duty Factor', 'Mean Absolute Interlimb Distance',
                 'CV of Absolute Interlimb Distance',
                 'SD of Absolute Interlimb Distance']]

    output.to_csv(newpath, columns=['filename',
                 'Base of Support', 'Stride Length', 'Step Length',
                 'Stance Duration', 'Average of Maximum Areas',
                 'Stride Speed First Stride', 'Stride Speed Second Stride',
                 'Stride Speed Third Stride', 'Right Limb Stance to Swing Ratio',
                 'Left Limb Stance to Swing Ratio', 'Right Limb Duty Factor',
                 'Left Limb Duty Factor', 'Mean Absolute Interlimb Distance',
                 'CV of Absolute Interlimb Distance',
                 'SD of Absolute Interlimb Distance'])

    return output

def do_all(folder):
    make_day_file(folder)


if __name__ == '__main__':
    StartupMenu()
    #raw_input("Press Enter To Exit: ")
