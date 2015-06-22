from configInfo import ConfigInfo
from debug import myDebug

fakeList = [['./11/21', '11', '22', '0', 'nope'],
            ['./11/22', '11', '22', '1', 'nope'],
            ['./11/23', '11', '22', '2', 'nope'],
            ['./11/25', '11', '22', '1', 'nope'],
            ['./11/26', '11', '22', '2', 'nope']]


class Driver:
    def __init__(self):
        # get settings from default configuration file
        self.confList = [ConfigInfo(x[0], x[1], x[2], x[3], x[4])
                         for x in fakeList]
        self.fileList = []

    def getConfList(self):
        return [x.getConfig() for x in self.confList]

    def setConfList(self, newConfList):
        for x in len(newConfList):
            if (self.confList(x).getConfig is not newConfList(x)):
                self.confList(x).setConfig(newConfList(x))

    def setFileList(self, newFileList):
        self.fileList = newFileList

    def applyFilter(self, filename):
        myDebug("apply Filter")
        # for i in self.confList
        # if keep: continue
        # if delete: delete
        # if change: call change

    def run(self):
        for x in self.fileList:
            myDebug("run")
            # apply filter for each file
