This is a description of how to install Python, OpenCV and all other necessary elements to make the Gait Analyzer and Parameter Analyzer work.

Written by Hayley Bounds on 5/16/17.

The elements you will need for the program to run are: Python 2.7 and the OpenCV 3, pandas, and numpy packages
You'll need the following Python standard library packages: csv, os.path, Tkinter, math, glob, random, time, logging, pprint

Program last run using: Python 2.7.13 with Anaconda 4.0.0 (64-bit)
Tkinter 8.5
numpy 1.10.4
OpenCV 3.1.0

BASIC NOTE:
When I say the path and things as "C:\Users\Yourname\" or similar things, that means that that's the sequence of folders, starting from the C Drive, that you should click through to get to the right folder. You can also click on the bar at the top and type directly into there. PATH refers to the system path. 

TO INSTALL:
The following instructions are for Windows 7. They may work for Windows 10. The program will work on other systems. Installation is generally simpler on non-Windows systems, so instructions from other resources should suffice.
FOLLOW THESE EXTREMELY CAREFULLY. OPENCV INSTALLATION IS VERY FINICKY.

1. Anaconda:
	a) Download the latest Python 2.7 version of Anaconda from the continuum.io website. Make sure you install the Python 2 version, and pick the correct 64 and 32 bit option. 
	b) Install Anaconda. Several settings are important:
		-For installation type, select "just me."
		-For install location, make note of the destination folder! I recommend C:\Users\YourName\Anaconda2. 			Whatever you choose, remember it. We will refer to this destination folder as *ANACONDA_PATH*.
		-For Advanced Installation Options, make sure that the "add anaconda to my PATH environment variable" 		option is checked (it should be by default).
	c) Confirm installation by opening the Command Prompt program and typing "python" and pressing enter. It should show a few lines telling you the version of Python and Anaconda that you have.
	d) Then in the same window on the next line type "import numpy" and press enter. If nothing happens, numpy is installed correctly.
	e) Notes:
	--->This installs a number of useful tools for using Python programs.
	--->This installation includes numpy, pandas, and all standard library packages.

2. OpenCV Shortcut: For 64 bit Windows 7 computers, you can try using these files rather than starting from scratch. This may not work in a few years.
	a) Go to "R:\CLPS_Burwell_Lab\Lab Projects\GAIT Analysis Project\Program\Shortcut OpenCV Install Files" and copy cv2.pyd, and paste it into *ANACONDA_PATH*\Lib\ (for example C:\Users\YourName\Anaconda2\Lib). Also paste it to *ANACONDA_PATH*\Lib\site-packages.
	b) Confirm the base installation by opening a new Command Prompt window. Type "python" and press enter. Then type "import cv2" and press enter. If you get an error, double check that cv2.pyd was pasted into the correct directories, or that it was the correct cv2.pyd. Check your version of opencv by entering "cv2.__version__", it should return 3.x.x.
	c) Go to "R:\CLPS_Burwell_Lab\Lab Projects\GAIT Analysis Project\Program\Shortcut OpenCV Install Files" and copy opencv_ffmpeg310_64.dll, and paste it into *ANACONDA_PATH* (for example C:\Users\YourName\Anaconda2).
	d) To check the FFMPEG install, try running Gait Analyzer - if it returns an error that says that you should check your OpenCV installation, that means the FFMPEG component isn't working. See troubleshooting FFMPEG.
	


