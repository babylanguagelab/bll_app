from configInfo import ConfigInfo
from debug import myDebug
from xmlParser import XMLParser2


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

    # def getDefaultConfList(self):
    def getConfList(self):
        return [x.getConfig() for x in self.confList]

    def setConfList(self, newConfList):
        for x in len(newConfList):
            if (self.confList(x).getConfig != newConfList(x)):
                self.confList(x).setConfig(newConfList(x))

    def setFileList(self, newFileList):
        self.fileList = newFileList

    def applyFile(self, filename):
        _parser = XMLParser2(filename)
        for i in self.confList:
            if i.getConfig() == 1:
                _parser.delAttr

        # for i in self.confList
        # if keep: continue
        # if delete: delete
        # if change: call change

    def run(self):
        if len(self.fileList) == 0:
            return 1
        if len(self.confList) == 0:
            return 2

        for x in self.fileList:
            self.applyFile(x)

        return 0
