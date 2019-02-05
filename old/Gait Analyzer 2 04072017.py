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
TODO: it's also likely numpy has a csv writing function that would work just
as well.

3/30/2017: Changing quit dist to 200 and removing display of contour-less frames.
Deleting some unused printlines.
TODO: the logic on skipping frames doesn't actually make sense bc the frame
hasn't been being displayed that whole time?

04/05/2017: Trying to fix l/r detection to be less affected by tails and to
be better at front paws. The midline thing is a good principle, doesn't really
seem to help but let's leave it there.

4/5/2017
TODO: fix that apostrophe thing, remove Set_Manager unless it's
actually necessary?
TODO: Add a more info button next to each option that explains what it does.

04/07/2017
stopped cropping rois by ten.
removed backgrund subtraction in favor of just a negative.


warning: don't put an apostrophe in any folder you want to run through this.
It freaks out.



"""
import cv2
import numpy as np
import tkinter as tk
import tkinter.filedialog as tkFileDialog
import csv
import os.path
import math
import glob
import random
import logging
import time
import string
import pprint
logging.basicConfig(filename='timing.log',level=logging.INFO)
logger = logging.getLogger('myapp')
hdlr = logging.FileHandler('gg.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.WARN)


class startup_menu():
    def __init__(self):
        self.root = tk.Tk()
        self.root.update()
        #top = tk.Frame(self.root)
        #bottom = tk.Frame(self.root)
        #top.pack(side=tk.TOP)
        #bottom.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)


        self.folder = ""

        tk.Label(self.root, text="Paw Size Setting:").grid(row=0, sticky=tk.W)
        self.dist_set = tk.IntVar()
        tk.Entry(self.root, width = 15, textvariable=self.dist_set).grid(row=0, column=1)
        self.dist_set.set(25)

        tk.Label(self.root, text="Low Threshold Canny:").grid(row=1, sticky=tk.W)
        self.low_canny = tk.IntVar()
        tk.Entry(self.root, width = 15, textvariable = self.low_canny).grid(row=1, column=1)
        self.low_canny.set(30)

        tk.Label(self.root, text="High Threshold Canny:").grid(row=2, sticky=tk.W)
        self.high_canny = tk.IntVar()
        tk.Entry(self.root, width = 15, textvariable = self.high_canny).grid(row=2, column=1)
        self.high_canny.set(80)

        tk.Label(self.root, text="Denoising Iterations:").grid(row=3, sticky=tk.W)
        self.dn_it = tk.IntVar()
        tk.Entry(self.root, textvariable = self.dn_it, width = 15).grid(row=3, column=1)
        self.dn_it.set(3)

        tk.Label(self.root, text="File Type:").grid(row=4, sticky=tk.W)
        self.file_type = tk.Entry(self.root, width = 15)
        self.file_type.insert(0,".mp4")
        self.file_type.grid(row=4, column=1)

        #1 for true 0 for false
        self.rot = tk.BooleanVar()
        tk.Checkbutton(self.root, text="Rotate Videos", variable=self.rot).grid(row=5, column=0, columnspan=2)

        self.sec_combo = tk.BooleanVar()
        self.sec_combo.set(1)
        temp = tk.Checkbutton(self.root, text="Do Second Combination", variable=self.sec_combo)
        temp.select()
        temp.grid(row=6, column=0, columnspan=2)


        fold_but = tk.Button(self.root, text="Choose Folder:", command = self.get_folder)
        self.fold_lab = tk.Label(self.root, text=self.folder)
        quit_but = tk.Button(self.root, text="Continue", command = self.close)

        fold_but.grid(row=7)
        self.fold_lab.grid(row=7, column=1)
        quit_but.grid(row=8, column=0, columnspan=2)

        self.root.mainloop()

    def close(self):
        #this is bad form
        if self.folder == "":
            self.root.destroy()
            self.root.quit()
            raise Exception("No Folder Selected")

        try:
            self.low_canny.get()
            self.high_canny.get()
            self.dn_it.get()
        except ValueError:
            raise ValueError("Input to Denoising Iterations, Low Canny and High Canny must be integers")

        batch_management(self.folder, self.dist_set.get(), self.low_canny.get(),
                         self.high_canny.get(), self.dn_it.get(),
                         video_type=self.file_type.get(),
                         should_rotate=self.rot.get(), do_second_combo = self.sec_combo.get())

        self.root.destroy()
        self.root.quit()

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
def make_file_path(input_file, file_type, add_text=''):
    #add a space to additional text if it exists for formatting purposes
    if len(add_text) > 0:
        add_text = ' ' + add_text
    #splits the filepath into directory + the files name
    splitpath = os.path.split(input_file)
    newpath = (splitpath[0] + '/' + splitpath[1].split('.')[0] +
              ' automated scoring' + add_text + file_type)

    #If file already exists append numbers to its name until it doesn't exist
    counter = 1
    while os.path.exists(newpath):
        counter += 1
        newpath = (splitpath[0] + '/' + splitpath[1].split('.')[0] +
                  ' automated scoring' + add_text + ' (' + str(counter) + ')' +
                  file_type)

    return newpath


"""
Takes two contours and for every x, y point in 1, compares it to every
point in 2. If the dist between any two points is less than close_dist the two
contours are close, return True. If the dist between any two points is greater
than far_dist, return False, they're automatically not close. This was added
to improve efficiency, as this becomes quite slow for larger values. Numpy
is not used for distance calculations as it is slower than the math package.

