from gi.repository import Gtk as gtk
from utils.ui_utils import UIUtils
from utils.progress_dialog import ProgressDialog
from parsers.trs_splitter import TRSSplitter

class OptionsWindow():
    def __init__(self, filename, dest_folder):
        self.filename = filename
        self.dest_folder = dest_folder
        
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Select Options')
        self.window.set_border_width(10)
        self.window.set_default_size(150, 100)

        vbox = gtk.VBox()

        entry_box, hours_spinner, mins_spinner, secs_spinner = UIUtils.get_time_spinners(mins=15)

        button_box = gtk.HButtonBox()
        cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel_button.connect('clicked', lambda w: self.window.destroy())
        button_box.pack_start(cancel_button, True, True, 0)
        ok_button = gtk.Button(stock=gtk.STOCK_OK)
        ok_button.connect('clicked', lambda w: self.split_file(
                hours_spinner.get_value_as_int(),
                mins_spinner.get_value_as_int(),
                secs_spinner.get_value_as_int()))
        button_box.pack_start(ok_button, True, True, 0)
        button_box.set_layout(gtk.ButtonBoxStyle.EDGE)

        vbox.pack_start(gtk.Label('Please enter a length for the split segments (hour:min:sec):'), True, True, 0)
        vbox.pack_start(entry_box, True, True, 0)
        vbox.pack_end(button_box, True, True, 0)
        
        self.window.add(vbox)

        self.window.show_all()

    def split_file(self, hours, mins, secs):
        win_len = hours * 60 * 60 + mins * 60 + secs
        
        progress_dialog = ProgressDialog(title='Splitting file', phases=['Splitting TRS file...'])
        splitter = TRSSplitter(self.filename, self.dest_folder)
        
        self.window.destroy()
        
        progress_dialog.show()
        splitter.split(win_len, progress_dialog.set_fraction)
    
