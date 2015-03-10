from gi.repository import Gtk as gtk
from gi.repository import GObject as gobject
import datetime

from data_structs.check import Check
from db.bll_database import BLLDatabase
from test_window import TestWindow
from utils.ui_utils import UIUtils

class LoadWindow():
    def __init__(self):
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Load Check')
        self.window.connect('destroy', lambda w: self.window.destroy())
        self.window.set_border_width(10)
        self.window.set_default_size(1000, 400)

        vbox = gtk.VBox()

        treeview = self._build_treeview()
        scrolled_win = gtk.ScrolledWindow()
        scrolled_win.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
        scrolled_win.add(treeview)
        vbox.pack_start(scrolled_win, True, True, 0)

        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.ButtonBoxStyle.EDGE)
        cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL, label='Cancel')
        cancel_button.connect('clicked', lambda w: self.window.destroy())
        button_box.pack_start(cancel_button, False, False, 0)

        delete_button = gtk.Button(stock=gtk.STOCK_DELETE)
        delete_button.connect('clicked', lambda w: self._confirm_delete(treeview))
        button_box.pack_start(delete_button, False, False, 0)
        
        load_button = gtk.Button('Load')
        load_image = gtk.Image()
        load_image.set_from_stock(gtk.STOCK_EXECUTE, gtk.ICON_SIZE_BUTTON)
        load_button.set_image(load_image)
        load_button.connect('clicked', lambda w: self._load(treeview))
        button_box.pack_end(load_button, False, False, 0)
        
        vbox.pack_end(button_box, False, False, 0)
        vbox.pack_end(gtk.HSeparator(), False, False, 0)
        
        self.window.add(vbox)
        self.window.show_all()

    def _build_list_store(self):
        list_store = gtk.ListStore(gobject.TYPE_INT,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_INT,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   )
        db = BLLDatabase()
        checks_list = Check.db_select(db)
        for check in checks_list:
            created = UIUtils.get_db_timestamp_str(str(check.created)) if check.created != None else '-'
            last_run = UIUtils.get_db_timestamp_str(str(check.last_run)) if check.last_run != None else '-'
            completed = UIUtils.get_db_timestamp_str(str(check.completed)) if check.completed != None else '-'

            filters_str = ''
            if not check.filters:
                filters_str = '-'
            else:
                for i in range(len(check.filters)):
                    filters_str += check.filters[i].get_filter_desc_str()
                    if i < len(check.filters) - 1:
                        filters_str += ',\n'
                
            list_store.append([check.db_id,
                               check.name,
                               created,
                               completed,
                               last_run,
                               check.input_filename,
                               check.wav_filename,
                               check.default_context_padding,
                               str(check.pick_randomly),
                               filters_str,
                               ])
        db.close()

        return list_store

    def _build_treeview(self):
        list_store = self._build_list_store()

        treeview = gtk.TreeView(list_store)
        
        #create hidden id column
        col = gtk.TreeViewColumn('ID', gtk.CellRendererText(), text=0)
        col.set_visible(False)
        treeview.append_column(col)

        #create the rest of the columns
        column_names = ['Name', 'Created', 'Completed', 'Last Run', 'Input Filename', 'WAV Filename', 'Default Context padding (sec)', 'Pick Segs Randomly', 'Filters']
        for i in range(len(column_names)):
            col = gtk.TreeViewColumn(column_names[i], gtk.CellRendererText(), text=(i + 1))
            col.set_resizable(True)
            col.set_min_width( UIUtils.calc_treeview_col_min_width(column_names[i]) )
            treeview.append_column(col)

        return treeview

    def _confirm_delete(self, treeview):
        (model, it) = treeview.get_selection().get_selected()
        db_id = model.get_value(it, 0) if it else None

        if db_id != None:
            response = UIUtils.show_confirm_dialog('Are you sure you want to delete the selected check?')

            if response:
                db = BLLDatabase()
                rows_deleted = Check.db_select(db, [db_id])[0].db_delete(db)
                db.close()

                if rows_deleted > 0:
                    model.remove(it)

                else:
                    UIUtils.show_message_dialog('An error occurred and the check could not be deleted.')
        
        else:
            UIUtils.show_no_sel_dialog()

    def _load(self, treeview):
        (model, it) = treeview.get_selection().get_selected()
        db_id = model.get_value(it, 0) if it else None

        if db_id != None:
            db = BLLDatabase()
            check = Check.db_select(db, [db_id])[0]
            db.close()

            self.window.destroy()
            TestWindow(check)
            
        else:
            UIUtils.show_no_sel_dialog()