Input: cnt1 and cnt2: two opencv contours (so numpy arrays) to be compared and
close_dist: int that is the max cut off for being close
far_dist: int that is the min cut off for being automatically considered far
Output: boolean that's true if they are close, and false if not.
"""
def find_if_close(cnt1, cnt2, close_dist, far_dist):
    #start = time.time()
    row1, row2 = cnt1.shape[0], cnt2.shape[0]
    for i in range(0,row1):
        for j in range(0,row2):
            #get pythagorean distance between two points
            dist = math.sqrt((cnt1[i][0][0] - cnt2[j][0][0])**2 +
                            (cnt1[i][0][1] - cnt2[j][0][1])**2)
            if abs(dist) < close_dist:
                #logger.info('time for close for length ' + str(row1) + ' and ' +
                           # str(row2) + ' is ' + str(time.time() - start))
                return True
            elif abs(dist) > far_dist:
                #logger.info('forcing out of dist comparisons')
                return False
    #logger.info('time for not for length ' + str(row1) + ' and ' +
                            #str(row2) + ' is ' + str(time.time() - start))
    #logger.info('didn"t force out or work out')
    return False


"""my roi set up. allows you to choose two points which serve as the bottom and
top of the roi rectangle.
May still be buggy, further tests needed.
Is a class because of the necessity of having mouse_click be altered and alter
the state of set_roi.
p
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

        return roi

    """Responds to user clicks by setting the top and bottom of the roi. If both
    top and bottom have been set, draws a representing the roi.
    """
    def mouse_click(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            
            self.top = y
            if self.top != None and self.bottom != None:
                cv2.rectangle(self.curr_bg, (0, self.top),
                              (self.orig_bg.shape[1], self.bottom),
                              (0, 0, 255), thickness=2)
        elif event == cv2.EVENT_RBUTTONDOWN:
            
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
                 denoising_its, should_rotate, do_second_combo):
        self.filepath = filepath
        self.should_rotate = should_rotate
        self.video = cv2.VideoCapture(self.filepath)
        self.rand_name = rand_name
        self.close_dist = close_dist
        self.low_canny = low_canny
        self.high_canny = high_canny
        self.denoising_its = denoising_its
        self.do_second_combo = do_second_combo


        #stop if the video isn't opened
        if not self.video.isOpened():
            #BAD FORM: do a better warning
            #and make sure vid filepath exists I guess
            raise Warning("Unable to open video, check installation of OpenCV")

        #save the firstframe after converting to greyscale
        eh, ff = self.video.read()
        self.first_frame = cv2.cvtColor(ff, cv2.COLOR_BGR2GRAY)

        #these will store the roi and rotation matrix set by the user.
        self.rotationM = None
        self.roi = None

        """trying to make something that will write out the video with contours but
        it's not working great right now"""
        #videopath = make_file_path(filename, ".avi")
        #fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        #out = cv2.VideoWriter(videopath,fourcc, 30.0, firstFrame.shape)

    def get_ff(self):
        return self.first_frame

    def set_rotation_matrix(self, matrix):
        self.rotationM = matrix

    def set_roi(self, roi):
        self.roi = roi

    def analyze(self):
        start_time = time.time()

        cv2.namedWindow(self.rand_name)
        logger.info('beginning analysis on ' + os.path.split(self.filepath)[1])
        #frame 1 has already been read, so start at 1
        frame_numb = 1
        #stores unified contours, the frames they're from, centroid x + centroid y
        unified = [[],[],[],[]]
        #stores the last frame accessed, so that it can be saved to an image.
        last_frame = None
        #rotate and crop the first frame using opencv
        rows, cols = self.first_frame.shape
        if self.should_rotate:
            rotatedFF = cv2.warpAffine(self.first_frame, self.rotationM,
                                   (cols, rows))
            croppedFF = rotatedFF[self.roi[1]:self.roi[3],
                                  self.roi[0]:self.roi[2]]
        else:
            croppedFF = self.first_frame[self.roi[1]:self.roi[3],
                                         self.roi[0]:self.roi[2]]

        while True:
            while_start_time = time.time()

            #rval is bool that's False if a frame not read, meaning vid is over
            rval, frame = self.video.read()
            frame_numb += 1

            #Break out of loop if vid is over
            if rval == False:
                break

            #transform curr frame to greyscale roi, then background subtract
            rotated = None
            if self.should_rotate:
                rotated = cv2.warpAffine(frame, self.rotationM, (cols, rows))
            else:
                rotated = frame
            cropped = rotated[self.roi[1]:self.roi[3], self.roi[0]:self.roi[2]]
            grey = cv2.cvtColor(cropped, cv2.COLOR_BGR2GRAY)
            #Background subtraction currently very crude, just
            #subtracting the current frame from the first frame.
            subtracted = cv2.absdiff(grey, croppedFF)

            #a few manipulations to remove noise
            subtracted = cv2.erode(subtracted, None, iterations=self.denoising_its)
            subtracted = cv2.dilate(subtracted, None, iterations=self.denoising_its)

            #Do Canny edge detection and then find contours from those edges
            edges = cv2.Canny(subtracted, self.low_canny, self.high_canny, True)
            contours = cv2.findContours(edges, cv2.RETR_TREE,
                                        cv2.CHAIN_APPROX_SIMPLE)[1]
            cv2.drawContours(rotated, contours, -1, (0, 255, 0), 2,
                             offset=(self.roi[0], self.roi[1]))

            time_manips = time.time()

            #This section of code combines nearby contours because toes were
            #often detected separately.
            #cloud tracks what 'cloud' the contour at the same index as the index
            #in cloud is. Each starts in their own cloud, if they are found to
            #be close with another contour they one is changed to have the
            #same cloud number as the leftmost one.
            cloud = np.linspace(1, len(contours), len(contours))
            if len(contours) > 0:
                for i, cnt1 in enumerate(contours):
                    x = i #this will track index in the cloud array
                    if i != len(contours) - 1:
                        for cnt2 in contours[i + 1:]:
                            x += 1
                            #don't compare if they're already the same
                            if cloud[i] == cloud[x]:
                                continue
                            else:
                                #!!!! Here is where it sets the max distance
                                #contours can be apart and still be the same
                                #paw - it's 25. And if any point on the two
                                #is greater than 300 apart they're automatically
                                #not the same. Of course this only applies to
                                #two contours so if cnt1 is 15 away from cnt2
                                #and 30 away from cnt3, but cnt3 is only 5
                                #away from cnt2, they'll all be combined.
                                close = find_if_close(cnt1, cnt2, self.close_dist, 250)
                                if close:
                                    val2 = min(cloud[i], cloud[x])
                                    cloud[x] = cloud[i] = val2

                #now combine clouds to be the same contour
                cloud_numbers = np.unique(cloud)
                for i in cloud_numbers:
                    pos = np.where(cloud == i)[0]
                    if pos.size != 0:
                        cont = np.vstack(contours[i] for i in pos)
                        hull = cv2.convexHull(cont)
                        cv2.drawContours(rotated, [hull], 0, (255, 255, 255), 3,
                                         offset=(self.roi[0], self.roi[1]))

                        #if the area is too small or too large, don't save them
                        if (cv2.contourArea(hull) > 200 and
                            cv2.contourArea(hull) < 8000):
                            unified[0].append(hull)
                            unified[1].append(frame_numb)
                            M = cv2.moments(hull)
                            unified[2].append(int(M['m10'] / M['m00']))
                            unified[3].append(int(M['m01'] / M['m00']))

            time_combine = time.time()

            #draw all accepted contours and their centroids
            if len(unified[0]) > 1:
                cv2.drawContours(rotated, unified[0], -1, (255, 255, 255), 2,
                                 offset=(self.roi[0], self.roi[1]))
                for i in range(len(unified[0])):
                    cv2.circle(rotated, (unified[2][i] + self.roi[0],
                                         unified[3][i] + self.roi[1]),
                               5, (0, 0, 255))

            #cv2.imshow(os.path.split(self.filepath)[1], rotated)
            cv2.imshow(self.rand_name, rotated)
            last_frame = rotated

            time_draw = time.time()
            logger.info('time to manipulate: ' + str(time_manips -
                                                           while_start_time))
            logger.info('time to combine for ' + str(len(contours)) +
                            ': ' + str(time_combine - time_manips))
            logger.info('time to draw: ' + str(time_draw-time_combine))

            time_elapsed_ms = (time.time() - while_start_time) * 1000
            time_for_frame = int(1000/30 - time_elapsed_ms)
            if time_for_frame <= 1:
                time_for_frame = 2

            if len(contours) >= 1:
                key = cv2.waitKey(int(time_for_frame))
                if key == ord('q'):
                    break

        print(time.time() - start_time)

        self.video.release()
        cv2.destroyAllWindows()
        if len(unified[0]) > 1:
            process_contours(unified, last_frame, self.filepath, self.roi, self.do_second_combo)


