# Description:
# Date: 2016-01-17

import logging as lg
import openpyxl
import ConfigParser as mParser


class CommentProcessor(object):
    def __init__(self, database):
        # excel content info, includes: head -> table headers,
        # body -> table content, column -> set of column options
        # body structure: [child_ID] => {head:[values]}
        self.content = {}
        self.config = {'DB': database, 'filename': ""}
        self.switch = {} # output info
        self.output = []

    def open_comment_file(self):
        lg.debug("open comment file: " + self.config['filename'])
        workbook = openpyxl.load_workbook(self.config['filename'])
        sheet = workbook.get_sheet_by_name("Special Cases")
        excel_head = [x.value for x in sheet.rows[0] if x.value is not None]

        # get content body list
        # for each record is a dictionary
        excel_body = []
        for rnum in range(2, sheet.max_row):
            # sometimes the max_row number is not accurate, so I add an addition check
            if sheet.cell(row=rnum, column=2).value is None:
                break

            if sheet.cell(row=rnum, column=1).value is not None:
                child_dict = {}
                for i, item in enumerate(excel_head):
                    if sheet.cell(row=rnum, column=i+1).value is None:
                        child_dict[item] = [" "]
                    else:
                        child_dict[item] = [sheet.cell(row=rnum, column=i+1).value]
                excel_body.append(child_dict)
            else:
                for i, item in enumerate(excel_head):
                    if sheet.cell(row=rnum, column=i+1).value is not None:
                        excel_body[-1][item].append(sheet.cell(row=rnum,
                                                               column=i+1).value)

        # get option dictionary
        # key: item name
        # value: item options
        excel_column = {}
        for item in excel_body:
            for name in excel_head:
                if name not in excel_column:
                    excel_column[name] = set(item[name])
                else:
                    excel_column[name] = excel_column[name].union(set(item[name]))

        self.content["head"] = excel_head
        self.content["body"] = excel_body
        self.content["column"] = excel_column

        self.set_configs()

    def get_options(self, item):
        return self.content["column"][item]

    # init configurations
    def set_configs(self):
        for item in self.content["head"]:
            self.switch[item] = [True, self.content["column"][item]]

    # update output options
    def update_switch(self, item, enable, content="all", reverse=False):

        original = self.content["column"][item]

        if enable is False:
            self.switch[item] = [False, original]
            return

        if content is "all":
            self.switch[item] = [True, original]
            return

        if reverse:
            self.switch[item] = [True, set(original) - set(content)]
        else:
            self.switch[item] = [True, set(content)]

    # process switches and find its files to remove
    def run(self):
        remove_its = []

        # match information in child
        for item in self.content["head"]:
            if self.switch[item][0]:
                nfilter = self.content["column"][item] - self.switch[item][1]
                for child in self.content["body"]:
                    for info in child[item]:
                        if set(info).issubset(nfilter):
                            remove_its.append(child["ITS File"])

        # record the filtered child information
        for child in self.content["body"]:
            # get the number of rows for this child
            max_len = len(child["ITS File"])

            for i in range(max_len):
                if child["ITS File"][i] not in remove_its:
                    new_output = []
                    for item in self.content["head"]:
                        if len(child[item]) <= i:
                            new_output.append(" ")
                            continue

                        if self.switch[item][0] is True:
                            if len(child[item][i]) == 0:
                                new_output.append(" ")
                            else:
                                new_output.append(child[item][i])

                    self.output.append(new_output)

    def save_DB(self):
        lg.debug("save DB")

    def save_file(self, filename):
        results = []
        head = []
        for item in self.content["head"]:
            if self.switch[item][0] is True:
                head += [item]

        results.append(head)

        for i in self.output:
            results.append(i)

        mParser.excel_writer(filename, 'Special Cases', results)
