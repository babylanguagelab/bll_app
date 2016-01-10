import openpyxl
import logging as lg
from debug import init_debug

COMMENT_SHEET = "/home/zhangh15/Dev/bll_app/src/app/summary_generator/LENASpreadsheet.xlsx"

COMMENT_LIST = [
    'Study Number',
    'Recording',
    'Recording Dates',
    'Recording Type',
    'ITS File',
    'Recording Notes/Errors?',
    'Note in File',
    'Language Other than English',
    'Child Sick',
    'Short Recording',
    'Pause in Recording',
    'Unusual Behaviour',
    'LENA Device off Child',
    'Paired Recording (home AND homedaycare/daycare)',
    'Child Development Concern',
    'Clock Drift']


class CommentProcessor:
    def __init__(self):
        self.heads = []
        self.content = []

    def saveResults(self, filename):
        newWB = openpyxl.Workbook()
        newWB.create_sheet(title='Special Cases')
        sheet = newWB.get_sheet_by_name("Special Cases")

        for row_index in range(len(self.content)):
            for col_index in range(len(self.content[row_index])):
                sheet.cell(row=row_index+1, column=col_index+1).value = self.content[row_index][col_index]

        newWB.save(filename)


    def openCommentFile(self, filename):
        wb = openpyxl.load_workbook(filename)
        self.sheet = wb.get_sheet_by_name("Special Cases")
        self.heads = [x.value for x in self.sheet.rows[0]]

    def setSwitches(self, switch):
        self.switch = [(x, True) for x in self.heads]

    # process switches and filter content
    def run(self):
        switch_dict = dict(self.switch)
        new_heads = []

        for index in range(len(self.heads)):
            if switch_dict[self.heads[index]]:
                new_heads.append(index)

        for row_index in range(self.sheet.max_row):
            line = []
            for column_index in new_heads:
                line.append(self.sheet.cell(row=row_index+1, column=column_index+1).value)
            self.content.append(line)


init_debug()
mProcess = CommentProcessor()
mProcess.openCommentFile(COMMENT_SHEET)
mProcess.setSwitches([1])
mProcess.run()
mProcess.saveResults('result.xlsx')
