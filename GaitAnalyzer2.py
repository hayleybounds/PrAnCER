#!/Users/rdb_lab/Anaconda2

"""
Created on Wed Mar 09 20:52:23 2016

Takes a single folder full of videos of the gait analysis set up and scores
them. Is not able to detect pauses, so videos with those should be manually
eliminated before or after this script. If the rat behaves strangely - turning
around, pausing, placing its tail on the ground, ect, the scoring can become
quite messy and get rather slow. A video can be exited without finishing
scoring at any time by pressing 'q'. Used to run faster before I reduced
the combining area, but some sacrifices must be made for accuracy. This is
fairly well commented, but not as thoroughly as some of the labs other
scripts as it's very long. Areas you may want to change include: turning on
rotation - if you want the option to rotate the videos (if you recorded at
an angle), you can set that in the call under main. If you want to set all rois
separately for each video, call set_rois with the additional set_separate = True.
If you want to change the distance for contours to be considered part of the
same paw, which might be necessary if recording at a different size or maybe
if recording with much different size rats, ect, that should be changed in
the call to find_if_close in the analyze method of video_analyzer. Changing the
threshold for edge detections can also be done in the analyze method. This
could allow you to put the numbers higher if you're getting detection of light
objects you don't want, or to put them lower if you're missing detection
of lighter objects you do want. The first number indicates the number below
which something is considered definitely not an edge, and the second number
indicates the number above which something is considered definitely an edge.
Numbers in the middle are only counted as edges if they're connected to something
higher than the second number.

@author: Hayley Bounds

Changes done on July 19th: reduced combining area from 60 to 25. Have not fully
tested this change, but it appears to reduce combinations with nose and not
effect paw detection.


11/8/2016: Changes to the way blinding is done. Also changes to include
the frame number of the max contact area. No impact on how scoring is
done.

02/03/2017: Just changed how dictionary reports the name of the video to make
things easier.

02/05/2017: Working on adding a gui.

2/08/2017: Continuing to add a tkinter GUI. Altered other classes to accept
arguments that were previously built in from gui.

2/10/2017: Adding pretty printing for the blinding key

3/5/2017: Trying to fix some false tail detections.
3/18/2017: URGENT: Noticed problems w/how second combo is doing frames -
it seems to be taking first and last frames from only one? I wasn't paying
attention and saved a few comments changes when I was talking to Ishan, maybe
I broke it then? Hopefully this hasn't been going wrong the whole time??
I found it.
ANOTHER BUG: in write_file, the dumby row has already been deleted, so
I'm actually deleting real data. Now fixed. Not sure what impact this has.

3/30/2017: Changing quit dist to 200 and removing display of contour-less frames.
Deleting some unused printlines.
TODO: the logic on skipping frames doesn't actually make sense bc the frame
hasn't been being displayed that whole time?

04/05/2017: Trying to fix l/r detection to be less affected by tails and to
be better at front paws. The midline thing is a good principle, doesn't really
seem to help but let's leave it there. The mideline detection was changed
to use quartiles instead of minimum and maximum.

4/5/2017
TODO: fix that apostrophe thing, remove Set_Manager unless it's
actually necessary?
DONE: Add a more info button next to each option that explains what it does.

04/07/2017
stopped cropping rois by ten.
removed backgrund subtraction in favor of just a negative.

4/03/2018: Redid everything in the contour processing to use pandas instead
of numpy and lists. Removed now irrelevant writer method.

4/24/2018: Added same_paw_dist and do_tail_deletion as alterable options
in the startup menu. same_paw_dist controls whether prints are considered
the same paw or are combined. Began factoring code out of advanced_processing
so that things make more sense and can be tested.

4/25/2018: Added a json that saves the settings video was run with.
Began splitting up methods in video_analyzer to clean things up.
***Removed upper limit on size

4/29/2018: Added message box to display errors in inputs to the StartUpMenu.
Added more info button to each parameter in StartUpMenu.
create_combo_prints no longer calls find_matches_and_combine or
delete_tail_detections. These are called by process_and_write in VideoAnalyzer

***Altered assign_print_numbers so that it selects the closest match, rather
than just the first one. Also it disallows two prints in the same frame having
the same print number



warning: don't put an apostrophe in any folder you want to run through this.
It freaks out.
"""
import cv2
import numpy as np
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
import logging
import time
import pprint
import pandas as pd
import json
logging.basicConfig(filename='timing.log',level=logging.INFO)
logger = logging.getLogger('myapp')
hdlr = logging.FileHandler('gg.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.WARN)


class StartUpMenu():
    def __init__(self):
        self.root = tk.Tk()
        self.root.update()
        self.folder = ""

        tk.Label(self.root, text="Paw Size Setting:").grid(row=0, sticky=tk.W)
        self.dist_set = tk.IntVar()
        tk.Entry(self.root, width = 15, textvariable=self.dist_set).grid(
                row=0, column=1)
        self.dist_set.set(25)

        tk.Label(self.root, text="Low Threshold Canny:").grid(
                row=1, sticky=tk.W)
        self.low_canny = tk.IntVar()
        tk.Entry(self.root, widt =15, textvariable = self.low_canny).grid(row=1, column=1)
        self.low_canny.set(30)

        tk.Label(self.root, text="High Threshold Canny:").grid(row=2, sticky=tk.W)
        self.high_canny = tk.IntVar()
        tk.Entry(self.root, width=15, textvariable=self.high_canny).grid(row=2, column=1)
        self.high_canny.set(80)

        tk.Label(self.root, text="Denoising Iterations:").grid(row=3, sticky=tk.W)
        self.dn_it = tk.IntVar()
        tk.Entry(self.root, textvariable = self.dn_it, width = 15).grid(row=3, column=1)
        self.dn_it.set(3)

        tk.Label(self.root, text="Video File Type:").grid(row=4, sticky=tk.W)
        self.file_type = tk.Entry(self.root, width = 15)
        self.file_type.insert(0,".mp4")
        self.file_type.grid(row=4, column=1)

        tk.Label(self.root, text="Same Paw Distance:").grid(row=5, sticky=tk.W)
        self.same_paw_dist = tk.IntVar()
        tk.Entry(self.root, width = 15, textvariable = self.same_paw_dist).grid(row=5, column=1)
        self.same_paw_dist.set(20)

        #1 for true 0 for false
        self.rot = tk.BooleanVar()
        tk.Checkbutton(self.root, text="Rotate Videos", variable=self.rot).grid(row=6, column=0, columnspan=2)

        self.sec_combo = tk.BooleanVar()
        self.sec_combo.set(1)
        temp = tk.Checkbutton(self.root, text="Do Second Combination", variable=self.sec_combo)
        temp.select()
        temp.grid(row=7, column=0, columnspan=2)

        self.tail_del = tk.BooleanVar()
        self.tail_del.set(1)
        temp = tk.Checkbutton(self.root, text="Do Tail Deletion", variable=self.tail_del)
        temp.select()
        temp.grid(row=8, column=0, columnspan=2)

        fold_but = tk.Button(self.root, text="Choose Folder:", command = self.get_folder)
        self.fold_lab = tk.Label(self.root, text=self.folder)
        quit_but = tk.Button(self.root, text="Continue", command = self.close)

        fold_but.grid(row=9)
        self.fold_lab.grid(row=9, column=1)
        quit_but.grid(row=10, column=0, columnspan=3)
        
        #add a more info button for each of the parameters
        parameters = ['paw_size', 'low_canny', 'high_canny', 'dn_it',
                      'file_type', 'same_paw_dist', 'rotate', 'sec_combo',
                      'tail_delete']
        self.buts=[]
        for i, param in enumerate(parameters):
            def handler(self=self, param=param):
                return self.disp_info(param) 
            self.buts.append(tk.Button(self.root, width=20, bitmap='question',
                  command=handler).grid(
                          row=i, column=2, padx=5))

        self.root.mainloop()
        
    def disp_info(self, parameter):
        disp_info_dict = {'paw_size': 'This controls how close together two ' +
                          'contours need to be to be considered a single hull.',
            'low_canny': 'Higher numbers will result in fewer detected edges,'+
            ' smaller in more. This number is the number below which something' +
            ' is considered definitely not an edge.',
            'high_canny': 'Higher numbers will result in fewer detected edges,'+
            ' smaller in more. This number is the number above which something' +
            ' is considered definitely an edge.',
            'dn_it': 'The number of iterations of dilation and erosion to' +
            'perform. Larger numbers may reduce detection of edges due to noise',
            'file_type': 'The file type of the video to be read. All types' +
            ' supported by opencv should work',
            'same_paw_dist': 'The maximum distance between two separate print'+
            ' detections in adjacent frames that will still classify them' +
            ' as part of the same print',
            'rotate': 'Whether or not to rotate videos prior to scoring',
            'sec_combo': 'Whether to try to combine similar prints after'+
            ' initial assignment',
            'tail_delete': 'Whether to try to delete prints that are likely' +
            'actually detections of dragged tails'}
        tkMessageBox.showinfo(title=parameter,
                              message=disp_info_dict[parameter])

    def close(self):
        if self.folder == "":
            tkMessageBox.showerror(title = 'Select a Folder',
                                   message = 'You must select a folder of ' +
                                             'videos')
            return

        try:
            self.low_canny.get()
            self.high_canny.get()
            self.same_paw_dist.get()
            self.dn_it.get()
            self.dist_set.get()
        except ValueError:
            tkMessageBox.showerror(title = 'Invalid Input',
                                   message = 'Input to Denoising, Distance,' +
                                   ' and Canny settings must be integers')
            return
        
        keyword_args_dict = {'folder': self.folder,
                             'close_dist': self.dist_set.get(),
                             'low_canny': self.low_canny.get(),
                             'high_canny': self.high_canny.get(),
                             'denoising_its': self.dn_it.get(),
                             'same_paw_dist': self.same_paw_dist.get(),
                             'video_type': self.file_type.get(),
                             'should_rotate': self.rot.get(),
                             'do_second_combo': self.sec_combo.get(),
                             'do_tail_deletion': self.tail_del.get()
                             }
        
        self.root.destroy()
        self.root.quit()

        batch_management(**keyword_args_dict)

    def get_folder(self):
        #make a label that displays the chosen folder
        self.folder = tkFileDialog.askdirectory(title='Choose a Folder')
        self.fold_lab.configure(text = self.folder)


"""Uses string and path manipulations to create the output filenames for
the different outputs of the program.

Input: inputfile: the full filepath of the video being analyzed, filetype: the
type of file being written, and add_text: any additional text, defaults to empty
string
Output: a unique filepath for the output file to be written to.
"""
def make_file_path(input_file, file_type, add_text = '', no_overwrite = False):
    #add a space to additional text if it exists for formatting purposes
    if len(add_text) > 0:
        add_text = ' ' + add_text
    #splits the filepath into directory + the files name
    splitpath = os.path.split(input_file)
    newpath = (splitpath[0] + '/' + splitpath[1].split('.')[0] +
               add_text + file_type)
    
    if no_overwrite:
        #If file already exists append numbers to its name until it doesn't exist
        counter = 1
        while os.path.exists(newpath):
            counter += 1
            newpath = (splitpath[0] + '/' + splitpath[1].split('.')[0] +
                      add_text + ' (' + str(counter) + ')' + file_type)

    return newpath


"""
Takes two contours and for every x, y point in 1, compares it to every
point in 2. If the dist between any two points is less than close_dist the two
contours are close, return True. If the dist between any two points is greater
than far_dist, return False, they're automatically not close. This was added
to improve efficiency, as this becomes quite slow for larger values.
EDIT 3.14.2018: changed to be element-wise ops on an array for speed improvements.

Input: cnt1 and cnt2: two opencv contours (so numpy arrays) to be compared and
close_dist: int that is the max cut off for being close
far_dist: int that is the min cut off for being automatically considered far
Output: boolean that's true if they are close, and false if not.
"""
def find_if_close(cnt1, cnt2, close_dist, far_dist):
    for i in range(0, cnt2.shape[0]):
            dists = np.sqrt((cnt1[:,0,0] - cnt2[i,0,0])**2 +
                            (cnt1[:,0,1] - cnt2[i,0,1])**2)
            if dists.min() < close_dist:
                return True
            elif dists.max() > far_dist:
                return False
    return False


"""my roi set up. allows you to choose two points which serve as the bottom and
top of the roi rectangle.
May still be buggy, further tests needed.
Is a class because of the necessity of having mouse_click be altered and alter
the state of set_roi.
Takes in background, the first frame of a video in its constructor. Because
opencv drawing permanently alters the image, it displays a copy of that, curr_bg.
When set_roi is called, it is displayed. The user clicking left sets the top of
the roi, which has its length preset to be the length of the video minus ten
pixels on each side to account for rotation chopping off some edges. Right
clicks set the bottom of the roi. If there has been both a right and a left click,
the roi is drawn as a rectangle on the image. It is automatically updated by
the continuous while loop. If the user presses z, the top and bottom of the roi
are reset and the image returns to the original one. Pressing n finalizes the
roi and breaks out of the while loop, ending the set up. The roi is returned by
set_roi as a list of four points.
"""
class RoiChooser():
    def __init__(self, background):
        self.orig_bg = background
        self.curr_bg = self.orig_bg.copy()
        self.top = None
        self.bottom = None

    """Displays the curr_bg image and automatically updates it via a while loop
    that is only broken out of when the user presses n to update. Sets mouse
    clicks to call the mouse_click method. Pressing z resets instance variables
    to their inital values.
    Output: roi: a list of the form [left x, top y, right x, bottom y]
    """
    def set_roi(self):
        tkMessageBox.showinfo('Set ROI', 'Set ROI by left clicking for top border, ' +
            'right clicking for bottom border, and then pressing n. To reset roi, ' +
            'press z')
        roi = None
        cv2.namedWindow('Set ROI')
        cv2.setMouseCallback('Set ROI', self.mouse_click)
        while True:
            cv2.imshow('Set ROI', self.curr_bg)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('z') or key == ord('Z'):
                self.curr_bg = self.orig_bg.copy()
                self.top = None
                self.bottom = None


            elif key == ord('n') or key == ord('N'):
                if self.top != None and self.bottom != None:
                    roi = [0, self.top, self.orig_bg.shape[1], self.bottom]
                    cv2.destroyAllWindows()
                    break

        print("roi finished")
        return roi

    """Responds to user clicks by setting the top and bottom of the roi. If both
    top and bottom have been set, draws a representing the roi.
    """
    def mouse_click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            print(y)
            self.top = y
            if self.top != None and self.bottom != None:
                cv2.rectangle(self.curr_bg, (0, self.top),
                              (self.orig_bg.shape[1], self.bottom),
                              (0, 0, 255), thickness=2)
        elif event == cv2.EVENT_RBUTTONDOWN:
            print(y)
            self.bottom = y
            if self.top != None and self.bottom != None:
                cv2.rectangle(self.curr_bg, (0, self.top),
                              (self.orig_bg.shape[1], self.bottom),
                              (0, 0, 255), thickness=2)


"""Similar to RoiChooser, but handles rotation instead. Only methods that
differ significantly from RoiChooser are commented. The user clicks at two
points along the line of the apparatus to establish what should become a
straight line. The left point must be designated using the left click button,
and the right one using the right button. The image is then rotated and
3 lines are displayed to allow the user to double check that the rotation
corrected properly.
"""
class Rotater():
    def __init__(self, background):
        self.orig_bg = background
        self.curr_bg = self.orig_bg.copy()
        self.pt_one = None
        self.pt_two = None
        self.matrix = None

    def rotate_image(self):
        cv2.namedWindow('Set Rotation')
        cv2.setMouseCallback('Set Rotation', self.mouse_click)
        while True:
            cv2.imshow('Set Rotation', self.curr_bg)
            key = cv2.waitKey(1) & 0xFF

            if key == ord('z') or key == ord('Z'):
                self.curr_bg = self.orig_bg.copy()
                self.pt_one = None
                self.pt_two = None

            elif key == ord('n') or key == ord('N'):
                if self.pt_one != None and self.pt_two != None:
                    cv2.destroyAllWindows()
                    break

        print('rotation finished')
        return self.matrix

    def mouse_click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.pt_one = (x,y)
            self.rotate()

        elif event == cv2.EVENT_RBUTTONDOWN:
            self.pt_two = (x,y)
            self.rotate()

    """If both points are set, finds the angle to rotate through, and rotates
    either ccw or cw based on the left + right points. Draws 3 lines to
    the user to check that the rotation moved things to straight
    """
    def rotate(self):

        if self.pt_one != None and self.pt_two != None:
            cv2.line(self.curr_bg, self.pt_one, self.pt_two, (0, 255, 0))

            deltay = (max(self.pt_one[1], self.pt_two[1]) -
                        min(self.pt_one[1], self.pt_two[1]))
            deltax = (max(self.pt_one[0], self.pt_two[0]) -
                        min(self.pt_one[0], self.pt_two[0]))
            tanval = deltay/float(deltax)
            angle = math.degrees(np.arctan(tanval))
            print(angle)
            rows, cols = self.orig_bg.shape

            #if the left is higher than the right rotate ccw
            if self.pt_one[1] < self.pt_two[1]:
                self.matrix= cv2.getRotationMatrix2D((cols / 2, rows / 2),
                                                     angle, 1)
            else:
                self.matrix= cv2.getRotationMatrix2D((cols / 2, rows / 2),
                                                     -angle, 1)
            self.curr_bg = cv2.warpAffine(self.curr_bg, self.matrix,
                                          (cols, rows))

            cv2.line(self.curr_bg, (0, self.pt_one[1]), (cols, self.pt_one[1]),
                     (0, 255, 0))
            cv2.line(self.curr_bg, (0, self.pt_two[1]), (cols, self.pt_two[1]),
                     (0, 255, 0))
            cv2.line(self.curr_bg, (0, self.pt_one[1] + 10),
                     (cols, self.pt_one[1] + 10), (0, 255, 0))


"""here's the idea: this is given all the information it needs from the video_analyzers
It stores this info (namely, the frames and the instances of video analyzer), then it
allows the user to go through all the rotations and roi settings, sending the info
to the relevant analyzer as soon as its completed. Once it is finished, main will
tell the video analyzers to begin analysis.

Pairs of analyzers with the first frames of their videos are added to the
analyzers list. do_rotations() does rotations for each video, saving the
rotated frame if the roi
"""
class SetUpManager():
    def __init__(self):
        #store analyzers
        self.analyzers = []

    def add_analyzer(self, analyzer, firstframe):
        self.analyzers.append([analyzer, firstframe])

    def do_rotations(self):
        for pair in self.analyzers:
            mat = Rotater(pair[1]).rotate_image()
            pair[0].set_rotation_matrix(mat)
            rows, cols = pair[1].shape
            pair[1] = cv2.warpAffine(pair[1], mat, (cols, rows))

    #currently, all ROIs are consistent enough I only set them once for a batch,
    #if this changes just call this with set_separate = True.
    def set_rois(self, set_separate = False):
        roi = RoiChooser(self.analyzers[0][1]).set_roi()
        for pair in self.analyzers:
            if set_separate:
                roi = RoiChooser(pair[1]).set_roi()
            pair[0].set_roi(roi)

    def run_analyses(self):
        for pair in self.analyzers:
            pair[0].analyze()

class video_analyzer():
    """takes in the filepath of the video it is to analyze, and should_rotate,
    a boolean that indicates whether the video should be rotated for analysis.
    """
    def __init__(self, filepath, rand_name, close_dist, low_canny, high_canny,
                 denoising_its, same_paw_dist, should_rotate, do_second_combo,
                 do_tail_deletion):
        self.filepath = filepath
        self.should_rotate = should_rotate
        self.video = cv2.VideoCapture(self.filepath)
        self.rand_name = rand_name
        self.close_dist = close_dist
        self.same_paw_dist = same_paw_dist
        self.low_canny = low_canny
        self.high_canny = high_canny
        self.denoising_its = denoising_its
        self.do_second_combo = do_second_combo
        self.do_tail_deletion = do_tail_deletion

        #stop if the video isn't opened
        if not self.video.isOpened():
            if not os.path.exists(self.filepath):
                raise Exception(self.filepath + ' does not exist')

            raise Exception("Unable to open video, check installation of OpenCV")

        #save the firstframe after converting to greyscale
        _, ff = self.video.read()
        self.first_frame = cv2.cvtColor(ff, cv2.COLOR_BGR2GRAY)

        #these will store the roi and rotation matrix set by the user.
        self.rotationM = None
        self.roi = None

        #this stores the last frame analyzed for saving
        self.last_frame = None

    def get_ff(self):
        return self.first_frame

    def set_rotation_matrix(self, matrix):
        self.rotationM = matrix

    def set_roi(self, roi):
        self.roi = roi

    """performs rotations if desired, then crops to roi
    TODO: check how this works on color vs greyscale??
    """
    def _rotate_and_crop(self, frame):
        rows, cols = self.first_frame.shape
        #if doing rotation, rotate, otherwise just keep current frame
        rotated = frame
        if self.should_rotate:
            rotated = cv2.warpAffine(frame, self.rotationM, (cols, rows))
        #crop to ROI
        cropped = rotated[self.roi[1]:self.roi[3], self.roi[0]:self.roi[2]]
        return rotated, cropped

    """As part of combining contours, determine which ones belong to the same
    cloud. cloud tracks what 'cloud' the contour at the same index as the index
    in cloud is. Each starts in their own cloud, if they are found to
    be close with another contour they one is changed to have the
    same cloud number as the leftmost one.

    Utilizes find_if_close to determine if the two contours should be in
    the same cloud.
    If any point on the two is greater than close_dist*10 apart they're
    automatically not the same. Of course this only applies to two contours so
    if cnt1 is 15 away from cnt2 and 30 away from cnt3, but cnt3 is only 5
    away from cnt2, they'll all be combined.
    """
    def _assign_clouds(self, contours):
        cloud = np.linspace(1, len(contours), len(contours))
        for i, cnt1 in enumerate(contours):
            x = i #this will track index in the cloud array
            if i != len(contours) - 1:
                for cnt2 in contours[i + 1:]:
                    x += 1
                    #don't compare if they're already the same
                    if cloud[i] == cloud[x]:
                        continue
                    else:
                        close = find_if_close(cnt1, cnt2, self.close_dist,
                                              self.close_dist*10)
                        if close:
                            val2 = min(cloud[i], cloud[x])
                            cloud[x] = cloud[i] = val2
        return cloud

    """rotate and crop the frame, then convert to greyscale and background
    subtract. Finally, perform erosions and dilations to minimize noise.
    Currently background subtraction is very crude, just subtracting the
    current frame from the first frame.
    """
    def _preprocess_frame(self, frame):
        rows, cols = self.first_frame.shape
        rotated, cropped = self._rotate_and_crop(frame)
        grey = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
        #subtract the first frame
        subtracted = cv2.absdiff(grey, self.processed_first_frame)
        #denoise with erosion and dilation
        subtracted = cv2.erode(subtracted, None, iterations=self.denoising_its)
        subtracted = cv2.dilate(subtracted, None, iterations=self.denoising_its)

        return rotated, subtracted

    """Based on the cloud indexes, combines all contours in a cloud into
    a single contour, and then takes the convex hull of that to get one
    hull per print. Draws this hull.
    Then, add the hull to hulls_df and unified, to store its info
    Does a basic size check to determine if the contour should be kept.
    TODO: modularize the size check?
    """
    def _combine_contours(self, contours, cloud, frame_numb, rotated):
        cloud_numbers = np.unique(cloud)
        for i in cloud_numbers:
            pos = np.where(cloud == i)[0]
            if pos.size != 0:
                cont = np.vstack(contours[i] for i in pos)
                hull = cv2.convexHull(cont)
                cv2.drawContours(rotated, [hull], 0, (255, 255, 255), 3,
                                 offset=(self.roi[0], self.roi[1]))

                #if the area is too small or too large, mark for deletion
                to_keep = (cv2.contourArea(hull) > 200) #and
                    #cv2.contourArea(hull) < 8000)
                M = cv2.moments(hull)

                if M['m00'] > 0:
                    #add the hull and consituent contours and info to dataframe
                    #to get pandas to accept it, must be a list not
                    #a np array
                    self.hulls_df = self.hulls_df.append(pd.DataFrame({
                                         'frame': frame_numb,
                                         'hull': [hull],
                                         'contours':
                                             [[contours[i] for i in pos]],
                                         'area': M['m00'],
                                         'X': int(M['m10'] / M['m00']),
                                         'Y': int(M['m01'] / M['m00']),
                                         'is_kept': to_keep}),
                                         ignore_index=True)

                    #TODO: remove eventually, for now save
                    if to_keep:
                        self.unified[0].append(hull)
                        self.unified[1].append(frame_numb)
                        self.unified[2].append(int(M['m10'] / M['m00']))
                        self.unified[3].append(int(M['m01'] / M['m00']))

    """Given a frame and the number of that frame, goes through the steps
    to preprocess it, detect contours, combine contours into hulls, and
    then save the hulls. Also draws some outputs to be visualized.
    """
    def _analyze_one_frame(self, frame, frame_numb):
        start_time = time.time()
        rotated, subtracted = self._preprocess_frame(frame)
        #Do Canny edge detection and then find contours from those edges
        edges = cv2.Canny(subtracted, self.low_canny, self.high_canny, True)
        contours = cv2.findContours(edges, cv2.RETR_TREE,
                                    cv2.CHAIN_APPROX_SIMPLE)[1]
        cv2.drawContours(rotated, contours, -1, (0, 255, 0), 2,
                         offset=(self.roi[0], self.roi[1]))

        time_manips = time.time()

        #This section of code combines nearby contours because toes were
        #often detected separately.
        if len(contours) > 0:
            cloud = self._assign_clouds(contours)
            self._combine_contours(contours, cloud, frame_numb, rotated)

        time_combine = time.time()

        #draw all accepted contours and their centroids
        if len(self.unified[0]) > 0:
            cv2.drawContours(rotated, self.unified[0], -1, (255, 255, 255), 2,
                             offset=(self.roi[0], self.roi[1]))
            for i in range(len(self.unified[0])):
                cv2.circle(rotated, (self.unified[2][i] + self.roi[0],
                                     self.unified[3][i] + self.roi[1]),
                           5, (0, 0, 255))

        self.last_frame = rotated

        time_draw = time.time()
        logger.info('time to manipulate: ' + str(time_manips -
                                                       start_time))
        logger.info('time to combine for ' + str(len(contours)) +
                        ': ' + str(time_combine - time_manips))
        logger.info('time to draw: ' + str(time_draw-time_combine))

        return rotated, len(contours) > 0

    def analyze(self):
        start_time = time.time()
        cv2.namedWindow(self.rand_name)
        logger.info('beginning analysis on ' + os.path.split(self.filepath)[1])
        #frame 1 has already been read, so start at 1
        frame_numb = 1
        #stores unified contours,frame, centroid x + centroid y for easy drawing
        self.unified = [[],[],[],[]]
        #new dataframe to store the single print info
        self.hulls_df = pd.DataFrame(columns = ['frame', 'hull', 'contours',
                                             'X','Y', 'area', 'is_kept'])
        #rotate and crop the first frame using opencv
        _, self.processed_first_frame = self._rotate_and_crop(self.first_frame)

        while True:
            while_start_time = time.time()
            #rval is bool that's False if a frame not read, meaning vid is over
            rval, frame = self.video.read()
            frame_numb += 1
            if rval == False: #break out of loop if vid is over
                print("total frames: ", frame_numb)
                break

            analyzed_frame, do_display = self._analyze_one_frame(frame, frame_numb)

            time_elapsed_ms = (time.time() - while_start_time) * 1000
            time_for_frame = int(1000/30 - time_elapsed_ms)
            if time_for_frame <= 1:
                time_for_frame = 2

            if do_display:
                cv2.imshow(self.rand_name, analyzed_frame)
                key = cv2.waitKey(int(time_for_frame))
                if key == ord('q'):
                    break

        self.video.release()
        cv2.destroyAllWindows()
        print(time.time() - start_time)
        
        if len(self.hulls_df) > 0:
            self.process_and_write()
    
    def process_and_write(self):
        assign_print_numbers(self.hulls_df, self.same_paw_dist)
        combo_prints = create_combo_prints(self.hulls_df, self.same_paw_dist,
                                           self.last_frame.shape[1])
        #if two prints of the same classification are close, combine them
        if self.do_second_combo:
            find_matches_and_combine(combo_prints, self.same_paw_dist,
                                     hulls_df=self.hulls_df, file=self.filepath)
        #Delete detections that are probably tails, then redo l/r assignment
        if self.do_tail_deletion:
            delete_tail_detections(combo_prints, self.same_paw_dist, 7,
                                   hulls_df=self.hulls_df)
            assign_left_right(combo_prints)
        
        #write outputs
        combo_prints = combo_prints.astype('int')
        combo_prints.to_csv(make_file_path(self.filepath, '.csv', 'combo df'),
                            index=False, columns = ['print_numb','max_area',
                                                    'X','Y','first_frame',
                                                    'last_frame', 'is_right',
                                                    'is_hind', 'frame_max_a'])
        path = make_file_path(self.filepath, '.csv', 'hull')
        write_hulls_df = self.hulls_df.fillna(-1) #in order to write, make all nans -1
        write_hulls_df.drop(['contours', 'hull'], axis=1, inplace=True)
        write_hulls_df.astype('int').to_csv(path, index=False)
        self.hulls_df.to_pickle(make_file_path(self.filepath, '.p', 'hull'))

        self.last_frame = draw_final_print_classification(self.last_frame,
                                        self.roi, combo_prints)
        cv2.imwrite(make_file_path(self.filepath, '.png'), self.last_frame)
            

"""First, group sets of hulls into prints, and label with a unique id.
Do this by figuring out which ones are within same_paw_dist of each other
Iterates through hulls_df and finds which hulls probably belong to the same
print, and assigns them that number. Also eliminates prints that have only
one detection, as they are almost always tail or nose detections

4/29/18 if multiple matches are found, assign to number of closest one
Also now disallows multiple hulls from the same frame being assigned the same
print number. Instead, will check which of the two hulls is further from
the matching print in the previous frame, and then assigns that further one
a new number, so that only the closest one stays a match.
Also changed so that it only iterates through kept prints.
"""
def assign_print_numbers(hulls_df, same_paw_dist):
    hulls_df['print_numb'] = np.nan
    print_numb = 1
    #first we identify areas that are likely to be the same print
    for idx, hull in hulls_df[hulls_df.is_kept].iterrows():
        this_print = np.nan
        #get hulls that occured one frame before, and are w/i same_paw_dist
        possible_matches = hulls_df[(hull.frame - hulls_df.frame == 1) &
            (hulls_df.is_kept) & 
            (np.sqrt(((hull.X-hulls_df.X)**2+(hull.Y-hulls_df.Y)**2).astype('float64')) < same_paw_dist)]
        if len(possible_matches) >= 1: #if multiple matches, pick closest
            closest_idx = get_closest_hull_index(possible_matches, hull)
            this_print = possible_matches.print_numb[closest_idx]
            #if there's another print in same frame w/this number
            same_frame_hulls = hulls_df[hulls_df.frame==hull.frame]
            if len(same_frame_hulls[same_frame_hulls.print_numb == this_print])>0:
                best_idx = get_closest_hull_index(same_frame_hulls,
                                       possible_matches.loc[closest_idx])
                if best_idx != idx:
                    this_print = np.nan
                else: #if this is a better match
                    #retroactively assign a unique print numb to the duplicate
                    hulls_df.loc[(hulls_df.frame==hull.frame) &
                        hulls_df.print_numb==this_print, 'print_numb'] = print_numb
                    print_numb += 1
        elif np.isnan(this_print): #if it doesn't match previous prints
            this_print = print_numb #give it a unique name
            print_numb += 1
        hulls_df.loc[idx, 'print_numb'] = this_print

    #count the occurences of each print number
    counts = hulls_df.print_numb.value_counts()
    single_occurences = counts.index[counts.values == 1].values
    #mark all numbers that occur only once to be discarded
    hulls_df.loc[hulls_df.print_numb.isin(single_occurences),'is_kept'] = False
                 
                 
def get_closest_hull_index(df, row):
    """gets the index of the row in df that is closest to row, based on
    euclidian distance between X and Y column values
    """
    best_idx = -1
    min_dist = np.Inf
    for m_idx, match in df.iterrows():
        dist = abs(math.hypot(row.X-match.X, row.Y-match.Y))
        if dist < min_dist:
            best_idx, min_dist = m_idx, dist
    return best_idx

"""This takes the full listing of things that were detected as prints and combines
that data into more readable and shortened form - one line per print.
if no paw has been as far in the x as this one has, its a front paw
--> aka, if it's the minimum in the x direction of 0:i above it
take the y values, establish the middle of the two extremes (excluding outliers)
and then divide up right and left based on that
"""
def create_combo_prints(hulls_df, same_paw_dist, x_size):
    if len(hulls_df) < 0: #if there isn't enough data skip
        return
    
    grouped_prints = hulls_df.loc[hulls_df.is_kept].groupby(['print_numb'])
    combo_prints = pd.DataFrame(grouped_prints.print_numb.mean())
    combo_prints['first_frame'] = grouped_prints.frame.min().values
    combo_prints['last_frame'] = grouped_prints.frame.max().values
    combo_prints['max_area'] = grouped_prints.area.max().values

    #get values based on the hull of maximum area
    combo_prints['X'] = hulls_df.loc[grouped_prints.area.idxmax(), 'X'].values
    combo_prints['Y'] = hulls_df.loc[grouped_prints.area.idxmax(), 'Y'].values
    combo_prints['frame_max_a'] = hulls_df.loc[grouped_prints.area.idxmax(), 'frame'].values
    assign_left_right(combo_prints)
    
    #for front/hind sorting, first sort prints by first frame then X, ascending
    combo_prints.sort_values(['first_frame', 'X'], inplace=True)
    #used to track if something is a front paw
    curr_min_x = x_size
    #the furthest forward paw so far is a front paw
    min_xes = grouped_prints.X.min()
    for idx in combo_prints.print_numb.unique():
        combo_prints.loc[idx, 'is_hind'] = min_xes[idx] > curr_min_x
        curr_min_x = min(curr_min_x, min_xes[idx])
    return combo_prints

"""Draws circles for prints based on their classification and labels
them with the final print number.
"""
def draw_final_print_classification(last_frame, roi, combo_prints):
    for idx, print_ in combo_prints.iterrows():
        if print_.is_right:
            if print_.is_hind:
                col = (255, 191, 0)
            else:
                col = (238, 238, 175)
        else:
            if print_.is_hind:
                col = (0, 69, 255)
            else:
                col = (128, 128, 240)

        cv2.circle(last_frame,
                   (print_.X + roi[0], print_.Y + roi[1]),
                   int(math.sqrt(print_.max_area / 3.14)), col,
                   thickness = 3)
        cv2.putText(last_frame, str(print_.print_numb),
                    (print_.X + roi[0], print_.Y + roi[1]),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), thickness = 2)
    return last_frame

