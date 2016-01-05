# ADEX summary generator
# grub required information from ADEX files
# author: zhangh15@myumanitoba.com

import logging as lg
import glob
import os
import time
import ConfigParser as mParser
from database import Database

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
                  'Clock_Time_TZAdj'   :'TEXT',
                  'Audio_Duration'     :'REAL'}

HEAD_NAME_LIST = ['File_Name', 'Number_Recordings', 'File_Hours',
                  'Child_ChildID', 'Child_Age', 'Child_Gender',
                  'AWC', 'Turn_Count', 'Child_Voc_Duration',
                  'FAN_Word_Count', 'FAN', 'MAN_Word_Count', 'MAN',
                  'CXN', 'OLN', 'TVN', 'NON', 'SIL', 'Clock_Time_TZAdj',
                  'Audio_Duration']

class ADEXControl:
    def __init__(self):
        self.db = ""
        self.useNaptime = False
        self.remove5mins = False
        self.switches = []
        # child_ID:(date, time_start, time_end)
        self.naptime = {}

    def set_db_name(self, name):
        self.db = name

    def set_use_naptime(self, ifuse):
        self.useNaptime = ifuse

    def set_remove_5mins(self, ifuse):
        self.remove5mins = ifuse

    def set_switches(self, switches):
        self.switches = switches

    def read_naptime(self):
        db_name = "/home/hao/Develop/projects/bll/bll_app/test/bll_db.db"
        naptime_db = Database(db_name)
        naptime_list = naptime_db.select('naptime', ['child_cd', 'start', 'end'])
        naptime_db.close()

        for entry in naptime_list:
            child_id = entry[0].split('_')[0].lower()
            date = entry[0].split('_')[1]
            if child_id not in self.naptime:
                self.naptime[child_id] = [(date, entry[1], entry[2])]
            else:
                self.naptime[child_id].append((date, entry[1], entry[2]))

    def dump(self):
        return [True, self.useNaptime, self.remove5mins, self.switches]

# read ADEX csv files with required columns only
# then save these columns to DB
class ADEXProcessor:
    def __init__(self, adex_control):
        self.control = adex_control
        tmp = list(zip(HEAD_NAME_LIST, self.control.switches))
        self.head = [x[0] for x in tmp if x[1] is True]
        self.content = []
        self.start_time = 0
        self.child_id = ""
        self.db = Database(self.control.db + ".sqlite3")

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
        lg.debug("removing 5 minutes...")
        self.content = self.content[final_start:final_end+1]

    def getChildID(self):
        index = self.head.index('Child_ChildID')
        self.child_id = self.content[0][index].lower()

    def getStartTime(self):
        index = self.head.index('Clock_Time_TZAdj')
        self.start_time = self.timeToSecond(self.content[0][index])

    # convert time string to seconds
    def timeToSecond(self, string):
        # string = 6/10/2009 8:37:45
        return time.mktime(time.strptime(string, '%m/%d/%Y %H:%M:%S'))

    # convert seconds to human readable string
    def SecondTotime(self, second):
        return time.ctime(second)

    def check_naptime(self):
        if self.child_id in self.control.naptime:
            date = time.strftime('%Y%m%d', time.localtime(self.start_time))
            for i in self.control.naptime[self.child_id]:
                lg.debug("removing naptime...")
                if i[0] == date:
                    self.remove_time(self.start_time + i[1],
                                     self.start_time + i[2])

    def remove_time(self, start_time, end_time):
        start = 0
        end = len(self.content)
        count = 0
        index = self.head.index('Clock_Time_TZAdj')

        for row in self.content:
            time = self.timeToSecond(row[index])

            if (time >= start_time) and (start == 0):
                start = count
            if (time > end_time) and (end == len(self.content)):
                end = count

            count += 1

        del self.content[start:end]

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

    def getAverage(self, table, column):
        sql = "SELECT AVG(%s) from %s " %(table, column)
        return self.db.execute_script()

    def run(self, filename):
        self.readCSV(filename)
        self.getChildID()
        lg.debug("Processing: " + self.child_id)
        self.getStartTime()

        if (self.control.useNaptime):
            self.check_naptime()

        if (self.control.remove5mins):
            self.remove_5mins()

        self.saveToDB()
