import csv

class myConfig:
    def __init__(self, filename):
        self._filename = filename

    def readConfig(self):
        reader = csv.reader(self._filename, 'rb')

    def writeConfig(self, newFile):
        writer = csv.write(newFile, )
