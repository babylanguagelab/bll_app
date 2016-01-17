# Description: core parts to glue each processor
# Author: zhangh15@myumanitoba.com
# Date: 2015-01-17

import logging as lg
from ADEXProcessor import ADEXProcessor
from commentProcessor import commentProcessor


class controller(object):
    def __init__(self):
        self.ADEX_folders = []
        self.ADEX_proc = ADEXProcessor()
        self.CMT_proc = commentProcessor()
        self.load_configs()

    def run(self):
        self.ADEX_proc.run(self.ADEX_folders)
        self.CMT_proc.run()
        lg.debug("Done!")

    def save_output(self, filename):
        self.ADEX_proc.saveResults(filename)
        self.CMT_proc.save_results(filename)

    def load_configs(self):
        # ADEX configurations
        self.ADEX_proc.set_switches([True]*11)
        self.ADEX_proc.remove5mins = True
        self.ADEX_proc.removeNaptime = True

        # CMT configurations:
        self.CMT_proc.set_switches([True]*14)

    def save_configs(self):
        configs = [self.ADEX_proc.getConfigs()]
