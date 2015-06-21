from gi.repository import Gtk


class MainWindow:
    def __init__(self):
        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui.glade")
        self.window = self.builder.get_object("main")
        self.config = self.builder.get_object("config")
        self.config_statusbar = self.builder.get_object("statusbar")
        self.config_context_id = self.config_statusbar.get_context_id("")
        self.config_statusbar.push(self.config_context_id,
                                   "will show some descriptions here.")
        self.connect_signals()

    def connect_signals(self):
        handlers = {
            "mainExit": Gtk.main_quit,
            "config": self.openConfig
        }
        self.builder.connect_signals(handlers)

    def openConfig(self, button):
        self.config.show_all()

    def run(self):
        self.window.show_all()
        Gtk.main()
