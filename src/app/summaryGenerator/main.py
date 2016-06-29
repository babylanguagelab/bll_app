# Description: core parts to glue each processor
# Author: zhangh15@myumanitoba.com
# Date: 2015-11-17

import logging as lg
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
                       'ADEX': False,
                       'Comment': False,
                       'Transcribe': True,
                       'output_file': ""}
        self.adex = ADEXProcessor(self.config["DB"])
        self.com = CommentProcessor(self.config["DB"])
        self.trans = TranscribedProcessor(self.config["DB"])

    def load_configs(self):
        self.adex.set_configs()

    def save_configs(self):
        lg.debug("save configs")

    def save_file(self):
        filename = "/home/hao/Develop/bll/bll_app/test/summary_test/results.xlsx"
        if self.config['ADEX']:
            self.adex.save_file(filename)

        if self.config['Comment']:
            self.com.save_file(filename)

        if self.config['Transcribe']:
            self.trans.save_file(filename)

    def run(self):
        if self.config['ADEX']:
            self.adex.run()

        if self.config['Comment']:
            self.com.run()

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
