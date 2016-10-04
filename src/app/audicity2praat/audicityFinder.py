class AudicityFinder(object):
    size = 0
    intervals = []

    def __init__(self, filename=None):
        if filename is not None:
            self.parseFile(filename)

    def parseFile(self, filename):
        self.intervals.clear()
        with open(filename, 'rt') as fp:
            lastMax = 0.00

            for line in fp:
                context = line.split()
                xmin = float(context[0])
                xmax = float(context[1])
                text = context[2]

                if lastMax != xmin:
                    self.intervals.append([lastMax, xmin, ""])
                lastMax = xmax

                self.intervals.append([xmin, xmax, text])

    def getIntervals(self):
        return self.intervals
