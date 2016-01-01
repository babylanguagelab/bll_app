# core parts to glue each processor
#
# author: zhangh15@myumanitoba.com

import logging as lg
import os
from adex_processor import ADEXProcessor
from adex_processor import ADEXControl

class Controller:
    def __init__(self):
        self.ADEX_folders = []
        self.adex_control = ADEXControl()
        self.output_file = ""

    def run(self):
        for path in self.ADEX_folders:
            basename = os.path.basename(path)
            self.adex_control.set_db_name(basename)
            filelist = os.listdir(path)
            os.chdir(path)
            for file in filelist:
                if not file.endswith(".csv"):
                    continue
                mADEX = ADEXProcessor(self.adex_control)
                mADEX.run(file)
        lg.debug("Job Complete!")

    def read_config(self):
        lg.debug("read config")

    def save_config(self):
        configs = [self.adex_control.dump()]
        lg.debug("save config")

    def clean(self):
         for path in self.ADEX_folders:
             basename = os.path.basename(path)
             os.remove(basename + ".sqlite3")
