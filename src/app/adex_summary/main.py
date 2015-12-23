import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import logging as lg
from debug import init_debug 
from controller import Controller


class MainWindow:
    def __init__(self):
        init_debug()
        self.builder = Gtk.Builder()
        self.builder.add_from_file("UI.glade")

        self.window = self.builder.get_object("g_main_window")
        self.connect_signals()

        self.controller = Controller()

    def connect_signals(self):
        handlers = {
            "g_main_quit": Gtk.main_quit,
            "g_add_ADEX": self.add_Adex_files,
            "g_run_configs": self.run_configs
        }
        self.builder.connect_signals(handlers)

    def add_Adex_files(self, button):
        dialog = Gtk.FileChooserDialog("Please choose ADEX folders",
                                       self.window,
                                       Gtk.FileChooserAction.SELECT_FOLDER,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_select_multiple(True)
        dialog.set_local_only(True)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            self.controller.ADEX_folders = dialog.get_filenames()

        dialog.destroy()

    def run_configs(self, button):
        if (len(self.controller.ADEX_folders) == 0):
            dialog = Gtk.MessageDialog(self.window,
                                       Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                       Gtk.MessageType.INFO, Gtk.ButtonsType.OK,
                                       "Please choose ADEX folders first!")
            dialog.run()
            dialog.destroy()
            return

        self.controller.run()

    def show(self):
        self.window.show_all()
        Gtk.main()


mMain = MainWindow()
mMain.show()
