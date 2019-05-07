# -*- coding: utf-8 -*-
"""
Created on Thu Jun 16 12:41:53 2016

@author: Hayley Bounds

Note: because of pandas being weird, I have to use .loc to get the entire
column i want, and then use .iloc to get the entry in that column. Thats because
entries also have unique numbered ids which would be what loc uses, but I want
its pos in the list which is what iloc uses. I could probably find a better
way but I haven't yet.

04/06:
Changing speed calcs to be done from ff to ff

04/09:
Adding some new variables

05/16/17:
Adding GUI.

TODO: Change it to analyze a single file at a time.
TODO: finish changing globals and making that work everywhere.
TODO: add description of how video files should be named and how folder should
be named.
TODO: can change all bacs_ff.loc[:,""].iloc[] to backs_df.ColName.iloc[]
TODO: Add back the percent supported parameters.
"""

import tkinter as tk
import tkinter.filedialog as tkFileDialog
import os.path
import math
import glob
import numpy as np
import pandas as pd

"""This global variable is a list of the rat numbers which are experimental.
Change it when analyzing different groups. It is assumed that any numbers not
listed are experimentals.
"""

experimental_numbers = []
hind_prints_to_analyze = 0


"""allows the user to set parameters
"""
class StartupMenu():
    def __init__(self):
        self.root = tk.Tk()
        self.root.update()
        self.folder = ""
        self.exp_numbs = []

        tk.Label(self.root,
                 text="Number of Hind Prints to Analyze:").grid(row=0, sticky=tk.W)
        self.numb_prints = tk.IntVar()
        tk.Entry(self.root, width=15,
                 textvariable=self.numb_prints).grid(row=0, column=1)
        self.numb_prints.set(4)

        tk.Label(self.root,
                 text="Number of Experimental Animals:").grid(row=1, sticky=tk.W)
        self.numb_exps = tk.IntVar()
        tk.Entry(self.root, width=15,
                 textvariable=self.numb_exps).grid(row=1, column=1)

        exp_but = tk.Button(self.root, text="Choose Exp Numbers:",
                            command = self.set_exps)
        self.exp_lab = tk.Label(self.root, text=self.exp_numbs)

        exp_but.grid(row=2)
        self.exp_lab.grid(row=2, column=1)

        fold_but = tk.Button(self.root, text="Choose Cohort Folder:",
                             command = self.get_folder)
        self.fold_lab = tk.Label(self.root, text=self.folder)
        quit_but = tk.Button(self.root, text="Continue", command = self.close)

        fold_but.grid(row=3)
        self.fold_lab.grid(row=3, column=1)
        quit_but.grid(row=4, column=0, columnspan=2)

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
            self.numb_exps.get()
        except ValueError:
            raise ValueError("Input to Number of Prints and Experimental Animals must be integers")

         
        if self.numb_prints.get() < 4:
            raise ValueError("Number Prints to Analyze must be >=4")

        hind_prints_to_analyze = self.numb_prints.get()
        do_all(self.folder)
        self.root.destroy()
        self.root.quit()

    def get_folder(self):
        self.folder = tkFileDialog.askdirectory(title='Choose a Folder')
        self.fold_lab.configure(text = self.folder)

    def set_exps(self):
        try:
            self.numb_exps.get()
        except ValueError:
            raise ValueError("Input to Number of Experimental Animals must be integers")

        wind = tk.Toplevel(self.root)

        text_vars = []
        for i in range(0, self.numb_exps.get()):
            tk.Label(wind, text="Input One ID:").grid(row=i, sticky=tk.W)
            temp = tk.StringVar()
            tk.Entry(wind, width = 15, textvariable=temp).grid(row=i, column=1)
            text_vars.append(temp)

        tk.Button(wind, text="Set",
                  command=lambda:self.close_exps(text_vars)).grid(columnspan=2,
                                                    row=self.numb_exps.get())

    def close_exps(self, text_vars):
        global experimental_numbers
        experimental_numbers = []
        for var in text_vars:
            experimental_numbers.append(var.get())

        self.exp_lab.configure(text = str(experimental_numbers))


def make_file_path(inputfolder, filetype='.csv'):
    #splits the filepath into directory + the files name
    splitpath = os.path.split(inputfolder)
    newpath = inputfolder + "/" + splitpath[1] + " group analysis" + filetype

    #if this file already exists append numbers to it until it doesn't exist anymore
    counter = 1
    while os.path.exists(newpath):
        counter += 1
        temp = splitpath[1].split('.')[0] + ' group analysis' + ' (' + str(counter) + ')' + filetype
        newpath = inputfolder + '/' + temp

    return newpath


