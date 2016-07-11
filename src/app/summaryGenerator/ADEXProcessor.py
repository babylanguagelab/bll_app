import logging as lg
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


# convert time string to seconds
def timestr_to_second(string):
    # string = 6/10/2009 8:37:45
    return time.mktime(time.strptime(string, '%m/%d/%Y %H:%M:%S'))


# convert seconds to human readable string
def second_to_timestr(second):
    return time.ctime(second)


class ADEXProcessor:
    def __init__(self, database):
        self.config = {'DB': database,
                       'adex_dirs': "",
                       'naptime_file': "/tmp/test/bll_db.db",
                       # seconds, could be 300, 600, 1800, 3600
                       'time_interval': 300}
        for i in ['f30mins', 'partial_records', 'naptime', 'last2rows']:
            self.config[i] = False
        self.switches = ['AWC', 'Turn_Count', 'Child_Voc_Count', 'CHN', 'FAN',
                         'MAN', 'CXN', 'OLN', 'TVN', 'NON', 'SIL']
        self.naptime = {}
        self.output = {}

    def set_configs(self, configs=None, switches=None):
        if configs is not None:
            for i,j in configs:
                self.config[i] = j

        if switches is not None:
            self.switches = switches

    def read_naptime(self):
        naptime_db = Database(self.config['naptime_file'])
        naptime_list = naptime_db.select('naptime', ['child_cd', 'start', 'end'])
        naptime_db.close()

        for entry in naptime_list:
            child_id = entry[0].split('_')[0].lower()
            date = entry[0].split('_')[1]

            if child_id not in self.naptime[child_id]:
                self.naptime[child_id] = [(date, entry[1], entry[2])]
            else:
                self.naptime[child_id] += [(date, entry[1], entry[2])]

    # get average for values in switches
    def get_average(self):
        cIDs = list(self.output.keys())
        cIDs.sort()
        avg_param = ['AVG(' + x + ')' for x in self.switches]

        # generate average values for each ID (all files)
        for cID in cIDs:
            avg_values = list(self.config['DB'].select(cID, avg_param)[0])
            self.output[cID] += avg_values

    def run(self):
        if self.config['naptime']:
            self.read_naptime()

        # create result table
        if self.config['DB'].select('sqlite_master', ['name'],
                             where="type='table' AND name='ADEX'") is None:

            param = ['ChildID', 'Age', 'Gender', 'Recordings'] + self.switches
            params = ",".join(param)
            sql = "CREATE TABLE ADEX" + "(" + params + ",PRIMARY KEY (ChildID)" + ")"
            self.config['DB'].execute_script(sql)

        for path in self.config['adex_dirs']:
            file_list = os.listdir(path)

            for ADEX_file in file_list:
                if not ADEX_file.endswith(".csv"):
                    continue

                #[TODO] check remove list

                mADEX = ADEXFileProcessor(path + '/' + ADEX_file)
                if mADEX.child_id not in self.output:
                    # the third param is count for its file
                    self.output[mADEX.child_id] = [mADEX.get_ChildAge(),
                                                   mADEX.get_ChildGender(),
                                                   1]
                else:
                    self.output[mADEX.child_id][2] += 1

                if self.config['f30mins']:
                    mADEX.remove_30mins()

                if self.config['naptime']:
                    mADEX.remove_naptime(self.naptime)

                if self.config['partial_records']:
                    interval_sec = int(self.config['time_interval'])
                    mADEX.remove_partial_time(interval_sec)

                if self.config['last2rows']:
                    mADEX.remove_last2rows()

                mADEX.save_DB(self.config['DB'])

            self.get_average()

    # save results to DB
    def save_DB(self):
        cIDs = list(self.output.keys())
        cIDs.sort()
        output_title = ['ChildID', 'Age', 'Gender', 'Recordings'] + self.switches

        for cID in cIDs:
            output =  [cID] + self.output[cID]
            self.config['DB'].insert("ADEX", output_title, output)

            # format to show only two digits
            # for i in range(len(result)):
            #     result[i] = "{:.2f}".format(result[i])


    # save intermediate results to file
    def save_file(self, filename):
        cIDs = list(self.output.keys())
        cIDs.sort()
        output_title = ['File_Name'] + self.switches
        output = []

        for cID in cIDs:
            output.append([cID])
            output.append(["age", self.output[cID][0]])
            output.append(["gender", self.output[cID][1]])
            output.append(output_title)

            # if there are more than 1 file, save separately
            child_file = set(self.config['DB'].select(cID, ['File_Name'], distinct=True))

            if len(child_file) is 1:
                child_values = self.config['DB'].select(cID, ['File_Name'] + self.switches)
                for i in child_values:
                    output.append(i)
            else:
                file_list = [x[0] for x in child_file]
                file_list.sort()
                for j in file_list:
                    child_values = self.config['DB'].select(cID,
                                                            ['File_Name'] + self.switches,
                                                            where='File_Name == '
                                                            + '\'' + j + '\'')
                    for i in child_values:
                        output.append(i)

                    output.append([" "])

            mParser.excel_writer(filename, cID, output)


