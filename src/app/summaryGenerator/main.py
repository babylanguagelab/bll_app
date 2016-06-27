# Description: core parts to glue each processor
# Author: zhangh15@myumanitoba.com
# Date: 2015-11-17

import logging as lg
from debug import debug_init
from database import Database
from ADEXProcessor import ADEXProcessor
from commentProcessor import CommentProcessor
import ui

class Controller(object):
    def __init__(self):
        debug_init()
        #self.load_configs()
        #self.db = Database(":memory:")
        self.config = {'DB': Database("test.db"),
                       'ADEX': True,
                       'Comment': True,
                       'Transcribe': True,
                       'output_file': ""}
        self.adex = ADEXProcessor(self.config['DB'])
        self.com = CommentProcessor(self.config['DB'])

    def run(self):
        lg.debug("Start!")

    # def export_output(self, filename):
    #     self.adex_proc.save_results(filename)
    #     self.CMT_proc.save_results(filename)

    # def load_configs(self):
        # ADEX configurations
        # CMT configurations:
        #self.CMT_proc.set_switches([True]*14)

    def save_configs(self):
        print("save")
    #     configs = {"ADEX":self.ADEX_proc.getConfigs()}

class Main(object):
    def __init__(self):
        self.m_con = Controller()
        self.m_win = ui.MainWindow(self.m_con)

    def run(self):
        self.m_con.run()
        self.m_win.show()

# for test
mMain = Main()
mMain.run()
