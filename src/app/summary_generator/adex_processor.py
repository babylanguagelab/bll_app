# ADEX summary generator
# grub required information from ADEX files
# author: zhangh15@myumanitoba.com

import logging as lg
import glob
import os
import time
import ConfigParser as mParser
from database import Database

HEAD_NAME_LIST = [['File_Name'          ,'TEXT'],
                  ['Number_Recordings'  ,'INT'],
                  ['File_Hours'         ,'REAL'],
                  ['Child_ChildID'      ,'TEXT'],
                  ['Child_Age'          ,'INT'],
                  ['Child_Gender'       ,'TEXT'],
                  ['AWC'                ,'INT'],
                  ['Turn_Count'         ,'INT'],
                  ['Child_Voc_Count'    ,'INT'],
                  ['CHN'                ,'REAL'],
                  ['Child_Voc_Duration' ,'INT'],
                  ['FAN_Word_Count'     ,'INT'],
                  ['FAN'                ,'REAL'],
                  ['MAN_Word_Count'     ,'INT'],
                  ['MAN'                ,'REAL'],
                  ['CXN'                ,'REAL'],
                  ['OLN'                ,'REAL'],
                  ['TVN'                ,'REAL'],
                  ['NON'                ,'REAL'],
                  ['SIL'                ,'REAL'],
                  ['Clock_Time_TZAdj'   ,'TEXT'],
                  ['Audio_Duration'     ,'REAL']]

HEAD_TYPE_DICT = dict(HEAD_NAME_LIST)

class ADEXProcessor:
    def __init__(self):
        self.removeNaptime = False
        self.remove5mins = False
        self.switches = [['AWC', True],
                         ['Turn_Count', True],
                         ['Child_Voc_Count', True],
                         ['CHN', True],
                         ['FAN', True],
                         ['MAN', True],
                         ['CXN', True],
                         ['OLN', True],
                         ['TVN', True],
                         ['NON', True],
                         ['SIL', True]]


    def setSwitches(self, switches):
        for x in range(len(switches)):
            self.switches[x][1] != switches[x]
            self.switches[x][1] = switches[x]

        item_list = [x[0] for x in self.switches if x[1] is True]
        self.avg_param = ['AVG(' + x + ')' for x in item_list]
        self.summary = [['ID', 'Age', 'Gender'] + item_list]

    def readNaptime(self, DB):
        naptime_db = Database(DB)
        naptime_list = naptime_db.select('naptime', ['child_cd', 'start', 'end'])
        naptime_db.close()
        self.naptime_dict = {}

        for entry in naptime_list:
            child_id = entry[0].split('_')[0].lower()
            date = entry[0].split('_')[1]
            if child_id not in self.naptime_dict:
                self.naptime_dict[child_id] = [(date, entry[1], entry[2])]
            else:
                self.naptime_dict[child_id].append((date, entry[1], entry[2]))

    def getAverage(self, DB):
        id_list = DB.select('sqlite_sequence', ['name'], order_by='name ASC')
        id_list = [x[0] for x in id_list]

        # # generate preliminary results for each ID (every file is separated)
        # summary_dict = {}
        # for id in id_list:
        #     file_list = DB.select(id, ['File_Name'], distinct=True,
        #                           order_by='File_Name ASC')
        #     file_list = [x[0] for x in file_list]

        #     for file in file_list:
        #         wcondition = 'File_Name=\'' + file  + '\''
        #         preliminary = DB.select(id, avg_list, where=wcondition)
        #         if id in summary_dict:
        #             summary_dict[id].append([file, preliminary[0]])
        #         else:
        #             summary_dict[id] = [[file, preliminary[0]]]

        # generate average values for each ID (all files)
        for child_id in id_list:
            count = len(DB.select(child_id, ['File_Name'],
                                       distinct=True,
                                       order_by='File_Name ASC'))
            result = list(DB.select(child_id, self.avg_param)[0])

            # format to keep only two digits
            for i in range(len(result)):
                result[i] = "{:.2f}".format(result[i])

            self.summary.append([child_id,
                                 self.child[child_id][0],
                                 self.child[child_id][1]] + result)

    def run(self, dir_list):
        if self.removeNaptime:
            self.readNaptime("/home/hao/Develop/projects/bll/bll_app/test/bll_db.db")
            self.child = {}

        for path in dir_list:
            basename = os.path.basename(path)
            current_DB = Database(basename+'.sqlite3')
            file_list = os.listdir(path)

            for file in file_list:
                if not file.endswith(".csv"):
                    continue

                ADEX_file = ADEXFileProcessor(path+'/'+file)
                if ADEX_file.child_id not in self.child:
                    self.child[ADEX_file.child_id] = [ADEX_file.getChildAge(),
                                      ADEX_file.getChildGender()]

                if self.remove5mins:
                    ADEX_file.remove5mins()

                if self.readNaptime:
                    ADEX_file.removeNaptime(self.naptime_dict)

                ADEX_file.saveToDB(current_DB)

            self.getAverage(current_DB)
            current_DB.close()
            os.remove(basename + ".sqlite3")

    def saveResults(self, filename):
        mParser.excel_writer(filename, 'ADEX_OUTPUT', self.summary)

    def getConfigs(self):
        return [True, self.removeNaptime, self.remove5mins, self.switches]

