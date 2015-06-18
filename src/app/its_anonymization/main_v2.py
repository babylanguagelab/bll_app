#!/usr/bin/python2
from gi.repository import Gtk


class MainWindow:
    def __init__(self, filename):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("main_v2.glade")
        self.window = self.builder.get_object("main")
        self.config = self.builder.get_object("config")
        self.config_statusbar = self.builder.get_object("statusbar")
        self.config_context_id = self.config_statusbar.get_context_id("")
        self.config_statusbar.push(self.config_context_id,
                                   "will show some descriptions here.")
        # self.config_statusbar.push

        handlers = {
            "mainExit": Gtk.main_quit,
            "config": self.openConfig
        }
        self.builder.connect_signals(handlers)

    def openConfig(self, button):
        self.config.show_all()

    def show(self):
        self.window.show_all()
        Gtk.main()

if __name__ == "__main__":
    mainWindow = MainWindow("main.glade")
    mainWindow.show()
