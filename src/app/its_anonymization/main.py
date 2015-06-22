# from ui import MainWindow
from ConfigInfo import ConfigInfo

fakeList = [['./11/21', '11', '22', '0', 'nope'],
['./11/22', '11', '22', '0', 'nope'],
['./11/23', '11', '22', '0', 'nope'],
['./11/24', '11', '22', '0', 'nope'],
['./11/25', '11', '22', '0', 'nope'],
['./11/26', '11', '22', '0', 'nope']]

class main:
    def __init__(self):
        # get settings from default configuration file
        self.confList = [SettingInfo(x[0], x[1], x[2], x[3], x[4]) for x in fakeList]
