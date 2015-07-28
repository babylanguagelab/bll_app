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
        self.note = self.builder.get_object("note")
        self.config = self.builder.get_object("config")

        self.config_rbutton = []
        for i in range(18):
            self.config_rbutton.append(
                self.builder.get_object("radiobutton" + str(i)))
        self.config_entry = []
        for i in range(4):
            self.config_entry.append(
                self.builder.get_object("entry" + str(i)))

        self.config_statusbar = self.builder.get_object("statusbar")
        self.config_context_id = self.config_statusbar.get_context_id("0")
        self.config_statusbar.push(self.config_context_id,
                                   "setup item list")

        self.connect_signals()

    def connect_signals(self):
        handlers = {
            "mainExit": Gtk.main_quit,
            "selectFiles": self.select_files,
            "config": self.open_config,
            "changeSelect": self.change_rbuttons,
            "entryChanged": self.change_entry,
            "inMessage": self.change_message,
            "outMessage": self.restore_message,
            "saveConf": self.save_config,
            "finishConf": self.finish_config,
            "run": self.run
        }
        self.builder.connect_signals(handlers)

    def select_files(self, button):
        dialog = Gtk.FileChooserDialog("Please choose its folder",
                                       self.window,
                                       Gtk.FileChooserAction.SELECT_FOLDER,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            selected = dialog.get_filenames()
        else:
            myDebug("file choose dialog: ", response)

        self.control.set_files(selected[0])
        dialog.destroy()

    def open_config(self, button):
        conf = self.control.get_conf()
        items = conf.items

        for i in range(9):
            config_list = conf.get_config(items[i])
            config = config_list[0]
            value = config_list[1]
            # print i, items[i], config.get_config(items[i])
            if config != 0:
                self.config_rbutton[i*2 + 1].set_active(True)

        self.config.show_all()

    def change_rbuttons(self, button, data=None):
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

    def change_entry(self, widget, data=None):
        index = int(widget.get_name())
        text = widget.get_text()
        config = self.control.get_conf()
        key = config.items[index]

        self.config_rbutton[index*2 + 1].set_active(True)
        self.control.set_conf(key, 2, text)

    def save_config(self, widget, data=None):
        self.control.save_config()

    def finish_config(self, widget):
        self.config.hide()

    def change_message(self, widget, data=None):
        name = widget.get_name()
        message = ""

        if name == "ok":
            message = "return to main menu"
        elif name == "save":
            message = "save as default value"
        elif name == '0':
            message = "Serial Number"
        elif name == '3':
            message = "Child ID"
        elif name == '4':
            message = "Child Key"
        elif name == '6':
            message = "DOB"
        else:
            message = "unkonw"

        self.config_statusbar.push(self.config_context_id, message)

    def restore_message(self, widget, data=None):
        self.config_statusbar.pop(self.config_context_id)

    def run(self, widget):
        result = self.control.run()
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
        self.note.run()
        self.note.destroy()
        self.window.show_all()
        Gtk.main()

if __name__ == '__main__':
    mWindow = MainWindow()
    mWindow.show()
