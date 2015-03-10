from gi.repository import Gtk as gtk
from ui.splitter_app.options_window import OptionsWindow
from utils.ui_utils import UIUtils
from utils.progress_dialog import ProgressDialog
from parsers.trs_splitter import TRSMerger

class MainWindow():
    def __init__(self):
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('TRS Splitter')
        self.window.connect('destroy', lambda w: gtk.main_quit())
        self.window.set_border_width(10)
        self.window.set_default_size(150, 100)
                                         
        box = gtk.VBox(False, 5)
        split_button = UIUtils.create_button('Split File', UIUtils.BUTTON_ICONS.SPLIT)
        split_button.connect('clicked', lambda w: self.split_file())
        box.pack_start(split_button, False, False, 0)
        split_button.show()

        merge_button = UIUtils.create_button('Merge Files', UIUtils.BUTTON_ICONS.MERGE)
        merge_button.connect('clicked', lambda w: self.merge_files())
        box.pack_start(merge_button, False, False, 0)
        merge_button.show()

        exit_button = UIUtils.create_button('Exit', UIUtils.BUTTON_ICONS.EXIT)
        exit_button.connect('clicked', lambda w: gtk.main_quit())
        box.pack_start(exit_button, False, False, 0)
        exit_button.show()

        self.window.add(box)
        box.show()
        self.window.show()

    def split_file(self):
        filename = UIUtils.open_file('Select trs file', [UIUtils.TRS_FILE_FILTER, UIUtils.ALL_FILE_FILTER])

        dest_folder = None
        if filename:
            dialog = gtk.FileChooserDialog(title='Select Folder for Split Files',
                                           action=gtk.FileChooserAction.SELECT_FOLDER,
                                           buttons=(gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL, gtk.STOCK_OPEN, gtk.ResponseType.OK))
            dialog.set_default_response(gtk.ResponseType.OK)

            response = dialog.run()
            if response == gtk.ResponseType.OK:
                dest_folder = dialog.get_filename()
                OptionsWindow(filename, dest_folder)

            dialog.destroy()

    def merge_files(self):
        dialog = gtk.FileChooserDialog(title='Select Folder Containing Split Files',
                                           action=gtk.FileChooserAction.SELECT_FOLDER,
                                           buttons=(gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL, gtk.STOCK_OPEN, gtk.ResponseType.OK))
        dialog.set_default_response(gtk.ResponseType.OK)

        response = dialog.run()
        if response == gtk.ResponseType.OK:
            src_folder = dialog.get_filename()
            dialog.destroy()

            progress_dialog = ProgressDialog(title='Merging files', phases=['Merging TRS files...'])
            progress_dialog.show()
            merger = TRSMerger(src_folder)
            merger.merge(progress_dialog.set_fraction)

        else:
            dialog.destroy()