"""Takes unified contours, finds which are likely to be the same print and
labels them with that print number and stores them in the prints numpy
structured array. Uses numpy rather than python lists even though everything
else uses python lists because that's just something that happened I guess.
"""
#TODO: make the distance in here set-able

def process_contours(cnts, last_frame, filename, roi, do_second_combo):
    prints = np.array([(0, 0, 0, 0, 0)],
                      dtype = [('centroidx', '>i4'), ('centroidy', '>i4'),
                               ("area",">i4"), ('frame','>i4'),
                               ('print_numb', '>i4')])

    #first we identify areas that are likely to be the same print
    print_numb = 1
    for i in range(0, len(cnts[0])):
        this_print = None
        M = cv2.moments(cnts[0][i])

        #check prev cnts to see if they belong to same foot
        if i!=0:
            frame_sep = 0
            j = 0
            #go back until you find contours at different frames
            while frame_sep == 0 and j <= i:
                j+=1
                frame_sep = cnts[1][i] - cnts[1][i-j]

            #only compare if they're separated by one frame
            while frame_sep == 1:
                dist = abs(math.hypot(cnts[2][i] - cnts[2][i-j],
                                      cnts[3][i] - cnts[3][i-j]))
                if dist < 20:
                    #have to have +1 bc of the dumby row!
                    this_print = prints['print_numb'][i-j+1];
                    break
                #check further down until frame_sep is too big
                j += 1
                frame_sep = cnts[1][i] - cnts[1][i - j]

        #if it doesn't match previous prints, give it a unique new name
        if this_print == None:
            this_print = print_numb
            print_numb += 1

        new = np.array([(cnts[2][i], cnts[3][i], M['m00'], cnts[1][i], this_print)],
                                         dtype = [('centroidx', '>i4'),('centroidy', '>i4'),
                                                  ("area",">i4"),('frame','>i4'), ('print_numb', '>i4')])
        prints = np.vstack((prints, new))

    """then we go through and delete prints with only one representative, as they are likely
    not actually a true print. In the future maybe I can try to combine these with another print
    as this sometimes results from an intermediate frame where the contour was too small and was
    deleted.
    After doing this, draw the prints that have more than 1 representative
    EVENTUALLY: renumber prints so print numbering isn't so odd.
    """
    maximum = int(prints['print_numb'].max())+1
    for i in range(0,maximum):
        #generate a random color to draw with
        color = (random.randint(0, 255), random.randint(0, 255),
                 random.randint(0, 255))
        #Get all indices where the print_numb is i.
        pos = np.where(prints['print_numb'] == i)[0]

        #if it only occurs once, delete it
        if pos.size == 1:
            logger.info("gonna delete print number " + str(i))
            prints = np.delete(prints, pos[0], axis=0)

        if pos.size > 1:
            for z in pos:
                #draw circle with the same area as the print, centered at the
                #centroid (plus the offset from the roi)
                cv2.circle(last_frame,
                           (prints['centroidx'][z] + roi[0],
                            prints['centroidy'][z] + roi[1]),
                           int(math.sqrt(prints['area'][z]/3.14)), color)

    """next, send it off for processing of each print as a whole
    """
    write_file(prints, filename)
    advanced_processing(last_frame, prints, filename, roi, do_second_combo)

