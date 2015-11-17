# ADEX summary generator
# author: unioah@gmail.com

import ConfigParser as mParser
from debug import my_print as deg
from cusList import del_list_by_indices
import glob
import os

# read ADEX csv files to filter out required columns
# then save the columns as intermediate results
class ADEXProcessor:
    def __init__(self):
        self.head = ['File_Name', 'Child_ChildID', 'Child_Gender',
                          'AWC', 'Turn_Count', 'Child_Voc_Duration',
                          'CHN', 'FAN', 'MAN', 'CXN', 'OLN', 'TVN', 'NON', 'SIL', 'Audio_Duration']
        self.content = {}
        self.length = 0
        for i in self.head:
            self.content[i] = []

    def get_key(self, row, key):
        key_index = self.ADEX_head.index(key)
        return self.content[row][key_index]

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
            deg(i, self.items[i])

    # remove unnecessary columns
    def filter_cols(self):
        new_head = self.child_info + self.child_score
        deg(new_head)
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

    def parse(self, csv_file):
        content = mParser.csv_reader(csv_file)
        old_head = content[0]

        for row in range(1, len(content)):
            for col in range(0, len(row)):
                key = old_head[col]
                if key in self.content:
                    self.content[key].append(row[col])

        self.length = len(content)

    def dump(self):
        filename = "childID"
        result = []

        if not os.path.exists(filename):
            result.append(self.head)

        for i in range(self.length):
            new_row = []
            for j in self.head:
                new_row.append(self.content[j][i])
            result.append(new_row)

        mParser.csv_writer(filename, result)


class Test:
    def __init__(self):
        self.mADEX = ADEXProcessor()

    def run(self):
        for name in glob.glob('*.csv'):
            self.mADEX.parse(name)

        # result = self.mADEX.dump()
        # mParser.csv_writer('/tmp/tmp.csv', result)


if __name__ == '__main__':
    mTest = Test()
    mTest.run()