"""Gets the avg base of support for a trial.
Only takes in filename so it can throw errors
TODO: make it actually throw an error, remove partial prints
"""
def get_avg_bos(prints_df, name):
    numbPrints = hind_prints_to_analyze
    #first, delete all non back paws
    backs_df = prints_df[prints_df['ForB'] == 'b']

    #give a warning for partial prints
    if backs_df.loc[:,'centroidx'].iloc[0] > 1880:
        print('warning, may be partial print for ' + name)

    boses = []

    #iterate through and compare backwards for 2 - # to compare
    for i in range(1, numbPrints):
        #this should always compare right and left values
        #so double check that's happening
        if ((backs_df.loc[:, 'RorL'].iloc[i] == "r" and backs_df.loc[:, 'RorL'].iloc[i-1] != "l") or
            (backs_df.loc[:, 'RorL'].iloc[i] == "l" and backs_df.loc[:, 'RorL'].iloc[i-1] != "r")):
                print('WARNING: for ' + name + ' paws out of order')
                return

        boses.append(abs(backs_df.loc[:, 'centroidy'].iloc[i-1] -
                        backs_df.loc[:, 'centroidy'].iloc[i]))

    return np.mean(boses)


"""gets the avg stride length for a trial.
Uses absolute distance, not just x distance.
"""
def get_avg_stride(prints_df, name):
    numbPrints = hind_prints_to_analyze
    #first, delete all non back paws
    backs_df = prints_df[prints_df['ForB'] == 'b']

    stride_lengths = []

    #iterate through and compare backwards for 2 - # to compare
    for i in range(2, numbPrints):
        #this should always compare right and left values, but bos checks that
        if ((backs_df.loc[:, 'RorL'].iloc[i] == "r" and backs_df.loc[:, 'RorL'].iloc[i-1] != "l") or
            (backs_df.loc[:, 'RorL'].iloc[i] == "l" and backs_df.loc[:, 'RorL'].iloc[i-1] != "r")):
                #print 'for ' + name + ' paws out of order'
                return

        length = math.sqrt((backs_df.loc[:, 'centroidx'].iloc[i-2] -
                            backs_df.loc[:,'centroidx'].iloc[i])**2 +
                            (backs_df.loc[:, 'centroidy'].iloc[i-2] -
                            backs_df.loc[:,'centroidy'].iloc[i])**2)
        stride_lengths.append(length)

    return np.mean(stride_lengths)


"""gets the avg step length for a trial.
"""
def get_avg_step(prints_df, name):
    numbPrints = hind_prints_to_analyze
    #first, delete all non back paws
    backs_df = prints_df[prints_df['ForB'] == 'b']

    step_lengths = []

    #iterate through and compare backwards for 2 - # to compare
    for i in range(1, numbPrints):
        #this should always compare right and left values, but bos checks that
        if ((backs_df.loc[:,'RorL'].iloc[i] == "r" and backs_df.loc[:, 'RorL'].iloc[i-1] != "l") or
            (backs_df.loc[:, 'RorL'].iloc[i] == "l" and backs_df.loc[:, 'RorL'].iloc[i-1] != "r")):
                #print 'for ' + name + ' paws out of order'
                return

        step_lengths.append(abs(backs_df.loc[:, 'centroidx'].iloc[i-1] -
                        backs_df.loc[:,'centroidx'].iloc[i]))

    return np.mean(step_lengths)

def get_avg_frame(prints_df, name):
    numbPrints = hind_prints_to_analyze
    #first, delete all non back paws
    backs_df = prints_df[prints_df['ForB'] == 'b']

    frames = []
    #iterate through and get first - last frame for all first 4 back paws.
    for i in range(numbPrints):

        frames.append(abs(backs_df.loc[:, 'lastframe'].iloc[i] -
                        backs_df.loc[:,'firstframe'].iloc[i]))
    return np.mean(frames)

