# ADEX summary generator
# author: unioah@gmail.com

import ConfigParser as mParser
from debug import my_print as deg
import glob


# def combine
class ADEX_processor:
    def __init__(self):
        self.content = []
        self.filename = []
        self.child_ID = ""
        self.child_age = ""
        self.child_gender = ""
        self.ADEX_head = []
        self.items = {'AWC': 0, 'Turn_Count': 0, 'Child_Voc_Duration': 0,
                      'CHN': 0, 'FAN': 0, 'MAN': 0, 'CXN': 0, 'OLN': 0,
                      'TVN': 0, 'NON': 0, 'SIL': 0, 'Audio_Duration': 0}

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

    def filter_cols(self):
        self.filename = self.content[0][1]
        self.child_ID = self.content[0][4]
        self.child_age = self.content[0][5]
        self.child_gender = self.content[0][6]
        new_content = []

        new_content.append([self.filename,
                           self.child_ID,
                           self.child_age,
                           self.child_gender])

        # write new head info
        new_head = []
        for col in range(7, len(self.ADEX_head)):
            if self.ADEX_head[col] in self.items:
                new_head.append(self.ADEX_head[col])

        # take any columns in self.items list
        for row in self.content:
            new_row = []
            for col in range(7, len(row)):
                if self.ADEX_head[col] in self.items:
                    new_row.append(row[col])

            new_content.append(new_row)

        self.content = new_content
        self.ADEX_head = new_head

    def run(self):
        self.remove_5mins()
        self.cal_average()
        self.filter_cols()


class driver:
    def __init__(self):
        self.mADEX = ADEX_processor()

    def run(self):
        for name in glob.glob('*.csv'):
            content = mParser.csv_reader(name)
            self.mADEX.ADEX_head = content[0]
            self.mADEX.content = content[1:]

        self.mADEX.run()
        mParser.csv_writer('/tmp/tmp.csv', self.mADEX.content)


if __name__ == '__main__':
    mDriver = driver()
    mDriver.run()
