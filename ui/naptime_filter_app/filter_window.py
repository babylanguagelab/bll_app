from gi.repository import Gtk as gtk
import os
import glob
from utils.enum import Enum
from utils.ui_utils import UIUtils
from utils.naptime import Naptime
from db.bll_database import BLLDatabase
from utils.progress_dialog import ProgressDialog

class FilterWindow():
    FILTER_TYPES = Enum('FILE FOLDER'.split())
    def __init__(self, filter_type):
        self.filter_type = filter_type
        
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Naptime Filter')
        self.window.connect('destroy', lambda x: self.window.destroy())
        self.window.set_border_width(10)
        self.window.set_default_size(210, 150)

        self._build_window()
        
        self.window.show_all()

    def _build_window(self):
        vbox = gtk.VBox()
        
        #table = gtk.Table(2,3, False)
        grid = gtk.Grid()
        
        src_label = gtk.Label('Source:')
        #table.attach(src_label, 0, 1, 0, 1, gtk.EXPAND, gtk.EXPAND)
        grid.attach(src_label, 0, 0, 1, 1)
        src_entry = gtk.Entry()
        src_entry.set_width_chars(50)
        #table.attach(src_entry, 1, 2, 0, 1, gtk.EXPAND, gtk.EXPAND)
        grid.attach(src_entry, 1, 0, 1, 1)
        src_browse_button = gtk.Button('Browse')
        #table.attach(src_browse_button, 2, 3, 0, 1, gtk.EXPAND, gtk.EXPAND)
        grid.attach(src_browse_button, 2, 0, 1, 1)

        if self.filter_type == FilterWindow.FILTER_TYPES.FILE:
            src_browse_button.connect('clicked', lambda w: UIUtils.browse_file('Select file', src_entry, [UIUtils.CSV_FILE_FILTER, UIUtils.ALL_FILE_FILTER]))
        elif self.filter_type == FilterWindow.FILTER_TYPES.FOLDER:
            src_browse_button.connect('clicked', lambda w: UIUtils.browse_folder('Select folder', src_entry)) #[UIUtils.CSV_FILE_FILTER, UIUtils.ALL_FILE_FILTER]))

        dest_label = gtk.Label('Destination:')
        #table.attach(dest_label, 0, 1, 1, 2, gtk.EXPAND, gtk.EXPAND)
        grid.attach(dest_label, 0, 1, 1, 1)
        dest_entry = gtk.Entry()
        dest_entry.set_width_chars(50)
        #table.attach(dest_entry, 1, 2, 1, 2, gtk.EXPAND, gtk.EXPAND)
        grid.attach(dest_entry, 1, 1, 1, 1)
        dest_browse_button = gtk.Button('Browse')
        #table.attach(dest_browse_button, 2, 3, 1, 2, gtk.EXPAND, gtk.EXPAND)
        grid.attach(dest_browse_button, 2, 1, 1, 1)

        dest_browse_button.connect('clicked', lambda w: UIUtils.browse_folder('Select folder', dest_entry))#, [UIUtils.CSV_FILE_FILTER, UIUtils.ALL_FILE_FILTER]))

        vbox.pack_start(grid, True, True, 0)
            
        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.ButtonBoxStyle.EDGE)
        cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL, label='Cancel')
        cancel_button.connect('clicked', lambda w: self.window.destroy())
        button_box.add(cancel_button)

        ok_button = gtk.Button(stock=gtk.STOCK_OK, label='Ok')
        ok_button.connect('clicked', lambda w: self._process(src_entry.get_text(), dest_entry.get_text()))
        button_box.add(ok_button)

        vbox.pack_start(button_box, True, True, 0)
        
        self.window.add(vbox)

    def _process(self, src, dest):
        in_files = None
        out_files = None

        if src and os.path.exists(src):
            src = src.replace('\\', '/')

            if self.filter_type == FilterWindow.FILTER_TYPES.FILE:
                if not src.endswith('.csv'):
                    src += '.csv'
            elif self.filter_type == FilterWindow.FILTER_TYPES.FOLDER:
                if src.endswith('/'):
                    src = src[:-1]
            
            if os.path.isdir(src):
                in_files = map(lambda name: name.replace('\\', '/'), glob.glob('%s/*.csv' % (src)))
            else:
                in_files = [src]

        else:
            UIUtils.show_message_dialog('Source path does not exist!')
            return

        if dest and os.path.exists(dest):
            dest = dest.replace('\\', '/')
            if dest.endswith('/'):
                dest = dest[:-1]
            out_files = map(lambda name: '%s/%s-noNaps.csv' % (dest, os.path.basename(name)[:-4]), in_files)

        else:
            UIUtils.show_message_dialog('Destination path does not exist!')
            return

        self.window.destroy()
        prog_diag = ProgressDialog(
            title='Processing...',
            phases=['Please Wait']
        )
        prog_diag.show()

        db = BLLDatabase()
        
        for i in range(len(in_files)):
            Naptime.filter_file(db, in_files[i], out_files[i])
            prog_diag.set_fraction(float(i + 1) / float(len(in_files)))
            
        db.close()
        prog_diag.ensure_finish()        
