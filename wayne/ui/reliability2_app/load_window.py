from gi.repository import Gtk as gtk
from gi.repository import GObject as gobject

from utils.ui_utils import UIUtils
from parsers.reliability2_parser import Reliability2Parser
from db.bll_database import BLLDatabase
from data_structs.check2 import Check2
from data_structs.test2 import Test2
from ui.reliability2_app.test_window import TestWindow

class LoadWindow():
    def __init__(self):
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Load')
        self.window.connect('destroy', lambda w: self.window.destroy())
        self.window.set_border_width(10)
        self.window.set_default_size(900, 350)

        vbox = gtk.VBox()

        treeview = self._build_treeview()
        scrolled_win = gtk.ScrolledWindow()
        scrolled_win.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
        scrolled_win.add(treeview)
        vbox.pack_start(scrolled_win, True, True, 0)
        
        button_box = self._build_button_box(treeview)
        vbox.pack_start(button_box, False, False, 0)
        self.window.add(vbox)

        self.window.show_all()

    def _build_button_box(self, treeview):
        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.ButtonBoxStyle.EDGE)

        cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel_button.connect('clicked', lambda w: self.window.destroy())
        button_box.add(cancel_button)

        delete_button = UIUtils.create_button('Delete', UIUtils.BUTTON_ICONS.DELETE, UIUtils.BUTTON_ICON_SIZES.PX32)
        delete_button.connect('clicked', lambda w: self.delete_check(treeview))
        button_box.add(delete_button)

        ok_button = gtk.Button(stock=gtk.STOCK_OK)
        ok_button.connect('clicked', lambda w: self.load_check(treeview))
        button_box.add(ok_button)

        return button_box

    def _build_treeview(self):
        list_store = gtk.ListStore(
            gobject.TYPE_INT,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            gobject.TYPE_STRING,
            )

        db = BLLDatabase()
        check2s_list = Check2.db_select(db)
        
        for check2 in check2s_list:
            created = UIUtils.get_db_timestamp_str(check2.created)
            
            modified = '-'
            #don't display modification date if it is the same as creation date
            if check2.modified != None and check2.modified != check2.created:
                modified = UIUtils.get_db_timestamp_str(check2.modified)
                
            completed = '-'
            if check2.completed != None:
                completed = UIUtils.get_db_timestamp_str(check2.completed)

            list_store.append([
                    check2.db_id,
                    check2.csv_filename,
                    check2.wav_foldername,
                    completed,
                    created,
                    modified,
                    ])
            
        db.close()
        treeview = gtk.TreeView(list_store)

        #create the hidden id column
        col = gtk.TreeViewColumn('ID', gtk.CellRendererText(), text=0)
        col.set_visible(False)
        treeview.append_column(col)

        #create the rest of the columns
        column_names = [
            'CSV File',
            'WAV Folder',
            'Completed',
            'Created',
            'Modified'
            ]
        for i in range(len(column_names)):
            col = gtk.TreeViewColumn(column_names[i], gtk.CellRendererText(), text=(i + 1))
            col.set_resizable(True)
            col.set_min_width( UIUtils.calc_treeview_col_min_width(column_names[i]) )
            treeview.append_column(col)

        return treeview

    def delete_check(self, treeview):
        model, sel_paths = treeview.get_selection().get_selected_rows()
        if sel_paths:
            if UIUtils.show_confirm_dialog('Are you sure you want to delete this row?'):
                it = model.get_iter(sel_paths[0])
                check2_id = model.get_value(it, 0)

                db = BLLDatabase()
                #this is a little awkward, but it works for now...
                check2 = Check2.db_select(db, ids=[check2_id])[0]
                if check2.db_delete(db) > 0:
                    model.remove(it)
                else:
                    UIUtils.show_message_dialog('An error has prevented this row from being deleted. Please check the log files for details.', gtk.MESSAGE_ERROR)
                db.close()

        else:
            UIUtils.show_no_sel_dialog()

    def load_check(self, treeview):
        model, sel_paths = treeview.get_selection().get_selected_rows()
        if sel_paths:
            it = model.get_iter(sel_paths[0])
            check2_id = model.get_value(it, 0)

            db = BLLDatabase()
            check2 = Check2.db_select(db, ids=[check2_id])[0]
            db.close()

            TestWindow(check2)
            self.window.destroy()

        else:
            UIUtils.show_no_sel_dialog()
