import logging as lg
import os
from debug import debug_init
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
                       'ADEX': True,
                       'ADEX_folders': [],
                       'Comment': False,
                       'Transcribe': False,
                       'output': "",
                       'Preliminary': True}
        self.adex = ADEXProcessor(self.config["DB"])
        self.com = CommentProcessor(self.config["DB"])
        self.trans = TranscribedProcessor(self.config["DB"])

    def load_configs(self):
        self.adex.set_configs()

    def save_configs(self):
        lg.debug("save configs")

    def set_output(self, folder):
        output_folder = folder + "/summary"
        if not os.path.exists(output_folder):
            os.mkdir(output_folder)

        self.config['output'] = output_folder

    def run(self):
        if self.config['Comment']:
            self.com.run()

        if self.config['ADEX']:
            self.adex.run(self.config['ADEX_folders'], self.config['output'])

        if self.config['Transcribe']:
            self.trans.run()


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
