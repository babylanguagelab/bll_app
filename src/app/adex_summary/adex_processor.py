# ADEX summary generator
# author: zhangh15@myumanitoba.com

import ConfigParser as mParser
from debug import init_debug
from database import Database
import logging as lg
import glob
import os

# read ADEX csv files with required columns only
# then save these columns to DB
class ADEXProcessor:
    def __init__(self):
        self.head = ['File_Name',
                     'Number_Recordings',
                     'File_Hours',
                     'Child_ChildID',
                     'Child_Age',
                     'Child_Gender',
                     'AWC',
                     'Turn_Count',
                     'Child_Voc_Duration',
                     'FAN_Word_Count',
                     'FAN',
                     'MAN_Word_Count',
                     'MAN',
                     'CXN',
                     'OLN',
                     'TVN',
                     'NON',
                     'SIL',
                     'Audio_Duration']
        self.content = []
        self.child_id = ""
        self.db = Database('adex.db')

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
        if (len(self.child_id) == 0):
            self.getChildID()
        sql = ""
        # check existence of table
        if self.db.select('sqlite_master',
                            ['name'],
                            where="type='table' AND name='"+self.child_id +"'") is None:
            lg.debug(self.child_id + " is not in database")
            typeList = ['TEXT',
                        'INT',
                        'REAL',
                        'TEXT',
                        'INT',
                        'TEXT',
                        'INT',
                        'INT',
                        'INT',
                        'INT',
                        'REAL',
                        'INT',
                        'REAL',
                        'REAL',
                        'REAL',
                        'REAL',
                        'REAL',
                        'REAL',
                        'REAL']

            param = map(lambda x,y: x + ' ' + y, self.head, typeList)
            param.insert(0, "ID INTEGER PRIMARY KEY AUTOINCREMENT")
            param = ",".join(param)
            sql = "CREATE TABLE " + self.child_id + "(" + param + ")"
            self.db.execute_script(sql)

        # insert content into DB
        self.db.insert_table(self.child_id, self.head, self.content)

    def getAverage(self, table, column):
        sql = "SELECT AVG(%s) from %s " %(table, column)
        return self.db.execute_script()


class Test:
    def __init__(self):
        init_debug()
        self.mADEX = ADEXProcessor()

    def run(self):
        for name in glob.glob('*.csv'):
            self.mADEX.readCSV(name)
            self.mADEX.remove_5mins()
            self.mADEX.saveToDB()

mTest = Test()
mTest.run()