"""I'm going back to python lists for this I guess, I should really decide
on either numpy arrays or python lists but my life and this code is a mess
python version of which : indices = [i for i, x in enumerate(my_list) if x == "whatever"]
This takes the full listing of things that were detected as prints and combines
that data into more readable and shortened form - one line per print.
"""
def advanced_processing(last_frame, prints, filename, roi, do_second_combo):
    if prints.size == 0 or prints.size == 1:
        return
    #col #0 = print #, col #1 = max area, col#2 = centroid of max area x, col3, centroid of maxA y
    #col #4 first frame, col #5 last frame, #6 front or back, #7 left or right, 8-frame of max area
    combo_prints = [[],[],[],[],[],[],[],[],[]]
    allNumbs = np.unique(prints['print_numb'])
    #used to track if front paw
    currMinX = last_frame.shape[1]
    #get the midline for right vs left based on the furthest separation
    #maxY = prints['centroidy'].max()
    #minY = prints['centroidy'].min()
    #4/5: now take a quartile to get this
    upper_quart_y = np.percentile(prints['centroidy'],75)
    lower_quart_y = np.percentile(prints['centroidy'],25)
    midline = (upper_quart_y - lower_quart_y) / 2 + lower_quart_y

    #go through and fill out the basic info
    for i in allNumbs:
        pos = np.where(prints['print_numb'] == i)[0]
        allOfOnePrint = prints[pos]

        combo_prints[0].append(i)
        combo_prints[1].append(allOfOnePrint['area'].max())

        indexMaxA = np.argmax(allOfOnePrint['area'], axis=0)
        combo_prints[2].append(allOfOnePrint['centroidx'][indexMaxA][0])
        combo_prints[3].append(allOfOnePrint['centroidy'][indexMaxA][0])
        combo_prints[8].append(allOfOnePrint['frame'][indexMaxA][0][0])

        combo_prints[4].append(allOfOnePrint['frame'].min())
        combo_prints[5].append(allOfOnePrint['frame'].max())

        #check if its a front paw:
        if allOfOnePrint['centroidx'].min() < currMinX:
            currMinX =  allOfOnePrint['centroidx'].min()
            combo_prints[6].append("f")
        else:
            combo_prints[6].append("b")

        #check if right or left
        if allOfOnePrint['centroidy'].max() > midline:
            combo_prints[7].append("r")
        else:
            combo_prints[7].append("l")

    if do_second_combo:
    #now we're going to check for double detection of the same pawprint.
    #!!! eventually maybe this should also re-add contours deleted for having
    #only a single instance, but that sounds real hard.
        for i in range(1,len(combo_prints[0])):
            for j in range(1,3):
                if i-j < 0:
                    continue
                if i >= len(combo_prints[6]):
                    continue
                #if the one behind it is the same for front/back and left/right and
                    #within three frames of each other
                if (combo_prints[6][i] == combo_prints[6][i-j] and
                    combo_prints[7][i] == combo_prints[7][i-j] and
                    (combo_prints[5][i-j]+4 > combo_prints[4][i] or
                    combo_prints[5][i]+4 > combo_prints[4][i-j])):
                    print(combo_prints)
                    print(i)
                    print(j)
                    #and if they're within 3x the distance value for the initial check
                    #TODO: make this modular to initial dist check
                    dist = abs(math.hypot(combo_prints[2][i] - combo_prints[2][i-j],
                               combo_prints[3][i] - combo_prints[3][i-j]))
                    if dist < 60:
                        #combine them to the i row, setting centroid to the maxA
                        #and the frame of max a
                        if combo_prints[1][i-j] > combo_prints[1][i]:
                            combo_prints[1][i] = combo_prints[1][i - j]
                            combo_prints[2][i] = combo_prints[2][i - j]
                            combo_prints[3][i] = combo_prints[3][i - j]
                            combo_prints[8][i] = combo_prints[8][i - j]
                        combo_prints[4][i] = min(combo_prints[4][i - j],
                                                 combo_prints[4][i])
                        combo_prints[5][i] = max(combo_prints[5][i - j],
                                                 combo_prints[5][i])

                        #delete using list comprehension and pop
                        [col.pop(i - j) for col in combo_prints]

    #Delete detections that are back paws and are newly detected more than some
    #dist behind an already detected back print
    #go backwards because these are usually at the end?
    #TODO: also make this moduar to initial check
    #TODO: and make this optional since sometimes it screws up?
    #TODO: or maybe just make a print out that has the no second combo
    #and no tail deletion, so that someone can add them back in if wanted
    #without rerunning! I'm so clever.
    #making this not happen on first 600 pixels bc f turning
    for i in range(len(combo_prints[0])-1,0, -1):
        #don't bother checking fronts
        if combo_prints[6][i] == "f":
            continue
        if combo_prints[2][i] < 600:
            continue

        for j in range(1, i):
            #don't compare to fronts
            if combo_prints[6][i-j] == "f":
                continue

            #if it comes after the comparison paw and is far behind it
            if (combo_prints[4][i] > combo_prints[4][i-j] and
                combo_prints[2][i] > (combo_prints[2][i-j] + 60)):
                    #delete using list comprehension and pop
                    [col.pop(i) for col in combo_prints]
                    break
            #or if it comes very far after as is still fairly far back
            if (combo_prints[4][i] > (combo_prints[4][i-j]+7) and
                combo_prints[2][i] > (combo_prints[2][i-j] + 20)):
                    #delete using list comprehension and pop
                    [col.pop(i) for col in combo_prints]
                    break
            #or if it's at the same time but way futher back
            #TODO: this will miss this if the further back one is detected
            #before the other in the list. Actually for now this is too risky.

    #now redo left right detection with tail deleted
    upper_quart_y = np.percentile(combo_prints[3],75)
    lower_quart_y = np.percentile(combo_prints[3],25)
    midline = (upper_quart_y - lower_quart_y) / 2 + lower_quart_y

    for i in range(0, len(combo_prints[0])):
        if combo_prints[3][i] > midline:
            combo_prints[7][i] = "r"
        else:
            combo_prints[7][i] = "l"


    newpath = make_file_path(filename, '.csv', 'analyzed')
    """
    with open(newpath, 'wb') as f:
        writer = csv.writer(f)
        #write a header row for the csv
        writer.writerow(['print_numb', 'maxA', 'centroidx', 'centroidy',
                         'firstframe', 'lastframe', 'ForB', 'RorL', 'FrameMaxA'])
        for i in range(len(combo_prints[0])):
            #TODO: eventually I should maybe do this in pandas so it isn't so
            #tediously specific, but for now this will work
            writer.writerow([combo_prints[0][i], combo_prints[1][i],
                             combo_prints[2][i][0], combo_prints[3][i][0],
                             combo_prints[4][i], combo_prints[5][i],
                             combo_prints[6][i], combo_prints[7][i],
                             combo_prints[8][i]])
    print("file written to " + newpath)
    """

    for i in range(0, len(combo_prints[0])):
        col = None
        if combo_prints[7][i] == 'r':
            if combo_prints[6][i] == 'f':
                col = (238, 238, 175)
            else:
                col = (255, 191, 0)
        else:
            if combo_prints[6][i] == 'f':
                col = (128, 128, 240)
            else:
                col = (0, 69, 255)


        cv2.circle(last_frame,
                   (combo_prints[2][i] + roi[0], combo_prints[3][i] + roi[1]),
                   int(math.sqrt(combo_prints[1][i] / 3.14)), col,
                   thickness = 3)

        cv2.putText(last_frame, str(combo_prints[0][i]),
                    (combo_prints[2][i] + roi[0], combo_prints[3][i] + roi[1]),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 0), thickness = 2)

    imgpath = make_file_path(filename, '.png')
    cv2.imwrite(imgpath, last_frame)


