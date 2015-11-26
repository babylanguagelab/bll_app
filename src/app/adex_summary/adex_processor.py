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
        self.head = []
        self.content = []

    def readCSV(self, csv_file):
        mContent = mParser.csv_reader(csv_file)
        self.head = mContent[0]
        self.content = mContent[1:]

    # remove unnecessary columns
    def filter_cols(self):
        new_head = self.child_info + self.child_score
        # column number -> domain item table
        new_head_dic = {}

        k = 0
        for i in range(0, len(self.ADEX_head)):
            if (self.ADEX_head[i] == new_head[k]):
                new_head_dic[i] = new_head[k]
                k = k + 1

        self.ADEX_head = new_head

        new_content = []

        # take any columns in self.items list
        for row in self.content:
            new_row = []
            for col in range(0, len(row)):
                if col in new_head_dic:
                    new_row.append(row[col])

            new_content.append(new_row)

        self.content = new_content

    def remove_5mins(self):
        start_lines = 0
        end_lines = 0
        content_length = len(self.content)
        counter = 0
        # remove 1800 sec at the begin
        for x in range(content_length):
            counter += float(self.get_key(x, 'Audio_Duration'))
            if counter >= 1800:
                break
            else:
                start_lines += 1

        # add extra line in order add up to 1800 sec
        start_lines += 1
        del self.content[:start_lines]

        content_length = len(self.content)
        counter = 0
        # remove 1800 sec at the end
        for x in range(content_length):
            counter += float(self.get_key(content_length - x - 1,
                                          'Audio_Duration'))
            if counter >= 1800:
                break
            else:
                end_lines -= 1

        # add extra line in order to add up to 1800 sec
        end_lines -= 1
        del self.content[end_lines:]

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

        # result = self.mADEX.dump()
        # mParser.csv_writer('/tmp/tmp.csv', result)


mTest = Test()
mTest.run()
