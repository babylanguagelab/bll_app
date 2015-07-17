from gi.repository import Gtk as gtk
import logging

from utils.ui_utils import UIUtils
from db.csv_database import CSVDatabase

class FilterWindow():
    class Filter():
        OPS = ('', '=', '!=', '<', '<=', '>=', '>', 'contains')
        CONJUNCTS = ('', 'AND', 'OR')
        
        def __init__(self, col_index, op, val, conjunct):
            self.col_index = col_index
            self.op = op
            self.val = val
            self.conjunct = conjunct

    def __init__(self, existing_filters, col_headers, callback):
        self.existing_filters = existing_filters
        self.col_headers = col_headers
        self.callback = callback
        
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Filters')
        self.window.connect('destroy', lambda w: self._cancel())
        self.window.set_border_width(10)
        self.window.set_default_size(400, 100)
        self.logger = logging.getLogger(__name__)

        self.add_button = self._build_add_button()
        
        self.filters_vbox = gtk.VBox()

        for cur_filter in self.existing_filters:
            self._add_filter(cur_filter)

        if not self.existing_filters:
            self._add_filter()
            
        button_box = self._build_button_box()

        win_vbox = gtk.VBox()
        win_vbox.pack_start(self.add_button, False, False, 0)
        win_vbox.pack_start(self.filters_vbox, False, False, 0)
        win_vbox.pack_end(button_box, False, False, 0)

        self.window.add(win_vbox)
        win_vbox.show_all()
        self.add_button.hide()
        self.window.show()

    def _build_add_button(self):
        add_button = gtk.Button(stock=gtk.STOCK_ADD)
        add_button.connect('clicked', lambda w: self._add_filter())

        return add_button
        
    def _build_button_box(self):
        bbox = gtk.HButtonBox()
        bbox.set_layout(gtk.ButtonBoxStyle.EDGE)

        cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel_button.connect('clicked', lambda w: self._cancel())

        ok_button = gtk.Button(stock=gtk.STOCK_OK)
        ok_button.connect('clicked', lambda w: self._ok())

        bbox.pack_start(cancel_button, False, False, 0)
        bbox.pack_end(ok_button, False, False, 0)

        return bbox

    def _cancel(self):
        self.window.destroy()
        self.callback(None)

    def _ok(self):
        filters = self._get_filters()
        if self._validate_filters(filters):
            self.window.destroy()
            self.callback(filters)
        else:
            UIUtils.show_message_dialog('Please make sure that all combo boxes are set, with the exception of the last "conjunction" box.')

    def _add_filter(self, existing_filter=None):
        hbox = gtk.HBox(spacing=5)

        #remove non-visible columns from the column dropdown's list
        filtered_headers = ['']
        filtered_vals = [-1]
        for i in range(len(self.col_headers)):
            if self.col_headers[i] != '' and self.col_headers[i] != '# segments' and self.col_headers[i] != 'id':
                filtered_headers.append(self.col_headers[i])
                filtered_vals.append(i - 1)
        
        col_combo = UIUtils.build_simple_combo(
            (str, int),
            filtered_headers,
            filtered_vals,
            )
        col_combo.set_active(self._find_combo_index(col_combo, existing_filter.col_index, 1) if existing_filter else 0)

        ops_combo = UIUtils.build_simple_combo(
            (str, int),
            FilterWindow.Filter.OPS,
            range(len(FilterWindow.Filter.OPS)),
            )
        ops_combo.set_active(self._find_combo_index(ops_combo, existing_filter.op, 0) if existing_filter else 0)

        val_entry = gtk.Entry()
        val_entry.set_width_chars(10)
        val_entry.connect('activate', lambda w: self._ok()) #connect the 'enter' button press (make it equivalent to clicking ok)
        val_entry.set_text(existing_filter.val if existing_filter else '')

        conjuncts_combo = UIUtils.build_simple_combo(
            (str, int),
            FilterWindow.Filter.CONJUNCTS,
            range(len(FilterWindow.Filter.CONJUNCTS)),
            )
        conjuncts_combo.set_active(self._find_combo_index(conjuncts_combo, existing_filter.conjunct, 0) if existing_filter else 0)
        conjuncts_combo.connect('changed', lambda w: self._conjunct_changed(w, hbox))

        del_button = gtk.Button(stock=gtk.STOCK_REMOVE)
        del_button.connect('clicked', lambda w: self._remove_filter(hbox))
        
        hbox.pack_start(col_combo, False, False, 0)
        hbox.pack_start(ops_combo, False, False, 0)
        hbox.pack_start(val_entry, False, False, 0)
        hbox.pack_start(conjuncts_combo, False, False, 0)
        hbox.pack_start(del_button, False, False, 0)

        self.filters_vbox.pack_start(hbox, False, False, 0)
        
        self.add_button.hide()
        hbox.show_all()

    def _find_combo_index(self, combo, val, model_search_col):
        model = combo.get_model()
        it = model.get_iter_first()
        path = -1
        while path < 0 and it:
            if model.get_value(it, model_search_col) == val:
                path = model.get_path(it)[0]
            it = model.iter_next(it)

        return path

    def _conjunct_changed(self, combo, hbox):
        if hbox == self.filters_vbox.get_children()[-1] and combo.get_active() > 0:
            self._add_filter()
        
    def _remove_filter(self, sel_hbox):
        self.filters_vbox.remove(sel_hbox)
        if len(self.filters_vbox.get_children()) == 0:
            self.add_button.show()

    def _get_filters(self):
        filters = []
        
        for cur_row in self.filters_vbox.get_children():
            col_combo, ops_combo, val_entry, conjuncts_combo, del_button = cur_row.get_children()

            col_ui_index = col_combo.get_active()
            col_index = None
            if col_ui_index > 0:
                model = col_combo.get_model()
                it = model.get_iter(col_ui_index)
                col_index = model.get_value(it, 1)

            op_ui_index = ops_combo.get_active()
            op = None
            if op_ui_index > 0:
                model = ops_combo.get_model()
                it = model.get_iter(op_ui_index)
                op = model.get_value(it, 0)
                
            val = val_entry.get_text()

            conjunct_ui_index = conjuncts_combo.get_active()
            conjunct = None
            if conjunct_ui_index > 0:
                model = conjuncts_combo.get_model()
                it = model.get_iter(conjunct_ui_index)
                conjunct = model.get_value(it, 0)

            filters.append(FilterWindow.Filter(col_index, op, val, conjunct))

        return filters

    def _validate_filters(self, filters):
        is_valid = True
        i = 0
        while is_valid and i < len(filters):
            is_valid = filters[i].col_index != None and filters[i].op != None

            if i < len(filters) - 1:
                is_valid = is_valid and filters[i].conjunct != None

            i += 1

            if len(filters) == 1:
                is_valid = is_valid and filters[0].conjunct == None

        return is_valid

    @staticmethod
    def get_sql_where_cond(filters):
        where_cond = ''
        params = []

        for cur_filter in filters:
            if cur_filter.op == 'contains':
                where_cond += '%s%d LIKE ?' % (CSVDatabase.COL_PREFIX, cur_filter.col_index + 1) #add one to compensate for id column in database (which is col0)
                params.append('%%%s%%' % (cur_filter.val))

            else:
                where_cond += '%s%d %s ?' % (CSVDatabase.COL_PREFIX, cur_filter.col_index + 1, cur_filter.op) #add one to compensate for id column in database (which is col0)
                params.append(str(cur_filter.val))
            
            if cur_filter.conjunct:
                where_cond += ' %s ' % (cur_filter.conjunct)

        return where_cond, params

    @staticmethod
    def get_filters_desc(filters, col_headers):
        desc = ''
        if filters:
            for cur_filter in filters:
                desc += '%s %s "%s"%s' % (col_headers[cur_filter.col_index + 1],
                                      cur_filter.op,
                                      cur_filter.val,
                                      (' %s ' % (cur_filter.conjunct)) if cur_filter.conjunct is not None else '',
                                      )

        return desc
