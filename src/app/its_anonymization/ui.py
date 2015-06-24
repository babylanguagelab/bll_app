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

        self.config_rbutton = []
        for i in range(3, 3 * len(self.confList) + 3):
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
            "selectFiles": self.selectFiles,
            "config": self.openConfig,
            "changeSelect": self.changeConfig,
            "finishConf": self.finishConfig,
            "run": self.run
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
        for i in range(len(self.confList)):
            if self.confList[i] == '0':
                self.config_rbutton[i*3].set_active(True)
            elif self.confList[i] == '1':
                self.config_rbutton[i*3 + 1].set_active(True)
            else:
                self.config_rbutton[i*3 + 2].set_active(True)
        self.config.show_all()

    def changeConfig(self, button, data=None):
        if (button.get_active()):
            index = int(button.get_name()) - 1
            content = button.get_label()
            if (content == "keep"):
                self.confList[index] = '0'
            elif (content == "delete"):
                self.confList[index] = '1'
            else:
                self.confList[index] = '2'

    # fun: load default
    # fun: save as default

    def finishConfig(self, widget):
        self.driver.setConfList(self.confList)
        self.config.hide()

    def run(self, widget):
        result = self.driver.run()
        # 1 - file list is empty
        # 2 - config list is empty
        myDebug(result)

    def show(self):
        self.window.show_all()
        Gtk.main()

if __name__ == '__main__':
    mWindow = MainWindow()
    mWindow.show()
