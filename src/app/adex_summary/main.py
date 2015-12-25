import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GObject
import logging as lg
from debug import init_debug
from controller import Controller


class MainWindow(GObject.GObject):
    __gsignals__ = {"start_task": (GObject.SIGNAL_RUN_FIRST, None, (int,)),
                    "stop_task": (GObject.SIGNAL_RUN_FIRST, None, (int,))}

    def __init__(self):
        GObject.GObject.__init__(self)
        init_debug()
        self.builder = Gtk.Builder()
        self.builder.add_from_file("UI.glade")

        self.window = self.builder.get_object("g_main_window")
        self.run_dialog = self.builder.get_object("g_run_dialog")
        self.connect_signals()

        self.controller = Controller()

    def do_start_task(self, data):
        self.controller.run()
        self.emit("stop_task", 0)

    def do_stop_task(self, data):
        self.run_dialog.hide()

    def connect_signals(self):
        handlers = {
            "g_main_quit": Gtk.main_quit,
            "g_add_ADEX": self.add_Adex_files,
            "g_run_finish": self.run_finish,
            "g_run_configs": self.run_configs
        }
        self.builder.connect_signals(handlers)

    # choose ADEX folders
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

    # run on all configurations
    def run_configs(self, button):
        if (len(self.controller.ADEX_folders) == 0):
            dialog = Gtk.MessageDialog(self.window,
                                       Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                       Gtk.MessageType.INFO, Gtk.ButtonsType.OK,
                                       "Please choose ADEX folders first!")
            dialog.run()
            dialog.destroy()
            return

        save_dialog = Gtk.FileChooserDialog("Please choose where to save output",
                                       self.window,
                                       Gtk.FileChooserAction.SAVE,
                                       (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT,
                                        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        save_dialog.set_local_only(True)
        response = save_dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            self.controller.output_file = save_dialog.get_filename()

        save_dialog.destroy()
        if not self.controller.output_file:
            lg.error("You haven't choose the place for output yet!")
            return

        self.run_dialog.show_all()
        while(Gtk.events_pending()):
            Gtk.main_iteration()

        self.emit("start-task", 0)

    def run_finish(self, button):
        self.run_dialog.hide()

    def show(self):
        self.window.show_all()
        Gtk.main()

mMain = MainWindow()
mMain.show()
