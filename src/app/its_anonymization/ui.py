from gi.repository import Gtk
from debug import myDebug
from driver import Driver

class MainWindow:
    def __init__(self):
        self.driver = Driver()
        self.file_list = []
        self.conf_list = self.driver.get_conf_list()

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
                                   "will show some descriptions here.")

        self.connect_signals()

    def connect_signals(self):
        handlers = {
            "mainExit": Gtk.main_quit,
            "selectFiles": self.select_files,
            "config": self.open_config,
            "changeSelect": self.change_config,
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

        self.driver.set_file_list(self.file_list)
        dialog.destroy()

    def open_config(self, button):
        for i in range(len(self.conf_list)):
            print i, self.conf_list[i]
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
        self.driver.set_conf_list(self.conf_list)
        self.config.hide()

    def run(self, widget):
        result = self.driver.run()
        if result == 1:
            myDebug("file list is empty!")
        elif result == 2:
            myDebug("config list is empty")

    def show(self):
        self.window.show_all()
        Gtk.main()

if __name__ == '__main__':
    mWindow = MainWindow()
    mWindow.show()
