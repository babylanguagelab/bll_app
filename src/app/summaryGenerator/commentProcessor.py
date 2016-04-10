# Description:
# Author: zhangh15@myumanitoba.ca
# Date: 2016-01-17

import logging as lg
import openpyxl
import ConfigParser as mParser

COMMENT_OPTIONS = (("Recording Type" ,              ("Daycare", "Home", "Home Daycare")),
                   ("ITS File" ,                    ()),
                   ("Recording Notes/Errors?" ,     ("No", "Yes")),
                   ("Note in File" ,                ("None")),
                   ("Paired Recording" ,            ("No")),
                   ("Language Other than English" , ("English", "French")),
                   ("Child Sick" ,                  ("No", "Yes")),
                   ("Child Development Concern" ,   ("No", "Yes")),
                   ("Withdrew from Study" ,         ("No", "Yes")))

COMMENT_OPTIONS_DICT = dict(COMMENT_OPTIONS)


class CommentProcessor(object):
    def __init__(self, database):
        self.content = {}
        self.heads = []

        self.config = {'DB': database, 'filename': ""}

        # 0 for no, 1 for default, 2 for second, -1 for all
        self.switches = dict([[x[0], [True, 1]] for x in COMMENT_OPTIONS])

    def open_comment_file(self):
        lg.debug("open comment file: " + self.config['filename'])
        workbook = openpyxl.load_workbook(self.config['filename'])
        sheet = workbook.get_sheet_by_name("Special Cases")
        self.heads = [x.value for x in sheet.rows[0] if x.value is not None]

        # if self.config['DB'].select('sqlite_master', ['name'],
        #                             where="type='table' AND name='comment_summary'") is None:

        #     param = self.output[0]
        #     #param.insert(0, "ID INTEGER PRIMARY KEY AUTOINCREMENT")
        #     param = ",".join(param)
        #     sql = "CREATE TABLE ADEX_summary" + "(" + param + ",PRIMARY KEY (ChildID)" + ")"
        #     self.config['DB'].execute_script(sql)

        child_id = ""
        for rnum in range(2, sheet.max_row):
            if sheet.cell(row=rnum, column=1).value is not None:
                child_id = sheet.cell(row=rnum, column=1).value
                self.content[child_id] = {}

            content_dict = {}
            for i, item in enumerate(self.heads):
                content_dict[item] = sheet.cell(row=rnum, column=i+1).value

            ifilename = sheet.cell(row=rnum, column=3).value
            if ifilename is not None:
                self.content[child_id][ifilename] = content_dict

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
#mCP = CommentProcessor("test")
#mCP.config['filename'] = "/tmp/test/test.xlsx"
#mCP.open_comment_file()
#options = mCP.get_options()
#print(options["Child Sick"])
