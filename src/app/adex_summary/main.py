# adex summary generator
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
        self.items = ['AWC', 'Turn_Count', 'Child_Voc_Duration', 'CHN',
                      'FAN', 'MAN', 'CXN', 'OLN', 'TVN', 'NON', 'SIL',
                      'Audio_Duration']

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

        # add extra line in order add up to 1800 sec
        end_lines -= 1
        del self.content[end_lines:]

    def filter(self):
        self.filename = self.content[0][1]
        self.child_ID = self.content[0][4]
        self.child_age = self.content[0][5]
        self.child_gender = self.content[0][6]

        # remove any columns not in self.items list
        for row in self.content:
            k = 0
            for col in range(7, len(row)):
                deg(len(row))
                if self.ADEX_head[col] != self.items[k]:
                    del row[col]
                else:
                    k += 1

            # remove first 6 columns
            del row[:7]

    def run(self):
        self.remove_5mins()
        self.filter()


class driver:
    def __init__(self):
        self.mADEX = ADEX_processor()

    def run(self):
        for name in glob.glob('*.csv'):
            content = mParser.csv_reader(name)
            self.mADEX.ADEX_head = content[0]
            self.mADEX.content = content[1:]
        self.mADEX.run()
        deg(self.mADEX.content)


if __name__ == '__main__':
    mDriver = driver()
    mDriver.run()
