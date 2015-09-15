from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GObject as gobject
import os

from utils.ui_utils import UIUtils
from utils.progress_dialog import ProgressDialog
from parsers.reliability2_parser import Reliability2Parser
from db.bll_database import BLLDatabase
from data_structs.check2 import Check2
from ui.reliability2_app.test_window import TestWindow

class CreateCheckWindow():
    def __init__(self):
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('New')
        self.window.connect('destroy', lambda w: self.window.destroy())
        self.window.set_border_width(10)
        self.window.set_default_size(210, 100)

        vbox = gtk.VBox()

        self.envs_treeview = None
        self.acts_treeview = None
        self.parser = None

        settings_grid = self._build_settings_grid()
        vbox.pack_start(settings_grid, True, True, 0)
        button_box = self._build_button_box()
        #vbox.pack_start(gtk.HSeparator())
        vbox.pack_start(button_box, True, True, 0)
        self.window.add(vbox)

        self.window.show_all()

    def _build_settings_grid(self):
        #table = gtk.Table(5, 3)
        grid = gtk.Grid()

        csv_label = gtk.Label('CSV File:')
        csv_label.set_justify(gtk.JUSTIFY_RIGHT)
        #table.attach(csv_label, 0, 1, 0, 1, gtk.EXPAND, gtk.EXPAND)
        grid.attach(csv_label, 0, 0, 1, 1)
        
        csv_entry = gtk.Entry()
        csv_entry.set_width_chars(60)
        #table.attach(csv_entry, 1, 2, 0, 1, gtk.EXPAND, gtk.EXPAND)
        grid.attach(csv_entry, 1, 0, 1, 1)
        self.csv_entry = csv_entry

        csv_button = gtk.Button('Browse')
        #table.attach(csv_button, 2, 3, 0, 1, gtk.EXPAND, gtk.EXPAND)
        grid.attach(csv_button, 2, 0, 1, 1)
        csv_button.connect('clicked', lambda w: UIUtils.browse_file('Select csv file', csv_entry, [UIUtils.CSV_FILE_FILTER, UIUtils.ALL_FILE_FILTER]))

        wav_label = gtk.Label('Wav Folder:')
        wav_label.set_justify(gtk.JUSTIFY_RIGHT)
        #table.attach(wav_label, 0, 1, 1, 2, gtk.EXPAND, gtk.EXPAND)
        grid.attach(wav_label, 0, 1, 1, 1)

        wav_entry = gtk.Entry()
        wav_entry.set_width_chars(60)
        #table.attach(wav_entry, 1, 2, 1, 2, gtk.EXPAND, gtk.EXPAND)
        grid.attach(wav_entry, 1, 1, 1, 1)
        self.wav_entry = wav_entry

        wav_button = gtk.Button('Browse')
        #table.attach(wav_button, 2, 3, 1, 2, gtk.EXPAND, gtk.EXPAND)
        grid.attach(wav_button, 2, 1, 1, 1)
        wav_button.connect('clicked', lambda w: UIUtils.browse_folder('Select parent wav folder', wav_entry))

        blocks_label = gtk.Label('Blocks per Activity:')
        blocks_label.set_justify(gtk.JUSTIFY_RIGHT)
        #table.attach(blocks_label, 0, 1, 2, 3, gtk.EXPAND, gtk.EXPAND)
        grid.attach(blocks_label, 0, 2, 1, 1)
        
        spin_adj = gtk.Adjustment(value=3, lower=1, upper=1000, step_incr=1, page_incr=10)
        blocks_spinner = gtk.SpinButton(adjustment=spin_adj)
        #table.attach(blocks_spinner, 1, 2, 2, 3, gtk.EXPAND, gtk.EXPAND)
        grid.attach(blocks_spinner, 1, 2, 1, 1)
        self.blocks_spinner = blocks_spinner

        vbox = gtk.VBox(spacing=5)
        #table.attach(vbox, 1, 2, 3, 5)
        grid.attach(vbox, 1, 3, 1, 2)
        
        csv_entry.connect('changed', lambda w: self._build_treeviews(w.get_text(), vbox))

        return grid

    def _build_button_box(self):
        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.ButtonBoxStyle.EDGE)

        cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL, label='Cancel')
        cancel_button.connect('clicked', lambda w: self.window.destroy())
        button_box.add(cancel_button)
        
        ok_button = gtk.Button(stock=gtk.STOCK_OK, label='Run')
        ok_button.connect('clicked', lambda w: self.run())
        button_box.add(ok_button)

        return button_box

    def _set_default_treeview_sel(self, treeview, defaults_dict):
        it = treeview.get_model().get_iter_first()
        while it:
            if treeview.get_model().get_value(it, 0) in defaults_dict:
                treeview.get_selection().select_iter(it)

            it = treeview.get_model().iter_next(it)

    def _build_treeviews(self, filename, vbox):
        if os.path.exists(filename):
            vbox.hide_all()
            map(lambda child: vbox.remove(child), vbox.get_children())

            if self.parser:
                self.parser.close()
            self.parser = Reliability2Parser(filename)
            envs_names = self.parser.get_envs_list()
            envs_names.sort()
            acts_names = self.parser.get_acts_list()
            acts_names.sort()

            self.envs_treeview = UIUtils.build_multiselect_treeview(envs_names, envs_names, gobject.TYPE_STRING, 'Select Environments:')
            self.acts_treeview = UIUtils.build_multiselect_treeview(acts_names, acts_names, gobject.TYPE_STRING, 'Select Activities:')
            
            #modify the selection colours that appear when the treeview is not in focus, to make them a bit easier to see
            self.envs_treeview.modify_base(gtk.StateFlags.ACTIVE, gdk.Color.parse('#4285F4')[1])
            self.acts_treeview.modify_base(gtk.StateFlags.ACTIVE, gdk.Color.parse('#4285F4')[1])

            #set default selection
            envs_defaults = {
                'daycare': True,
                'home': True,
                }
            self._set_default_treeview_sel(self.envs_treeview, envs_defaults)

            acts_defaults = {
                'mealtime',
                'personal care',
                'playtime - outside',
                'playtime - general',
                'playtime - organized'
                }
            self._set_default_treeview_sel(self.acts_treeview, acts_defaults)

            vbox.pack_start(self.envs_treeview, True, True, 0)
            vbox.pack_start(self.acts_treeview, True, True, 0)
            vbox.show_all()

    def run(self):
        csv_path = self.csv_entry.get_text()
        wav_path = self.wav_entry.get_text()
        blocks_per_activity = self.blocks_spinner.get_value_as_int()

        activities = []
        if self.acts_treeview and self.acts_treeview.get_selection():
            model, sel_paths = self.acts_treeview.get_selection().get_selected_rows()
        
            for path in sel_paths:
                it = model.get_iter(path)
                activities.append(model.get_value(it, 0))

        environments = []
        if self.envs_treeview and self.envs_treeview.get_selection():
            model, sel_paths = self.envs_treeview.get_selection().get_selected_rows()
        
            for path in sel_paths:
                it = model.get_iter(path)
                environments.append(model.get_value(it, 0))

        is_valid = csv_path and wav_path and blocks_per_activity and len(activities) and len(environments)
        if is_valid:
            check2 = Check2(
                csv_path,
                wav_path,
                activities,
                environments,
                blocks_per_activity,
                )

            sel_test2s = None
            enough_blocks, counts_str = self.parser.have_enough_blocks(check2, False)
            if enough_blocks:
                print counts_str
                sel_test2s = self.parser.pick_rows(
                    check2,
                    lambda filename: UIUtils.open_file('Please locate %s' % (filename), filters=[UIUtils.WAV_FILE_FILTER], save_last_location=True, cur_location=wav_path),
                    False
                    )
            else:
                enough_blocks, counts_str = self.parser.have_enough_blocks(check2, True)
                if enough_blocks:
                    print counts_str
                    if UIUtils.show_confirm_dialog('There are not enough unused rows left for some activities (see command window for row counts). If you proceed, the same row will be selected twice. Ok to continue?'):
                        sel_test2s = self.parser.pick_rows(
                            check2,
                            lambda filename: UIUtils.open_file('Please locate %s' % (filename), filters=[UIUtils.WAV_FILE_FILTER], save_last_location=True, cur_location=wav_path),
                            True
                            )
                else:
                    print counts_str
                    UIUtils.show_message_dialog('The input file does not contain enough blocks of the specified types. Please refer to the command window for a printout of the activity counts.')
            
            if sel_test2s:
                progress_dialog = ProgressDialog(title='Setting up...', phases=[''])
                progress_dialog.show()

                db = BLLDatabase()
                check2.db_insert(db)
                check2.test2s = sel_test2s
                for i in range(len(check2.test2s)):
                    test2 = check2.test2s[i]
                    test2.check2_id = check2.db_id
                    test2.db_insert(db)

                    progress_dialog.set_fraction(float(i + 1) / float(len(check2.test2s)))
                db.close()
                progress_dialog.ensure_finish()

                TestWindow(check2)
                if self.parser:
                    self.parser.close()
                self.window.destroy()
                
        else:
            UIUtils.show_empty_form_dialog()
