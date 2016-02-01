# Description:
# Author: zhangh15@myumanitoba.ca
# Date: 2016-01-17

import logging as lg
import openpyxl
import myUtils.ConfigParser as mParser


class commentProcessor(object):
    def __init__(self):
        self.content = {}
        self.heads = []

    def open_comment_file(self, filename):
        wb = openpyxl.load_workbook(filename)
        self.sheet = wb.get_sheet_by_name("Special Cases")
        self.heads = [x.value for x in self.sheet.rows[0] if x.value is not None]

        child_id = ""
        for rnum in range(2, self.sheet.max_row):
            if self.sheet.cell(row=rnum, column=1).value is not None:
                child_id = self.sheet.cell(row=rnum, column=1).value
                self.content[child_id] = {}

            content_dict = {}
            for i, item in enumerate(self.heads):
                content_dict[item] = self.sheet.cell(row=rnum, column=i+1).value

            ITS_file = self.sheet.cell(row=rnum, column=3).value
            if ITS_file is not None:
                self.content[child_id][ITS_file] = content_dict

    def get_options(self):
        option_dict = {}

        for item in self.heads:
            option_dict[item] = self.get_options_from_title(item)

        return option_dict

    def get_options_from_title(self, title):
        CMT_options = []

        if title == "Recording Notes/Errors?" or \
           title == "Child Sick" or \
           title == "Child Development Concern" or \
           title == "Withdrew from Study":
            CMT_options = ["Yes", "No", "Both"]

        elif title == "Language Other than English":
            CMT_options.append("English")
            for key1 in sorted(self.content.keys()):
                for key2 in sorted(self.content[key1].keys()):
                    note = self.content[key1][key2][title]
                    if (note is not None) and (note not in CMT_options):
                        CMT_options.append(note)
            CMT_options.append("All")

        else:
            for key1 in sorted(self.content.keys()):
                for key2 in sorted(self.content[key1].keys()):
                    note = self.content[key1][key2][title]
                    if note is not None and note not in CMT_options:
                        CMT_options.append(note)

        return CMT_options

    #def filter_options_from_title(self, title, options)


    # process switches and filter content
    #def run(self):

    def save_results(self, filename):
        mParser.excel_writer(filename, 'Special Cases', self.content)


# for test
# mCP = commentProcessor()
# mCP.open_comment_file("/home/hao/Develop/projects/bll/bll_app/test/test.xlsx")
# options = mCP.get_options()
# print(options["Recording Notes/Errors?"])
