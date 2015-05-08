from gi.repository import Gtk as gtk
from utils.ui_utils import UIUtils
from db.database import Database
from ui.pitch_study_app.testing_window import TestingWindow

class BatchSelectionWindow():
    PARTICIPANTS_PER_BATCH = 10
    
    def __init__(self, db_path):
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Select Batch Number')
        self.window.connect('destroy', lambda w: self.window.destroy())
        self.window.set_border_width(10)
        self.window.set_default_size(210, 100)

        db = Database(db_path)
        
        vbox = gtk.VBox()

        next_batch_num, next_part_num = self._get_next_nums(db)
        
        label = gtk.Label('Select the batch number to run: ')
        batch_spin_adj = gtk.Adjustment(value=1, lower=1, upper=self._get_total_batches(db) + 1, step_increment=1, page_increment=1, page_size=1)
        self.batch_spin = gtk.SpinButton()
        self.batch_spin.set_adjustment(batch_spin_adj)
        self.batch_spin.set_snap_to_ticks(True)
        self.batch_spin.set_value(next_batch_num)
        hbox = gtk.HBox()
        hbox.pack_start(label, True, True, 0)
        hbox.pack_start(self.batch_spin, True, True, 0)
        vbox.pack_start(hbox, True, True, 0)

        label = gtk.Label('Select the participant number to use: ')
        part_spin_adj = gtk.Adjustment(value=1, lower=1, upper=BatchSelectionWindow.PARTICIPANTS_PER_BATCH + 1, step_increment=1, page_increment=1, page_size=1)
        self.part_spin = gtk.SpinButton()
        self.part_spin.set_adjustment(part_spin_adj)
        self.part_spin.set_snap_to_ticks(True)
        self.part_spin.set_value(next_part_num)
        hbox = gtk.HBox()
        hbox.pack_start(label, True, True, 0)
        hbox.pack_start(self.part_spin, True, True, 0)
        vbox.pack_start(hbox, True, True, 0)
        
        button_box = self._build_button_box(db)
        vbox.pack_start(button_box, True, True, 0)

        self.window.add(vbox)
        self.window.show_all()

    def _get_next_nums(self, db):
        batch_num = 1
        part_num = 1
        
        total_batches = self._get_total_batches(db)
        
        rows = db.select(
            'clips c join ratings r on c.id = r.clip_id',
            ['max(c.Batch_Num)'],
            where_cond = 'r.Participant_Num is not null'
        )
        if rows and rows[0][0] is not None:
            cur_batch_num = rows[0][0]
            rows = db.select(
                'clips c join ratings r on c.id = r.clip_id',
                ['max(r.Participant_Num)'],
                where_cond = 'c.Batch_Num = ?',
                params = [cur_batch_num]
            )
            if rows and rows[0][0] is not None:
                cur_part_num = rows[0][0]

                if cur_part_num < BatchSelectionWindow.PARTICIPANTS_PER_BATCH:
                    part_num = cur_part_num + 1
                    batch_num = cur_batch_num
                elif cur_batch_num < total_batches:
                    batch_num = cur_batch_num + 1
                    #part_num = 1

        return batch_num, part_num

    def _get_total_batches(self, db):
        rows = db.select(
            'clips',
            ['max(Batch_Num)']
        )
        return rows[0][0]
        
    def _check_if_used(self, db, batch_num, participant_num):
        rows = db.select(
            'clips c join ratings r on c.id = r.clip_id',
            ['count(c.id)'],
            where_cond = 'c.Batch_Num = ? and r.Participant_Num = ?',
            params = [batch_num, participant_num]
        )
        return rows[0][0] > 0

    def _build_button_box(self, db):
        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.ButtonBoxStyle.EDGE)

        cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL, label='Cancel')
        cancel_button.connect('clicked', lambda w: self.window.destroy())
        button_box.add(cancel_button)
        
        ok_button = gtk.Button(stock=gtk.STOCK_OK, label='Run')
        ok_button.connect('clicked', lambda w: self.check_input(db))
        button_box.add(ok_button)

        return button_box

    def check_input(self, db):
        batch_num = self.batch_spin.get_value_as_int()
        participant_num = self.part_spin.get_value_as_int()
        if self._check_if_used(db, batch_num, participant_num):
            response = UIUtils.show_confirm_dialog('Participant %d has recorded responses for Batch %d.\nContinuing will overwrite the existing data for this participant (in this batch).\nDo you want continue?' % (participant_num, batch_num))
            if response:
                db.delete(
                    'ratings',
                    where_cond = 'clip_id in (select id from clips where Batch_Num = ?) and Participant_Num = ?',
                    params = [batch_num, participant_num]
                )
                self._start_testing(db, batch_num, participant_num)

        else:
            self._start_testing(db, batch_num, participant_num)

        #db.close()
        
    def _start_testing(self, db, batch_num, participant_num):
        self.window.destroy()
        TestingWindow(db, batch_num, participant_num)
