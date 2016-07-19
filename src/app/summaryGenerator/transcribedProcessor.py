import logging as lg
import os
import ConfigParser as mParser

class TranscribedProcessor(object):
    def __init__(self):
        self.config = {'trans_file': "",
                       'calc_type': 1, # calc_type: 1 for avg, 2 for sum
                       'preliminary': True}
        self.content = {"head": [], "body": {}}
        self.filtered_files = []
        self.output = {}

    # init configurations
    def set_configs(self, configs=None):
        if configs:
            for i,j in configs:
                self.config[i] = j

    def parse_file(self):
        lg.debug("open transcribed file: " + self.config['trans_file'])

        content = mParser.csv_reader(self.config['trans_file'])
        # get the transcribed items
        self.content['head'] = ['Child ID', 'Count'] + content[0][1:]

        # merge TRS files with same ID
        body = {}
        for record in content[1:]:
            ID = record[0].split('_')[0].lower()

            file_name = record[0]
            if file_name.endswith('_FINAL'):
                file_name = record[0][:-6].lower()

            if ID not in body:
                body[ID] = [[file_name] + [float(x) for x in record[1:]]]
            else:
                body[ID].append([file_name] + [float(x) for x in record[1:]])
        self.content['body'] = body

    def cal_sum(self):
        lg.debug("calculating sum...")
        CIDs = self.content['body'].keys()
        output = {}
        
        for cid in CIDs:
            sum_values = []
            length = 0
            for record in self.content['body'][cid]:

                if record[0] in self.filtered_files:
                    continue

                length += 1
                for index, item in enumerate(record[1:]):
                    if index >= len(sum_values):
                        sum_values.append(item)
                    else:
                        sum_values[index] += item

            if len(sum_values) > 0:
                output[cid] = [length] + sum_values

        return output

    def cal_average(self):
        lg.debug("calculating average...")
        output = self.cal_sum()
        CIDs = output.keys()

        for cid in CIDs:
            count = output[cid][0]
            for i in range(len(output[cid][1:])):
                if output[cid][1+i] != 0:
                    output[cid][1+i] = output[cid][1+i] / count

        return output

    def run(self, filename, output):
        self.config['trans_file'] = filename
        self.parse_file()

        if self.config['calc_type'] == 1:
            self.output = self.cal_average()
        else:
            self.output = self.cal_sum()

        if self.config['preliminary']:
            pfilename = os.path.dirname(output) + "/Transcribed.xlsx"
            self.save_preliminary(pfilename)

    def save_preliminary(self, filename):
        lg.debug("saving preliminary results...")

        if os.path.isfile(filename):
            os.remove(filename)

        output = [self.content['head']]
        if self.config['calc_type'] == 1:
            output.append(['calc type', "average"])
        else:
            output.append(['calc type', "sum"])

        CIDs = self.output.keys()
        CIDs.sort()

        for cid in CIDs:
            output.append([cid] + self.output[cid])

        mParser.excel_writer(filename, 'Transcribed', output)