3. OpenCV from Scratch: If 2 doesn't work or isn't an option, do this.
	a) Go to opencv.org and open the resources page
	b) Select any pack that begins with 3 (3.x.x), click on Win pack. It will open a new page and download a .exe
	c) Double click the .exe file, extract it to a folder of your choosing (C:\opencv or C:\Users\You\Opencv is a good option). From now on I will refer to the path to this opencv folder (such as C:\opencv) as *OPENCV_PATH*
	d) Go to the folder you extracted the files to. Go to *OPENCV_PATH*\build\python\2.7
	e) For 64 bit machines, open the x64 folder, for 32-bit, go to the folder x84
	f) Copy the file cv2.pyd that is in this folder. Now we will move it to the Anaconda installation.
	g) Go to *ANACONDA_PATH*\Lib\ (for example C:\Users\YourName\Anaconda2\Lib). Paste cv2.pyd there. Also paste it to *ANACONDA_PATH*\Lib\site-packages.
	i) Confirm the base installation by opening a new Command Prompt window. Type "python" and press enter. Then type "import cv2" and press enter. If you get an error, double check that cv2.pyd was pasted into the correct directories, or that it was the correct cv2.pyd. Check your version of opencv by entering "cv2.__version__", it should return 3.x.x.
	h) Now copy the FFMPEG information, which allows videos to be read. Go to *OPENCV_PATH*\build\bin. There should be two .dll files (they should be something like opencv_ffmpeg310.dll and opencv_ffmpeg310_64.dll, but possibly with different numbers than 310 depending on your version. If they're in the format opencv_ffmpeg.dll and opencv_ffmpeg_64.dll, see troubleshooting step 3.) For 32-bit systems, copy opencv_ffmpeg*versionnumber*.dll, for 64-bit copy opencv_ffmpeg*versionnumber*_64.dll (or copy both, it doesn't hurt). Paste it into the *ANACONDA_PATH* base folder (for example C:\Users\YourName\Anaconda2).
	i) To check the FFMPEG install, try running Gait Analyzer - if it returns an error that says that you should check your OpenCV installation, that means the FFMPEG component isn't working. See troubleshooting FFMPEG.

4. Make Python scripts run with a double click: Only possible on Windows (I think)
	a) Go tO Control Panel->Default Programs->Associate a file type with a program
	b) Find the .py file type, change it to associate with python.



TROUBLESHOOTING:
The final component of OpenCV installation, transferring the ffmpeg files, is finicky and I have read about different things working for different people, even on the same operating system. I have a few suggestions for troubleshooting, follow them IN ORDER:

1. Make sure you actually copied the files frp, 2(h) to the Anaconda2 folder.

2. Make sure that Anaconda2 folder is in the system path. Go to Control Panel->System->Advanced System Settings. In the "Advanced" tab click on "Environmental Variables". DO NOT CHANGE ANYTHING HERE, THIS CAN REALLY MESS UP YOUR COMPUTER. Under "User variables for *yourname*", look at the values for PATH (you may need to double click to expand them). One of its values should be "C:\Users\YourName\Anaconda2\", or whichever equivalent directory you copied the .dll files into.
	If it isn't, and there's a different Anaconda folder there (for example C:\Users\YourName\Anaconda2\Lib, or a folder in a different location), you probably did something strange to the Anaconda installation, but it may be fine. Try copying the .dll files from step h into the folder specified in the PATH variable.
	If there is no Anaconda folder there, double check that you're looking at the right thing - there are many resources online for looking at your system path folders. As far as I know it is impossible to not have an Anaconda folder in the path but still have Anaconda work, so you should find it eventually.

3. Check that the .dll files from 2(h) have the correct name. If they are named opencv_ffmpeg.dll or opencv_ffmpeg_64.dll instead of opencv_ffmpeg*versionnumber*_64.dll (for example opencv_ffmpeg310_64.dll), they may not work. Change the names of the two .dll files in the Anaconda2 folder to the correct format. To find your opencv version number, follow step 2(i), and then type those numbers into the file name after ffmpeg (remove the three periods).

4. If the .dll files are properly copied, have the right names, and the folder they're in is the system path, you may need to install FFMPEG. I have not had to do this, but others have done it as part of installing OpenCV. You should look for resources online, I have provided one link below.
https://gist.github.com/Atlas7/1fae0ad835586278bc0a#file-how-to-install-opencv-python-package-to-anaconda-windows-md