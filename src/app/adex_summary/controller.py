# core parts to glue each processor
#
# author: zhangh15@myumanitoba.com

import logging as lg
import os
from adex_processor import ADEXProcessor

class Controller:
    def __init__(self):
        self.ADEX_folders = []
        self.adex_config = [True] * 16
        self.useNaptime = False
        self.useTranscribed = False
        self.output_file = ""

    def run(self):
        for path in self.ADEX_folders:
            basename = os.path.basename(path)
            filelist = os.listdir(path)
            os.chdir(path)
            for file in filelist:
                if not file.endswith(".csv"):
                    continue
                mADEX = ADEXProcessor(self.adex_config, basename)
                mADEX.run(file)
        lg.debug("Job Complete!")

    def clean(self):
         for path in self.ADEX_folders:
             basename = os.path.basename(path)
             os.remove(basename + ".sqlite3")
