import glob
from ui import MainWindow
from adex_processor import ADEXProcessor
import logging as lg
from debug import init_debug 

class Main:
    def __init__(self):
        init_debug()
        self.mWindow = MainWindow()
        self.mADEX = ADEXProcessor()
        self.ADEX_HEAD = ['File_Name', 'Number_Recordings', 'File_Hours',
                          'Child_ChildID', 'Child_Age', 'Child_Gender',
                          'AWC', 'Turn_Count', 'Child_Voc_Duration',
                          'FAN_Word_Count', 'FAN', 'MAN_Word_Count', 'MAN',
                          'CXN', 'OLN', 'TVN', 'NON', 'SIL', 'Audio_Duration']

        self.useNaptime = False
        self.useTranscribed = False

    def run(self):
        for name in glob.glob('*.csv'):
            self.mADEX.set_head(self.ADEX_HEAD)
            self.mADEX.readCSV(name)
            self.mADEX.remove_5mins()
            #if naptime remove naptime
            self.mADEX.saveToDB()

        # self.mWindow.show()

if __name__ == '__main__':
    mMain = Main()
    mMain.run()
