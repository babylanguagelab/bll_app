from gi.repository import Gtk as gtk
from utils.ui_utils import UIUtils
from db.bll_database import BLLDatabase
from data_structs.pitch_study_props import PitchStudyProps
from utils.form import Form

class OptionsWindow():
    def __init__(self):
        self.bll_db = BLLDatabase()
        self.props = PitchStudyProps.db_select(self.bll_db)[0]
        
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Options')
        self.window.connect('destroy', lambda w: self.window.destroy())
        self.window.set_border_width(10)
        self.window.set_default_size(210, 100)

        vbox = gtk.VBox()
        grid = self._build_options_grid()
        bbox = self._build_button_box()

        vbox.pack_start(grid, False, False, 0)
        vbox.pack_start(bbox, False, False, 0)
        
        self.window.add(vbox)
        self.window.show_all()

    def _build_button_box(self):
        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.ButtonBoxStyle.EDGE)

        cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL, label='Cancel')
        cancel_button.connect('clicked', lambda w: self.window.destroy())
        button_box.add(cancel_button)
        
        ok_button = gtk.Button(stock=gtk.STOCK_OK, label='Run')
        ok_button.connect('clicked', lambda w: self._update_options())
        button_box.add(ok_button)

        return button_box
        
    def _build_options_grid(self):
        grid = gtk.Grid()

        self.form = Form()
        
        adj = gtk.Adjustment(value=1, lower=1, upper=100, step_increment=1, page_increment=1, page_size=1)
        max_parts_spinner = gtk.SpinButton()
        max_parts_spinner.set_adjustment(adj)
        max_parts_spinner.set_snap_to_ticks(True)
        max_parts_spinner.set_value(self.props.max_parts_per_batch)
        self.form.max_parts_spinner = max_parts_spinner
        max_parts_label = gtk.Label('Max Participants/Batch')
        grid.attach(max_parts_label, 0, 0, 1, 1)
        grid.attach(max_parts_spinner, 1, 0, 1, 1)

        adj = gtk.Adjustment(value=1, lower=1, upper=100, step_increment=1, page_increment=1, page_size=1)
        num_opts_spinner = gtk.SpinButton()
        num_opts_spinner.set_adjustment(adj)
        num_opts_spinner.set_snap_to_ticks(True)
        num_opts_spinner.set_value(self.props.num_options)
        self.form.num_opts_spinner = num_opts_spinner
        num_opts_label = gtk.Label('Judgement Options')
        grid.attach(num_opts_label, 0, 1, 1, 1)
        grid.attach(num_opts_spinner, 1, 1, 1, 1)

        adj = gtk.Adjustment(value=1, lower=1, upper=100000, step_increment=1, page_increment=1, page_size=1)
        break_interval_spinner = gtk.SpinButton()
        break_interval_spinner.set_adjustment(adj)
        break_interval_spinner.set_snap_to_ticks(True)
        break_interval_spinner.set_value(self.props.break_interval)
        self.form.break_interval_spinner = break_interval_spinner
        break_interval_label = gtk.Label('Clip break interval')
        grid.attach(break_interval_label, 0, 2, 1, 1)
        grid.attach(break_interval_spinner, 1, 2, 1, 1)

        adj = gtk.Adjustment(value=0.0, lower=0.0, upper=100.0, step_increment=0.1, page_increment=0.1, page_size=0.1)
        sound_del_spinner = gtk.SpinButton()
        sound_del_spinner.set_adjustment(adj)
        sound_del_spinner.set_increments(0.1, 0.1)
        sound_del_spinner.set_digits(1)
        sound_del_spinner.set_snap_to_ticks(True)
        sound_del_spinner.set_value(self.props.inter_clip_sound_del)
        self.form.sound_del_spinner = sound_del_spinner
        sound_del_label = gtk.Label('Sec between sounds')
        grid.attach(sound_del_label, 0, 3, 1, 1)
        grid.attach(sound_del_spinner, 1, 3, 1, 1)
        
        return grid

    def _update_options(self):
        max_parts = self.form.max_parts_spinner.get_value_as_int()
        self.props.update_prop(self.bll_db, PitchStudyProps.PROPS.MAX_PARTS_PER_BATCH, max_parts)
        
        num_opts = self.form.num_opts_spinner.get_value_as_int()
        self.props.update_prop(self.bll_db, PitchStudyProps.PROPS.NUM_OPTIONS, num_opts)
        
        break_interval = self.form.break_interval_spinner.get_value_as_int()
        self.props.update_prop(self.bll_db, PitchStudyProps.PROPS.BREAK_INTERVAL, break_interval)
        
        sound_del = self.form.sound_del_spinner.get_value()
        self.props.update_prop(self.bll_db, PitchStudyProps.PROPS.INTER_CLIP_SOUND_DEL, sound_del)
        self.window.destroy()

        
