from gi.repository import Gtk as gtk
import os
from db.bll_database import BLLDatabase, DBConstants
from utils.progress_dialog import ProgressDialog
from utils.ui_utils import UIUtils
from utils.naptime import Naptime

class DBWindow():
    def __init__(self):
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Naptime Filter')
        self.window.connect('destroy', lambda x: self.window.destroy())
        self.window.set_border_width(10)
        self.window.set_default_size(210, 150)

        self.build_window()
        
        self.window.show_all()

    def build_window(self):
        vbox = gtk.VBox()

        last_update_label = gtk.Label()
        markup = 'None'
        if DBConstants.SETTINGS.LAST_NAPTIME_UPDATE:
            markup = UIUtils.utc_to_local_str(DBConstants.SETTINGS.LAST_NAPTIME_UPDATE)
        last_update_label.set_markup('Last Update: <b>%s</b>' % (markup))
        vbox.pack_start(last_update_label, True, True, 0)

        last_path_label = gtk.Label()
        last_path_label.set_markup('Last Path: <b>%s</b>' % (str(DBConstants.SETTINGS.LAST_NAPTIME_FOLDER)))
        vbox.pack_start(last_path_label, True, True, 0)

        hbox = gtk.HBox()
        folder_label = gtk.Label('Naptime Folder:')
        folder_entry = gtk.Entry()
        folder_entry.set_width_chars(50)
        browse_button = gtk.Button('Browse')
        browse_button.connect('clicked', lambda w: UIUtils.browse_folder('Select naptime folder', folder_entry))#, [UIUtils.CSV_FILE_FILTER, UIUtils.ALL_FILE_FILTER]))
        hbox.pack_start(folder_label, True, False, 0)
        hbox.pack_start(folder_entry, True, False, 0)
        hbox.pack_start(browse_button, True, False, 0)
        vbox.pack_start(hbox, True, False, 0)

        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.ButtonBoxStyle.EDGE)
        cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL, label='Cancel')
        cancel_button.connect('clicked', lambda w: self.window.destroy())
        button_box.add(cancel_button)
        
        update_button = gtk.Button(stock=gtk.STOCK_OK, label='Update')
        update_button.connect('clicked',
                              lambda w: self.update_db(folder_entry.get_text())
        )
        button_box.add(update_button)

        vbox.pack_end(button_box, True, True, 0)
        
        self.window.add(vbox)

    def update_db(self, path):
        prog_diag = ProgressDialog(title='Processing...', phases=['Please Wait'])
        prog_diag.show()
        
        db = BLLDatabase()
        error_filenames = Naptime.update_naptime_data(db, path, prog_diag=prog_diag)
        db.close()
        prog_diag.ensure_finish()

        if error_filenames:
            UIUtils.show_message_dialog(
                'Unable to process the following files - see the log file for details:\n' +
                '\n'.join(map(os.path.basename, error_filenames)),
                dialog_type=gtk.MessageType.ERROR
            )
            
        else:
            UIUtils.show_message_dialog('Naptime database table updated successfully.')
            self.window.destroy()
