from gi.repository import Gtk as gtk
import re
import threading
import subprocess

from utils.ui_utils import UIUtils
from utils.progress_dialog import ProgressDialog
from utils.handler_manager import HandlerManager
from parsers.reliability2_parser import Reliability2Parser
from parsers.reliability2_exporter import Reliability2Exporter
from parsers.wav_parser import WavParser
from db.bll_database import BLLDatabase, DBConstants
from data_structs.check2 import Check2
from data_structs.test2 import Test2
from utils.backend_utils import BackendUtils
from utils.enum import Enum

class TestWindow():
    def __init__(self, check2):
        self.handler_man = HandlerManager()
        
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Reliability Testing')
        self.handler_man.add_handler(self.window, 'destroy', lambda w: self.save_and_exit())
        self.window.set_border_width(10)
        self.window.set_default_size(900, 500)

        self.check2 = check2

        vbox = gtk.VBox()

        self.controls = TestWindow.Controls()
        grid = self._build_layout_grid(self.controls)
        
        self.controls.set(self.check2)
        self.controls.hookup(self.check2)
        
        vbox.pack_start(grid, True, True, 0)
        button_box = self._build_button_box()
        vbox.pack_start(button_box, False, False, 0)
        self.window.add(vbox)

        self.window.show_all()

    def _build_button_box(self):
        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.ButtonBoxStyle.EDGE)

        back_button = gtk.Button(stock=gtk.STOCK_GO_BACK)
        button_box.add(back_button)
        save_button = UIUtils.create_button('Save & Exit', UIUtils.BUTTON_ICONS.SAVE, UIUtils.BUTTON_ICON_SIZES.PX32)
        button_box.add(save_button)
        next_button = gtk.Button(stock=gtk.STOCK_GO_FORWARD)
        button_box.add(next_button)

        next_handler = lambda w: self.next_test2(back_button, next_button)

        if self.check2.test2_index >= len(self.check2.test2s) - 1:
            next_button.set_label(gtk.STOCK_OK)
            next_handler = lambda w: self.save_and_export()

        self.handler_man.add_handler(next_button, 'clicked', next_handler)
        self.handler_man.add_handler(back_button, 'clicked', lambda w: self.back_test2(back_button, next_button))
        self.handler_man.add_handler(save_button, 'clicked', lambda w: self.window.destroy()) #this will call save_and_exit() since the window 'destroy' signal is connected to that method (see constructor)

        back_button.set_sensitive(self.check2.test2_index > 0)
        next_button.set_sensitive(self.check2.test2_index < len(self.check2.test2s))

        return button_box

    def _check_completion(self):
        msgs = []
        complete = True
        
        if self.controls.scale.get_fill_level() != 300:
            msgs.append('- The segment has not been fully played.')

        start_iter = self.controls.trans_entry.get_buffer().get_start_iter()
        end_iter = self.controls.trans_entry.get_buffer().get_end_iter()
        if not self.controls.trans_entry.get_buffer().get_text(start_iter, end_iter).strip():
            msgs.append('- The transcription box is empty.')

        if not self.controls.child_voc_spinner.get_value_as_int():
            msgs.append('- No child vocs have been recorded.')

        if msgs:
            dialog_text = 'The following issues have been detected:\n'
            dialog_text += '\n'.join(msgs)
            dialog_text += '\n\nProceed anyway?'

            complete = UIUtils.show_confirm_dialog(dialog_text)

        return complete

    def _save_to_cur_test2(self):
        #save current UI data
        self.check2.test2s[self.check2.test2_index].ui_save_data = self._get_ui_save_data()
        self.check2.test2s[self.check2.test2_index].transcription = self.controls.trans_entry.get_buffer().get_text(self.controls.trans_entry.get_buffer().get_start_iter(),
                                                                                                             self.controls.trans_entry.get_buffer().get_end_iter())
        self.check2.test2s[self.check2.test2_index].child_vocs = self.controls.child_voc_spinner.get_value_as_int()

    def back_test2(self, back_button, next_button):
        if self.check2.test2_index > 0:
            self._save_to_cur_test2()
            
            self.check2.test2_index -= 1
            self.controls.update_progress_labels(self.check2)
            self.controls.unhook()
            self.controls.set(self.check2)
            self.controls.hookup(self.check2)

            if self.check2.test2_index == len(self.check2.test2s) - 2:
                next_button.set_label(gtk.STOCK_GO_FORWARD)
                self.handler_man.remove_handlers(next_button, ['clicked'])
                self.handler_man.add_handler(next_button, 'clicked', lambda w: self.next_test2(back_button, next_button))
            
        back_button.set_sensitive(self.check2.test2_index > 0)
        next_button.set_sensitive(self.check2.test2_index < len(self.check2.test2s))

    def next_test2(self, back_button, next_button):
        #validate
        if self._check_completion():
            #save the data that's currently in the window
            self._save_to_cur_test2()

            #if there are more test2s left, increment the index and update the UI for the next test2
            num_tests = len(self.check2.test2s)
            if self.check2.test2_index < num_tests - 1:
                self.check2.test2_index += 1
                self.controls.update_progress_labels(self.check2)
                self.controls.unhook()
                self.controls.set(self.check2)
                self.controls.hookup(self.check2)

            back_button.set_sensitive(self.check2.test2_index > 0)
            next_button.set_sensitive(self.check2.test2_index < num_tests) #note: next button must be sensitive for "finish" state (so no - 1 here)

            #swap next button for finish button if we're on the last test2
            if self.check2.test2_index == num_tests - 1:
                next_button.set_label(gtk.STOCK_OK)
                self.handler_man.remove_handlers(next_button, ['clicked'])
                self.handler_man.add_handler(next_button, 'clicked', lambda w: self.save_and_export())

    #completed is a boolean
    def save(self, completed, progress_dialog=None):
        self._save_to_cur_test2()
        
        db = BLLDatabase()
        for i in range(len(self.check2.test2s)):
            test2 = self.check2.test2s[i]
            if test2.db_id != None:
                test2.db_delete(db)
            test2.db_insert(db)
            
            if progress_dialog:
                progress_dialog.set_fraction(float(i + 1) / float(len(self.check2.test2s)))
                
        self.check2.update_test2_index(db)

        #update modification timestamp
        self.check2.update_modified(db)

        #only update completed timestamp the first time the check2 is completed
        if completed and self.check2.completed == None:
            self.check2.update_completed(db)
        db.close()

    def save_and_exit(self):
        progress_dialog = ProgressDialog(title='Saving...', phases=['Saving records to DB'])
        progress_dialog.show()
        self.save(False, progress_dialog)
        progress_dialog.ensure_finish()
        self.window.destroy()

    def save_and_export(self):
        if self._check_completion():
            checkbuttons = []
            include_trans_check = gtk.CheckButton('Include Transcription')
            checkbuttons.append(include_trans_check)
            open_now_check = gtk.CheckButton('Open Immediately')
            open_now_check.set_active(True)
            checkbuttons.append(open_now_check)

            filename, results = UIUtils.show_file_dialog_with_checks('Save File', [UIUtils.CSV_FILE_FILTER, UIUtils.ALL_FILE_FILTER], gtk.FileChooserAction.SAVE, gtk.STOCK_SAVE, checkbuttons, save_last_location=True)

            if filename:
                progress_dialog = ProgressDialog(title='Saving...', phases=['Saving records to DB', 'Matching DB records to rows', 'Writing rows to file'])
                progress_dialog.show()
            
                self.save(True, progress_dialog)
                progress_dialog.next_phase()
                
                if not filename.lower().endswith('.csv'):
                    filename += '.csv'

                exporter = Reliability2Exporter(filename, self.check2)
                exporter.export(results[0], progress_update_fcn=progress_dialog.set_fraction, progress_next_fcn=progress_dialog.next_phase)
                exporter.close()
                progress_dialog.ensure_finish()

                self.handler_man.block_handler(self.window, 'destroy')
                self.window.destroy()
                #note: there is no need for a corresponding self.handler_man.unblock_handler() call, since the object the handler is operating upon (the window) is destroyed)

                #show immediately, if requested
                if results[1]:
                    subprocess.Popen(['%s' % DBConstants.SETTINGS.SPREADSHEET_PATH, filename])
                else:
                    UIUtils.show_message_dialog('Results exported successfully!')

    def _build_layout_grid(self, controls):
        #table = gtk.Table(10, 10)
        grid = gtk.Grid()

        #table.attach(controls.status_table, 9, 10, 0, 1)
        grid.attach(controls.status_grid, 9, 0, 1, 1)

        #table.attach(controls.scale, 0, 10, 1, 2)
        grid.attach(controls.scale, 0, 1, 10, 1)

        snd_ctrl_hbox = gtk.HBox()
        snd_ctrl_hbox.pack_start(controls.prev_button, True, True, 0)
        snd_ctrl_hbox.pack_start(controls.play_button, True, True, 0)
        snd_ctrl_hbox.pack_start(controls.next_button, True, True, 0)
        #table.attach(snd_ctrl_hbox, 4, 6, 2, 3, gtk.EXPAND, gtk.EXPAND)
        grid.attach(snd_ctrl_hbox, 4, 2, 2, 1)

        clip_len_hbox = gtk.HBox()
        clip_label = gtk.Label('Clip Length:')
        clip_label.set_justify(gtk.JUSTIFY_RIGHT)
        clip_len_hbox.pack_start(clip_label, True, True, 0)
        clip_len_hbox.pack_start(controls.clip_spinner, True, True, 0)
        #table.attach(clip_len_hbox, 6, 7, 2, 3, gtk.EXPAND, gtk.EXPAND)
        grid.attach(clip_len_hbox, 6, 2, 1, 1)

        child_voc_hbox = gtk.HBox()
        child_voc_label = gtk.Label('Child Vocs:')
        child_voc_label.set_justify(gtk.JUSTIFY_RIGHT)
        child_voc_hbox.pack_start(child_voc_label, True, True, 0)
        child_voc_hbox.pack_start(controls.child_voc_spinner, True, True, 0)
        #table.attach(child_voc_hbox, 7, 8, 2, 3, gtk.EXPAND, gtk.EXPAND)
        grid.attach(child_voc_hbox, 7, 2, 1, 1)

        trans_label = gtk.Label('Transcription:')
        trans_label.set_justify(gtk.JUSTIFY_LEFT)
        #table.attach(trans_label, 0, 1, 3, 4, gtk.EXPAND, gtk.EXPAND)
        grid.attach(trans_label, 0, 3, 1, 1)

        scrolled_win = gtk.ScrolledWindow()
        scrolled_win.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
        scrolled_win.add(controls.trans_entry)
        #table.attach(scrolled_win, 0, 10, 4, 9)
        grid.attach(scrolled_win, 0, 4, 10, 5)

        word_count_hbox = gtk.HBox()
        words_label = gtk.Label('Word Count:')
        words_label.set_justify(gtk.JUSTIFY_RIGHT)
        word_count_hbox.pack_start(words_label, True, True, 0)
        word_count_hbox.pack_end(controls.words_entry, True, True, 0)
        #table.attach(word_count_hbox, 0, 1, 9, 10, gtk.EXPAND, gtk.EXPAND)
        grid.attach(word_count_hbox, 0, 9, 1, 1)
        
        return grid

    def _get_ui_save_data(self):
        save_data = self.controls.get_ui_save_data()

        return save_data

    class Controls():
        def __init__(self):
            self.handler_man = HandlerManager()
            self.sm = None

            #self.status_table = gtk.Table(3, 2)
            self.status_grid = gtk.Grid()

            name_label = gtk.Label('Environment: ')
            name_label.set_justify(gtk.JUSTIFY_RIGHT)
            #self.status_table.attach(name_label, 0, 1, 0, 1, gtk.EXPAND, gtk.EXPAND)
            self.status_grid.attach(name_label, 0, 0, 1, 1)
            self.env_label = gtk.Label('')
            self.env_label.set_justify(gtk.JUSTIFY_LEFT)
            #self.status_table.attach(self.env_label, 1, 2, 0, 1, gtk.EXPAND, gtk.EXPAND)
            self.status_grid.attach(self.env_label, 1, 0, 1, 1)

            name_label = gtk.Label('Activity: ')
            name_label.set_justify(gtk.JUSTIFY_RIGHT)
            #self.status_table.attach(name_label, 0, 1, 1, 2, gtk.EXPAND, gtk.EXPAND)
            self.status_grid.attach(name_label, 0, 1, 1, 1)
            self.act_label = gtk.Label('')
            self.act_label.set_justify(gtk.JUSTIFY_LEFT)
            #self.status_table.attach(self.act_label, 1, 2, 1, 2, gtk.EXPAND, gtk.EXPAND)
            self.status_grid.attach(self.act_label, 1, 1, 1, 1)

            name_label = gtk.Label('Block: ')
            name_label.set_justify(gtk.JUSTIFY_RIGHT)
            #self.status_table.attach(name_label, 0, 1, 2, 3, gtk.EXPAND, gtk.EXPAND)
            self.status_grid.attach(name_label, 0, 2, 1, 1)
            self.block_label = gtk.Label('')
            self.block_label.set_justify(gtk.JUSTIFY_LEFT)
            #self.status_table.attach(self.block_label, 1, 2, 2, 3, gtk.EXPAND, gtk.EXPAND)
            self.status_grid.attach(self.block_label, 1, 2, 1, 1)
            
            self.prev_button = gtk.Button(stock=gtk.STOCK_MEDIA_PREVIOUS)
            self.play_button = gtk.Button(stock=gtk.STOCK_MEDIA_PLAY)
            self.next_button = gtk.Button(stock=gtk.STOCK_MEDIA_NEXT)
            self.next_button.set_use_stock(True)

            scale_adj = gtk.Adjustment(value=0, lower=0, upper=300, step_incr=10, page_incr=10, page_size=0)
            self.scale = gtk.HScale(scale_adj)
            self.scale.set_show_fill_level(True)
            self.scale.set_restrict_to_fill_level(True)
            self.scale.set_fill_level(0)
            self.scale.set_draw_value(False)
            self.scale.set_update_policy(gtk.UPDATE_DISCONTINUOUS)

            clip_adj = gtk.Adjustment(value=10, lower=1, upper=300, step_incr=1, page_incr=10)
            self.clip_spinner = gtk.SpinButton(clip_adj)

            child_voc_adj = gtk.Adjustment(value=0, lower=0, upper=1000000, step_incr=1, page_incr=10)
            self.child_voc_spinner = gtk.SpinButton(child_voc_adj)

            self.trans_entry = gtk.TextView()
            self.trans_entry.set_wrap_mode(gtk.WRAP_WORD)

            self.words_entry = gtk.Entry()
            self.words_entry.set_sensitive(False)
            self.words_entry.set_width_chars(4)
            self.words_entry.set_text('0')

        def _update_word_count(self):
            text_buf = self.trans_entry.get_buffer()
            text = text_buf.get_text( text_buf.get_start_iter(), text_buf.get_end_iter() )
            num_words = BackendUtils.get_word_count(text)
            self.words_entry.set_text(str(num_words))

        def _snap_scale(self, adj):
            adj.set_value(self.sm.markers[self.sm.marker_index])

        def update_progress_labels(self, check2):
            env_index = check2.test2_index / (len(check2.activities) * check2.blocks_per_activity)
            act_index = (check2.test2_index / check2.blocks_per_activity) % len(check2.activities)
            block_index = check2.test2_index % check2.blocks_per_activity

            self.env_label.set_text('%d of %d (%s)' % (env_index + 1, len(check2.environments), check2.environments[env_index]))
            self.act_label.set_text('%d of %d (%s)' % (act_index + 1, len(check2.activities), check2.activities[act_index]))
            self.block_label.set_text('%d of %d' % (block_index + 1, check2.blocks_per_activity))

        def set(self, check2):
            test2 = check2.test2s[check2.test2_index]

            self.scale.clear_marks()

            scale_val = 0
            fill_lev = 0
            clip_len_val = 10
            trans = ''
            child_vocs = 0
            markers = []
            if test2.ui_save_data:
                scale_val = test2.ui_save_data['markers'][test2.ui_save_data['marker_index']]
                fill_lev = test2.ui_save_data['fill_lev']
                clip_len_val = test2.ui_save_data['markers'][test2.ui_save_data['marker_index'] + 1] - test2.ui_save_data['markers'][test2.ui_save_data['marker_index']]
                trans = test2.transcription
                child_vocs = test2.child_vocs
                markers = test2.ui_save_data['markers']

            self.scale.set_fill_level(fill_lev)
            self.scale.set_value(scale_val)
            self.clip_spinner.set_value(clip_len_val)
            self.trans_entry.get_buffer().set_text(trans)
            self._update_word_count()

            self.child_voc_spinner.set_value(child_vocs)
            for pos in markers:
                self.scale.add_mark(pos, gtk.POS_BOTTOM, BackendUtils.get_time_str(pos, pad_hour_min=False, show_hours=False, show_decimals=False))

            self.update_progress_labels(check2)

        def hookup(self, check2):
            test2 = check2.test2s[check2.test2_index]

            self.sm = TestWindow.TestStateMachine(self, test2)
            
            self.handler_man.add_handler(self.next_button, 'clicked', lambda w: self.sm.drive(TestWindow.TestStateMachine.ACTIONS.NEXT))
            self.handler_man.add_handler(self.prev_button, 'clicked', lambda w: self.sm.drive(TestWindow.TestStateMachine.ACTIONS.PREV))
            self.handler_man.add_handler(self.play_button, 'clicked', lambda w: self.sm.drive(TestWindow.TestStateMachine.ACTIONS.PLAY))

            self.handler_man.add_handler(self.clip_spinner, 'value-changed', lambda w: self.sm.drive(TestWindow.TestStateMachine.ACTIONS.ADJUST))
            self.handler_man.add_handler(self.scale.get_adjustment(), 'value-changed', self._snap_scale)

            self.handler_man.add_handler(self.trans_entry.get_buffer(), 'changed', lambda w: self._update_word_count())

            self.handler_man.add_handler(self.child_voc_spinner, 'value-changed', lambda w: self.trans_entry.grab_focus())

        def unhook(self):
            self.handler_man.remove_handlers(self.next_button, ['clicked'])
            self.handler_man.remove_handlers(self.prev_button, ['clicked'])
            self.handler_man.remove_handlers(self.play_button, ['clicked'])

            self.handler_man.remove_handlers(self.clip_spinner, ['value-changed'])
            self.handler_man.remove_handlers(self.scale.get_adjustment(), ['value-changed'])

            self.handler_man.remove_handlers(self.trans_entry.get_buffer(), ['changed'])

            self.handler_man.remove_handlers(self.child_voc_spinner, ['value-changed'])

            self.sm = None

        def get_ui_save_data(self):
            save_data = self.sm.get_ui_save_data() if self.sm else {}
            #note: clip length and word count don't need to be saved, as they can be calculated from info we are storing

            return save_data

    class TestStateMachine():
        STATES = Enum('INITIAL MARKER_UNPLAYED MARKER_PLAYED'.split())
        ACTIONS = Enum('NEXT PREV PLAY ADJUST'.split())
        
        def __init__(self, controls, test2):
            self.controls = controls
            self.test2 = test2
            
            self.seg_len = self.controls.scale.get_adjustment().get_upper()

            self.route_dict = {
                TestWindow.TestStateMachine.STATES.INITIAL: lambda action: self._initial(),
                TestWindow.TestStateMachine.STATES.MARKER_UNPLAYED: self._marker_unplayed,
                TestWindow.TestStateMachine.STATES.MARKER_PLAYED: self._marker_played,
                }

            if self.test2.ui_save_data:
                self.markers = self.test2.ui_save_data['markers']
                self.marker_index = self.test2.ui_save_data['marker_index']
                self.state = self.test2.ui_save_data['sm_state']
            else:
                self.markers = []
                self.marker_index = -1
                self.state = TestWindow.TestStateMachine.STATES.INITIAL
                self.drive(None)

        def _update_clip_spinner(self):
            self.controls.handler_man.block_handler(self.controls.clip_spinner, 'value-changed')
            
            enabled = (self.marker_index == len(self.markers) - 2)
            self.controls.clip_spinner.set_sensitive(enabled)

            val = self.markers[self.marker_index + 1] - self.markers[self.marker_index]
            self.controls.clip_spinner.set_value(val)

            self.controls.handler_man.unblock_handler(self.controls.clip_spinner, 'value-changed')

        def _append_marker(self, pos, append_to_self=True):
            if append_to_self:
                self.markers.append(pos)
            self.controls.scale.add_mark(pos, gtk.POS_BOTTOM, BackendUtils.get_time_str(pos, pad_hour_min=False, show_hours=False, show_decimals=False))

        def _update_scale_pos(self):
            self.controls.handler_man.block_handler(self.controls.scale.get_adjustment(), 'value-changed')
            self.controls.scale.set_value(self.markers[self.marker_index])
            self.controls.handler_man.unblock_handler(self.controls.scale.get_adjustment(), 'value-changed')

        def _update_scale_fill_lev(self, lev):
            if self.controls.scale.get_fill_level() < lev:
                self.controls.scale.set_fill_level(lev)

        def drive(self, action):
            #old_state = self.state
            self.route_dict[self.state](action)
            self.controls.trans_entry.grab_focus()
            #new_state = self.state
            #states = TestWindow.TestStateMachine.STATES.get_ordered_keys()
            #print '%s -> %s' % (states[old_state], states[new_state])

        def get_ui_save_data(self):
            return {
                'markers': self.markers,
                'marker_index': self.marker_index,
                'sm_state': self.state,
                'fill_lev': self.controls.scale.get_fill_level(),
                }

        def _play_clip(self, start, end):
            wav_parser = WavParser(self.test2.wav_filename)
            wav_parser.play_clip(start, end)
            wav_parser.close()

        def _initial(self):
            self.marker_index = 0
            self._append_marker(0)
            next_pos = self.controls.clip_spinner.get_value_as_int()

            max_pos = self.controls.scale.get_adjustment().get_upper()
            if next_pos >= max_pos:
                next_pos = max_pos

            self._append_marker(next_pos)
            self.state = TestWindow.TestStateMachine.STATES.MARKER_UNPLAYED

        def _marker_unplayed(self, action):
            if action == TestWindow.TestStateMachine.ACTIONS.NEXT:
                pass
            
            elif action == TestWindow.TestStateMachine.ACTIONS.PREV:
                #go back if we're not at the initial mark
                if self.marker_index > 0:
                    self.marker_index -= 1
                    self._update_scale_pos()
                    self.state = TestWindow.TestStateMachine.STATES.MARKER_PLAYED
                    self._update_clip_spinner()

            elif action == TestWindow.TestStateMachine.ACTIONS.PLAY:
                fill_lev = self.markers[self.marker_index + 1]
                if self.controls.scale.get_fill_level() < fill_lev:
                    self.controls.scale.set_fill_level(fill_lev)
                self.state = TestWindow.TestStateMachine.STATES.MARKER_PLAYED

                wav_offset_sec = self.test2.get_start_time_offset()
                start = wav_offset_sec + self.markers[self.marker_index]
                end = wav_offset_sec + self.markers[self.marker_index + 1]
                t = threading.Thread(target=self._play_clip, args=(start, end))
                t.start()

            elif action == TestWindow.TestStateMachine.ACTIONS.ADJUST:
                #assume we are at the second-last marker (this is enforced by setting clip_spinner to insensitive at all other times)
                max_pos = self.controls.scale.get_adjustment().get_upper()
                fill_lev = self.controls.scale.get_fill_level()
                new_pos = self.markers[self.marker_index] + self.controls.clip_spinner.get_value_as_int()
                if new_pos > max_pos:
                    new_pos = max_pos

                self.controls.scale.clear_marks()
                self.markers.pop(-1)
                for mark in self.markers:
                    self._append_marker(mark, False)
                self._append_marker(new_pos)
                
                self.controls.scale.set_fill_level(fill_lev)
                self._update_scale_pos()

        def _marker_played(self, action):
            if action == TestWindow.TestStateMachine.ACTIONS.NEXT:
                max_pos = self.controls.scale.get_adjustment().get_upper()
                
                if self.markers[self.marker_index + 1] != max_pos:
                    self.marker_index += 1
                    self._update_scale_pos()

                    if self.marker_index == len(self.markers) - 1:
                        next_pos = self.markers[self.marker_index] + self.controls.clip_spinner.get_value_as_int()
                        if next_pos > max_pos:
                            next_pos = max_pos

                        self._append_marker(next_pos)

                    self._update_clip_spinner()
                    if self.controls.scale.get_fill_level() == self.markers[self.marker_index]:
                        self.state = TestWindow.TestStateMachine.STATES.MARKER_UNPLAYED

            elif action == TestWindow.TestStateMachine.ACTIONS.PREV:
                #go back if we're not at the initial mark
                if self.marker_index > 0:
                    self.marker_index -= 1
                    self._update_scale_pos()
                    self._update_clip_spinner()

            elif action == TestWindow.TestStateMachine.ACTIONS.PLAY:
                self.controls.trans_entry.grab_focus()
                wav_offset_sec = self.test2.get_start_time_offset()
                start = wav_offset_sec + self.markers[self.marker_index]
                end = wav_offset_sec + self.markers[self.marker_index + 1]
                t = threading.Thread(target=self._play_clip, args=(start, end))
                t.start()

            elif action == TestWindow.TestStateMachine.ACTIONS.ADJUST:
                #assume we are at the second-last marker (this is enforced by setting clip_spinner to insensitive at all other times)
                max_pos = self.controls.scale.get_adjustment().get_upper()
                new_pos = self.markers[self.marker_index] + self.controls.clip_spinner.get_value_as_int()
                if new_pos > max_pos:
                    new_pos = max_pos

                self.controls.scale.clear_marks()
                self.markers.pop(-1)
                for mark in self.markers:
                    self._append_marker(mark, False)
                self._append_marker(new_pos)

                self.controls.scale.set_fill_level(self.markers[-2]) #last segment is now unplayed
                self._update_scale_pos()

                if self.marker_index == len(self.markers) - 2:
                    self.state = TestWindow.TestStateMachine.STATES.MARKER_UNPLAYED
