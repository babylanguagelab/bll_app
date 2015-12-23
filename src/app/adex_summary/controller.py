# core parts to glue each processor 
#  
# author: zhangh15@myumanitoba.com

import logging as lg
import os
from adex_processor import ADEXProcessor

class Controller:
    def __init__(self):
        self.ADEX_HEAD = ['File_Name', 'Number_Recordings', 'File_Hours',
                          'Child_ChildID', 'Child_Age', 'Child_Gender',
                          'AWC', 'Turn_Count', 'Child_Voc_Duration',
                          'FAN_Word_Count', 'FAN', 'MAN_Word_Count', 'MAN',
                          'CXN', 'OLN', 'TVN', 'NON', 'SIL', 'Audio_Duration']

        self.ADEX_folders = []
        self.useNaptime = False
        self.useTranscribed = False

    def run(self):
        for path in self.ADEX_folders:
            basename = os.path.basename(path)
            filelist = os.listdir(path)
            os.chdir(path)
            for file in filelist:
                if not file.endswith(".csv"):
                    continue
                lg.debug(file)
                # mADEX = ADEXProcessor(self.ADEX_HEAD, basename)
                # mADEX.run(file)

    def clean(self):
         for path in self.ADEX_folders:
             basename = os.path.basename(path)
             os.remove(basename + ".sql")
