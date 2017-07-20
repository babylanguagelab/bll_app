-------- Project: CDSAnnotator.py --------

This is an application for annotating the descriptive aspects of child-directed speech. It takes day-long LENA recordings that have previously been made into conversational blocks (see How to Make Blocks below) and allows researches to code short 1-2 second segments of these blocks for information on the child-directed speech in those segments. The goal is to provide researchers with an annotation tool that they can use or modify for their specific research questions.

-------- Getting Started --------

Prerequisites:
This application runs on Python 2.7 and requires PyAudio and ffmpeg.
You can find out what version of Python your computer has by opening the terminal (Mac or Linux) or command prompt (Windows) and typing 'python' > enter.
You can get the latest version of Python from https://www.python.org/downloads/ (make sure that version 2.7 is insatlled)
Install PyAudio from https://people.csail.mit.edu/hubert/pyaudio/
Install ffmpeg from https://ffmpeg.org/

Initial Set-up:
Once you have all these programs on your computer, you will need to set up your project directory. Name this directory something useful, like "CDS Annotation Project". 
Inside this directory, you will need several sub-directories:
'input' --> should contain NO MORE THAN TEN folders labelled with unique participant codes. Each of these folders should contain the corresponding participant's .wav and .cha files provided by LENA.
'output' --> when you make blocks, they will appear here in folders labelled with their participant codes.
'backups' --> a backup of all the labelled data is saved here.
'labelled_data' --> This is where the data will be saved, once it is labelled.
You will also need several python programs:
CDSAnnotator5.0.py --> this is the main app.
makeblocks.py --> a program that takes the files in the input directory, and makes conversational blocks, which are saved in the output folder.
utils.py --> contains some methods required by CDSAnnotator.py

How to Make Blocks:
The CDSAnnotator works with conversational blocks that have been cut into separate segments, and lets you code information about these segments. But first, you need to take the information provided by LENA in .cha files, and divide the corresponding .wav recording into blocks that contain FAN, MAN, and CHN speech segments.
To make the blocks, find a .wav recording and the corresponfing .cha file for a participant. Make a new folder for this participant and insert both files there. Then, put the participant's folder into the 'input' sub-directory in your project directory. You can have up to 10 participant folders in the 'input' directory at once (too many participants at once will take a very long time for the make blocks program to process, or possibly make the program crash, depending on your computer).
Next, open CDSAnnotator5.0.py and in the dropdown menu, select 'Make blocks'. The program will start processing the data. Once it is done, a message will appear and the recordings will show up in the 'Recordings' listbox. It might take about 20 minutes to process 10 recordings, so budget your time accordingly. Participant folders containing the finished blocks will appear in the 'output' folder.
Note: once a participant's recordings have appeared as blocks in the 'output' folder, you can remove that participant's .wav and .cha files from the 'input' folder and make more blocks with new participants without loosing the blocks that you have already made.

-------- Deployment --------

To Start the App:
Double-click on 'CDSAnnotator5.0.py' in your project directory.
Alternately, you can open a terminal (Mac and Linux) or command prompt (Windows) window at the directory and type 'python CDSAnnotator5.0.py' > enter.

To Use the App:
Enter your name in the '-->CoderName<--' box in the top left corner, then click the 'Load' button to load your data. Select the recording you want to work on from the 'Recordings' listbox. A list of the blocks for that recording will appear in the 'Blocks' listbox. When you click on a block, a list of the segments in the block will appear in the 'Segments' listbox. You can either listen to the whole block, or you can select individual segments to listen to them, and to annotate them according to the specificatinos in the Annotation Manual. Be sure to submit each label by clicking the 'Submit' button, or by typing CTRL+s, before moving on to the next segment. Labelled segments will appear greyed-out in the 'Segments' listbox.

Exit, Save, and Export:
Be sure to save the data before you leave! If you have unsaved data and you clicked the 'X' button, a warning window will appear asking if you want to save the data before leaving. You can also save the data by selecting 'save the data' from the menu.
You can export the saved data by selecting 'export as csv' from the menu. This will lead you to a window where you can name the csv file and save it wherever you like. You can export, alter, and delete these csv files as you like - they will not alter the underlying data saved in the program.

-------- Authors --------

CDSAnnotator.py (and it's subsequent versions) were written by Sarah MacEwan

-------- Acknowledgments --------

Many thanks to Roman Belenya for providing the code for convolabel.py, from which CDSAnnotator.py grew. Also for all the help de-bugging :)

-------- Questions? --------
 Email Sarah at smacewan@mts.net