def write_file(prints, filename):
    return

    newpath = make_file_path(filename, '.csv')

    with open(newpath, 'wb') as f:
        writer = csv.writer(f)
        writer.writerow(['centroidx', 'centroidy', 'area', 'frame', 'print_numb'])
        for row in prints:
            writer.writerow([row['centroidx'][0], row['centroidy'][0],
                             row['area'][0], row['frame'][0], row['print_numb'][0]])


"""Notes on labelling which paw a print is :
first, group sets of paws: label with a unique id.
Do this by figuring out which ones are within +/- lets say 30 of each other

if no paw has been as far in the x as this one has, its a front paw
--> aka, if it's the minimum in the x direction of 0:i above it

take the y values, establish the middle of the two extremes (excluding outliers)
and then divide up right and left based on that
"""

"""sets up batch videos - gets folder, finds all videos in folder, then initializes
all the instances of read_video, adding them to a SetUpManager. Then it calls
the appropriate methods to complete set up and begin analysis.
You can set what extension of video it should look for. Defaults to .mp4 .
"""
def batch_management(folder, close_dist, low_canny, high_canny, denoising_its, video_type = '.mp4', should_rotate = False, do_second_combo = True):

    #get list of all files of type video_type in that folder
    video_paths = glob.glob(folder + '/*' + video_type)
    if len(video_paths) < 1:
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
        vidA = video_analyzer(path, rand_name, close_dist, low_canny, high_canny, denoising_its, should_rotate, do_second_combo)
        setMan.add_analyzer(vidA,vidA.get_ff())
        blinding_dict[counter] = os.path.split(path)[1]
        counter += 1

    if should_rotate:
        setMan.do_rotations()
    setMan.set_rois()
    setMan.run_analyses()

    pp = pprint.PrettyPrinter(indent=4)
    pp.pprint(blinding_dict)


if __name__ == '__main__':
    startup_menu()
    raw_input("Press Enter To Exit: ")
