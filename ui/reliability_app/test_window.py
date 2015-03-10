from gi.repository import Gtk as gtk
import datetime
import logging
import subprocess

from data_structs.check import Check
from data_structs.segment import Segment
from data_structs.test import Test
from db.bll_database import BLLDatabase, DBConstants
from parsers.wav_parser import WavParser
from parsers.reliability_exporter import ReliabilityExporter
from utils.ui_utils import UIUtils
from utils.form import Form
from utils.handler_manager import HandlerManager
from utils.backend_utils import BackendUtils
from utils.praat_interop import PraatInterop

class TestWindow():
    def __init__(self, check):
        self.logger = logging.getLogger(__name__)
        
        self.check = check

        self.wav_parser = WavParser(self.check.wav_filename)

        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Testing')
        self.window.connect('destroy', lambda w: self._exit()) #will save current input and exit
        self.window.set_border_width(10)
        self.window.set_default_size(350, 200)

        self.wo_form = Form()
        self.wo_form.handler_man = HandlerManager()
        self.w_form = Form()
        self.w_form.handler_man = HandlerManager()

        self.button_form = Form()
        self.button_form.handler_man = HandlerManager()
        
        self.progress_bar = self._build_progress_bar()
        self.w_context_frame = self._build_w_context_frame()
        button_box = self._build_button_box()
        
        self.wo_context_frame = self._build_wo_context_frame()
        self.wo_context_checkbox = self._build_wo_context_checkbox(self.wo_context_frame)

        vbox = gtk.VBox()
        vbox.pack_start(self.progress_bar, True, True, 0)
        vbox.pack_start(self.wo_context_checkbox, True, True, 0)
        vbox.pack_start(self.wo_context_frame, True, True, 0)
        vbox.pack_start(self.w_context_frame, True, True, 0)
        vbox.pack_end(button_box, True, True, 0)

        self.window.add(vbox)
        self.window.show_all()

        self._update_progress_bar()
        self._toggle_wo_context_frame(self.wo_context_checkbox.get_active())
        self._set_ui_to_cur_test()

    def _build_progress_bar(self):
        progress_bar = gtk.ProgressBar()
        progress_bar.set_orientation(gtk.Orientation.HORIZONTAL)

        return progress_bar

    def _set_ui_to_cur_test(self):
        cur_test = self.check.tests[self.check.test_index]

        cat_index = 0
        if cur_test.category_input != None:
            cat_index = cur_test.category_input - DBConstants.COMBO_OPTIONS[DBConstants.COMBO_GROUPS.RELIABILITY_CATEGORIES].EMPTY
        self.w_form.type_combo.set_active(cat_index)

        self.w_form.uncertain_checkbox.set_active(cur_test.is_uncertain or False)

        self.w_form.context_pad_spinner.set_value(cur_test.context_padding)

        self.w_form.syllables_spinner.set_value(cur_test.syllables_w_context if cur_test.syllables_w_context != None else 0)

        #these boundaries are displayed without context, but opening in praat or listening will play with context
        seg_start, seg_end = self._get_bounds()
        self.w_form.user_start_entry.set_text(str(cur_test.seg.user_adj_start) if cur_test.seg.user_adj_start != None else str(seg_start))
        self.w_form.user_end_entry.set_text(str(cur_test.seg.user_adj_end) if cur_test.seg.user_adj_end != None else str(seg_end))

        self.wo_form.syllables_spinner.set_value(cur_test.syllables_wo_context if cur_test.syllables_wo_context != None else 0)
        self.wo_context_checkbox.set_active(cur_test.syllables_wo_context != None) #this will toggle the visibility of the frame because of the handler attached to it

    def _build_w_context_frame(self):
        cur_test = self.check.tests[self.check.test_index]
        frame = gtk.Frame(label='With Context')
        
        #table = gtk.Table(6, 4, False)
        grid = gtk.Grid()
        
        play_button = UIUtils.create_button('', UIUtils.BUTTON_ICONS.PLAY, UIUtils.BUTTON_ICON_SIZES.PX32)
        #table.attach(play_button, 0, 1, 0, 1, gtk.EXPAND, gtk.EXPAND)
        grid.attach(play_button, 0, 0, 1, 1)

        type_label = gtk.Label('Seg Category:')
        #table.attach(type_label, 1, 2, 0, 1, gtk.EXPAND, gtk.EXPAND)
        grid.attach(type_label, 1, 0, 1, 1)

        self.w_form.type_combo = UIUtils.build_options_combo(DBConstants.COMBO_GROUPS.RELIABILITY_CATEGORIES)
        #table.attach(self.w_form.type_combo, 2, 3, 0, 1, gtk.EXPAND, gtk.EXPAND)
        grid.attach(self.w_form.type_combo, 2, 0, 1, 1)
        
        uncertain_label = gtk.Label('Other/Uncertain:')
        self.w_form.uncertain_checkbox = gtk.CheckButton()
        #table.attach(uncertain_label, 1, 2, 1, 2, gtk.EXPAND, gtk.EXPAND)
        grid.attach(uncertain_label, 1, 1, 1, 1)
        #table.attach(self.w_form.uncertain_checkbox, 2, 3, 1, 2, gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL)
        grid.attach(self.w_form.uncertain_checkbox, 2, 1, 1, 1)

        padding_label = gtk.Label('Padding:')
        context_pad_adj = gtk.Adjustment(value=0, lower=1, upper=1000, step_incr=1, page_incr=5)
        self.w_form.context_pad_spinner = gtk.SpinButton(context_pad_adj)
        #table.attach(padding_label, 1, 2, 2, 3, gtk.EXPAND, gtk.EXPAND)
        grid.attach(padding_label, 1, 2, 1, 1)
        #table.attach(self.w_form.context_pad_spinner, 2, 3, 2, 3, gtk.EXPAND, gtk.EXPAND)
        grid.attach(self.w_form.context_pad_spinner, 2, 2, 1, 1)
        
        self.w_form.handler_man.add_handler(play_button, 'clicked', lambda w: self.play_seg(int(self.w_form.context_pad_spinner.get_value())))

        syllables_label = gtk.Label('Syllables:')
        syllables_adj = gtk.Adjustment(value=0, lower=0, upper=1000, step_incr=1, page_incr=5)
        self.w_form.syllables_spinner = gtk.SpinButton(syllables_adj)
        #table.attach(syllables_label, 1, 2, 3, 4, gtk.EXPAND, gtk.EXPAND)
        grid.attach(syllables_label, 1, 3, 1, 1)
        #table.attach(self.w_form.syllables_spinner, 2, 3, 3, 4, gtk.EXPAND, gtk.EXPAND)
        grid.attach(self.w_form.syllables_spinner, 2, 3, 1, 1)

        user_start_label = gtk.Label('User Start:')
        self.w_form.user_start_entry = gtk.Entry()
        self.w_form.user_start_entry.set_width_chars(10)
        #table.attach(user_start_label, 1, 2, 4, 5, gtk.EXPAND, gtk.EXPAND)
        grid.attach(user_start_label, 1, 4, 1, 1)
        #table.attach(self.w_form.user_start_entry, 2, 3, 4, 5, gtk.EXPAND, gtk.EXPAND)
        grid.attach(self.w_form.user_start_entry, 2, 5, 1, 1)
        
        user_end_label = gtk.Label('User End:')
        self.w_form.user_end_entry = gtk.Entry()
        self.w_form.user_end_entry.set_width_chars(10)
        #table.attach(user_end_label, 1, 2, 5, 6, gtk.EXPAND, gtk.EXPAND)
        grid.attach(user_end_label, 1, 5, 1, 1)
        #table.attach(self.w_form.user_end_entry, 2, 3, 5, 6, gtk.EXPAND, gtk.EXPAND)
        grid.attach(self.w_form.user_end_entry, 2, 5, 1, 1)

        open_praat_button = gtk.Button('Open Praat')
        #table.attach(open_praat_button, 3, 4, 4, 5, gtk.EXPAND, gtk.EXPAND)
        grid.attach(open_praat_button, 3, 4, 1, 1)
        self.w_form.handler_man.add_handler(open_praat_button, 'clicked', lambda w: self._open_praat())

        close_praat_button = gtk.Button('Close Praat')
        #table.attach(close_praat_button, 3, 4, 5, 6, gtk.EXPAND, gtk.EXPAND)
        grid.attach(close_praat_button, 3, 5, 1, 1)
        self.w_form.handler_man.add_handler(close_praat_button, 'clicked', lambda w: self._close_praat())

        frame.add(grid)

        return frame

    def _build_wo_context_frame(self):
        cur_test = self.check.tests[self.check.test_index]
        frame = gtk.Frame(label='Without Context')

        #table = gtk.Table(1, 3, False)
        grid = gtk.Grid()

        self.wo_form.play_button = UIUtils.create_button('', UIUtils.BUTTON_ICONS.PLAY, UIUtils.BUTTON_ICON_SIZES.PX32)
        self.wo_form.handler_man.add_handler(self.wo_form.play_button, 'clicked', lambda w: self.play_seg(0))
        #table.attach(self.wo_form.play_button, 0, 1, 0, 1, gtk.EXPAND, gtk.EXPAND)
        grid.attach(self.wo_form.play_button, 0, 0, 1, 1)

        syllables_label = gtk.Label('Syllables:')
        syllables_adj = gtk.Adjustment(value=0, lower=0, upper=1000, step_incr=1, page_incr=5)
        self.wo_form.syllables_spinner = gtk.SpinButton(syllables_adj)
        #table.attach(syllables_label, 1, 2, 0, 1, gtk.EXPAND, gtk.EXPAND)
        grid.attach(syllables_label, 1, 0, 1, 1)
        #table.attach(self.wo_form.syllables_spinner, 2, 3, 0, 1, gtk.EXPAND, gtk.EXPAND)
        grid.attach(self.wo_form.syllables_spinner, 2, 0, 1, 1)

        frame.add(grid)

        return frame

    def _toggle_wo_context_frame(self, visible):
        if visible:
            self.wo_context_frame.show()
        else:
            self.wo_context_frame.hide()
            self.check.tests[self.check.test_index].syllables_wo_context = None
            self.wo_form.syllables_spinner.get_adjustment().set_value(1)
        

    def _build_wo_context_checkbox(self, wo_context_frame):
        cur_test = self.check.tests[self.check.test_index]
        checkbox = gtk.CheckButton(label='Test Without Context')
        checkbox.connect('toggled', lambda w: self._toggle_wo_context_frame(w.get_active()))

        checkbox.set_active(cur_test.syllables_wo_context != None)

        return checkbox

    def _build_button_box(self):
        box = gtk.HButtonBox()
        box.set_layout(gtk.ButtonBoxStyle.EDGE)
        
        self.button_form.back_button = gtk.Button(stock=gtk.STOCK_GO_BACK)
        self.button_form.handler_man.add_handler(self.button_form.back_button, 'clicked', lambda w: self._back())

        self.button_form.save_button = UIUtils.create_button('Save & Exit', UIUtils.BUTTON_ICONS.SAVE, UIUtils.BUTTON_ICON_SIZES.PX32)
        self.button_form.handler_man.add_handler(self.button_form.save_button, 'clicked', lambda w: self._exit())
        
        self.button_form.forward_button = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        self.button_form.handler_man.add_handler(self.button_form.forward_button, 'clicked', lambda w: self._forward())
        
        self._update_step_buttons()
        
        box.pack_start(self.button_form.back_button, False, False, 0)
        box.pack_start(self.button_form.save_button, False, False, 0)
        box.pack_end(self.button_form.forward_button, False, False, 0)

        return box

    def _update_progress_bar(self):
        if self.check.num_segs == 1: #avoid dividing by zero
            self.progress_bar.set_fraction(1.0)
        else:
            #print self.check.test_index
            self.progress_bar.set_fraction( float(self.check.test_index) / float(self.check.num_segs - 1) )
            
        self.progress_bar.set_text('Segment %d of %d' % (self.check.test_index + 1, self.check.num_segs))

    def _set_step_button(self, button, stock, label_text, clicked_handler):
        img = gtk.Image()
        img.set_from_stock(stock, gtk.ICON_SIZE_BUTTON)
        button.set_label(label_text)
        button.set_image(img)

        self.button_form.handler_man.remove_handlers(button, ['clicked'])
        self.button_form.handler_man.add_handler(button, 'clicked', clicked_handler)

    def _update_step_buttons(self):
        finish_text = 'Finish'
        forward_text = 'Forward'

        if self.check.test_index == self.check.num_segs - 1:
            self._set_step_button(self.button_form.forward_button, gtk.STOCK_OK, finish_text, lambda w: self._finish())

        elif self.button_form.forward_button.get_label() == finish_text:
            self._set_step_button(self.button_form.forward_button, gtk.STOCK_GO_FORWARD, forward_text, lambda w: self._forward())

        self.button_form.back_button.set_sensitive(self.check.test_index > 0)

    def _exit(self, save=True):
        if save:
            self.save_input(mark_last_run=True)

        self.wav_parser.close()
        self.window.destroy()

    def _finish(self):
        if self._validate_cur_test():
            self.save_input(mark_last_run=True, mark_as_completed=True)

            filename, check_results = UIUtils.save_file(filters=[UIUtils.CSV_FILE_FILTER], open_now_opt=True, save_last_location=True)

            if filename:
                exporter = ReliabilityExporter(self.check, filename)
                if exporter.export():
                    if check_results:
                        subprocess.Popen(['%s' % DBConstants.SETTINGS.SPREADSHEET_PATH, filename])
                    else:
                        UIUtils.show_message_dialog('Results exported successfully.')

                    self._exit(False) #we have already saved above

                else:
                    UIUtils.show_message_dialog('An error occurred while exporting the results. These results are still saved in the database, and can be exported at a later time, pending the correction of this problem. Please bother the programmer until this happens.')

    def _validate_cur_test(self):
        #validate w_context form
        w_context_valid = (self.w_form.type_combo.get_active() != 0 and
                    int(self.w_form.syllables_spinner.get_adjustment().get_value()) > 0 and
                    BackendUtils.is_float(self.w_form.user_start_entry.get_text()) and
                    BackendUtils.is_float(self.w_form.user_end_entry.get_text()))

        #print 'w_context_valid: %s' % str(w_context_valid)

        wo_context_valid = (not self.wo_context_checkbox.get_active() or int(self.wo_form.syllables_spinner.get_adjustment().get_value()) > 0)

        #print 'wo_context_valid: %s' % str(wo_context_valid)

        is_valid = w_context_valid and wo_context_valid

        if is_valid:
            #make sure user-boundaries have been updated
            #note: they are guarenteed to contain floats at this point because of the w_context_valid condition
            user_start = float(self.w_form.user_start_entry.get_text())
            user_end = float(self.w_form.user_end_entry.get_text())
            cur_test = self.check.tests[self.check.test_index]

            is_valid = (cur_test.seg.start != user_start or cur_test.seg.end != user_end)
            if not is_valid:
                is_valid = UIUtils.show_confirm_dialog('Segment boundaries have not been adjusted. Continue anyway?')

        else:
            UIUtils.show_message_dialog('Please ensure that all of the inputs have a correct value.')

        return is_valid

    def _move(self, incr):
        self.save_input()
        self.check.test_index += incr
        self._update_progress_bar()
        self._update_step_buttons()
        self._set_ui_to_cur_test()
        
    def _forward(self):
        if self._validate_cur_test():
            self._move(1)
            
    def _back(self):
        self._move(-1)

    def _get_bounds(self, include_context=False):
        start_time = self.check.tests[self.check.test_index].seg.start
        end_time = self.check.tests[self.check.test_index].seg.end
        
        if include_context:
            context_len = self.w_form.context_pad_spinner.get_value_as_int() if include_context else 0
            start_time = max(start_time - context_len, 0)
            end_time = min(end_time + context_len, self.wav_parser.get_sound_len())

        return start_time, end_time

    def _open_praat(self):
        start_time, end_time = self._get_bounds(include_context=True)
        PraatInterop.open_praat()
        PraatInterop.send_commands( PraatInterop.get_open_clip_script(start_time, end_time, self.check.wav_filename) )

    def _close_praat(self):
        socket = PraatInterop.create_serversocket()
        PraatInterop.send_commands( PraatInterop.get_sel_bounds_script(self.check.wav_filename) )
        start_time, end_time = PraatInterop.socket_receive(socket)
        socket.close()
        PraatInterop.close_praat()
        
        if start_time != end_time: #make sure something was selected
            #update the inputs in the UI
            start_time = str( round(float(start_time), 3) )
            end_time = str( round(float(end_time), 3) )

            self.w_form.user_start_entry.set_text(start_time)
            self.w_form.user_end_entry.set_text(end_time)

    def play_seg(self, context_len):
        self.wav_parser.play_seg(self.check.tests[self.check.test_index].seg, context_len)

    def save_input(self, mark_last_run=False, mark_as_completed=False):
        cur_test = self.check.tests[self.check.test_index]
        
        cur_test.category_input = self.w_form.type_combo.get_model()[self.w_form.type_combo.get_active()][1]
        cur_test.is_uncertain = self.w_form.uncertain_checkbox.get_active()
        cur_test.context_padding = int(self.w_form.context_pad_spinner.get_adjustment().get_value())
        cur_test.syllables_w_context = int(self.w_form.syllables_spinner.get_adjustment().get_value())
        cur_test.seg.user_adj_start = float(self.w_form.user_start_entry.get_text())
        cur_test.seg.user_adj_end = float(self.w_form.user_end_entry.get_text())

        cur_test.syllables_wo_context = None
        if self.wo_context_checkbox.get_active():
            cur_test.syllables_wo_context = int(self.wo_form.syllables_spinner.get_adjustment().get_value())

        db = BLLDatabase()
        cur_test.db_update_user_inputs(db)
        self.check.db_update_test_index(db)

        if mark_last_run:
            self.check.mark_last_run(db)

        if mark_as_completed:
            self.check.mark_as_completed(db)
            
        db.close()
        