# read an ADEX csv file with required columns only
# filter out information and then
# save processed data to DB
class ADEXFileProcessor:
    def __init__(self, ADEX_file):
        lg.debug(ADEX_file)
        self.heads = [x[0] for x in HEAD_NAME_LIST]
        self.content = mParser.csv_dict_reader(ADEX_file, self.heads)
        self.child_id = self.get_ChildID()
        self.start_time  = self.get_start_time()

    def remove_30mins(self):
        final_start = 0
        counter = 0
        index = self.heads.index('Audio_Duration')

        # remove first 1800 sec at the beginning
        for row in self.content:
            value = float(row[index])
            counter += value
            final_start += 1
            if counter >= 1800:
                break

        lg.debug("removing 5 minutes...")
        self.content = self.content[final_start:]

    def remove_last2rows(self):
        final_end = len(self.content) - 2
        if final_end > 0:
            self.content = self.content[:final_end]

    # find any time duration not up to the time interval
    # remove 1 row before and 1 row after
    def remove_partial_time(self, interval_sec):
        index = self.heads.index('Audio_Duration')
        clock_index = self.heads.index('Clock_Time_TZAdj')
        start_time = 0
        end_time = 0

        for row in self.content:
            value = float(row[index])
            if value != interval_sec:
                if start_time == 0:
                    start_time = timestr_to_second(row[clock_index]) - interval_sec
                end_time = timestr_to_second(row[clock_index]) + interval_sec
            else:
                if start_time != 0:
                    self.remove_time(start_time, end_time)
                    start_time = 0

            # for the last row
            if start_time != 0:
                self.remove_time(start_time, end_time)

    def get_ChildID(self):
        index = self.heads.index('Child_ChildID')
        return self.content[0][index].lower()

    def get_ChildAge(self):
        index = self.heads.index('Child_Age')
        return self.content[0][index].lower()

    def get_ChildGender(self):
        index = self.heads.index('Child_Gender')
        return self.content[0][index].upper()

    def get_start_time(self):
        index = self.heads.index('Clock_Time_TZAdj')
        return timestr_to_second(self.content[0][index])

    def remove_naptime(self, naptime_dict):
        if self.child_id in naptime_dict:
            start_date = time.strftime('%Y%m%d', time.localtime(self.start_time))
            for i in naptime_dict[self.child_id]:
                if i[0] == start_date:
                    self.remove_time(self.start_time + i[1],
                                     self.start_time + i[2])

    def remove_time(self, start_time, end_time):
        lg.debug("removing naptime...")

        time_start = 0
        time_end = len(self.content)
        count = 0
        index = self.heads.index('Clock_Time_TZAdj')

        for row in self.content:
            cur_time = timestr_to_second(row[index])

            if (cur_time >= start_time) and (time_start == 0):
                time_start = count
            if (cur_time > end_time) and (time_end == len(self.content)):
                time_end = count

            count += 1

        del self.content[time_start : time_end]

    def save_DB(self, DB):
        sql = ""

        # check the existence of childID
        if DB.select('sqlite_master', ['name'],
                     where="type='table' AND name='"+self.child_id +"'") is None:

            lg.debug(self.child_id + " is not in database, insert it.")
            param = [i + ' ' + HEAD_TYPE_DICT[i] for i in self.heads]
            param.insert(0, "ID INTEGER PRIMARY KEY AUTOINCREMENT")
            param = ",".join(param)
            sql = "CREATE TABLE " + self.child_id + "(" + param + ")"
            DB.execute_script(sql)

        # insert content into DB
        DB.insert_table(self.child_id, self.heads, self.content)

