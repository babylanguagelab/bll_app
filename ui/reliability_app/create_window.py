from gi.repository import Gtk as gtk
import os

from data_structs.check import Check
from data_structs.test import Test
from data_structs.seg_filters import *
from db.bll_database import BLLDatabase, DBConstants
from parsers.trs_parser import TRSParser
from parsers.csv_parser import CSVParser
from parsers.parser_tools import ParserTools
from utils.ui_utils import UIUtils
from utils.progress_dialog import ProgressDialog
from ui.reliability_app.test_window import TestWindow
from utils.filters_frame import FiltersFrame
from utils.form import Form

class CreateWindow():
    def __init__(self):
        self.form = Form()
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Create Check')
        self.window.connect('destroy', lambda w: self.window.destroy())
        self.window.set_border_width(10)

        vbox = gtk.VBox()
        settings_frame = self._build_settings_frame()
        vbox.pack_start(settings_frame, True, True, 0)

        self.filters_frame = FiltersFrame()
        vbox.pack_start(self.filters_frame, True, True, 0)
        
        buttons_box = self._build_buttons_box()
        vbox.pack_end(buttons_box, True, True, 0)

        self.window.add(vbox)
        #name_entry.grab_focus()
        self.window.show_all()

    def _build_buttons_box(self):
        vbox = gtk.VBox()
        
        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.ButtonBoxStyle.EDGE)

        cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL, label='Cancel')
        cancel_button.connect('clicked', lambda w: self.window.destroy())
        button_box.add(cancel_button)
        
        create_button = gtk.Button(stock=gtk.STOCK_OK, label='Create')
        create_button.connect('clicked', lambda w: self.create_check())
        button_box.add(create_button)

        vbox.pack_start(gtk.HSeparator(), True, True, 0)
        vbox.pack_start(button_box, True, True, 0)
        
        return vbox

    def _build_settings_frame(self):
        settings_frame = gtk.Frame(label='Settings')

        #table = gtk.Table(7, 3, False)
        grid = gtk.Grid()
        
        name_label = gtk.Label('Name:')
        name_label.set_justify(gtk.JUSTIFY_RIGHT)
        #table.attach(name_label, 0, 1, 0, 1, gtk.EXPAND, gtk.EXPAND)
        grid.attach(name_label, 0, 0, 1, 1)
        
        self.form.name_entry = gtk.Entry()
        self.form.name_entry.set_width_chars(50)
        #table.attach(self.form.name_entry, 1, 2, 0, 1)
        grid.attach(self.form.name_entry, 1, 0, 1, 1)

        input_file_label = gtk.Label('TRS / CSV File:')
        input_file_label.set_justify(gtk.JUSTIFY_RIGHT)
        #table.attach(input_file_label, 0, 1, 1, 2, gtk.EXPAND, gtk.EXPAND)
        grid.attach(input_file_label, 0, 1, 1, 1)

        self.form.input_file_entry = gtk.Entry()
        self.form.input_file_entry.set_width_chars(50)
        self.form.wav_file_entry = gtk.Entry()
        self.form.wav_file_entry.set_width_chars(50)
        #table.attach(self.form.input_file_entry, 1, 2, 1, 2, gtk.EXPAND, gtk.EXPAND)
        grid.attach(self.form.input_file_entry, 1, 1, 1, 1)

        input_file_button = gtk.Button('Browse')
        input_file_button.connect('clicked', lambda w: UIUtils.browse_file('Select trs/csv file', self.form.input_file_entry, [UIUtils.TRS_CSV_FILE_FILTER, UIUtils.ALL_FILE_FILTER], self.form.wav_file_entry))
        #table.attach(input_file_button, 2, 3, 1, 2, gtk.EXPAND, gtk.EXPAND)
        grid.attach(input_file_button, 2, 1, 1, 1)

        wav_file_label = gtk.Label('WAV File:')
        wav_file_label.set_justify(gtk.JUSTIFY_RIGHT)
        #table.attach(wav_file_label, 0, 1, 2, 3, gtk.EXPAND, gtk.EXPAND)
        grid.attach(wav_file_label, 0, 2, 1, 1)

        #table.attach(self.form.wav_file_entry, 1, 2, 2, 3, gtk.EXPAND, gtk.EXPAND)
        grid.attach(self.form.wav_file_entry, 1, 2, 1, 1)

        wav_file_button = gtk.Button('Browse')
        wav_file_button.connect('clicked', lambda w: UIUtils.browse_file('Select wav file', self.form.wav_file_entry, [UIUtils.WAV_FILE_FILTER, UIUtils.ALL_FILE_FILTER]))
        #table.attach(wav_file_button, 2, 3, 2, 3, gtk.EXPAND, gtk.EXPAND)
        grid.attach(wav_file_button, 2, 2, 1, 1)

        num_segs_label = gtk.Label('Number of Segments:')
        num_segs_label.set_justify(gtk.JUSTIFY_RIGHT)
        #table.attach(num_segs_label, 0, 1, 4, 5, gtk.EXPAND, gtk.EXPAND)
        grid.attach(num_segs_label, 0, 4, 1, 1)

        num_segs_adj = gtk.Adjustment(value=0, lower=1, upper=2**32, step_incr=1, page_incr=5)
        self.form.num_segs_spinner = gtk.SpinButton(num_segs_adj)
        #table.attach(self.form.num_segs_spinner, 1, 2, 4, 5, gtk.EXPAND, gtk.EXPAND)
        grid.attach(self.form.num_segs_spinner, 1, 4, 1, 1)

        context_pad_label = gtk.Label('Default context padding (sec):')
        context_pad_label.set_justify(gtk.JUSTIFY_RIGHT)
        #table.attach(context_pad_label, 0, 1, 5, 6, gtk.EXPAND, gtk.EXPAND)
        grid.attach(context_pad_label, 0, 5, 1, 1)

        context_pad_adj = gtk.Adjustment(value=0, lower=1, upper=60, step_incr=1, page_incr=5)
        self.form.context_pad_spinner = gtk.SpinButton(context_pad_adj)
        #table.attach(self.form.context_pad_spinner, 1, 2, 5, 6, gtk.EXPAND, gtk.EXPAND)
        grid.attach(self.form.context_pad_spinner, 1, 5, 1, 1)

        self.form.rand_checkbox = gtk.CheckButton('Pick segs randomly')
        #table.attach(self.form.rand_checkbox, 0, 1, 6, 7)
        grid.attach(self.form.rand_checkbox, 0, 6, 1, 1)

        settings_frame.add(grid)

        return settings_frame

    def validate_form(self):
        error_msgs = []

        if (self.form.name_entry.get_text() == '' or
            self.form.input_file_entry.get_text() == '' or
            self.form.wav_file_entry.get_text() == ''):
            error_msgs.append(' -Please ensure that all fields are filled.')
            
        if self.form.input_file_entry.get_text() != '' and not os.path.exists(self.form.input_file_entry.get_text()):
            error_msgs.append(' -Unable to locate TRS/CSV file. Please double-check the file path.')
            
        if self.form.wav_file_entry.get_text() != '' and not os.path.exists(self.form.wav_file_entry.get_text()):
            error_msgs.append(' -Unable to locate WAV file. Please double-check the file path.')

        composite_msg = None
        if error_msgs:
            composite_msg = 'The following issues were detected:\n%s' % ('\n'.join(error_msgs))
            
        return composite_msg

    def create_check(self):
        error_msg = self.validate_form()
        
        if error_msg:
            UIUtils.show_message_dialog(error_msg)

        else:
            filters = self.filters_frame.get_filters()

            check = Check(self.form.name_entry.get_text(),
                          self.form.input_file_entry.get_text(),
                          self.form.wav_file_entry.get_text(),
                          self.form.num_segs_spinner.get_value_as_int(),
                          self.form.context_pad_spinner.get_value_as_int(),
                          [],
                          0,
                          filters=filters,    
                          pick_randomly=self.form.rand_checkbox.get_active(),
                          )

            parser = None
            progress_dialog = ProgressDialog(title='Loading File',
                                                 phases=['Parsing file...', 'Setting up...'])
            segs = []

            #TRS files
            if check.input_filename.lower().endswith('.trs'):
                parser = TRSParser(check.input_filename)
                progress_dialog.show()
                segs = parser.parse(progress_update_fcn=progress_dialog.set_fraction,
                                progress_next_phase_fcn=progress_dialog.next_phase,
                                validate=False,
                                seg_filters=check.filters)

            #CSV files
            else:
                parser = CSVParser(check.input_filename)
                progress_dialog.show()
                segs = parser.parse(progress_update_fcn=progress_dialog.set_fraction,
                                seg_filters=check.filters)

            progress_dialog.next_phase()

            if check.pick_randomly:
                #segs = ParserTools.pick_rand_segs(check.num_segs, segs)
                segs = ParserTools.hacked_pick_rand_segs(check.num_segs, segs, os.path.basename(check.input_filename))
            else:
                segs = ParserTools.pick_contiguous_segs(check.num_segs, segs)
            progress_dialog.set_fraction(1.0)

            if len(segs) < check.num_segs:
                progress_dialog.ensure_finish() #close the progress bar (even though there's still one phase left)
                UIUtils.show_message_dialog('The input file does not contain enough segments of the specified types.', dialog_type=gtk.MessageType.ERROR)
                
            else:
                db = BLLDatabase()
                check.db_insert(db)

                for i in range(len(segs)):
                    if segs[i].db_id == None:
                        segs[i].db_insert(db)

                    test = Test(
                        check.db_id,
                        None,
                        None,
                        None,
                        segs[i],
                        None,
                        check.default_context_padding,
                        )
                    test.db_insert(db)
                    check.tests.append(test)
                    
                    progress_dialog.set_fraction( float(i + 1) / float(check.num_segs) )

                db.close()
                progress_dialog.ensure_finish()

                self.window.destroy()
                TestWindow(check)

