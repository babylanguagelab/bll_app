from configInfo import ConfigInfo
from xmlParser import XMLParser2

fakeList = [['./11/21', '11', '0', 'nope'],
            ['./11/22', '11', '0', 'nope'],
            ['./11/22', '11', '0', 'nope'],
            ['./11/22', '11', '1', 'nope'],
            ['./11/22', '11', '1', 'nope'],
            ['./11/22', '11', '0', 'nope'],
            ['./11/22', '11', '0', 'nope'],
            ['./11/22', '11', '0', 'nope'],
            ['./11/23', '11', '0', 'nope'],
            ['./11/25', '11', '0', 'nope'],
            ['./11/26', '11', '0', 'nope']]


class Driver:
    def __init__(self):
        # get settings from default configuration file
        self.confList = [ConfigInfo(x[0], x[1], x[2], x[3])
                         for x in fakeList]
        self.fileList = []

    # def getDefaultConfList(self):
    # def saveAsDefault():

    def getConfList(self):
        return [x.config for x in self.confList]

    def setConfList(self, newConfList):
        for x in range(len(newConfList)):
            if (self.confList[x].config != newConfList[x]):
                self.confList[x].config = newConfList[x]

    def setFileList(self, newFileList):
        self.fileList = newFileList

    def applyFile(self, filename):
        mParser = XMLParser2(filename)
        for i in self.confList:
            if i.config == "1":
                mParser.delAttr(i.xpath, i.key)
            if i.config == "2":
                mParser.setAttr(i.xpath, i.key, i.getDummy())
        mParser.save()

    def run(self):
        if len(self.fileList) == 0:
            return 1
        if len(self.confList) == 0:
            return 2

        for x in self.fileList:
            self.applyFile(x)

        return 0