"""Uses a the midline between the 75th and 25th percentile Y values to
assign prints as left or right.
4/24/18: Added. Now uses only combo prints, not hulls df, and not grouped prints.
Some slight changes in classification may occur, but overall accuracy
shouldn't be compromised.
"""
def assign_left_right(combo_prints):
    upper_quart_y = combo_prints.Y.quantile(.75)
    lower_quart_y =  combo_prints.Y.quantile(.25)
    midline = (upper_quart_y - lower_quart_y) / 2 + lower_quart_y
    combo_prints['is_right'] = combo_prints.Y > midline

"""Given combo_prints dataframe and indexes two combine, combines the two.
Optionally will update a hulls_df if its passed to reflect the changes.
4/24/18: Added by taking out code from advanced_processing. Altered some
code to be cleaner but no logic changes.
TODO: Warn if hulls_df not passed?
"""
def combine_prints(combo_prints, idx1, idx2, hulls_df = None):
    if (combo_prints.loc[idx1].is_right != combo_prints.loc[idx2].is_right or
        combo_prints.loc[idx1].is_hind != combo_prints.loc[idx2].is_hind):
            raise ValueError('prints to combine must have same classification')
    if idx1 == idx2:
        raise ValueError('cannot combine print with itself')

    #keep the higher indexed print to avoid errors
    if combo_prints.index.get_loc(idx1) > combo_prints.index.get_loc(idx2):
        keep_idx, del_idx = idx1, idx2
    else:
        keep_idx, del_idx = idx2, idx1
    big_idx = combo_prints.loc[[idx1,idx2]].max_area.idxmax()
    #update keep_idx row to have the area,X,Y, ect from the max area row
    cols_trans = ['max_area','X','Y', 'frame_max_a']
    combo_prints.loc[keep_idx, cols_trans] = \
        combo_prints.loc[big_idx, cols_trans].values
    #update frame numbers with the new info
    combo_prints.loc[keep_idx, 'first_frame'] = \
               combo_prints.loc[[idx1,idx2]].first_frame.min()
    combo_prints.loc[keep_idx, 'last_frame'] = \
               combo_prints.loc[[idx1,idx2]].last_frame.max()
    if hulls_df is not None: #update all in hulls_df
        hulls_df.loc[(hulls_df.print_numb ==
                      combo_prints.print_numb[del_idx]),
                     'print_numb'] = combo_prints.print_numb[keep_idx]
    #and then delete the row
    combo_prints.drop(del_idx, inplace=True)
    return keep_idx, del_idx

