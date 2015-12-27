# ADEX summary generator
# grub required information from ADEX files
# author: zhangh15@myumanitoba.com

import ConfigParser as mParser
from database import Database
import logging as lg
import glob
import os

HEAD_TYPE_LIST = {'File_Name'          :'TEXT',
                  'Number_Recordings'  :'INT',
                  'File_Hours'         :'REAL',
                  'Child_ChildID'      :'TEXT',
                  'Child_Age'          :'INT',
                  'Child_Gender'       :'TEXT',
                  'AWC'                :'INT',
                  'Turn_Count'         :'INT',
                  'Child_Voc_Duration' :'INT',
                  'FAN_Word_Count'     :'INT',
                  'FAN'                :'REAL',
                  'MAN_Word_Count'     :'INT',
                  'MAN'                :'REAL',
                  'CXN'                :'REAL',
                  'OLN'                :'REAL',
                  'TVN'                :'REAL',
                  'NON'                :'REAL',
                  'SIL'                :'REAL',
                  'Audio_Duration'     :'REAL'}

HEAD_NAME_LIST = ['File_Name', 'Number_Recordings', 'File_Hours',
                  'Child_ChildID', 'Child_Age', 'Child_Gender',
                  'AWC', 'Turn_Count', 'Child_Voc_Duration',
                  'FAN_Word_Count', 'FAN', 'MAN_Word_Count', 'MAN',
                  'CXN', 'OLN', 'TVN', 'NON', 'SIL', 'Audio_Duration']


# read ADEX csv files with required columns only
# then save these columns to DB
class ADEXProcessor:
    def __init__(self, adex_config, db_name):
        tmp = list(zip(HEAD_NAME_LIST, adex_config))
        self.head = [x[0] for x in tmp if x[1] is True]
        self.content = []
        self.child_id = ""
        self.db = Database(db_name+".sqlite3")

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
            if counter >= 1800:
                break

        # items start through final_end
        self.content = self.content[final_start:final_end+1]

    def getChildID(self):
        index = self.head.index('Child_ChildID')
        self.child_id = self.content[0][index]

    #def remove_naptime(self, list_of_naptime_pair)
    #for start,end in list_of_naptime_pair
    #del self.content[start, end]

    def saveToDB(self):
        if (len(self.child_id) == 0):
            self.getChildID()
        sql = ""
        # check the existence of childID
        if self.db.select('sqlite_master',
                            ['name'],
                            where="type='table' AND name='"+self.child_id +"'") is None:
            lg.debug(self.child_id + " is not in database")
            param = [i + ' ' + HEAD_TYPE_LIST[i] for i in self.head]
            param.insert(0, "ID INTEGER PRIMARY KEY AUTOINCREMENT")
            param = ",".join(param)
            sql = "CREATE TABLE " + self.child_id + "(" + param + ")"
            self.db.execute_script(sql)

        # insert content into DB
        self.db.insert_table(self.child_id, self.head, self.content)

    def getHEADNAMELIST(self):
        return HEAD_NAME_LIST

    def getAverage(self, table, column):
        sql = "SELECT AVG(%s) from %s " %(table, column)
        return self.db.execute_script()

    def run(self, filename):
        self.readCSV(filename)
        self.remove_5mins()
        self.saveToDB()


# init_debug()
# pro = ADEXProcessor(['AWC', 'Audio_Duration'], "test")
# pro.readCSV("C001A_20090630.csv")
# pro.remove_5mins()