"""this will need to be developed a lot more, but doing a vague speed test
by taking the time the first paw was detected to the time the last paw leaves
the first 1000 pixel distance.
"""
def get_speed(prints_df, name):
    #the first row will have the first thing found
    min_frame = prints_df.loc[:, 'firstframe'].min()
    min_loc = prints_df.loc[:, 'firstframe'].idxmin()
    #then eliminate all paws further than 1000 pixels from start
    shortened_df = prints_df[prints_df['centroidx'] <= 1920 - prints_df.loc[:,'centroidx'].iloc[min_loc] + 1000]
    max_frame = shortened_df.loc[:,'lastframe'].max()

    return (max_frame-min_frame)

"""Finds the speed the animal travelled for a single stride.
"""
def get_speed_by_stride(prints_df, name, which_stride):
     #first, delete all non back paws
    backs_df = prints_df[prints_df['ForB'] == 'b']
    #bc for now I'm getting several stride speeds
    if len(backs_df.ForB) < (which_stride + 2):
        return

    #iterate through and get first - last frame for all first 4 back paws.
    i = which_stride + 1

    if ((backs_df.loc[:, 'RorL'].iloc[i] == "r" and backs_df.loc[:, 'RorL'].iloc[i-1] != "l") or
            (backs_df.loc[:, 'RorL'].iloc[i] == "l" and backs_df.loc[:, 'RorL'].iloc[i-1] != "r")):
        print('for ' + name + ' paws out of order')
        return

    length = math.sqrt((backs_df.loc[:, 'centroidx'].iloc[i-2] -
                            backs_df.loc[:,'centroidx'].iloc[i])**2 +
                            (backs_df.loc[:, 'centroidy'].iloc[i-2] -
                            backs_df.loc[:,'centroidy'].iloc[i])**2)

    frames = (backs_df.loc[:, 'firstframe'].iloc[i] -
                        backs_df.loc[:,'firstframe'].iloc[i-2])

    return (float(length)/frames)

"""
Gets the stance to swing ratio for the right and left hind paws separately
"""
def get_stance_swing(prints_df, name, RorL):
    numbPrints = hind_prints_to_analyze
    #first, delete all non back paws
    backs_df = prints_df[prints_df['ForB'] == 'b']
    rights_df = backs_df[backs_df['RorL'] == RorL]
    ss_ratios = []

    #iterate through and compare backwards for 2 - # to compare
    for i in range(1, numbPrints-2):

        swing = (rights_df.loc[:, 'firstframe'].iloc[i] -
                        rights_df.loc[:,'lastframe'].iloc[i-1])

        stance = (rights_df.loc[:, 'lastframe'].iloc[i-1] -
                        rights_df.loc[:,'firstframe'].iloc[i-1])


        ss_ratios.append((float(stance)/swing))

    return np.mean(ss_ratios)

"""
Gets the duty factor for right and left paws separately
"""
def get_duty_factor(prints_df, name, RorL):
    numbPrints = hind_prints_to_analyze
    #first, delete all non back paws
    backs_df = prints_df[prints_df['ForB'] == 'b']
    rights_df = backs_df[backs_df['RorL'] == RorL]
    duty_factors = []

    #iterate through and compare backwards for 2 - # to compare
    for i in range(1, numbPrints-2):

        swing = (rights_df.loc[:, 'firstframe'].iloc[i] -
                        rights_df.loc[:,'lastframe'].iloc[i-1])

        stance = (rights_df.loc[:, 'lastframe'].iloc[i-1] -
                        rights_df.loc[:,'firstframe'].iloc[i-1])


        duty_factors.append((float(stance)/(stance+swing)))

    return np.mean(duty_factors)


"""gets average of max contact area for all back paws
"""
def get_avg_area(prints_df, name):
    numbPrints = hind_prints_to_analyze
    backs_df = prints_df[prints_df['ForB'] == 'b']
    return np.mean(backs_df.loc[:,'maxA'].iloc[range(numbPrints)])


