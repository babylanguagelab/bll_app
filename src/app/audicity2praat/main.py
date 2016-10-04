from audicityFinder import audicityFinder
from TextGrid import TextGrid

class Main(object):
    def run(self):
        audicity = audicityFinder("Label Track.txt")
        labels =audicity.getIntervals()

        tg = TextGrid()
        tg.addItem("IntervalTier", "dialog", labels)
        tg.output("results.TextGrid")

m = Main()
m.run()

