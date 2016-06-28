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
        #self.db = Database(":memory:")
        self.config = {'DB': Database("test.db"),
                       'ADEX': True,
                       'Comment': False,
                       'Transcribe': False,
                       'output_file': ""}
        self.adex = ADEXProcessor(self.config["DB"])
        self.com = CommentProcessor(self.config["DB"])
        self.trans = TranscribedProcessor(self.config["DB"])

    def load_configs(self):
        lg.debug("load configs")
        self.adex.set_configs()

    def save_configs(self):
        lg.debug("save configs")

    def run(self):
        lg.debug("run")
        self.adex.run()


class Main(object):
    def __init__(self):
        self.m_con = Controller()
        self.m_win = ui.MainWindow(self.m_con)

    def run(self):
        self.m_win.show()

# for test
mMain = Main()
mMain.run()
