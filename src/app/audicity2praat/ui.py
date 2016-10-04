import gi
import os
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

class MainWindow(Gtk.Window):
    def __init__(self, control):
        self.control = control
        Gtk.Window.__init__(self, title="Audacity2Praat")
        self.set_default_size(50, 50)
        self.set_position(Gtk.WindowPosition.CENTER)

        self.box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        self.add(self.box)

        self.label = Gtk.Label("ready")
        self.box.pack_start(self.label, True, True, 0)

        self.button = Gtk.Button(label="Select Audacity file")
        self.button.connect("clicked", self.onButtonClicked)
        self.box.pack_start(self.button, True, True, 0)

        self.connect("delete-event", Gtk.main_quit)

    def toShow(self):
        self.show_all()
        Gtk.main()

    def onButtonClicked(self, widget):
        dialog = Gtk.FileChooserDialog("Please choose the labels file", self,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
                                        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            origFile = dialog.get_filename()
            self.control.parseAudicity(origFile)

            newFile = os.path.splitext(origFile)[0]
            self.control.saveResults(newFile)

        dialog.destroy()
