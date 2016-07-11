Author: zhangh15@myumanitoba.ca
Date: 2016-01-17
-------

# Introduction (from Elizabeth):
ADEX Summary Spreadsheet:
The most current set of spreadsheets is saved here:
Experimental Data\Daycare Study\ADEX Output\ADEXAnalysis
-They are saved in folders for the appropriate childcare setting
* The most recent example of this is called SummarySpreadsheetJuly2014 and is saved here:
C:\Experimental Data\Daycare Study\ADEX Output\Elizabeth\June 2014 ADEX Analysis

## Instruction (updated with Dr. Melanie):
- 1. Remove 1st and last 30 minutes of data with Audio_Duration column. At least 1800 seconds, so 6-7 rows usually, sometimes you have to delete an extra row to get to 1800.
- 2. Filter out naptime using the naptime filter.
  Naptime Database is saved here:
  C:\Experimental Data\Daycare Study\ADEX Output\Elizabeth\2014 AdultChildRatio Project\Naptime Data
- 3. Organize summary spreadsheet into the 3 separate childcare settings
- 4. Pull out Participant code (ex. C001a), age of participant at first recording, and gender into the summary spreadsheet
- 5. Take averages of the following columns for each spreadsheet:
  AWC, Turn_Count, Child_Voc_Duration, FAN_Word_Count, FAN, MAN_Word_Count, MAN, CXN, OLN, TVN, NON, SIL
- 6. Add the averages of these columns from each participant separately, and then get an average per participant. (i.e. add all of the C001a averages together and find an average for C001a, do the same for C001b, etc.)
- 7. Have a column called # of recordings, and have the number of spreadsheets for that participant in that column. (i.e. C001a has 2 spreadsheets, so that number would be 2)

# Progress:
## ADEX Processor: 
- 1. read one CSV file as a list of list. [V] 
- 2. get required columns. [V]
- 3. process filters on data. [V]
- 4. calculate the average. [V]
- 5. put results into database. [V]
- 6. write results into excel. [V]
- 7. get filenames from other processors to exclude.

## Comments Processor: [75%]
- 1. filter required column. [V]
- 2. generate outputs. [V]
- 3. write results into excel. [V]
- 4. save results to database.

## Transcribed data handler [50%]
- 1. load information from csv [V]
- 2. merge with same ID [V]
- 3. save to database.
- 4. save results to excel. [V]

## load/save configuration [30%]
## sync data in database [50%]
