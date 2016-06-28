import logging as lg
import ConfigParser as mParser

class transcribedProcessor(object):
    def __init__(self, database):
        self.content = {"head":[], "body":{}}
        # child ID = [number of transcripts, title 1 number, title 2 number]
        self.config = {"DB": database, "filename": ""}

    def open_transcribed_file(self):
        lg.debug("open transcribed file: " + self.config["filename"])
        content = mParser.csv_reader(self.config["filename"])
        # get the transcribed items
        head = content[0][1:]
        head.insert(0, "Child ID")
        self.content["head"] = head

        # merge TRS files with same ID
        body = {}
        for record in content[1:]:
            ID = record[0].split('_')[0].lower()
            if ID not in body:
                body[ID] = [1] + [float(x) for x in record[1:]]
            else:
                tmp1_list = [float(x) for x in record[1:]]
                tmp2_list = body[ID][1:]
                tmp3_list = [sum(x) for x in zip(tmp1_list, tmp2_list)]
                body[ID] = [body[ID][0] + 1] + tmp3_list
        self.content["body"] = body

TSP = transcribedProcessor("1")
TSP.config["filename"] = "/home/hao/Develop/bll/bll_app/test/results/summary.csv"
TSP.open_transcribed_file()
