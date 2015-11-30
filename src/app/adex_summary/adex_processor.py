# ADEX summary generator
# author: zhangh15@myumanitoba.com

import ConfigParser as mParser
from cusList import del_list_by_indices
from debug import init_debug
import logging as lg
import glob
import os

# read ADEX csv files with required columns only
# then save these columns to DB
class ADEXProcessor:
    def __init__(self):
        self.head = ['Index', 'Child_ChildID', 'Audio_Duration']
        self.content = []
        self.child_id = ""

    def readCSV(self, csv_file):
       self.content = mParser.csv_dict_reader(csv_file, self.head)

    def remove_5mins(self):
        final_start = 0
        final_end = len(self.content) - 1
        lg.debug(len(self.content))
        counter = 0
        index = self.head.index('Audio_Duration')

        # remove first 1800 sec at the beginning
        for row in self.content:
            value = float(row[index])
            counter += value
            final_start += 1
            if counter >= 1800:
                break

        # remove 1800 sec at the end
        counter = 0
        for x in range(1, len(self.content)):
            value = float(self.content[-x][index])
            counter += value
            final_end -= 1
            if counter >= 1800:
                break

        self.content = self.content[final_start+1:final_end+1]

        def getChildID(self):
            index = self.head.index('Child_ChildID')
            if (self.content):
                self.child_id = self.content[0][index]

        def saveToDB(self):
            sql = ""

        # def getAverage(self, column)
        # def saveResults(self)

class Test:
    def __init__(self):
        self.mADEX = ADEXProcessor()
        init_debug()

    def run(self):
        for name in glob.glob('*.csv'):
            self.mADEX.readCSV(name)
            self.mADEX.remove_5mins()
            lg.debug(self.mADEX.content)

mTest = Test()
mTest.run()