"""Finds the relative positions of pairs of ipsilateral front and hind paws.
Is not reliant on correct classification of front paws as right or left,
could be made more accurate if it was.
Returns all the distance values for all pairs in the absolute (x+y), x and y
dimensions
"""
def get_h_f_positions(prints_df, name, numbPrints=4):
     #to tell how many paws there are after or before a pause, look for any
    #paw with a stance duration twice as long as the mean for the known
    #good paws and delete everything before or after
    avg_frame = get_avg_frame(prints_df, name)
    #if the avg frame is quite small, make it at least 2
    if avg_frame < 2:
        avg_frame = 2.0
    #TODO: I have no idea how this works with i loc vs loc, check it and fix for other methods too
    for i in prints_df.index.tolist():
        if (abs(prints_df.loc[:, 'lastframe'].loc[i] -
            prints_df.loc[:,'firstframe'].loc[i])) >= (2* avg_frame):
                #if the row of this one is less than the approved paws, delete the nes before it
                if i < prints_df[prints_df['ForB'] == 'b'].index.tolist()[0]:
                    prints_df = prints_df.loc[i+1:,:]
                #or if its greater than them, delete all after it
                elif i > prints_df[prints_df['ForB'] == 'b'].index.tolist()[3]:
                    prints_df = prints_df.loc[:(i-1),:]
                    break

    fronts_df = prints_df[prints_df['ForB'] == 'f']
    backs_df = prints_df[prints_df['ForB'] == 'b']

    abs_positions=[]
    x_positions=[]
    y_positions=[]
    final_matches=[]
    #now confusingly using iloc lol
    for i in range(len(prints_df.print_numb)):
        if prints_df.ForB.iloc[i]=='b':
            xval=prints_df.centroidx.iloc[i]
            yval=prints_df.centroidy.iloc[i]
            #look for a front paw that matches it
            #TODO: could add time elimination earlier
            matches = []
            for j in range(len(fronts_df.print_numb)):
                dist_to = math.sqrt((xval -
                            fronts_df.centroidx.iloc[j])**2 +
                            (yval -
                            fronts_df.centroidy.iloc[j])**2)
                if dist_to<200 and fronts_df.firstframe.iloc[j]<prints_df.firstframe.iloc[i]:
                    #then need to make sure that this bp is the closest thing to the fp that is in acceptable time range
                    min_bprint = 0
                    min_dist = 60000
                    candidate_backs = backs_df[backs_df.firstframe > fronts_df.firstframe.iloc[j]]
                    for u in range(len(candidate_backs.print_numb)):
                        dist_to = math.sqrt((fronts_df.centroidx.iloc[j] -
                            candidate_backs.centroidx.iloc[u])**2 +
                            (fronts_df.centroidy.iloc[j] -
                            candidate_backs.centroidy.iloc[u])**2)
                        if dist_to<min_dist:
                            min_bprint = candidate_backs.print_numb.iloc[u]
                            min_dist = dist_to

                    if min_bprint == prints_df.print_numb.iloc[i]:
                        matches.append(fronts_df.print_numb.iloc[j])
            #if there's more than one match
            if len(matches)>1:
                #store what the min one has been so far
                min_print = 0
                min_dist = 60000
                for k in matches:
                    dist_to = math.sqrt((xval -
                            fronts_df[fronts_df.print_numb==k].centroidx.iloc[0])**2 +
                            (yval -
                            fronts_df[fronts_df.print_numb==k].centroidy.iloc[0])**2)
                    if dist_to<min_dist:
                        min_dist = dist_to
                        min_print = k
                matches = [min_print]
            if len(matches) == 1:
                p = matches[0]
                abs_positions.append(math.sqrt((xval -
                            fronts_df[fronts_df.print_numb==p].centroidx.iloc[0])**2 +
                            (yval -
                            fronts_df[fronts_df.print_numb==p].centroidy.iloc[0])**2))
                x_positions.append((xval -
                            fronts_df[fronts_df.print_numb==p].centroidx.iloc[0]))
                y_positions.append((yval -
                            fronts_df[fronts_df.print_numb==p].centroidy.iloc[0]))
                final_matches.append(p)
            #elif len(matches)==0:
               # print" "
                #print "no matches for" + name + " " + str(prints_df.print_numb.iloc[i])

    #check for paws matched multiple times
    if len(set([x for x in final_matches if final_matches.count(x) > 1])) > 0:
        print ("for " + name)
        print (set([x for x in final_matches if final_matches.count(x) > 1]))

    return [abs_positions, x_positions, y_positions]


"""The following three methods use the output of get_h_f_positions to find the
mean, coefficient of variation, and standard deviation for a run, respectively
"""
def get_h_f_mean(prints_df, name):
    poses = get_h_f_positions(prints_df, name)
    return [np.mean(poses[0]), np.mean(poses[1]), np.mean(poses[2])]

def get_h_f_cv(prints_df, name):
    poses = get_h_f_positions(prints_df, name)
    return [np.std(poses[0])/np.mean(poses[0]),
            np.std(poses[1])/np.mean(poses[1]),
            np.std(poses[2])/np.mean(poses[2])]

