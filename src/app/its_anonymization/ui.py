from gi.repository import Gtk
from debug import myDebug
from driver import Driver


class MainWindow:
    def __init__(self):
        self.driver = Driver()
        self.fileList = []
        self.confList = self.driver.getConfList()

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
            "config": self.openConfig,
            "selectFiles": self.selectFiles,
            "finishConf": self.finishConf,
            "changeSelect": self.changeSelect
        }
        self.builder.connect_signals(handlers)

    def selectFiles(self, button):
        dialog = Gtk.FileChooserDialog("Please choose its files",
                                       self.window,
                                       Gtk.FileChooserAction.OPEN,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_select_multiple(True)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            self.fileList = dialog.get_filenames()
        else:
            myDebug("file choose dialog: ", response)

        self.driver.setFileList(self.fileList)
        dialog.destroy()

    def openConfig(self, button):
        self.config.show_all()

    def changeSelect(self, button, data=None):
        if (button.get_active()):
            index = int(button.get_name())
            content = button.get_label()
            if (content == "keep"):
                self.confList[index - 1] = '0'
            elif (content == "delete"):
                self.confList[index - 1] = '1'
            else:
                self.confList[index - 1] = '2'

    def finishConf(self, widget):
        myDebug(self.confList)

    def run(self):
        self.window.show_all()
        Gtk.main()

if __name__ == '__main__':
    mWindow = MainWindow()
    mWindow.run()
