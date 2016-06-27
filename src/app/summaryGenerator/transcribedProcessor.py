# Description: parse the transcribed file
# Data: 2016-06-26
# functions: 1. open transcribed file
#            2. get the transcribed items
#            3. merge TRS files with same ID

import logging as lg
import ConfigParser as mParser

class transcribedProcessor(object):
    def __init__(self, database):
        self.content = {"child":""}
        # child ID = [number of transcripts, title 1 number, title 2 number]
        self.config = {"DB": database, "filename": ""}

    def open_transcribed_file(self):
        lg.debug("open transcribed file: " + self.config['filename'])
        content = mParser.csv_reader(self.config['filename'])
        head = content[0][1:]

        body = {}
        for record in content[1:]:
            ID = record[0].split('_')[0].lower()
            if ID not in body:
                body[ID] = [1] + [float(x) for x in record[1:]]
                print(body[ID])
            else:
                tmp1_list = [float(x) for x in record[1:]]
                tmp2_list = body[ID][1:]
                body[ID] = [sum(x) for x in zip(tmp1_list, tmp2_list)]
                #body[ID][0] += 1


        print(body)

    # def run(self):


mTSP = transcribedProcessor("1")
mTSP.config["filename"] = "/home/hao/Develop/bll/bll_app/test/results/summary.csv"
mTSP.open_transcribed_file()


