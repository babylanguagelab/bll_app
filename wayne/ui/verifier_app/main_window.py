from gi.repository import Gtk as gtk
from ui.verifier_app.verification_window import VerificationWindow
from utils.ui_utils import UIUtils
from utils.progress_dialog import ProgressDialog
from ui.verifier_app.open_pair_window import OpenPairWindow

class MainWindow():
    def __init__(self):
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Transcription Verifier')
        self.window.connect('destroy', lambda w: gtk.main_quit())
        self.window.set_border_width(10)
        self.window.set_default_size(150, 100)
                                         
        box = gtk.VBox(False, 5)
        open_button = UIUtils.create_button('Check TRS File', UIUtils.BUTTON_ICONS.OPEN)
        open_button.connect('clicked', lambda w: self.open_file())
        box.pack_start(open_button, False, False, 0)

        comp_button = UIUtils.create_button('Compare Files', UIUtils.BUTTON_ICONS.MERGE)
        comp_button.connect('clicked', lambda w: self.compare_files())
        box.pack_start(comp_button, False, False, 0)

        exit_button = UIUtils.create_button('Exit', UIUtils.BUTTON_ICONS.EXIT)
        exit_button.connect('clicked', lambda w: gtk.main_quit())
        box.pack_start(exit_button, False, False, 0)

        self.window.add(box)
        self.window.show_all()

    def open_file(self):
        filename = UIUtils.open_file('Select trs file', [UIUtils.TRS_FILE_FILTER, UIUtils.ALL_FILE_FILTER])

        if filename:
            progress_dialog = ProgressDialog('Processing File...', ['Parsing trs file...', 'Validating data...', 'Building UI...'])
            progress_dialog.show()
            VerificationWindow(filename, progress_dialog)

    def compare_files(self):
        OpenPairWindow()
