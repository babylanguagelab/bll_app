from gi.repository import Gtk as gtk
from gi.repository import Gdk as gdk
from gi.repository import GdkPixbuf
import csv
import logging
import traceback
import re
import os
import subprocess
from datetime import datetime

from db.bll_database import DBConstants
from db.csv_database import CSVDatabase
from utils.ui_utils import UIUtils
from utils.progress_dialog import ProgressDialog
from utils.backend_utils import BackendUtils
from utils.praat_interop import PraatInterop
from parsers.wav_parser import WavParser
from ui.data_viewer_app.filter_window import FilterWindow

class MainWindow():
    #if none of these match, then string is used
    DATA_TYPE_REGEXS = {
        float: r'^-?\d+(\.\d+)?$',
        bool: r'^True|False$',
        }

    START_COL_NAMES = ['Start Time', 'Wav.Begin']
    END_COL_NAMES = ['End Time', 'Wav.End']
    DUR_COL_NAMES = ['Duration', 'Segment_Duration']
    EL_TIME_COL_NAMES = ['Elapsed_Time']
    
    def __init__(self):
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Data Viewer')
        self.window.connect('destroy', lambda w: self._clean_up())
        self.window.set_border_width(10)
        self.window.set_default_size(800, 600)
        self.logger = logging.getLogger(__name__)
                                         
        self.csv_filename = UIUtils.open_file('Select csv file', filters=[UIUtils.CSV_FILE_FILTER, UIUtils.ALL_FILE_FILTER])
        self.window.set_title('%s - %s' % (self.window.get_title(), os.path.basename(self.csv_filename)))
        if not self.csv_filename:
            exit(0)

        self.wav_filename = self._get_wav_filename()
        self.wav_parser = None
        if self.wav_filename:
            self.wav_parser = WavParser(self.wav_filename)
        # if not self.wav_filename:
        #     exit(0)

        self.sound_col_fcns = None

        col_datatypes, col_headers = self._get_col_info()

        db = self._build_db(col_datatypes, col_headers)
        
        model = self._get_model(col_datatypes)
        treeview = self._get_treeview(model, col_headers, db)

        self.filters = []
        self.where_cond = None
        self.where_params = []
        self.sort_order = None
        self.sort_col = None
        self._populate_model(db, model)

        toolbar = self._build_toolbar(db, treeview, col_headers)
        scrolled_win = gtk.ScrolledWindow()
        scrolled_win.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
        scrolled_win.add(treeview)

        vbox = gtk.VBox()
        vbox.pack_start(toolbar, False, False, 0)
        vbox.pack_start(scrolled_win, True, True, 0)
        self.window.add(vbox)

        self.window.show_all()

    def _get_wav_filename(self):
        wav_filename = None
        
        #try to find a wav file with the same name as the csv file
        if self.csv_filename.lower().endswith('.csv'):
            default_filename = self.csv_filename[:-3] + 'wav'
            if os.path.exists(default_filename):
                wav_filename = default_filename

        #if the above didn't succeed, prompt the user for a filename
        if not wav_filename:
            wav_filename = UIUtils.open_file(title='Select wav file', filters=[UIUtils.WAV_FILE_FILTER, UIUtils.ALL_FILE_FILTER])

        return wav_filename

    def _get_csv_delim(self, csv_file):
        pos = csv_file.tell()
        delim = ',' if csv_file.next().find(',') > -1 else '\t'
        csv_file.seek(pos)

        return delim

    def _get_col_info(self):
        csv_file = open(self.csv_filename, 'rb')
        delim = self._get_csv_delim(csv_file)
        reader = csv.reader(csv_file, delimiter=delim)
        headers = reader.next()

        line = reader.next()
        datatypes = [int] #for hidden id column
        headers = ['id'] + headers
        for col in line:
            datatypes.append(self._get_datatype(col))

        csv_file.close()

        #append marked column, if not already present
        if datatypes and not datatypes[-1] == bool:
            datatypes.append(bool)
            headers.append('Marked')

        return datatypes, headers

    def _get_datatype(self, col_val):
        col_type = None
        i = 0
        regex_keys = MainWindow.DATA_TYPE_REGEXS.keys()
        while not col_type and i < len(regex_keys):
            if re.match(MainWindow.DATA_TYPE_REGEXS[regex_keys[i]], col_val):
                col_type = regex_keys[i]
            i += 1

        if not col_type:
            col_type = str

        return col_type

    def _get_model(self, col_datatypes):
        #tell the treeview that all columns are strings (even those that are really floats). This way, floats and numbers will appear exactly as they do in the input spreadsheet, and not using gtk's default precision (i.e. we don't have to do any number formatting / rounding). Since the db has the actual types for its columns, and it is in change of filtering and sorting (NOT the UI), this works out fine.
        #The exception is the last column ('marked'); it requires type bool for the checkboxes to function properly in the ui

        col_types = [int] + [str] * (len(col_datatypes) - 2) + [bool]

        return gtk.ListStore(*col_types)

    def _get_treeview(self, model, headers, db):
        treeview = gtk.TreeView(model)

        #force the row selection colours to stay the same even when the treeview is deselected (otherwise the selection is hard to see - and seeing this at all times is important in this app's use cases)
        treeview.modify_base(gtk.StateFlags.ACTIVE, gdk.Color.parse('#3399FF')[1])
        treeview.modify_text(gtk.StateFlags.ACTIVE, gdk.Color.parse('#FFFFFF')[1])

        col_index = 0
        col = gtk.TreeViewColumn(headers[0], gtk.CellRendererText(), text=col_index)
        col.set_visible(False)
        treeview.append_column(col)
        
        for col_index in range(1, len(headers) - 1):
            col = gtk.TreeViewColumn(headers[col_index], gtk.CellRendererText(), text=col_index)
            col.set_resizable(True)
            col.set_reorderable(True)
            col.set_visible(col.get_title() != '' and col.get_title() != '# segments')
            if col.get_visible():
                col.set_clickable(True)
                col.connect('clicked', self._toggle_sort_column, treeview, db, col_index)
            treeview.append_column(col)

        toggleRenderer = gtk.CellRendererToggle()
        toggleRenderer.connect('toggled', self._toggle_renderer_callback, model, col_index + 1, db)
        mark_col = gtk.TreeViewColumn(headers[col_index + 1], toggleRenderer, active=col_index + 1)
        mark_col.set_resizable(True)
        mark_col.set_reorderable(True)
        mark_col.set_clickable(True)
        mark_col.connect('clicked', self._toggle_sort_column, treeview, db, col_index + 1)
        mark_col.set_alignment(0.5) #position the title in the middle, since this column's wider than the others (since it's the last visible column)
        treeview.append_column(mark_col)
        
        return treeview

    def _toggle_sort_column(self, treeview_col, treeview, db, treeview_col_index):
        #clear any previous sort indicators on all columns except the one we care about
        for col in treeview.get_columns():
            if col != treeview_col:
                col.set_sort_indicator(False)

        if treeview_col.get_sort_indicator():
            sort_order = treeview_col.get_sort_order()

            if sort_order == gtk.SortType.ASCENDING:
                self.sort_order = CSVDatabase.ORDER_DIRS.DESC
                self.sort_col = treeview_col_index

                treeview_col.set_sort_order(gtk.SortType.DESCENDING)
                
            elif sort_order == gtk.SortType.DESCENDING:
                self.sort_order = None
                self.sort_col = None

                treeview_col.set_sort_indicator(False)
        else:
            self.sort_order = CSVDatabase.ORDER_DIRS.ASC
            self.sort_col = treeview_col_index

            treeview_col.set_sort_indicator(True)
            treeview_col.set_sort_order(gtk.SortType.ASCENDING)

        self._populate_model(db, treeview.get_model())

    #for debugging
    def _print_model(self, model):
        for row in model:
            s = ''
            for item in row:
                s += str(item) + ' '
            print s

    def _toggle_renderer_callback(self, renderer, path, model, col_index, db):
        if path is not None:
            model[path][col_index] = not model[path][col_index]
            db.csv_update_by_index([model.get_n_columns() - 1], where_cond='id=?', params=[int(model[path][col_index]), model[path][0]])

    def _build_db(self, col_datatypes, col_headers):
        csv_file = open(self.csv_filename, 'rb')
        delim = self._get_csv_delim(csv_file)
        lines = csv_file.readlines()
        reader = csv.reader(lines, delimiter=delim)
        header_row = reader.next() #skip headers row

        db = CSVDatabase(col_headers, col_datatypes)

        progress_dialog = ProgressDialog(title='Loading file', phases=['Loading file...'])
        progress_dialog.show()
        
        num_rows = len(lines) - 1 #subtract one for header

        done = False
        i = 0
        while i < num_rows and not done:
            row = reader.next()

            #if this file already contains counts at the end (has already been exported), skip those rows
            done = row and (row[0].startswith('File Stats') or row[0].startswith('Count of'))
            if not done:
                #if we have a marked column, use it - otherwise, append one
                if re.match(MainWindow.DATA_TYPE_REGEXS[bool], row[-1]):
                    row = row[:-1] + [int(bool(row[-1] == 'True'))]
                else:
                    row = row + [0]

                db.csv_insert([i + 1] + row)

            if (i % 10):
                progress_dialog.set_fraction(float(i + 1) / float(num_rows))

            i += 1

        progress_dialog.ensure_finish()
        csv_file.close()
        
        return db

    def _populate_model(self, db, model):
        model.clear()

        #order_by_indices = None
        #order_by_dirs = None
        order_by = None
        if self.sort_col != None and self.sort_order != None:
            order_by = '%s%s %s' % (CSVDatabase.COL_PREFIX, self.sort_col, self.sort_order)
            # order_by_indices = [self.sort_col]
            # order_by_dirs = [self.sort_order]

        #print self.where_cond, self.where_params, model.get_n_columns()
        rows = db.select(
            CSVDatabase.TABLE_NAME,
            [('%s%d' % (CSVDatabase.COL_PREFIX, i)) for i in range(model.get_n_columns())],
            where_cond=self.where_cond,
            params=self.where_params,
            order_by=order_by
        )
        
        #rows = db.csv_select_by_index(where_cond=self.where_cond, params=self.where_params, order_by_indices=order_by_indices, order_by_dirs=order_by_dirs)
        for cur_row in rows:
            cur_row = list(cur_row)
            
            for i in range(1, len(cur_row) - 1):
                cur_row[i] = str(cur_row[i])
            cur_row[-1] = bool(cur_row[-1])
            
            model.append(cur_row)

    def _filter_callback(self, filters, db, model, search_entry, col_headers):
        #Filters will be None if the user clicked cancel in the FilterWindow
        if filters != None:
            self.filters = filters
            where_cond, where_params = FilterWindow.get_sql_where_cond(self.filters)
            self.where_cond = where_cond
            self.where_params = where_params
            self._populate_model(db, model)

            desc = FilterWindow.get_filters_desc(filters, col_headers)
            search_entry.set_text(desc)

    def _update_filters(self, db, model, col_headers, search_entry):
        FilterWindow(self.filters, col_headers, lambda filters: self._filter_callback(filters, db, model, search_entry, col_headers))

    def _clean_up(self):
        if self.wav_parser:
            self.wav_parser.close()
            
        gtk.main_quit()

    def _build_toolbar(self, db, treeview, col_headers):
        toolbar = gtk.Toolbar()

        clear_img_path = UIUtils.get_icon_path(UIUtils.BUTTON_ICONS.CLEAR, UIUtils.BUTTON_ICON_SIZES.PX16)
        #clear_pixbuf = gtk.gdk.pixbuf_new_from_file(clear_img_path)
        clear_pixbuf = GdkPixbuf.Pixbuf.new_from_file(clear_img_path)

        search_entry = gtk.Entry()
        search_entry.set_sensitive(False)
        search_entry.set_text(FilterWindow.get_filters_desc(self.filters, col_headers))
        
        filter_button = UIUtils.create_button('Filters', UIUtils.BUTTON_ICONS.FILTER, UIUtils.BUTTON_ICON_SIZES.PX16)
        filter_button.connect('clicked', lambda w: self._update_filters(db, treeview.get_model(), col_headers, search_entry))

        play_button = UIUtils.create_button('Play', UIUtils.BUTTON_ICONS.PLAY, UIUtils.BUTTON_ICON_SIZES.PX16)
        play_button.connect('clicked', lambda w: self._play_selected_row(col_headers, treeview))
        praat_button = UIUtils.create_button('Praat', UIUtils.BUTTON_ICONS.PRAAT, UIUtils.BUTTON_ICON_SIZES.PX16)
        praat_button.connect('clicked', lambda w: self._open_in_praat(col_headers, treeview))

        export_button = UIUtils.create_button('Export', UIUtils.BUTTON_ICONS.EXPORT, UIUtils.BUTTON_ICON_SIZES.PX16)
        export_button.connect('clicked', lambda w: self._export(treeview, col_headers, db))

        context_label = gtk.Label('Context')
        context_adj = gtk.Adjustment(value=0, lower=0, upper=99, step_increment=1)
        self.context_spinner = gtk.SpinButton()
        self.context_spinner.set_adjustment(context_adj)
        self.context_spinner.set_numeric(True)

        spacer = gtk.SeparatorToolItem()
        spacer.set_draw(False) #don't draw a vertical line
        spacer.set_expand(True)

        filter_label = gtk.Label('Filter state:')

        for widget in [filter_label, search_entry, filter_button, praat_button, play_button, self.context_spinner, context_label]:
            tool_item = gtk.ToolItem()
            tool_item.add(widget)
            if widget == search_entry:
                tool_item.set_expand(True)
            toolbar.insert(tool_item, -1)
        
        toolbar.insert(spacer, -1)

        tool_item = gtk.ToolItem()
        tool_item.add(export_button)
        toolbar.insert(tool_item, -1)
        
        return toolbar

    #Takes a time string in one of two formats, and returns a float set to the absolute number of seconds it represents.
    #time_str must be either a string in any of the formats accepted by BackendUtils.time_str_to_float(), or a stringified float.
    # (e.g. ''00:00:3.45 or '3.45')
    def _get_abs_time(self, time_str):
        sec = None
        
        if ':' in time_str:
            sec = BackendUtils.time_str_to_float(time_str)
        else:
            sec = float(time_str)

        return sec

    def _get_sel_row_clip_info(self, col_headers, treeview):
        start = None
        end = None
        
        model, it = treeview.get_selection().get_selected()
        if it:
            #find start and end column indices (if not already found)
            if self.sound_col_fcns == None:
                start_index, end_index, dur_index, el_time_index = self._get_sound_col_indices(col_headers)

                if start_index > -1 and end_index > -1:
                    self.sound_col_fcns = (
                        lambda model, it: self._get_abs_time(model.get_value(it, start_index)),
                        lambda model, it: self._get_abs_time(model.get_value(it, end_index)),
                        )
                    
                elif dur_index > -1 and el_time_index > -1:
                    self.sound_col_fcns = (
                        lambda model, it: self._get_abs_time(float(model.get_value(it, el_time_index))),
                        lambda model, it: self._get_abs_time(float(model.get_value(it, el_time_index)) + float(model.get_value(it, dur_index))),
                        )

                else:
                    error_msg = 'The program was unable to derive the sound clip start and end times from the columns.\n'
                    error_msg += '\nColumn headers must include:\n'
                    error_msg += '-One start name: %s\n' % (' or '.join(['"%s"' % (name) for name in MainWindow.START_COL_NAMES]))
                    error_msg += '-One end name: %s\n' % (' or '.join(['"%s"' % (name) for name in MainWindow.END_COL_NAMES]))
                    error_msg += '\nOr alternatively:\n'
                    error_msg += '-One duration name: %s\n' % (' or '.join(['"%s"' % (name) for name in MainWindow.DUR_COL_NAMES]))
                    error_msg += '-One elapsed time name: %s\n' % (' or '.join(['"%s"' % (name) for name in MainWindow.EL_TIME_COL_NAMES]))

                    error_msg += '\nPlease make sure your input spreadsheet contains one of these pairs.'

                    UIUtils.show_message_dialog(error_msg)

            if self.sound_col_fcns != None and self.wav_filename:
                try:
                    start = float( self.sound_col_fcns[0](treeview.get_model(), it) )
                    end = float( self.sound_col_fcns[1](treeview.get_model(), it) )
                except ValueError as err:
                    UIUtils.show_message_dialog('The program was unable to determine start and end times for this row.')
                    start = None
                    end = None
                    print err

        else:
            UIUtils.show_no_sel_dialog()

        return start, end

    def _open_in_praat(self, headers, treeview):
        start, end = self._get_sel_row_clip_info(headers, treeview)
        
        if self.wav_filename and start != None and end != None:
            PraatInterop.open_praat()
            PraatInterop.send_commands(PraatInterop.get_open_clip_script(start, end, self.wav_filename))

    def _play_selected_row(self, col_headers, treeview):
        #this populates self.wav_parser and self.wav_filename, if the file exists
        start, end = self._get_sel_row_clip_info(col_headers, treeview)
        
        if self.wav_parser and start != None and end != None:
            start = max(0, start - self.context_spinner.get_value())
            end = min(self.wav_parser.get_sound_len(), end + self.context_spinner.get_value())
            self.wav_parser.play_clip(start, end)

        #return the focus to the currenly selected row in the treeview, so the user can immediately press the down arrow to move on to the next row
        treeview.grab_focus()

    def _find_col(self, header_dict, key_list):
        index = -1
        i = 0
        
        while index < 0 and i < len(key_list):
            if key_list[i] in header_dict:
                index = header_dict[ key_list[i] ]
            i += 1

        return index

    def _get_sound_col_indices(self, headers):
        header_dict = dict( zip(headers, range(len(headers))) )
        
        start = self._find_col(header_dict, MainWindow.START_COL_NAMES)
        end = self._find_col(header_dict, MainWindow.END_COL_NAMES)
        dur = self._find_col(header_dict, MainWindow.DUR_COL_NAMES)
        el_time = self._find_col(header_dict, MainWindow.EL_TIME_COL_NAMES)

        return (start, end, dur, el_time)

    def _export(self, treeview, col_headers, db):
        write_filename, open_now = UIUtils.save_file(filters=[UIUtils.CSV_FILE_FILTER, UIUtils.ALL_FILE_FILTER], open_now_opt=True)
        if write_filename: #if they didn't click cancel
            #lag_time_cutoff = float( UIUtils.show_entry_dialog(None, 'Lag time cutoff for counts: ', default_text='2', validate_regex=r'^-?\d+(\.\d+)?$', invalid_msg='Please enter a number.') )
            lag_time_cutoff = 2.0

	if write_filename and lag_time_cutoff != None: #if user did not click cancel (note: lag time cutoff could be 0)
            if not write_filename.lower().endswith('.csv'):
                write_filename += '.csv'

            try:
                csv_file = open(write_filename, 'wb')
                writer = csv.writer(csv_file, quoting=csv.QUOTE_ALL)

                cols = treeview.get_columns()
                visible_col_indices = filter(lambda i: cols[i].get_visible(), range(len(cols)))

                filtered_headers = [col_headers[i] for i in visible_col_indices]
                writer.writerow(filtered_headers)

                progress_dialog = ProgressDialog(title='Exporting to file', phases=['Exporting...'])
                progress_dialog.show()

                num_rows = len(treeview.get_model())
                row_index = 1 #this is awkward, but there is no way to pull all the rows out of the model in one shot, so we have to use a non-indexed for loop and manually track the index
                for row in treeview.get_model():
                    filtered_row = [row[i] for i in visible_col_indices]
                    writer.writerow(filtered_row)

                    progress_dialog.set_fraction(float(row_index) / float(num_rows))
                    row_index += 1

                # export_stats = self._get_export_stats(lag_time_cutoff, db, col_headers)
                # if export_stats:
                #     for row in export_stats:
                #         writer.writerow(row)

                progress_dialog.ensure_finish()
                csv_file.close()

                if open_now:
                    subprocess.Popen(['%s' % DBConstants.SETTINGS.SPREADSHEET_PATH, write_filename])
                else:
                    UIUtils.show_message_dialog('Data exported successfully.')
                    

                #UIUtils.show_message_dialog('Data export completed.')
            except Exception as err:
                UIUtils.show_message_dialog('Unable to export data - please make sure the destination file is not already open in another program.')
                raise err

    def _get_export_stats(self, lag_time_cutoff, db, col_headers):
        stats = []
        
        cols = {
            'Speaker': None,
            'Sentence Type': None,
            'Lag Time': None,
            'Marked': None,
            }
        
        for i in range(1, len(col_headers)):
            if col_headers[i] in cols:
                cols[col_headers[i]] = '%s%d' % (CSVDatabase.COL_PREFIX, i - 1)

        have_all_cols = reduce(lambda accum, key: cols[key] != None and accum, cols, True)

        if have_all_cols:
            #Count of Marked MQ -> B
            #"SELECT count(d1.id) FROM data d1, data d2 WHERE d1.id = d2.id - 1 AND d1.sentence_type='Q' AND d2.speaker='B' AND d1.marked=1 AND d1.lag_time < cutoff"
            where_cond = "d1.id = d2.id - 1 AND d1.%s = 'M' AND d1.%s = 'Q' AND d2.%s = 'B' AND d1.%s = 1 AND d1.%s <= ?" % (cols['Speaker'], cols['Sentence Type'], cols['Speaker'], cols['Marked'], cols['Lag Time'])
            rows = db.select(
                '%s d1, %s d2' % (CSVDatabase.TABLE_NAME, CSVDatabase.TABLE_NAME),
                ['count(d1.id)'],
                where_cond=where_cond,
                params=[lag_time_cutoff],
                )
            if rows:
                stats.append( ['Count of "Marked MQ -> B": %d' % (int(rows[0][0]))] )

            #Avg lag time on mother utterance for (MQ or MD) -> B
            where_cond = "d1.id = d2.id - 1 AND d1.%s= 'M' AND (d1.%s = 'Q' OR d1.%s = 'D') AND d2.%s = 'B' AND d1.%s <= ?" % (cols['Speaker'], cols['Sentence Type'], cols['Sentence Type'], cols['Speaker'], cols['Lag Time'])
            rows = db.select(
                '%s d1, %s d2' % (CSVDatabase.TABLE_NAME, CSVDatabase.TABLE_NAME),
                ['avg(d1.%s)' % (cols['Lag Time'])],
                where_cond=where_cond,
                params=[lag_time_cutoff],
                )
            if rows:
                val = str(None)
                if len(rows[0]) and rows[0][0] != None:
                    val = '%0.3f' % (float(rows[0][0]))
                stats.append( ['Avg Lag Time for "(MQ or MD) -> B": %s' % (val)] )

            #Avg of lag time (first in pair) on mother utterance for MQ -> MQ
            where_cond = "d1.id = d2.id - 1 AND d1.%s= 'M' AND d1.%s = 'Q' AND d2.%s = 'M' AND d2.%s = 'Q' AND d1.%s <= ?" % (cols['Speaker'], cols['Sentence Type'], cols['Speaker'], cols['Sentence Type'], cols['Lag Time'])
            rows = db.select(
                '%s d1, %s d2' % (CSVDatabase.TABLE_NAME, CSVDatabase.TABLE_NAME),
                ['avg(d1.%s)' % (cols['Lag Time'])],
                where_cond=where_cond,
                params=[lag_time_cutoff],
                )
            if rows:
                val = str(None)
                if len(rows[0]) and rows[0][0] != None:
                    val = '%0.3f' % (float(rows[0][0]))
                stats.append( ['Avg Lag Time for "MQ -> MQ": %s' % (val)] )

            #Avg of lag time (first in pair) on mother utterance for MD -> MD
            where_cond = "d1.id = d2.id - 1 AND d1.%s= 'M' AND d1.%s = 'D' AND d2.%s = 'M' AND d2.%s = 'D' AND d1.%s <= ?" % (cols['Speaker'], cols['Sentence Type'], cols['Speaker'], cols['Sentence Type'], cols['Lag Time'])
            rows = db.select(
                '%s d1, %s d2' % (CSVDatabase.TABLE_NAME, CSVDatabase.TABLE_NAME),
                ['avg(d1.%s)' % (cols['Lag Time'])],
                where_cond=where_cond,
                params=[lag_time_cutoff],
                )
            if rows:
                val = str(None)
                if len(rows[0]) and rows[0][0] != None:
                    val = '%0.3f' % (float(rows[0][0]))
                stats.append( ['Avg Lag Time for "MD -> MD": %s' % (val)] )

            #Avg of lag time (first in pair) on baby utterance for B -> (MQ or MD)
            where_cond = "d1.id = d2.id - 1 AND d1.%s = 'B' AND d2.%s = 'M' AND d1.%s <= ?" % (cols['Speaker'], cols['Speaker'], cols['Lag Time'])
            rows = db.select(
                '%s d1, %s d2' % (CSVDatabase.TABLE_NAME, CSVDatabase.TABLE_NAME),
                ['avg(d1.%s)' % (cols['Lag Time'])],
                where_cond=where_cond,
                params=[lag_time_cutoff],
                )
            if rows:
                val = str(None)
                if len(rows[0]) and rows[0][0] != None:
                    val = '%0.3f' % (float(rows[0][0]))
                stats.append( ['Avg Lag Time for "B -> (MQ or MD)": %s' % (val)] )

            if stats:
                stats.insert(0, ['File Stats (lag time <= %0.3f)' % (lag_time_cutoff)])

        return stats
            
