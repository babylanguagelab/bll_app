import logging as lg
import os
import time
from debug import debug_init
from database import Database
from ADEXProcessor import ADEXProcessor
from commentProcessor import CommentProcessor
from transcribedProcessor import TranscribedProcessor
import ui

class Controller(object):
    def __init__(self):
        debug_init()
        #self.load_configs()
        self.config = {'DB': Database(":memory:"),
        #self.config = {'DB': Database("test.db"),
                       'ADEX': True,
                       'Comment': False,
                       'Transcribe': False,
                       'output': "",
                       'output_middle': ""}
        self.adex = ADEXProcessor(self.config["DB"])
        self.com = CommentProcessor(self.config["DB"])
        self.trans = TranscribedProcessor(self.config["DB"])

    def load_configs(self):
        self.adex.set_configs()

    def save_configs(self):
        lg.debug("save configs")

    def set_output(self, folder):
        if not os.path.exists(folder):
            os.mkdir(folder)

        self.config['output_middle'] = folder
        self.config['output'] = folder + "/summary.xlsx"

    def save_file(self):
        if self.config['ADEX']:
            self.adex.save_file(self.config['output'])

        if self.config['Comment']:
            self.com.save_file(self.config['output'])

        if self.config['Transcribe']:
            self.trans.save_file(self.config['output'])

    def run(self):
        if self.config['Comment']:
            self.com.run()

        if self.config['ADEX']:
            self.adex.run()

        if self.config['Transcribe']:
            self.trans.run()

        self.save_file()


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
