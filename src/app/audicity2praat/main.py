from audicityFinder import AudicityFinder
from TextGrid import TextGrid
import ui

class Controller(object):
    def __init__(self):
        self.audicity = AudicityFinder()
        self.tg = TextGrid()

    def parseAudicity(self, filename):
        self.audicity.parseFile(filename)

    def saveResults(self, filename):
        labels = self.audicity.getIntervals()
        self.tg.addItem("IntervalTier", "dialog", labels)
        self.tg.output(filename+".TextGrid")

class Main(object):
    def __init__(self):
        self.control = Controller()
        self.mWin = ui.MainWindow(self.control)

    def run(self):
        self.mWin.toShow()

m = Main()
m.run()