"""Iterates through all prints and for each print, gets all other prints
that are possibly repeats -that is, are the same for front/hind and left/right
and within three frames of the current print. If they are also within
a specified from the print (right now, 3x the distance of the initial check),
the two are combined
"""
def find_matches_and_combine(combo_prints, same_paw_dist, hulls_df = None, file=None):
    for idx, print_ in combo_prints.iterrows():
        possible_matches = combo_prints[(combo_prints.is_right == print_.is_right) &
                                (combo_prints.is_hind == print_.is_hind) &
                                (combo_prints.first_frame -
                                    print_.last_frame <= 3) &
                                    (combo_prints.index != idx)]
        if len(possible_matches) > 0:
            for m_idx, match in possible_matches.iterrows():
                #if it has already been merged into another print
                if idx not in combo_prints.index: break
                dist = abs(math.hypot(print_.X-match.X, print_.Y-match.Y))
                #and if they're within 3x the distance value for the initial check
                if dist < same_paw_dist*3:
                    combine_prints(combo_prints, m_idx, idx, hulls_df=hulls_df)
    #for testing, return indexes of possible matches
    return possible_matches.index.values

"""Delete detections that are back paws and are newly detected more than some
dist behind an already detected back print
"""
def delete_tail_detections(combo_prints, same_paw_dist, long_frame_thresh,
                           hulls_df = None):
    #for each print, check if it needs to be deleted
    for idx, print_ in combo_prints.iterrows():
        #get all hind prints that occur before the current
        #print and are far in front, or occur a long time before and are
        #slightly in front of the current print
        possible_matches = combo_prints[(combo_prints.is_hind) &
                                (((combo_prints.first_frame <
                                    print_.first_frame) &
                                (print_.X - combo_prints.X > same_paw_dist*3)) |
                                ((combo_prints.first_frame <
                                    print_.first_frame - long_frame_thresh) &
                                (print_.X - combo_prints.X > same_paw_dist)))]
        #if any such prints exist, delete the current print
        if len(possible_matches) > 0:
            if hulls_df is not None:
                hulls_df.loc[(hulls_df.print_numb == print_.print_numb),
                                 'is_kept'] = False
            combo_prints.drop(idx, inplace=True)


