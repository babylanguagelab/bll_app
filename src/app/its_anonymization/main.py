from gi.repository import Gtk
from myDebug import myDebug
from controller import Controller


class MainWindow:
    def __init__(self):
        self.controller = Controller()
        self.file_list = []
        self.conf_list = self.controller.get_conf_list()

        self.builder = Gtk.Builder()
        self.builder.add_from_file("ui.glade")

        self.window = self.builder.get_object("main")
        self.config = self.builder.get_object("config")

        self.config_rbutton = []
        for i in range(3 * len(self.conf_list) + 2):
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
        # for i in range(len(self.conf_list)):
        for i in range(11):
            if self.conf_list[i] == '0':
                self.config_rbutton[i*3].set_active(True)
            elif self.conf_list[i] == '1':
                self.config_rbutton[i*3 + 1].set_active(True)
            else:
                self.config_rbutton[i*3 + 2].set_active(True)
        self.config.show_all()

    def change_config(self, button, data=None):
        if button.get_active():
            index = int(button.get_name())
            content = button.get_label()
            if content == "keep":
                self.conf_list[index] = '0'
            elif content == "delete":
                self.conf_list[index] = '1'
            else:
                self.conf_list[index] = '2'

    # fun: load default
    # fun: save as default

    def finish_config(self, widget):
        self.controller.set_conf_list(self.conf_list)
        self.config.hide()

    def message_config(self, widget, data):
        name = widget.get_name()
        message = ""

        if name == "ok":
            message = "return to main menu"
        if name == "reset":
            message = "reset to default value"
        if name == "save":
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
