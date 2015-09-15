from gi.repository import Gtk as gtk
from utils.ui_utils import UIUtils
from utils.progress_dialog import ProgressDialog
from ui.wh_freq_app.freq_window import FreqWindow

class MainWindow():
    def __init__(self):
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('WH-Frequency Counter')
        self.window.connect('destroy', lambda w: gtk.main_quit())
        self.window.set_border_width(10)
        self.window.set_default_size(150, 100)

        box = gtk.VBox(False, 5)
        open_button = UIUtils.create_button('Open TRS File', UIUtils.BUTTON_ICONS.OPEN)
        open_button.connect('clicked', lambda w: self.open_file())
        box.pack_start(open_button, False, False, 0)
        open_button.show()

        exit_button = UIUtils.create_button('Exit', UIUtils.BUTTON_ICONS.EXIT)
        exit_button.connect('clicked', lambda w: gtk.main_quit())
        box.pack_start(exit_button, False, False, 0)
        exit_button.show()

        self.window.add(box)
        box.show()
        self.window.show()

    def open_file(self):
        filename = UIUtils.open_file('Select trs file', [UIUtils.TRS_FILE_FILTER, UIUtils.ALL_FILE_FILTER])

        if filename:
            progress_dialog = ProgressDialog('Processing File...', ['Parsing trs file...'])
            progress_dialog.show()
            FreqWindow(filename, progress_dialog)