def get_h_f_sd(prints_df, name):
    poses = get_h_f_positions(prints_df, name)
    return [np.std(poses[0]), np.std(poses[1]), np.std(poses[2])]


"""returns the experimental group of the input filename as a string
"""
def get_group(name):
    global experimental_numbers
    id_string = name.split(' ')[0]
    for n in experimental_numbers:
        if n in id_string:
            return 'e'
    else:
        return 'c'



def make_day_file(subfolder, week, day):
    print (week + " and day: " + day)

    #find all .csv  in that folder
    file_paths = glob.glob(subfolder + '/*' + '.csv')

    #get rid of csvs that don't contain 'analyzed'
    file_paths = [path for path in file_paths if 'combo df' in path]

    #then get rid of ones that don't say corrected
    #file_paths = [path for path in file_paths if 'corrected' in path]

    #read everything to panda dataframes
    dfs = []
    for path in file_paths:
        dfs.append(pd.read_csv(path))

    #a list of just the file name w/o path info
    file_names = [os.path.split(path)[1].split('.')[0] for path in file_paths]
    #gets whether it is a control or experimental, based on the number
    groups = [get_group(name) for name in file_names]

    ids = [name.split(' ')[0] for name in file_names]

    trials = [name.split(' ')[1] for name in file_names]

    avg_boses = [get_avg_bos(dfs[i], file_names[i]) for i in range(len(dfs))]

    avg_strides = [get_avg_stride(dfs[i], file_names[i]) for i in range(len(dfs))]

    avg_steps = [get_avg_step(dfs[i], file_names[i]) for i in range(len(dfs))]

    avg_frames = [get_avg_frame(dfs[i], file_names[i]) for i in range(len(dfs))]

    speeds = [get_speed(dfs[i], file_names[i]) for i in range(len(dfs))]
    avg_as = [get_avg_area(dfs[i], file_names[i]) for i in range(len(dfs))]

    stride_speed_one = [get_speed_by_stride(dfs[i], file_names[i], 1) for i in range(len(dfs))]
    stride_speed_two = [get_speed_by_stride(dfs[i], file_names[i], 2) for i in range(len(dfs))]
    stride_speed_three = [get_speed_by_stride(dfs[i], file_names[i], 3) for i in range(len(dfs))]

    r_stance_swing = [get_stance_swing(dfs[i], file_names[i], 'r') for i in range(len(dfs))]
    l_stance_swing = [get_stance_swing(dfs[i], file_names[i], 'l') for i in range(len(dfs))]

    r_duty = [get_duty_factor(dfs[i], file_names[i], 'r') for i in range(len(dfs))]
    l_duty = [get_duty_factor(dfs[i], file_names[i], 'l') for i in range(len(dfs))]

    h_f_abs_mean = [get_h_f_mean(dfs[i], file_names[i])[0] for i in range(len(dfs))]
    h_f_x_mean = [get_h_f_mean(dfs[i], file_names[i])[1] for i in range(len(dfs))]
    h_f_y_mean = [get_h_f_mean(dfs[i], file_names[i])[2] for i in range(len(dfs))]

    h_f_abs_cv = [get_h_f_cv(dfs[i], file_names[i])[0] for i in range(len(dfs))]
    h_f_x_cv = [get_h_f_cv(dfs[i], file_names[i])[1] for i in range(len(dfs))]
    h_f_y_cv = [get_h_f_cv(dfs[i], file_names[i])[2] for i in range(len(dfs))]

    h_f_abs_sd = [get_h_f_sd(dfs[i], file_names[i])[0] for i in range(len(dfs))]
    h_f_x_sd = [get_h_f_sd(dfs[i], file_names[i])[1] for i in range(len(dfs))]
    h_f_y_sd = [get_h_f_sd(dfs[i], file_names[i])[2] for i in range(len(dfs))]


    weeks = [week] * len(avg_frames)
    days = [day] * len(avg_frames)

    newpath = make_file_path(subfolder)

    #put everything together to a panda df
    zz = pd.DataFrame( {'filename':file_names, 'week': weeks, 'day': days, 'group':groups,
        'rat id':ids, 'trial':trials, 'Base of Support':avg_boses, 'Stride Length':avg_strides,
        'Step Length':avg_steps, 'Stance Duration': avg_frames, 'Run Speed': speeds,
        'Average of Maximum Areas': avg_as,
        'Stride Speed First Stride': stride_speed_one, 'Stride Speed Second Stride': stride_speed_two,
        'Stride Speed Third Stride': stride_speed_three,
        'Right Limb Stance to Swing Ratio': r_stance_swing,
        'Left Limb Stance to Swing Ratio': l_stance_swing,
        'Right Limb Duty Factor': r_duty, 'Left Limb Duty Factor': l_duty,
        'Mean Absolute Interlimb Distance': h_f_abs_mean,
        'Mean X Interlimb Distance': h_f_x_mean,
        'Mean Y Interlimb Distance': h_f_y_mean,
        'CV of Absolute Interlimb Distance':h_f_abs_cv,
        'CV of X Interlimb Distance':h_f_x_cv,
        'CV of Y Interlimb Distance': h_f_y_cv,
        'SD of Absolute Interlimb Distance': h_f_abs_sd,
        'SD of X Interlimb Distance':h_f_x_sd,
        'SD of Y Interlimb Distance':h_f_y_sd} )
    output = zz[['filename', 'week', 'day', 'group', 'rat id', 'trial',
                 'Base of Support', 'Stride Length', 'Step Length',
                 'Stance Duration', 'Run Speed', 'Average of Maximum Areas',
                 'Stride Speed First Stride', 'Stride Speed Second Stride',
                 'Stride Speed Third Stride', 'Right Limb Stance to Swing Ratio',
                 'Left Limb Stance to Swing Ratio', 'Right Limb Duty Factor',
                 'Left Limb Duty Factor', 'Mean Absolute Interlimb Distance',
                 'Mean X Interlimb Distance', 'Mean Y Interlimb Distance',
                 'CV of Absolute Interlimb Distance',
                 'CV of X Interlimb Distance', 'CV of Y Interlimb Distance',
                 'SD of Absolute Interlimb Distance',
                 'SD of X Interlimb Distance', 'SD of Y Interlimb Distance']]

    output.to_csv(newpath, columns=['filename', 'week', 'day', 'group', 'rat id', 'trial',
                 'Base of Support', 'Stride Length', 'Step Length',
                 'Stance Duration', 'Run Speed', 'Average of Maximum Areas',
                 'Stride Speed First Stride', 'Stride Speed Second Stride',
                 'Stride Speed Third Stride', 'Right Limb Stance to Swing Ratio',
                 'Left Limb Stance to Swing Ratio', 'Right Limb Duty Factor',
                 'Left Limb Duty Factor', 'Mean Absolute Interlimb Distance',
                 'Mean X Interlimb Distance', 'Mean Y Interlimb Distance',
                 'CV of Absolute Interlimb Distance',
                 'CV of X Interlimb Distance', 'CV of Y Interlimb Distance',
                 'SD of Absolute Interlimb Distance',
                 'SD of X Interlimb Distance', 'SD of Y Interlimb Distance'])

    return output

