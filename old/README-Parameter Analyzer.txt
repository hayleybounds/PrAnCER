This is a description of how to run the Gait Analyzer 2 program.

Written by Hayley Bounds on 5/16/17.

Make sure you have installed Anaconda according to the set up instructions.

NAMING CONVENTION:
In order to use this script, the files must be in a certain organization and named in certain ways.
Videos must be named "AnimalID TrialNumber *whatever you want*" The program is looking for spaces, so make sure that there are no double spaces or it will not work.

Folders containing videos for one group of runs (typically one day) should be named in the format "Word Number Word Number *whatever you want*". The standard for the CSF project is "Week X Day X Date" to indicate Weeks post surgery, whether it was the first or second day of that week, and then the date. Again, be careful about spacing.

These folders containing videos must then be in one larger folder, termed the cohort folder because there is typically a one per cohort. This folder has no naming restrictions. If you don't actually want to analyze them in groups, you can temporarily put the folder of videos into its own new folder then move it out following analysis, but it must be inside of another folder when this program is run.

RUNNING THE PROGRAM:
1. Go to R:\CLPS_Burwell_Lab\Lab Projects\GAIT Analysis Project\Program. Double click "Parameter Analyzer" to run it. 

2. It will open a command prompt window titled something like C:\Users\yourname\Anaconda2\python.exe and a menu screen (this may take a second). Choose the following options (all except choose cohort folder can be left as their default):
	Number of Hind Prints to Analyze - the number of hind prints to include in analysis. Must be at least 4. 
	Number of Experimental Animals - how many animals in the experimental group there are. May be left at 0, then all animals will be labelled as 'c' for control.
	Choose Exp Numbers - after telling the program how many animals there are in the experimental group, click this to open a separate window that will allow you to input one rat id per box. Input them as "16-075" or however you specified them in the videos. Do not add any spaces. When you've added them all, press "set" then close the window using the x at the top right.
	Choose Cohort Folder - Pick the folder containing all the folders with the videos (see above).

3. Press continue to run the program. The menu screen will stop responding, ignore that. And watch the command prompt window.

4. When the command prompt window says "press enter to exit" the program has finished. However, you should scroll through the printed text and heed any warnings. The program prints which folder its on in the "Week x and day x" format, and then prints all errors for videos in that folder below that. After taking note of the warnings, you can press enter to exit.

OUTPUTS:
In each folder of videos, it will put a file named "*folder name* group analysis.csv". If such a file already exists, it will create the file "*folder name* group analysis (2).csv" or however many numbers are necessary until the filename isn't taken. This contains parameters per run for all runs in that folder.

It will also output a file for the cohort folder that is the combination of all these group analysis files for all the folders in the cohort folder. This will be titled "*cohort folder name* group analysis.csv" or "*cohort folder name* group analysis (*number*).csv". 

COLUMNS OF THE OUTPUT: 
The first columns (filename, week, day, group, rat id, and trial) are self explanatory and based on the naming of the video/folder and the input to experimental numbers.

Parameter Columns: Unless otherwise specified, these are in pixel units and calculated as the mean for the first x hind prints of the run, with x being the user-specified number of prints to analyze

Base of Support - y width between consecutive contralateral hind paws
Stride Length - absolute distance
Step Length - x distance only, so less accurate than stride.
Stance Duration - unit is frames.
Run Speed - The number of frames it took for the rat to cross the first 1000 pixels of the apparatus. Takes into account both front and hind paws and will take into account more than the specified number to analyze. Unit is just frames, without distance. So the speed is misleading. We don't really use this right now.
'Average of Maximum Areas' - units are pixels ^ 2. 
Stride Speed X Stride - the speed the animal travelled over a stride for the first, second and third strides. Third stride data may be missing because not all runs have more than two strides. It will calculate this for the first 5 hind prints (thus getting three strides) no matter what the user inputs. Unit is pixels/frame
'Right/Left Limb Stance to Swing Ratio' - technically mean for a run, but if only four paws are supposed to be analyzed, it can only be calculate for the first right hind paw. It's stance duration/swing duration. Unit is frames. Calculated separately for left and right limbs so you can check for oddities, but I average the two when I do statistical analysis.
'Right/Left Limb Duty Factor' - stance duration/(stance duration+swing duration).tTechnically mean for a run, but if only four paws are supposed to be analyzed, it can only be calculate for the first right hind paw. Calculated separately for left and right limbs so you can check for oddities, but I average the two when I do statistical analysis.
'Mean Absolute/X/Y Interlimb Distance' - interlimb distance ignores the user-specified number of prints to look at because it should be mostly speed invariant. It does not rely on correct left/right classification of front paws because it does some complicated distance matching to try to find pairs without thinking about left and right. Accuracy suffers somewhat because of this, but it makes up for it by including more values (I think). Absolute means that the distance was calculated as the pythagorean distance, X means only the change in X is taken, and Y means only change in Y is taken.
'CV of Absolute/X/Y Interlimb Distance' - Same as above, except it's the coefficient of variation for a run.
'SD of Absolute/X/Y Interlimb Distance' - same as above, except it's the standard deviation for a run.

NOTE: Old versions output different columns than this. You can easily rerun the data to get the new columns.
