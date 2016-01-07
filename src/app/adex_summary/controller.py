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
        self.read_config()

    def run(self):
        self.run_adex()
        self.clean()

    def run_adex(self):
        for path in self.ADEX_folders:
            os.chdir(path)
            basename = os.path.basename(path)
            self.adex_control.open_db(basename)

            filelist = os.listdir(path)
            for file in filelist:
                if not file.endswith(".csv"):
                    continue
                mADEX = ADEXProcessor(self.adex_control)
                mADEX.run(file)

            self.adex_control.save_avg_results()
            self.adex_control.close_db()
        lg.debug("Job Complete!")

    def read_config(self):
        # ADEX configurations
        self.adex_control.remove5mins = True
        self.adex_control.useNaptime = True
        self.adex_control.read_naptime()

    def save_config(self):
        configs = [self.adex_control.dump()]

    def clean(self):
         for path in self.ADEX_folders:
             basename = os.path.basename(path)
             os.remove(basename + ".sqlite3")
