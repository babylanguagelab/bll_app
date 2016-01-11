# core parts to glue each processor
#
# author: zhangh15@myumanitoba.com

import logging as lg
import os
from adex_processor import ADEXProcessor
from comment_processor import CommentProcessor

COMMENT_SHEET = "/home/hao/Develop/projects/bll/bll_app/test/LENASpreadsheet.xlsx"

class Controller:
    def __init__(self):
        self.ADEX_folders = []
        self.ADEX_proc = ADEXProcessor()
        self.CMT_proc = CommentProcessor()
        self.loadConfigs()

    def run(self):
        self.ADEX_proc.run(self.ADEX_folders)
        self.CMT_proc.run()
        lg.debug("Done!")

    def saveOutput(self, filename):
        self.ADEX_proc.saveResults(filename)
        self.CMT_proc.saveResults(filename)

    def loadConfigs(self):
        # ADEX configurations
        self.ADEX_proc.setSwitches([True]*11)
        self.ADEX_proc.remove5mins = True
        self.ADEX_proc.removeNaptime = True

        # CMT configurations:
        self.CMT_proc.setSwitches([True]*14)

    def saveConfigs(self):
        configs = [self.ADEX_proc.getConfigs()]
