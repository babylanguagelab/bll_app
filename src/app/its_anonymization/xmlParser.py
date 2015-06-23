import xml.etree.cElementTree as ET


# incremental xml parser
class XMLParser:
    def __init__(self, filename):
        self.tree = ET.iterparse(filename, events=('start', 'end'))
        self.parse()

    def parse(self):
        for event, elem in self.tree:
            if event == 'end':
                elem.clear()


# normal xml parser, read xml file into memory
class XMLParser2:
    def __init__(self, filename):
        self.tree = ET.parse(filename)
        self.root = self.tree.getroot()
        self.filename = filename

    def findAttr(self, xpath, key):
        node = self.root.find(xpath + "[@" + key + "]")
        return node.attrib

    def changeAttr(self, path, key, value, single=True):
        if (single):
            node = self.root.find(path)
            node.set(key, value)
        else:
            nodes = self.root.findall(path)
            for node in nodes:
                node.set(key, value)

    def write(self, newFilename):
        self.tree.write(newFilename)

    # show function

mParser = XMLParser2("test.xml")
print mParser.findAttr("./country", "name")
