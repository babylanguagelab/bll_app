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


# normal xml parser, read the xml file into memory
class XMLParser2:
    def __init__(self, filename):
        self.tree = ET.parse(filename)
        self.root = self.tree.getroot()
        self.filename = filename

    def getAttr(self, xpath, key):
        nodeList = self.root.findall(xpath)
        return [x.attrib[key] for x in nodeList]

    def setAttr(self, path, key, value):
        nodeList = self.root.findall(path)
        for x in nodeList:
            x.attrib[key] = value

    def delAttr(self, path, key):
        nodeList = self.root.findall(path)
        for x in nodeList:
            del x.attrib[key]

    def save(self, newFilename):
        self.tree.write(newFilename)
