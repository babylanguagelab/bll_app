from gi.repository import Gtk as gtk
from gi.repository import GObject as gobject
import logging

from parsers.trs_parser import TRSParser
from parsers.wav_parser import WavParser
from utils.ui_utils import UIUtils
from utils.progress_dialog import ProgressDialog
from utils.enum import Enum
from utils.backend_utils import BackendUtils
from parsers.errors import ParserWarning, ParserError

class VerificationWindow():
    ERROR_STATES = Enum(['NONE', 'WARNING', 'ERROR'])
    def __init__(self, filename, progress_dialog):
        self.logger = logging.getLogger(__name__)
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Transcription Verifier')
        self.window.connect('destroy', lambda x: self.window.destroy())
        self.window.set_border_width(10)
        self.window.set_default_size(580, 500)

        self.trs_parser = TRSParser(filename)
        self.trs_parser.parse(
            progress_update_fcn=progress_dialog.set_fraction,
            progress_next_phase_fcn=progress_dialog.next_phase,
            remove_bad_trans_codes=False
        )
        self.wav_parser = None

        progress_dialog.next_phase()
        self.filter_errors = True
        self.toolbar = self.build_toolbar()
        self.treeview = self.build_treeview(progress_dialog.set_fraction)
        self.treeview.expand_all()

        scrolled_win = gtk.ScrolledWindow()
        scrolled_win.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
        scrolled_win.add(self.treeview)

        vbox = gtk.VBox(False, 2)
        vbox.pack_start(self.toolbar, False, False, 0)
        vbox.pack_start(scrolled_win, True, True, 0)

        self.window.add(vbox)
        
        self.window.show_all()

    def build_toolbar(self):
        toolbar = gtk.Toolbar()
        toolbar.set_orientation(gtk.Orientation.HORIZONTAL)

        filter_errors_button = gtk.ToggleToolButton()
        filter_errors_button.set_active(True) #set this before the connecting the clicked handler so it doesn't cause trouble
        filter_errors_button.connect('toggled', lambda w: self.toggle_filter_errors(w.get_active()))
        filter_errors_icon = gtk.Image()
        filter_errors_icon.set_from_file(UIUtils.get_icon_path(UIUtils.BUTTON_ICONS.FLAG))
        filter_errors_button.set_label('Show Errors Only')
        filter_errors_button.set_icon_widget(filter_errors_icon)

        expand_button = gtk.ToolButton()
        expand_icon = gtk.Image()
        expand_icon.set_from_file(UIUtils.get_icon_path(UIUtils.BUTTON_ICONS.EXPAND))
        expand_button.set_label('Expand All')
        expand_button.set_icon_widget(expand_icon)
        expand_button.connect('clicked', lambda w: self.treeview.expand_all())

        collapse_button = gtk.ToolButton()
        collapse_icon = gtk.Image()
        collapse_icon.set_from_file(UIUtils.get_icon_path(UIUtils.BUTTON_ICONS.COLLAPSE))
        collapse_button.set_label('Collapse All')
        collapse_button.set_icon_widget(collapse_icon)
        collapse_button.connect('clicked', lambda w: self.treeview.collapse_all())

        rescan_button = gtk.ToolButton()
        rescan_icon = gtk.Image()
        rescan_icon.set_from_file(UIUtils.get_icon_path(UIUtils.BUTTON_ICONS.REFRESH))
        rescan_button.set_label('Rescan File')
        rescan_button.set_icon_widget(rescan_icon)
        rescan_button.connect('clicked', lambda w: self._rescan_file())

        play_seg_button = gtk.ToolButton()
        play_icon = gtk.Image()
        play_icon.set_from_file(UIUtils.get_icon_path(UIUtils.BUTTON_ICONS.PLAY))
        play_seg_button.set_label('Play Seg')
        play_seg_button.set_icon_widget(play_icon)
        play_seg_button.connect('clicked', lambda w: self.play_selected_seg())

        close_button = gtk.ToolButton()
        close_icon = gtk.Image()
        close_icon.set_from_file(UIUtils.get_icon_path(UIUtils.BUTTON_ICONS.CLOSE))
        close_button.set_label('Close');
        close_button.set_icon_widget(close_icon)
        close_button.connect('clicked', lambda w: self.window.destroy())

        exit_button = gtk.ToolButton()
        exit_icon = gtk.Image()
        exit_icon.set_from_file(UIUtils.get_icon_path(UIUtils.BUTTON_ICONS.EXIT))
        exit_button.set_label('Exit')
        exit_button.set_icon_widget(exit_icon)
        exit_button.connect('clicked', lambda w: gtk.main_quit())

        toolbar.insert(filter_errors_button, -1)
        toolbar.insert(expand_button, -1)
        toolbar.insert(collapse_button, -1)
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        toolbar.insert(play_seg_button, -1)
        toolbar.insert(rescan_button, -1)
        toolbar.insert(gtk.SeparatorToolItem(), -1)
        toolbar.insert(close_button, -1)
        toolbar.insert(exit_button, -1)

        return toolbar

    def _rescan_file(self):
        self.window.set_sensitive(False)
        
        progress_dialog = ProgressDialog('Processing File...', ['Parsing trs file...', 'Validating data...', 'Building UI...'])
        progress_dialog.show()
        
        #this causes the parser to invalidate all cache, re-open and re-parse the file
        self.trs_parser.re_parse(progress_update_fcn=progress_dialog.set_fraction,
                                 progress_next_phase_fcn=progress_dialog.next_phase)

        #build a new treeview model based on the new data
        progress_dialog.next_phase()
        filter_model = self._build_tree_store(progress_dialog.set_fraction)
        self.treeview.set_model(filter_model)

        #Presumably the most common cause for rescanning is to check if errors have been fixed.
        #If the error filter is on, automatically expand all rows to show any remaining errors.
        if self.filter_errors:
            self.treeview.expand_all()
            
        self.window.set_sensitive(True)
    
    def _build_tree_store(self, progress_update_fcn):
        #segment/utter id, description, error_state (0 = none, 1 = warning, 2 = error)
        tree_store = gtk.TreeStore(gobject.TYPE_INT, gobject.TYPE_STRING, gobject.TYPE_INT)

        #note: these may be errors or warnings
        cur_utter = 0
        for seg in self.trs_parser.parse():
            seg_speakers = ''
            if seg.speakers:
                for i in range(len(seg.speakers)):
                    seg_speakers += seg.speakers[i].speaker_codeinfo.get_code()
                    if i < len(seg.speakers) - 1:
                        seg_speakers += ' + '
            else:
                seg_speakers = ' - '

            seg_iter = tree_store.append(None, [seg.num,
                                                '%s [%s - %s]' % ( seg_speakers, BackendUtils.get_time_str(seg.start), BackendUtils.get_time_str(seg.end) ),
                                                VerificationWindow.ERROR_STATES.NONE])
                
            for utter in seg.utters:
                speaker_cd = '?' #question mark indicates an error occured - if we have utter.speaker, we should have an utter code. Errors occur if the utter code isn't in the DB lookup table (which means that utter.speaker != None, but utter.speaker.speaker_codeinfo == None. This is the condition that falls through the if-else blocks below).
                if utter.speaker:
                    if utter.speaker.speaker_codeinfo:
                        speaker_cd = utter.speaker.speaker_codeinfo.get_code()
                else:
                    speaker_cd = ' - '

                desc_str = '%s [%s - %s]' % ( speaker_cd, BackendUtils.get_time_str(utter.start), BackendUtils.get_time_str(utter.end))
                if utter.lena_notes:
                    desc_str += ' %s' % (utter.lena_notes)
                if utter.trans_phrase:
                    desc_str += ' %s' % (utter.trans_phrase)
                if utter.lena_codes:
                    desc_str += ' |%s|' % ('|'.join(utter.lena_codes))
                if utter.trans_codes:
                    if not utter.lena_codes:
                        desc_str += ' |'
                    desc_str += '%s|' % ('|'.join(utter.trans_codes))
                    
                utter_iter = tree_store.append(seg_iter, [
                        utter.id,
                        desc_str,
                        VerificationWindow.ERROR_STATES.NONE
                        ])

                cur_utter += 1
                progress_update_fcn(float(cur_utter) / float(self.trs_parser.total_utters))
            
                error_list = self.trs_parser.error_collector.get_errors_by_utter(utter)
                for error in error_list:
                    error_type = VerificationWindow.ERROR_STATES.ERROR
                    if isinstance(error, ParserWarning):
                        error_type = VerificationWindow.ERROR_STATES.WARNING
                        
                    error_iter = tree_store.append(utter_iter, [
                            -1,
                             '%s' % (error.msg),
                             error_type
                             ])

                    parent_it = utter_iter
                    while parent_it:
                        parent_error_type = tree_store.get_value(parent_it, 2)
                        if parent_error_type < error_type:
                            tree_store.set_value(parent_it, 2, error_type)
                        
                        parent_it = tree_store.iter_parent(parent_it)
            
        filter_model = tree_store.filter_new()
        filter_model.set_visible_func(self.filter)

        return filter_model
    
    def build_treeview(self, progress_update_fcn):
        filter_model = self._build_tree_store(progress_update_fcn)
        treeview = gtk.TreeView(filter_model)

        col = gtk.TreeViewColumn('ID', gtk.CellRendererText(), text=0)
        col.set_visible(False)
        treeview.append_column(col)

        renderer = gtk.CellRendererText()
        col = gtk.TreeViewColumn('Description', renderer, text=1)
        col.set_cell_data_func(renderer, self.cell_render_fcn)
        treeview.append_column(col)

        col = gtk.TreeViewColumn('Error State', gtk.CellRendererText(), text=2)
        col.set_visible(False)
        treeview.append_column(col)

        return treeview

    def cell_render_fcn(self, col, cell_renderer, model, it, user_data=None):
        error_state = model.get_value(it, 2)
        if error_state == VerificationWindow.ERROR_STATES.WARNING:
            cell_renderer.set_property('foreground', 'orange')
        elif error_state == VerificationWindow.ERROR_STATES.ERROR:
            cell_renderer.set_property('foreground', 'red')
        else:
            cell_renderer.set_property('foreground', 'black')

        return
    
    #returns true if row pointed to by 'it' should be visible
    def filter(self, model, it, user_data):
        result = True
        if self.filter_errors:
            result = model.get_value(it, 2) > VerificationWindow.ERROR_STATES.NONE

        return result
    
    def toggle_filter_errors(self, filter_errors):
        self.filter_errors = not self.filter_errors
        self.treeview.get_model().refilter()

    def play_selected_seg(self):
        (model, it) = self.treeview.get_selection().get_selected()
        if it:
            #if they've selected an error row, find the top level parent (the segment) and use it instead
            parent = model.iter_parent(it)
            while parent:
                it = parent
                parent = model.iter_parent(it)

            seg_num = model.get_value(it, 0) if it else None
            seg = self.trs_parser.parse()[seg_num]

            if not self.wav_parser:
                dialog = gtk.FileChooserDialog(title='Select WAV File',
                                               action=gtk.FileChooserAction.OPEN,
                                               buttons=(gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL, gtk.STOCK_OPEN, gtk.ResponseType.OK))
                dialog.set_default_response(gtk.ResponseType.OK)

                for filter_opt in (('wav Files', '*.wav'), ('All Files', '*')):
                    file_filter = gtk.FileFilter()
                    file_filter.set_name(filter_opt[0])
                    file_filter.add_pattern(filter_opt[1])
                    dialog.add_filter(file_filter)

                response = dialog.run()
                if response == gtk.ResponseType.OK:
                    filename = dialog.get_filename()
                    self.wav_parser = WavParser(filename)

                dialog.destroy()

            if self.wav_parser:
                self.wav_parser.play_seg(seg)

            else:
                UIUtils.show_no_sel_dialog()
        else:
            UIUtils.show_no_sel_dialog()
        
