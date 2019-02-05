This is a description of how to run the Gait Analyzer 2 program.

Written by Hayley Bounds on 5/16/17.

Make sure you have set up Python and OpenCV according to the set up instructions.

HOW TO RUN:
1. Go to R:\CLPS_Burwell_Lab\Lab Projects\GAIT Analysis Project\Program. Double click "Gait Analyzer 2" to run it. 

2. It will open a command prompt window titled something like C:\Users\yourname\Anaconda2\python.exe and a menu screen (this may take a second). Choose the following options (all except choose folder can be left as their default):
	Paw Size Setting - the distance that two contours can be separated by and still considered a paw. Smaller distances may divide up single paws, larger may incorrectly combine them.
	Low Threshold Canny - The low threshold for the Canny Edge Detection Algorithm. See description.
	High Threshold Canny - The high threshold for the Canny Edge Detection Algorithm. See description.
	Denoising Iterations - the number of times to perform the denoising algorithms. Higher numbers should reduce noise, but may blur the image and distort correct detections. Defaults to 3.
	File Type - the file extension for the video files. Defaults to .mp4.
	Rotate - whether or not to rotate the videos.
	Do Second Combo - Whether or not to do the second round of combining similar paws. Uncheck to correct false combinations.
	Choose Folder - Pick the folder containing the videos you want to analyze. The program will find all videos in that folder, but will not find anything in subfolders.

3. Press Continue to begin.

4. If you selected to do rotations, a frame from each video will appear to be rotated. Left click at the top left of top edge, and right click at the top right of the right edge. Then press z to undo or n to redo. If you did not choose to do rotations, continue on.

5. An image will appear entitled "Set ROI". Left click just below the top edge of the tunnel and right click just above the bottom edge. A square will appear showing the roi. If it is acceptable, press n. to redo, press z.

6. The program will run. A number displayed above the video is used to identify it while blinding the user. If a video is taking too long and is clearly bad, the user can press 'q' to exit that video. Pressing 'q' too late may result in skipping the following video, however.

7. When the program finishes, the menu screen will close. Open the command prompt window to view the dictionary that tells you which video corresponds to which number. Once you are done, press enter to exit the command window. Be sure to press enter and exit after running the program!

OUTPUTS:
Three files per video: a file titled "*video name* automated scoring.png" that visually represents the outputs of the program, a file titled '*video name* automated scoring.csv" that contains raw print detections, and a file titled "*video name* automated scoring analyzed.csv" that contains the fully condensed and processed outputs of the program. 