"""sets up batch videos - gets folder, finds all videos in folder, then initializes
all the instances of read_video, adding them to a SetUpManager. Then it calls
the appropriate methods to complete set up and begin analysis.
You can set what extension of video it should look for. Defaults to .mp4 .
"""
def batch_management(folder, close_dist, low_canny, high_canny, denoising_its,
                     same_paw_dist, video_type = '.mp4', should_rotate = False,
                     do_second_combo = True, do_tail_deletion = True):
    #get list of all files of type video_type in that folder
    video_paths = glob.glob(folder + '/*' + video_type)
    if len(video_paths) < 1:
        root=tk.Tk()
        tkMessageBox.showerror(title='No Videos',
                               message='No videos with format ' + video_type +
                               ' in folder ' + folder)
        root.destroy()
        root.quit()
        print('No videos found!')
        return

    np.random.shuffle(video_paths)
    blinding_dict = {}
    setMan = SetUpManager()

    counter = 1
    for path in video_paths:
        #to blind me, generate a random string that will display when the video
        #runs. it's incredibly unlikely this will ever be a duplicate.
        #rand_name = ''.join(random.choice(string.ascii_uppercase + string.digits) for _ in range(10))
        #Instead, just use numbers
        rand_name = str(counter)
        vidA = video_analyzer(path, rand_name, close_dist, low_canny,
                              high_canny, denoising_its, same_paw_dist,
                              should_rotate, do_second_combo, do_tail_deletion)
        setMan.add_analyzer(vidA,vidA.get_ff())
        blinding_dict[counter] = os.path.split(path)[1]
        counter += 1

    if should_rotate:
        setMan.do_rotations()
    setMan.set_rois()
    setMan.run_analyses()

    #TODO: save ROIs in a more logical manner
    settings_info = {}
    settings_info['roi'] = setMan.analyzers[0][0].roi
    settings_info['close distance']  = close_dist
    settings_info['canny params'] = [low_canny, high_canny]
    settings_info['denoising iters'] = denoising_its
    settings_info['same paw dist'] = same_paw_dist
    settings_info['rotation'] = should_rotate
    settings_info['second combination'] = do_second_combo
    settings_info['tail deletion'] = do_tail_deletion

    with open(folder + '/SettingsData.txt', 'w') as outfile:
        json.dump(settings_info, outfile)


    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(blinding_dict)


if __name__ == '__main__':
    StartUpMenu()
    
    if (sys.version_info > (3, 0)):
        input('Press Enter To Exit: ')
    else:
        raw_input("Press Enter To Exit: ")
