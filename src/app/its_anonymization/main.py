#! /usr/bin/python2
from gi.repository import Gtk
import xml.etree.cElementTree as ET
import os.path
import random


class MainWindow:
    def __init__(self, filename):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("main.glade")
        self.window = self.builder.get_object("window")
        self.scroolWindow = self.builder.get_object("scrolledwindow1")

        handlers = {
            "exit": Gtk.main_quit
        }
        self.builder.connect_signals(handlers)

    def show(self):
        self.window.show_all()


class ItsNode:
    def __init__(self, tag, attrList):
        self.name = tag
        self.attributes = attrList
        self.children = []

    def addAttr(self, key, value):
        self.attributes[key] = value

    def addChild(self, child):
        self.children.append(child)

    def showNode(self, node, indent):
        print indent + "->" + node.name
        for x in node.attributes:
            print indent + " *" + x + ":" + node.attributes[x]

        if (len(node.children) > 0):
            for i in node.children:
                node.showNode(i, "  " + indent)

    def show(self):
        for i in self.children:
            self.showNode(i, "")


class dummyGenerater():
    def __init__(self):
        self.seed = random.seed()

    def genRangeInt(self, size):
        tmp = [str(random.randint(1, 9)) for x in range(size)]
        return ''.join(tmp)


class XMLParser2:
    def __init__(self, filename):
        self.tree = ET.parse(filename)
        self.root = self.tree.getroot()
        self.filename = filename

    def changeAttr(self, path, key, value, single=True):
        if (single):
            node = self.root.find(path)
            node.set(key, value)
        else:
            nodes = self.root.findall(path)
            for node in nodes:
                node.set(key, value)

    def write(self):
        newFilename = os.path.splitext(self.filename)[0] + "_dummy" + os.path.splitext(self.filename)[1]
        self.tree.write(newFilename)


class XMLParser:
    def __init__(self, filename):
        self.tree = ET.iterparse(filename, events=('start', 'end'))
        self.parse()

    def parse(self):
        _, root = next(self.tree)
        self.root = ItsNode(root.tag, root.attrib)
        nodeStack = []
        IdentifyHashMap = {}

        top = lambda x: x[len(x) - 1]
        for event, elem in self.tree:
            if event == 'start':
                # if this is a node without text, collect attrib first.
                if ((elem.text is None) or elem.text.isspace()):
                    newNode = ItsNode(elem.tag, elem.attrib)
                    nodeStack.append(newNode)
                else:
                    if (len(nodeStack) >= 1):
                        top(nodeStack).addAttr(elem.tag, elem.text)
                    else:
                        self.root.addAttr(elem.tag, elem.text)
            elif event == 'end':
                if (elem.tag == root.tag):
                    continue
                # after collecting attrib, add to its parent.
                if ((elem.text is None) or elem.text.isspace()):
                    cur = nodeStack.pop()
                    if (len(nodeStack) >= 1):
                        top(nodeStack).addChild(cur)
                    else:
                        self.root.addChild(cur)
                else:
                    continue
                elem.clear()

    def show(self):
        root = self.root
        root.show()

    # function: save as file

# if __name__ == "__main__":
# mainWindow = MainWindow("main.glade")
data = XMLParser2("test2.xml")
data.changeAttr('./ProcessingUnit/UPL_Header/TransferredUPL/RecordingInformation/TransferTime', 'LocalTime', 'hao')
data.write()
#ran = dummyGenerater()
#print ran.genRangeInt(5)
# data.show()
# mainWindow.show()
# Gtk.main()
