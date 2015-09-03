## Intro:
A python script that scans all LENA ITS files in the current folder and remove identifying information .

## Usage:
Put the main.py in a folder that contains ITS files and run this script.
It will generate a new folder named "output" in the current location with modified ITS files. It will also generate an overview spreadsheet in the output folder named "overview.csv". All changes to ITS files will be showed in the overview. If an item is deleted, it will only show this item. If an item is changed with a dummy value, it will show the original value and new value. 

## Configuration:
Based on different purposes, this script is designed to be configurable. At the beginning of this script, you will see something like this:
CONF_DICT = {
    "Serial Number": [2, "0000"],
    "Gender": [0, -1],
    "Algorithm Age": [0, -1],
    "Child ID": [2, "0000"],
    "Child Key": [2, "0000000000000000"],
    "Enroll Date": [1, -1],
    "DOB": [2, "2000-01-01"],
    "Time Zone": [1, -1],
    "UTC Time": [1, -1],
    "Clock Time": [2, "0"]
}
Before colon, it is domain items in ITS file. After colon, it is configuration for this domain item in square bracket.
0 stands for no change.
1 stands for delete.
2 stands for use dummy value followed after comma.

