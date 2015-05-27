from gi.repository import Gtk as gtk, Pango
from utils.ui_utils import UIUtils
from db.bll_database import BLLDatabase
from data_structs.pitch_study_props import PitchStudyProps
from parsers.wav_parser import WavParser
import time
import os

class TestingWindow():
    def _update_rating(self, db, rating):
        rows = db.select(
            'clips',
            ['id'],
            where_cond = 'Batch_Num = ? and Batch_Order = ?',
            params = [self.batch_num, self.order_num]
        )
        clip_id = rows[0][0]
        
        db.insert(
            'ratings',
            ['clip_id', 'Participant_Num', 'Question_Rating'],
            [[clip_id, self.participant_num, rating]]
        )
        
    def _get_num_clips(self, db):
        row = db.select(
            'clips',
            ['count(id)'],
            where_cond = 'Batch_Num = ?',
            params = [self.batch_num]
        )
        return row[0][0]

    def _next(self, db, rating):
        num_clips = self._get_num_clips(db)
        
        if self.order_num == num_clips:
            self._finish()
            
        else:
            self._update_rating(db, rating)
            self.order_num += 1
            self._update_step(db)

            if (self.order_num - 1) == num_clips or num_clips == 1:
                self._finish()

            elif (self.order_num - 1) % self.props.break_interval == 0:
                self.test_grid.hide()
                self.pause_grid.show_all()

            else:
                self._play_clip(db)

    def _finish(self):
        self.window.destroy()
        UIUtils.show_message_dialog('Testing complete! Thanks for your help.')

    def _update_step(self, db):
        row = db.select(
            'clips',
            ['Filename', 'Age'],
            where_cond = 'Batch_Num = ? and Batch_Order = ?',
            params = [self.batch_num, self.order_num]
        )
        filename, age = row[0]
        self.filename = '%sbatch%d/%s_%d-%d.wav' % (self.props.clips_dir_path, self.batch_num, filename[:-5], age, self.order_num)
        
        num_clips = self._get_num_clips(db)
        #self.label.set_text('Clip %d of %d' % (self.order_num, self._get_num_clips(db)))
        self.progress.set_fraction(self.order_num / float(self._get_num_clips(db)))

    def _play_clip(self, db):
        map(lambda button: button.set_sensitive(False), self.scale_buttons)
        while gtk.events_pending():
            gtk.main_iteration()

        time.sleep(self.props.inter_clip_sound_del)

        self._toggle_playing_icon(True)
            
        wav_parser = WavParser(self.filename)
        wav_parser.play_clip(0, wav_parser.get_sound_len())
        wav_parser.close()
        
        map(lambda button: button.set_sensitive(True), self.scale_buttons)
        self._toggle_playing_icon(False)

    def _continue(self, db):
        self.pause_grid.hide()
        self.test_grid.show_all()

        self._play_clip(db)

    def _get_pause_grid(self, db):
        vbox = gtk.VBox()

        label = gtk.Label('Click the button below when you\'re ready to continue.')
        vbox.pack_start(label, False, False, 0)
        
        button = gtk.Button('Continue')
        button.connect('clicked', lambda w: self._continue(db))
        hbox = gtk.HBox()
        hbox.pack_start(button, True, False, 0)
        vbox.pack_start(hbox, True, True, 10)
        
        return vbox

    def _toggle_playing_icon(self, is_on):
        icon = UIUtils.BUTTON_ICONS.VOLUME_OFF
        if is_on:
            icon = UIUtils.BUTTON_ICONS.VOLUME_ON

        icon_path = UIUtils.get_icon_path(
                icon,
                UIUtils.BUTTON_ICON_SIZES.PX64
            )
        
        self.playing_icon.set_from_file(icon_path)

        while gtk.events_pending():
            gtk.main_iteration()
        
    def _get_test_grid(self, db):
        grid = gtk.Grid()
        
        self.progress = gtk.ProgressBar()
        self.progress.set_orientation(gtk.Orientation.HORIZONTAL)
        self.progress.set_fraction(self.order_num + 1 / float(self._get_num_clips(db)))
        #self.progress.set_vexpand(False)
        #self.progress.set_vexpand_set(True)
        grid.attach(self.progress, 0, 0, 5, 1)
        
        #self.label = gtk.Label('Clip %d of %d' % (self.order_num + 1, self._get_num_clips(db)))
        #UIUtils.set_font_size(self.label, 25, bold=True)
        #self.label.set_hexpand(True)
        #self.label.set_hexpand_set(True)
        #grid.attach(self.label, 0, 0, 5, 1)

        question_label = gtk.Label('How much does this sentence sound like a question?')
        UIUtils.set_font_size(question_label, 30, bold=True)
        grid.attach(question_label, 0, 1, 5, 1)

        self.playing_icon = gtk.Image()
        self.playing_icon.set_vexpand(True)
        self.playing_icon.set_vexpand_set(True)
        self._toggle_playing_icon(False)
        grid.attach(self.playing_icon, 0, 2, 5, 1)

        self.scale_buttons = []
        button_grid = gtk.Grid()
        button_grid.set_column_homogeneous(True)

        label_low = gtk.Label('Not Very Much like a Question')
        label_low.set_alignment(0, 0)
        UIUtils.set_font_size(label_low, 20, bold=True)
        button_grid.attach(label_low, 0, 0, 2, 1)
        
        label_high = gtk.Label('Very Much like a Question')
        label_high.set_alignment(1, 0)
        UIUtils.set_font_size(label_high, 20, bold=True)
        button_grid.attach(label_high, self.props.num_options - 2, 0, 2, 1)
        
        for i in range(self.props.num_options):
            button = gtk.Button('\n' + str(i + 1) + '\n')
            UIUtils.set_font_size(button, 15, bold=True)
            button.connect('button-release-event', lambda w, e: self._next(db, int(w.get_label())))
            button.set_vexpand(False)
            button.set_vexpand_set(False)

            self.scale_buttons.append(button)
            button.set_hexpand(True)
            button.set_hexpand_set(True)
            button_grid.attach(button, i, 1, 1, 1)

        grid.attach(button_grid, 0, 3, 5, 1)

        return grid
    
    def __init__(self, db, batch_num, participant_num):
        self.bll_db = BLLDatabase()
        self.props = PitchStudyProps.db_select(self.bll_db)[0]
        self.bll_db.close()
        
        self.batch_num = batch_num
        self.participant_num = participant_num
        self.order_num = 1
        self.filename = None

        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Batch %d' % (batch_num))
        #self.window.set_resizable(False)
        #self.window.connect('delete-event', lambda x, y: True)
        self.window.connect('destroy', lambda w: self.window.destroy())
        self.window.set_border_width(10)
        self.window.set_size_request(800, 600)

        vbox = gtk.VBox()
        self.test_grid = self._get_test_grid(db)
        self._update_step(db)
        vbox.pack_start(self.test_grid, True, True, 0)
        self.test_grid.hide()

        self.pause_grid = self._get_pause_grid(db)
        vbox.pack_start(self.pause_grid, True, False, 0)
        self.pause_grid.show_all()

        self.window.add(vbox)
        vbox.show()
        self.window.show()        
        