def do_all(folder):
    subfolders = glob.glob(folder + '/*')
    
    #remove anything with a '.', so any non-folders
    subfolders = [ x for x in subfolders if os.path.isdir(x)]
    
    outputs = []
    #do the thing for all of the subfolders
    for fold in subfolders:
        
        name = os.path.split(fold)[1]
        week = name.split(' ')[1]
        day = name.split(' ')[3]
        outputs.append(make_day_file(fold, week, day))

    newpath = make_file_path(folder)
    all_days = pd.concat(outputs, ignore_index = True)
    all_days.to_csv(newpath, columns=['filename', 'week', 'day', 'group', 'rat id', 'trial',
                 'Base of Support', 'Stride Length', 'Step Length',
                 'Stance Duration', 'Run Speed', 'Average of Maximum Areas',
                 'Stride Speed First Stride', 'Stride Speed Second Stride',
                 'Stride Speed Third Stride', 'Right Limb Stance to Swing Ratio',
                 'Left Limb Stance to Swing Ratio', 'Right Limb Duty Factor',
                 'Left Limb Duty Factor', 'Mean Absolute Interlimb Distance',
                 'Mean X Interlimb Distance', 'Mean Y Interlimb Distance',
                 'CV of Absolute Interlimb Distance',
                 'CV of X Interlimb Distance', 'CV of Y Interlimb Distance',
                 'SD of Absolute Interlimb Distance',
                 'SD of X Interlimb Distance', 'SD of Y Interlimb Distance'])



if __name__ == '__main__':
    StartupMenu()
    #raw_input("Press Enter To Exit: ")
