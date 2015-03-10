from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GObject as gobject
import subprocess
import re
import sre_constants
import logging
import traceback

from utils.ui_utils import UIUtils
from utils.progress_dialog import ProgressDialog
from parsers.trs_parser import TRSParser
from data_structs.seg_filters import WHQFilter
from data_structs.output import Output
from data_structs.output_calcs import CountOutputCalc
from parsers.freq_exporter import FreqExporter
from parsers.filter_manager import FilterManager
from db.bll_database import DBConstants

class FreqWindow():
    def __init__(self, filename, progress_dialog):
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('WH-Frequency Counter')
        self.window.set_border_width(10)
        self.window.set_default_size(730, 400)
        
        self.logger = logging.getLogger(__name__)

        self.count_cols = self._get_initial_count_cols()
        self.trs_parser = TRSParser(filename)
        segments = self.trs_parser.parse(progress_update_fcn=progress_dialog.set_fraction, progress_next_phase_fcn=progress_dialog.next_phase, validate=False, seg_filters=[])

        self.filter_manager = FilterManager(segments) #this object caches original segs and helps with lookup by segment number
        calc = CountOutputCalc('', CountOutputCalc.COUNT_TYPES.PER_SEG, 1)
        self.output = Output('', '', [WHQFilter()], calc, False) #this object filters and allows us to retrieve the filtered segs
        map(lambda seg: self.output.add_item(seg), segments)

        treeview = self._build_treeview()
        #ensure progress dialog self-destructs even if no utterances are found (in that case the above call never invokes progress_dialog.set_fraction)
        progress_dialog.ensure_finish()
        
        scrolled_win = gtk.ScrolledWindow()
        scrolled_win.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        scrolled_win.add(treeview)

        export_button = UIUtils.create_button('Export Results', UIUtils.BUTTON_ICONS.EXPORT)
        export_button.connect('clicked', lambda widget: self._export_results(treeview))

        close_button = UIUtils.create_button('Close', UIUtils.BUTTON_ICONS.CLOSE)
        close_button.connect('clicked', lambda w: self.window.destroy())

        add_button = UIUtils.create_button('Add Count Column', UIUtils.BUTTON_ICONS.ADD)
        add_button.connect('clicked', lambda w: self._add_count_col(treeview))

        self.remove_button = UIUtils.create_button('Remove Count Column', UIUtils.BUTTON_ICONS.REMOVE)
        self.remove_button.connect('clicked', lambda w: self._remove_count_col(treeview))
        self._update_remove_button_state()

        options_frame = gtk.Frame(label='Options')
        options_vbox = gtk.VBox()
        self.linked_checkbox = gtk.CheckButton('Group Linked Segments')
        self.linked_checkbox.connect('toggled', self._toggle_seg_grouping, treeview)
        options_vbox.pack_start(self.linked_checkbox, False, False, 0)
        
        self.context_checkbox = gtk.CheckButton('Show Context')
        self.context_checkbox.connect('toggled', self._toggle_show_context, treeview)
        options_vbox.pack_start(self.context_checkbox, False, False, 0)

        options_frame.add(options_vbox)
        
        self.statusbar = gtk.Statusbar()
        self.statusbar.set_has_resize_grip(False)
        self.num_whq = treeview.get_model().iter_n_children(None)
        self._update_statusbar()
        
        vbox = gtk.VBox()
        
        bbox = gtk.HButtonBox()
        bbox.pack_start(export_button, True, False, 0)
        bbox.pack_start(add_button, True, False, 0)
        bbox.pack_start(self.remove_button, True, False, 0)
        bbox.pack_start(close_button, True, False, 0)

        vbox.pack_start(scrolled_win, True, True, 0)
        vbox.pack_start(self.statusbar, False, False, 0)
        vbox.pack_end(bbox, False, False, 0)
        vbox.pack_end(options_frame, False, False, 0)
        self.window.add(vbox)
        
        self.window.show_all()

    def _get_initial_count_cols(self):
        return map( lambda word: [word.capitalize(), word, 0], 'who what why when where how'.split() )

    def _toggle_show_context(self, checkbox, treeview):
        tree_model = self._build_list_store(link_segs=self.linked_checkbox.get_active(), prev_store=treeview.get_model(), show_context=self.context_checkbox.get_active())
        treeview.set_model(tree_model)
        
    def _toggle_seg_grouping(self, checkbox, treeview):
        tree_model = self._build_list_store(link_segs=self.linked_checkbox.get_active(), prev_store=None, show_context=self.context_checkbox.get_active())
        treeview.set_model(tree_model)
        self.num_whq = treeview.get_model().iter_n_children(None)
        self._update_statusbar()
        
    def _update_remove_button_state(self):
        self.remove_button.set_sensitive(len(self.count_cols) > 0)
        
    def _remove_count_col(self, treeview):
        dialog = gtk.Dialog(title='Remove Count Column',
                            buttons=(gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL, gtk.STOCK_OK, gtk.ResponseType.OK))
        dialog.set_default_response(gtk.ResponseType.OK)
        
        vbox = dialog.get_content_area()

        list_store = gtk.ListStore(gobject.TYPE_STRING)

        for i in range(len(self.count_cols)):
            list_store.append([ self.count_cols[i][0] ])
            
        combo = gtk.ComboBox(model=list_store)
        renderer = gtk.CellRendererText()
        combo.pack_start(renderer, True, True, 0)
        combo.add_attribute(renderer, 'text', 0)
        combo.set_active(0)
        
        hbox = gtk.HBox()
        hbox.pack_start(gtk.Label('Select Column:'), True, True, 0)
        hbox.pack_start(combo, True, True, 0)

        vbox.pack_start(hbox, True, True, 0)
        vbox.show_all()

        response = dialog.run()

        if response == gtk.ResponseType.CANCEL:
            dialog.destroy()
            done = True
            
        elif response == gtk.ResponseType.OK:
            col_index = combo.get_active()
            if col_index >= 0:
                dialog.destroy()

                self.count_cols = self.count_cols[:col_index] + self.count_cols[col_index + 1:]

                progress_dialog = ProgressDialog('Removing Column...', ['Rebuilding UI...'])
                progress_dialog.show()
                
                tree_model = self._build_list_store(link_segs=self.linked_checkbox.get_active(), prev_store=treeview.get_model(), show_context=self.context_checkbox.get_active())
                
                old_col = treeview.get_column(6 + col_index)
                treeview.remove_column(old_col)

                #update the 'text' property of the cell renderers in all columns after the removed column - otherwise cell values get mixed up
                i = 6 + col_index
                while i < tree_model.get_n_columns():
                    col = treeview.get_column(i)
                    renderer = col.get_cell_renderers()[0]
                    col.set_attributes(renderer, text=i)
                    i += 1

                treeview.set_model(tree_model)
                
                self._update_remove_button_state()
                self._update_statusbar()

                progress_dialog.ensure_finish()

    def _add_count_col(self, treeview):
        dialog = gtk.Dialog(title='Add Count Column',
                            buttons=(gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL, gtk.STOCK_OK, gtk.ResponseType.OK))
        dialog.set_default_response(gtk.ResponseType.OK)
        
        vbox = dialog.get_content_area()

        #table = gtk.Table(2, 2)
        grid = gtk.Grid()
        name_label = gtk.Label('Column Name:')
        #table.attach(name_label, 0, 1, 0, 1, gtk.EXPAND, gtk.EXPAND, 3, 3)
        grid.attach(name_label, 0, 0, 1, 1, 3)
        
        name_entry = gtk.Entry()
        #table.attach(name_entry, 1, 2, 0, 1, gtk.EXPAND, gtk.EXPAND, 3, 3)
        grid.attach(name_entry, 1, 0, 1, 1, 3)

        regex_label = gtk.Label('Search term:')
        #table.attach(regex_label, 0, 1, 1, 2, gtk.EXPAND, gtk.EXPAND, 3, 3)
        grid.attach(regex_label, 0, 1, 1, 1, 3)
        
        regex_entry = gtk.Entry()
        #table.attach(regex_entry, 1, 2, 1, 2, gtk.EXPAND, gtk.EXPAND, 3, 3)
        grid.attach(regex_entry, 1, 1, 1, 1, 3)
        
        vbox.pack_start(grid, True, True, 0)
        vbox.show_all()

        done = False
        while not done:
            response = dialog.run()
            if response == gtk.ResponseType.CANCEL:
                dialog.destroy()
                done = True

            elif response == gtk.ResponseType.OK:
                name = name_entry.get_text()
                regex = regex_entry.get_text()

                try:
                    re.compile(regex)

                    dialog.destroy()

                    self.count_cols.append( [name, regex, 0] ) #name, regex, total

                    progress_dialog = ProgressDialog('Adding New Column...', ['Counting occurrances...'])
                    progress_dialog.show()
                    list_store = self._build_list_store(link_segs=self.linked_checkbox.get_active(), prev_store=treeview.get_model(), show_context=self.context_checkbox.get_active())
                    progress_dialog.ensure_finish()
                    
                    treeview.set_model(list_store)
                    col = gtk.TreeViewColumn(name, gtk.CellRendererText(), text=list_store.get_n_columns() - 1)
                    treeview.append_column(col)
                    self._update_remove_button_state()
                    self._update_statusbar()
                    done = True

                except Exception as error:
                    if isinstance(error, sre_constants.error):
                        error_dialog = gtk.MessageDialog(buttons=(gtk.ButtonType.OK), message_format='The regular expression that has been entered is invalid.')
                        error_dialog.run()
                        error_dialog.destroy()
                    else:
                        error_dialog = gtk.MessageDialog(buttons=(gtk.ButtonType.OK), message_format='The application has encountered an internal error. Please contact your local programmer to assign blame.')
                        error_dialog.run()
                        error_dialog.destroy()
                        done = True
                        
                    if progress_dialog:
                        progress_dialog.destroy()

                    self.logger.error('Exception in add_column():\n %s\nStacktrace: %s' % (error, traceback.format_exc()))

    def _update_statusbar(self):
        context_id = self.statusbar.get_context_id('num_whq')
        self.statusbar.pop(context_id)
        totals = 'Totals: WHQ Count: %d' % (self.num_whq)

        for col in self.count_cols:
            totals += ', %s: %d' % (col[0], col[2])
            
        self.statusbar.push(context_id, totals)

    def _get_link_chain(self, cur_seg):
        cur = cur_seg
        chain = []
        while cur != None:
            chain.insert(cur, 0)
            cur = cur.prev

        cur = cur_seg.next
        while cur != None:
            chain.append(cur)

        return chain

    def _build_list_store_row(self, utter_id, start_time, end_time, trans_phrase, speaker_str, target_str, whq_count):
        start_time = ('%0.2f' % (start_time)) if start_time != None else ''
        end_time = ('%0.2f' % (end_time)) if end_time != None else ''
        
        return [
            utter_id,
            '%s - %s' % (start_time, end_time),
            trans_phrase,
            speaker_str,
            target_str,
            whq_count,
            ]

    def _find_utter_index(self, utter):
        utter_index = -1
        i = 0
        while i < len(utter.seg.utters) and utter_index < 0:
            if utter.seg.utters[i] == utter:
                utter_index = i
            i += 1

        return utter_index
    
    def _append_context(self, bwd_start_utter, fwd_start_utter, cur_phrase):
        #backward
        bwd_phrase = self._get_adjacent_phrase(bwd_start_utter, -1)
        fwd_phrase = self._get_adjacent_phrase(fwd_start_utter, 1)
        
        return '(%s)\n%s\n(%s)' % (bwd_phrase, cur_phrase, fwd_phrase)

    def _get_adjacent_phrase(self, start_utter, incr):
        utter_index = self._find_utter_index(start_utter) + incr
        seg_index = start_utter.seg.num
        phrase = None
        
        i_in_bounds = None
        init_j = None
        if incr < 0:
            i_in_bounds = lambda i: i >= 0
            init_j = lambda i, seg: utter_index if i == seg_index else len(seg.utters) - 1
            j_in_bounds = lambda j, seg: j >= 0
        else:
            i_in_bounds = lambda i: i < len(self.filter_manager.get_segs())
            init_j = lambda i, seg: utter_index if i == seg_index else 0
            j_in_bounds = lambda j, seg: j < len(seg.utters)

        i = seg_index
        while i_in_bounds(i) and not phrase:
            seg = self.filter_manager.get_seg_by_num(i)
            j = init_j(i, seg)
            while j_in_bounds(j, seg) and not phrase:
                phrase = seg.utters[j].trans_phrase
                j += incr
            i += incr

        return phrase or '-'

    def _build_list_store(self, link_segs=False, prev_store=None, show_context=False):
        #for now, we always grab segs and convert to chains later if needed
        segments = self.output.get_filtered_items()
        list_store = gtk.ListStore(gobject.TYPE_INT, #utterance id
                                   gobject.TYPE_STRING, #time
                                   gobject.TYPE_STRING, #phrase
                                   gobject.TYPE_STRING, #speakers
                                   gobject.TYPE_STRING, #target listeners
                                   gobject.TYPE_INT, #whq count
                                   *([gobject.TYPE_INT] * len(self.count_cols)) #user-defined 'count columns'
                                   )

        row_num = 0
        if link_segs:
            utter_chains = FilterManager.get_chains(segments)
            for head in utter_chains:
                cur = head
                prev = cur
                trans_phrase = cur.trans_phrase
                speaker_str = DBConstants.SPEAKER_CODES.get_option(cur.speaker.get_codeinfo().get_code()).desc if cur.speaker else '(Unknown)'
                target_str = DBConstants.TRANS_CODES[1].get_option(cur.trans_codes[1]).desc if cur.trans_codes else '(Unknown)'
                cur = cur.next

                count_col_vals = [0] * len(self.count_cols)
                
                while cur:
                    trans_phrase += '\n->%s' % (cur.trans_phrase)
                    if cur.speaker:
                        speaker_str += ', %s' % (DBConstants.SPEAKER_CODES.get_option(cur.speaker.get_codeinfo().get_code()).desc)
                    if cur.trans_codes:
                        target_str += ', %s' % (DBConstants.TRANS_CODES[1].get_option(cur.trans_codes[1]).desc)
                    prev = cur
                    cur = cur.next

                tail = FilterManager.get_endpoint(FilterManager.ENDPOINT_TYPES.TAIL, head)
                
                if show_context:
                    trans_phrase = self._append_context(head, tail, trans_phrase)
                
                whq_count = prev_store[row_num][5] if prev_store else 1
                row = self._build_list_store_row(head.id, head.start, tail.end, trans_phrase, speaker_str, target_str, whq_count)

                for j in range(len(self.count_cols)):
                    count = len(re.findall(self.count_cols[j][1], trans_phrase))
                    #reset column total on first iteration (if _build_list_store() was called in the past, then self.count_cols[j][2] may be > 0)
                    self.count_cols[j][2] = self.count_cols[j][2] + count if row_num else count
                    row.append(count)
                
                list_store.append(row)
                row_num += 1

        else:
            for i in range(len(segments)):
                for utter in segments[i].utters:
                    trans_phrase = utter.trans_phrase
                    if show_context:
                        trans_phrase = self._append_context(utter, utter, trans_phrase)
                    
                    whq_count = prev_store[row_num][5] if prev_store else 1
                    speaker_str = DBConstants.SPEAKER_CODES.get_option(utter.speaker.speaker_codeinfo.get_code()).desc if utter.speaker else '(Unknown)'
                    target_str = DBConstants.TRANS_CODES[1].get_option(utter.trans_codes[1]).desc if utter.trans_codes else '(Unknown)'
                    row = self._build_list_store_row(utter.id, utter.start, utter.end, trans_phrase, speaker_str, target_str, whq_count)

                    for j in range(len(self.count_cols)):
                        count = len(re.findall(self.count_cols[j][1], utter.trans_phrase.lower()))
                        #reset column total on first iteration (if _build_list_store() was called in the past, then self.count_cols[j][2] may be > 0)
                        self.count_cols[j][2] = self.count_cols[j][2] + count if row_num else count
                        row.append(count)

                    list_store.append(row)
                    row_num += 1

        return list_store
        
    def _build_treeview(self):
        list_store = self._build_list_store()
        treeview = gtk.TreeView(list_store)

        #create hidden id column
        col = gtk.TreeViewColumn('ID', gtk.CellRendererText(), text=0)
        col.set_visible(False)
        col.set_resizable(True)
        treeview.append_column(col)

        col_names = ['Time', 'Phrase', 'Speakers', 'Target Listeners']
        for i in range(len(col_names)):
            col = gtk.TreeViewColumn(col_names[i], gtk.CellRendererText(), text=(i + 1))
            col.set_resizable(True)
            treeview.append_column(col)
        
        spin_renderer = gtk.CellRendererSpin()
        adj = gtk.Adjustment(value=1, lower=0, upper=100, page_incr=5, step_incr=1, page_size=0)
        spin_renderer.set_property('adjustment', adj)
        spin_renderer.set_property('editable', True)
        spin_renderer.connect('edited', self._update_row, treeview)
        col = gtk.TreeViewColumn('WHQ Count', spin_renderer, text=(len(col_names) + 1))
        col.set_resizable(True)
        treeview.append_column(col)

        for i in range( len(self.count_cols) ):
            col = gtk.TreeViewColumn(self.count_cols[i][0], gtk.CellRendererText(), text=(len(col_names) + 2 + i))
            col.set_resizable(True)
            treeview.append_column(col)

        treeview.connect('key-press-event', self._keypress_callback, treeview)

        return treeview

    def _keypress_callback(self, widget, event, treeview):
        if gdk.keyval_name(event.keyval).lower() == 'tab':
            (model, paths) = treeview.get_selection().get_selected_rows()
            total_rows = model.iter_n_children(None)
            if paths and paths[0][0] + 1 < total_rows:
                treeview.set_cursor(paths[0][0] + 1, focus_column=treeview.get_column(3), start_editing=True)

    def _update_row(self, widget, path, value, treeview):
        #we must retrieve the model each time this method is called (rather than just passing in a reference to it), since the model is re-defined ever time a count column is added or removed
        model = treeview.get_model()
        old_val = int(model[path][5])
        new_val = int(value)
        self.num_whq += (new_val - old_val)
        
        model[path][5] = new_val
        self._update_statusbar()
    
    def _export_results(self, treeview):
        dialog = gtk.FileChooserDialog(title='Save',
                                            action=gtk.FileChooserAction.SAVE,
                                            buttons=(gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL, gtk.STOCK_SAVE, gtk.ResponseType.OK))
        dialog.set_default_response(gtk.ResponseType.OK)
        dialog.add_filter(UIUtils.CSV_FILE_FILTER)
        dialog.add_filter(UIUtils.ALL_FILE_FILTER)

        #splice in the 'open immediately checkbox'
        content_area = dialog.get_content_area()
        open_now_checkbox = gtk.CheckButton('Open Immediately')
        open_now_checkbox.set_active(True)
        align = gtk.Alignment(xalign=1.0, yalign=1.0)
        align.add(open_now_checkbox)
        content_area.pack_end(align, False, False, 0)
        open_now_checkbox.show()
        align.show()
        
        response = dialog.run()
        if response == gtk.ResponseType.CANCEL:
            dialog.destroy()
        elif response == gtk.ResponseType.OK:
            filename = dialog.get_filename()
            open_now = open_now_checkbox.get_active()
            dialog.destroy()

            count_col_headers, count_col_vals, count_col_totals = zip(*self.count_cols) if self.count_cols else [[]] * 3
            exporter = FreqExporter(filename, self.trs_parser.filename)

            exporter.write_header_row(count_col_headers)
            list_store = treeview.get_model()
            tree_it = list_store.get_iter_first()
            while tree_it:
                #we must remove newline chars, otherwise Excel thinks it's the end of a row (even when it's quoted...)
                phrase = list_store.get_value(tree_it, 2).replace('\n', ' ').replace('\r', '')
                time_str = list_store.get_value(tree_it, 1)
                speakers_str = list_store.get_value(tree_it, 3) or '(Unknown)'
                targets_str = list_store.get_value(tree_it, 4) or '(Unknown)'
                num_utters = int(list_store.get_value(tree_it, 5))
                i = 6
                count_col_vals = []
                while i < list_store.get_n_columns():
                    count_col_vals.append( int(list_store.get_value(tree_it, i)) )
                    i += 1
                
                exporter.write_count_row(time_str, phrase, speakers_str, targets_str, num_utters, count_col_vals)

                tree_it = list_store.iter_next(tree_it)

            exporter.finish(self.num_whq, count_col_totals)

            if open_now:
                subprocess.Popen(['%s' % DBConstants.SETTINGS.SPREADSHEET_PATH, filename])
            else:
                result_dialog = gtk.MessageDialog(buttons=gtk.ButtonType.OK, message_format='Results exported successfully.')
                result_dialog.run()
                result_dialog.destroy()            
