from gi.repository import Gtk
from myDebug import myDebug
from controller import Controller


class MainWindow:
    def __init__(self):
        self.control = Controller()
        self.file_list = []

        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui.glade")

        self.window = self.builder.get_object("main")
        self.config = self.builder.get_object("config")

        self.config_rbutton = []
        for i in range(30):
            self.config_rbutton.append(
                self.builder.get_object("radiobutton" + str(i)))

        self.config_statusbar = self.builder.get_object("statusbar")
        self.config_context_id = self.config_statusbar.get_context_id("")
        self.config_statusbar.push(self.config_context_id,
                                   "configure behavior on each domain.")

        self.connect_signals()

    def connect_signals(self):
        handlers = {
            "mainExit": Gtk.main_quit,
            "selectFiles": self.select_files,
            "config": self.open_config,
            "changeSelect": self.change_config,
            "inMessage": self.message_config,
            "saveConf": self.save_config,
            "finishConf": self.finish_config,
            "run": self.run
        }
        self.builder.connect_signals(handlers)

    def select_files(self, button):
        dialog = Gtk.FileChooserDialog("Please choose its files",
                                       self.window,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_select_multiple(True)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            self.file_list = dialog.get_filenames()
        else:
            myDebug("file choose dialog: ", response)

        self.controller.set_file_list(self.file_list)
        dialog.destroy()

    def open_config(self, button):
        config = self.control.get_conf()
        items = config.items

        for i in range(10):
            # print i, items[i], config.get_config(items[i])
            if config.get_config(items[i]) == 1:
                self.config_rbutton[i*3 + 1].set_active(True)
            elif config.get_config(items[i]) == 2:
                self.config_rbutton[i*3 + 2].set_active(True)

        self.config.show_all()

    def change_config(self, button, data=None):
        config = self.control.get_conf()

        if button.get_active():
            index = int(button.get_name())
            change = button.get_label()
            key = config.items[index]
            # print index, change, key, change

            if change == "keep":
                self.control.set_conf(key, 0)
            elif change == "delete":
                self.control.set_conf(key, 1)
            else:
                self.control.set_conf(key, 2)

    def save_config(self, widget, data=None):
        self.control.save_config()

    def finish_config(self, widget):
        self.config.hide()

    def message_config(self, widget, data):
        name = widget.get_name()
        message = ""

        if name == "ok":
            message = "return to main menu"
        elif name == "save":
            message = "save as default value"

        self.config_statusbar.push(self.config_context_id, message)

    def run(self, widget):
        result = self.controller.run()
        message = ""

        if result == 1:
            message = "Error: You haven't chosen any files yet!"
        elif result == 2:
            message = "Error: Configuration is empty!"
        else:
            message = "Make sure the filename is also anonymous."

        dialog = Gtk.MessageDialog(self.window,
                                   0,
                                   Gtk.MessageType.INFO,
                                   Gtk.ButtonsType.OK,
                                   "Job complete!")
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()

    def show(self):
        self.window.show_all()
        Gtk.main()

if __name__ == '__main__':
    mWindow = MainWindow()
    mWindow.show()
