import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class MainWindow:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui.glade")

        self.window = self.builder.get_object("main")
        self.config = self.builder.get_object("config")
        self.connect_signals()

    def connect_signals(self):
        handlers = {
            "mainExit": Gtk.main_quit,
            "addNewOutput": self.add_new_output,
            "selectAdexFiles": self.add_Adex_files,
            "finishConfig": self.finish_config,
        }
        self.builder.connect_signals(handlers)

    def add_Adex_files(self, button):
        dialog = Gtk.FileChooserDialog("Please choose Adex folder",
                                       self.window,
                                       Gtk.FileChooserAction.SELECT_FOLDER,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            selected = dialog.get_filenames()

        dialog.destroy()

    def add_new_output(self, button):
        self.config.show_all()

    def finish_config(self, button):
        self.config.hide_all()

    def show(self):
        self.window.show_all()
        Gtk.main()
