import logging as lg
import os
from debug import debug_init
import ConfigParser as mParser
from database import Database
from ADEXProcessor import ADEXProcessor
from commentProcessor import CommentProcessor
from transcribedProcessor import TranscribedProcessor
import ui


class Controller(object):
    def __init__(self):
        debug_init()
        self.config = {'DB': Database(":memory:"),
                       #self.config = {'DB': Database("test.db"),
                       'ADEX': False, 'ADEX_folders': [],
                       'comment': False, 'special_case_file': "",
                       'transcribed': False, 'transcribed_file': "",
                       'output': "",
                       'preliminary': False}
        self.adex = ADEXProcessor(self.config["DB"])
        self.com = CommentProcessor()
        self.trans = TranscribedProcessor()

    def load_configs(self):
        self.adex.set_configs()

    def save_configs(self):
        lg.debug("save configs")

    def set_output(self, folder):
        output_folder = folder + "/output"
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)

        self.config['output'] = output_folder + "/summary.xlsx"

        if os.path.isfile(self.config['output']):
            os.remove(self.config['output'])

    def set_preliminary(self, toggle):
        self.adex.set_configs(configs=[('preliminary', toggle)])
        self.com.set_configs(configs=[('preliminary', toggle)])
        self.trans.set_configs(configs=[('preliminary', toggle)])

    def run(self):
        if self.config['comment']:
            self.com.run(self.config['output'])
            self.adex.filtered_files = [x[0].lower() for x in self.com.its_to_remove]
            self.trans.filtered_files = [x[0].lower() for x in self.com.its_to_remove]

        if self.config['ADEX']:
            self.adex.run(self.config['ADEX_folders'], self.config['output'])

        if self.config['transcribed']:
            self.trans.run(self.config['transcribed_file'], self.config['output'])

        self.save(self.config['output'])

        lg.debug("Done!")

    def save(self, summary):
        output = [['LENA ADEX']]
        ADEX_CIDs = list(self.adex.output.keys())
        ADEX_CIDs.sort()
        ADEX_output_title = ['ChildID', 'Age', 'Gender', 'Recordings'] + self.adex.switches
        output.append(ADEX_output_title)

        if self.config['transcribed']:
            output[0] = output[0] + [' '] * (len(ADEX_output_title) - 1) + ["transcribed data"]
            trans_head  = [' ', self.trans.content['head'][1]]
            for i in self.trans.content['head'][2:]:
                if self.trans.switches[i] == 1:
                    trans_head.append(i + " (avg)")
                else:
                    trans_head.append(i + " (sum)")

            output[1] = output[1] + trans_head

        for ACID in ADEX_CIDs:
            if not self.config['transcribed']:
                output.append([ACID] + self.adex.output[ACID])
            else:
                if ACID in self.trans.output:
                    output.append([ACID] + self.adex.output[ACID] +
                                  self.trans.output[ACID])

        if self.config['transcribed']:
            TCIDs = set(self.trans.output.keys()) - set(ADEX_CIDs)

            for TCID in TCIDs:
                output.append([TCID] +
                              [' '] * len(ADEX_output_title) +
                              self.trans.output[TCID])

        mParser.excel_writer(summary, "summary", output)

class Main(object):
    def __init__(self):
        self.m_con = Controller()
        self.m_win = ui.MainWindow(self.m_con)

    def run(self):
        self.m_con.load_configs()
        self.m_win.show()

# for test
mMain = Main()
mMain.run()
