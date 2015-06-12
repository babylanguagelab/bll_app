from gi.repository import Gtk as gtk
from utils.ui_utils import UIUtils
import xml.etree.cElementTree as ET
import os.path


class XMLParser2:
    def __init__(self, filename):
        self.tree = ET.parse(filename)
        self.root = self.tree.getroot()
        self.filename = filename

    def changeAttr(self, path, key, value, single=True):
        if (single):
            node = self.root.find(path)
            if (node is not None):
                node.set(key, value)
        else:
            nodes = self.root.findall(path)
            for node in nodes:
                node.set(key, value)

    def getAttr(self, path, key):
        node = self.root.find(path)
        return node.get(key)

    def save(self):
        newFilename = os.path.splitext(self.filename)[0] + "_dummy" + os.path.splitext(self.filename)[1]
        self.tree.write(newFilename)


class DummyNode:
    def __init__(self, tag, path, value):
        self.tag = tag
        self.path = path
        self.value = value
        self.use = True

dummy_info = [['LocalTime', './ProcessingUnit/UPL_Header/TransferredUPL/RecordingInformation/TransferTime', '2015-06-01T00:00:00'],
              ['TimeZone', './ProcessingUnit/UPL_Header/TransferredUPL/RecordingInformation/TransferTime', 'UTC'],
              ['UTCTime', './ProcessingUnit/UPL_Header/TransferredUPL/RecordingInformation/TransferTime', '2015-06-01T00:00:00'],
              ['SerialNumber', './ProcessingUnit/UPL_Header/TransferredUPL/RecorderInformation/SRDInfo', '0000'],
              ['ChildKey', './ProcessingUnit/UPL_Header/TransferredUPL/ApplicationData/PrimaryChild', '0000000000000000'],
              ['DOB', './ProcessingUnit/UPL_Header/TransferredUPL/ApplicationData/PrimaryChild', '2000-01-01']]

class MainWindow():
    def __init__(self):
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('ITS Anonymity')
        self.window.connect('destroy', lambda w: gtk.main_quit())
        self.window.set_border_width(10)
        self.window.set_default_size(240, 320)

        box = gtk.VBox(False, 5)
        open_button = UIUtils.create_button('Open ITS File',
                                            UIUtils.BUTTON_ICONS.OPEN)
        open_button.connect('clicked', lambda w: self.open_file())
        box.pack_start(open_button, True, True, 0)

        config_button = UIUtils.create_button('Configure template',
                                              UIUtils.BUTTON_ICONS.MERGE)
        config_button.connect('clicked', lambda w: self.open_config())
        box.pack_start(config_button, True, True, 0)

        run_button = UIUtils.create_button('Run', UIUtils.BUTTON_ICONS.RUN)
        run_button.connect('clicked', lambda w: self.run())
        box.pack_start(run_button, True, True, 0)

        self.window.add(box)
        self.window.show_all()

    def open_file(self):
        self.filename = UIUtils.open_file('Select its file',
                                     [UIUtils.ITS_FILE_FILTER,
                                      UIUtils.ALL_FILE_FILTER])
        self.xmlParser = XMLParser2(self.filename)

    def open_config(self):
        self.config_window = gtk.Window()
        self.config_window.set_default_size(640, 480)
        self.config_window.connect('destroy', self.close_config)

        self.config_model = gtk.ListStore(bool, str, str)
        for i in dummy_info:
            self.config_model.append([True, i[0], i[2]])

        self.config_view = gtk.TreeView(self.config_model)

        rendered_toggle = gtk.CellRendererToggle()
        rendered_toggle.connect("toggled", self.on_cell_toggled)
        column_toggle = gtk.TreeViewColumn("mask", rendered_toggle, active=0)
        self.config_view.append_column(column_toggle)

        rendered_text = gtk.CellRendererText()
        column_text = gtk.TreeViewColumn("attributes", rendered_text, text=1)
        self.config_view.append_column(column_text)

        column_editabletext = gtk.CellRendererText()
        column_editabletext.set_property("editable", True)
        column_editabletext.connect("edited", self.on_cell_edit)
        column_text = gtk.TreeViewColumn("value", column_editabletext, text=2)
        self.config_view.append_column(column_text)

        self.config_window.add(self.config_view)
        self.window.hide()
        self.config_window.show_all()

    def on_cell_toggled(self, widget, path):
        self.config_model[path][0] = not self.config_model[path][0]

    def on_cell_edit(self, widget, path, text):
        self.config_model[path][2] = text

    def close_config(self, widget):
        # [BigFix] get new list and save config
        self.config_window.hide()
        self.window.show_all()

    def run(self):
        self.run_dialog = gtk.Dialog("run", self.window, 0)

        label = gtk.Label("Job complete! \nMake sure the filename is safe.")
        vbox = self.run_dialog.get_content_area()
        vbox.pack_start(label, False, False, 0)

        for i in dummy_info:
            self.xmlParser.changeAttr(i[1], i[0], i[2])
        self.xmlParser.save()

        button = gtk.Button("OK")
        vbox.pack_start(button, False, False, 0)
        button.connect('clicked', lambda w: gtk.main_quit())
        self.run_dialog.show_all()
