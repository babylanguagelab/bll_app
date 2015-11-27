# ADEX summary generator
# author: zhangh15@myumanitoba.com

import ConfigParser as mParser
from cusList import del_list_by_indices
from debug import init_debug
import logging as lg
import glob
import os

# read ADEX csv files to filter out required columns
# then save the columns as intermediate results
class ADEXProcessor:
    def __init__(self):
        self.head = ['Index', 'Audio_Duration']
        self.content = []

    def readCSV(self, csv_file):
       self.content = mParser.csv_dict_reader(csv_file, self.head)

    def remove_5mins(self):
        final_start = 0
        final_end = len(self.content) - 1
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
            lg.debug("%s/%s\n" %(counter, final_end))
            if counter >= 1800:
                break

        self.content = self.content[final_start+1:final_end-1]

    def cal_average(self):
        for row in self.content:
            for col in range(0, len(row)):
                key = self.ADEX_head[col]
                if key in self.items:
                    self.items[key] += float(row[col])

        for i in self.items:
            tmp = self.items[i] / len(self.content)
            # keep only two digits
            self.items[i] = float("{0:.2f}".format(tmp))

class Test:
    def __init__(self):
        self.mADEX = ADEXProcessor()
        init_debug()

    def run(self):
        for name in glob.glob('*.csv'):
            self.mADEX.readCSV(name)
            self.mADEX.remove_5mins()
            lg.debug(self.mADEX.content)
        # result = self.mADEX.dump()
        # mParser.csv_writer('/tmp/tmp.csv', result)

mTest = Test()
mTest.run()
