class TextGrid(object):
    fileType = "ooTextFile"
    objectClass = "TextGrid"
    xmin = 0
    xmax = 0
    items = []

    def __init__(self):
        print("TextGrid Init")

    def addItem(self, itemClass, name, intervals):
        if len(intervals) == 0:
            return

        xmin = intervals[0][0]
        xmax = intervals[-1][1]

        newItem = Item(itemClass, name, xmin, xmax)

        for value in intervals:
            newItem.addInterval(value[0], value[1], value[2])

        self.items.append(newItem)

        self.xmin = self.items[0].xmin
        self.xmax = self.items[-1].xmax

    def output(self, filename):
        with open(filename, 'wt') as fp:
            fp.write("File type = \"" + self.fileType + "\"\n")
            fp.write("Object class = \"" + self.objectClass + "\"\n")
            fp.write("\n")
            fp.write("xmin = " + str(self.xmin) + "\n")
            fp.write("xmax = " + str(self.xmax) + "\n")
            fp.write("tiers? <exists>\n")
            fp.write("size = " + str(len(self.items)) + "\n")
            fp.write("item []:\n")
            for index, value in enumerate(self.items):
                tabCount = 4 * " "
                fp.write(tabCount + "item [" + str(index + 1) + "]:\n")
                fp.write(tabCount * 2 + "class = \"" + value.classType + "\"\n")
                fp.write(tabCount * 2 + "name = \"" + value.name + "\"\n")
                fp.write(tabCount * 2 + "xmin = " + str(value.xmin) + "\n")
                fp.write(tabCount * 2 + "xmax = " + str(value.xmax) + "\n")
                fp.write(tabCount * 2 + "intervals: size  = "
                         + str(len(value.intervals)) + "\n")
                for i, j in enumerate(value.intervals):
                    fp.write(tabCount * 2 + "intervals [" + str(i + 1) + "]:\n")
                    fp.write(tabCount * 3 + "xmin = " + str(j["xmin"]) + "\n")
                    fp.write(tabCount * 3 + "xmax = " + str(j["xmax"]) + "\n")
                    fp.write(tabCount * 3 + "text = \"" + str(j["text"]) + "\"\n")

class Item(object):
    classType = ""
    intervals = []
    def __init__(self, itemClass, name, xmin, xmax):
        self.classType = itemClass
        self.name = name
        self.xmin = xmin
        self.xmax = xmax

    def addInterval(self, xmin, xmax, text):
        curInterval = {}
        curInterval["xmin"] = xmin
        curInterval["xmax"] = xmax
        curInterval["text"] = text

        self.intervals.append(curInterval)