# read ADEX csv files with required columns only
# then save these columns to DB
class ADEXFileProcessor:
    def __init__(self, ADEX_file):
        lg.debug(ADEX_file)
        self.heads = [x[0] for x in HEAD_NAME_LIST]
        self.content = mParser.csv_dict_reader(ADEX_file, self.heads)
        self.child_id = self.getChildID()
        self.start_time  = self.getStartTime()

    def remove5mins(self):
        final_start = 0
        final_end = len(self.content) - 1
        counter = 0
        index = self.heads.index('Audio_Duration')

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
        index = self.heads.index('Child_ChildID')
        return self.content[0][index].lower()

    def getChildAge(self):
        index = self.heads.index('Child_Age')
        return self.content[0][index].lower()

    def getChildGender(self):
        index = self.heads.index('Child_Gender')
        return self.content[0][index].lower()

    def getStartTime(self):
        index = self.heads.index('Clock_Time_TZAdj')
        return self.timeToSecond(self.content[0][index])

    # convert time string to seconds
    def timeToSecond(self, string):
        # string = 6/10/2009 8:37:45
        return time.mktime(time.strptime(string, '%m/%d/%Y %H:%M:%S'))

    # convert seconds to human readable string
    def SecondTotime(self, second):
        return time.ctime(second)

    def removeNaptime(self, naptime_dict):
        if self.child_id in naptime_dict:
            start_date = time.strftime('%Y%m%d', time.localtime(self.start_time))
            for i in naptime_dict[self.child_id]:
                if i[0] == start_date:
                    self.removeTime(self.start_time + i[1],
                                     self.start_time + i[2])

    def removeTime(self, start_time, end_time):
        lg.debug("removing naptime...")
        nap_start = 0
        nap_end = len(self.content)
        count = 0
        index = self.heads.index('Clock_Time_TZAdj')

        for row in self.content:
            cur_time = self.timeToSecond(row[index])

            if (cur_time >= start_time) and (nap_start == 0):
                nap_start = count
            if (cur_time > end_time) and (nap_end == len(self.content)):
                nap_end = count

            count += 1

        del self.content[nap_start : nap_end]

    def saveToDB(self, DB):
        sql = ""
        # check the existence of childID
        if DB.select('sqlite_master', ['name'],
                                  where="type='table' AND name='"+self.child_id +"'") is None:
            lg.debug(self.child_id + " is not in database")
            param = [i + ' ' + HEAD_TYPE_DICT[i] for i in self.heads]
            param.insert(0, "ID INTEGER PRIMARY KEY AUTOINCREMENT")
            param = ",".join(param)
            sql = "CREATE TABLE " + self.child_id + "(" + param + ")"
            DB.execute_script(sql)

        # insert content into DB
        DB.insert_table(self.child_id, self.heads, self.content)
