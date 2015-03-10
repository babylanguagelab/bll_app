from gi.repository import Gtk as gtk

from utils.ui_utils import UIUtils
from utils.filters_frame import FiltersFrame
from db.bll_database import DBConstants
from data_structs.output_calcs import *
from data_structs.output import Output

class OutputWindow():
    def __init__(self, action_callback, edit_output=None):
        self.action_callback = action_callback
        self.edit_output = edit_output
        
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('%s Output' % ('Edit' if self.edit_output else 'Create'))
        self.window.set_border_width(10)
        self.window.set_default_size(400, 400)

        vbox = gtk.VBox()
        #table = gtk.Table(10, 10)
        grid = gtk.Grid()

        props_frame = self._build_props_frame()
        filters_frame = FiltersFrame(existing_filters=edit_output.filters if edit_output else [])
        filters_frame.set_vexpand(True)
        options_frame = OptionsFrame(edit_output)
        options_frame.set_vexpand(True)

        vbox.pack_start(props_frame, False, False, 0)
        #table.attach(filters_frame, 0, 5, 2, 10, gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL)
        
        grid.attach(filters_frame, 0, 0, 1, 1)
        #table.attach(options_frame, 6, 10, 2, 10, gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL)
        
        grid.attach(options_frame, 1, 0, 1, 1)
        vbox.pack_start(grid, True, True, 0)
        
        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.ButtonBoxStyle.EDGE)

        cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel_button.connect('clicked', lambda w: self.window.destroy())
        button_box.pack_start(cancel_button, False, False, 0)

        ok_button = gtk.Button(stock=gtk.STOCK_OK)
        button_box.pack_start(ok_button, False, False, 0)
        ok_button.connect('clicked', lambda w: self._create_output(filters_frame, options_frame))
        vbox.pack_end(button_box, False, False, 0)

        self.window.add(vbox)
        self.window.show_all()

    def _build_props_frame(self):
        props_frame = gtk.Frame(label='Properties')
        #sub_table = gtk.Table(2, 2)
        sub_grid = gtk.Grid()
        name_label = gtk.Label('Name:')
        self.name_entry = gtk.Entry()
        self.name_entry.set_width_chars(50)
        if self.edit_output:
            self.name_entry.set_text(self.edit_output.name)

        #It appears that proper alignment can only be acheived with HBoxes here...
        name_label_hbox = gtk.HBox()
        name_label_hbox.pack_start(gtk.Alignment(xalign=1, yalign=0, xscale=0, yscale=0), True, True, 0)
        name_label_hbox.pack_start(name_label, False, False, 0)
        #sub_table.attach(name_label_hbox, 0, 1, 0, 1, gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL)
        sub_grid.attach(name_label_hbox, 0, 0, 1, 1)

        name_entry_hbox = gtk.HBox()
        name_entry_hbox.pack_start(self.name_entry, False, False, 0)
        #sub_table.attach(name_entry_hbox, 1, 2, 0, 1, gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL)
        sub_grid.attach(name_entry_hbox, 1, 0, 1, 1)

        desc_label = gtk.Label('Description:')
        self.desc_entry = gtk.Entry()
        self.desc_entry.set_width_chars(50)
        if self.edit_output:
            self.desc_entry.set_text(self.edit_output.desc)

        desc_label_hbox = gtk.HBox()
        desc_label_hbox.pack_start(gtk.Alignment(xalign=1, yalign=0, xscale=0, yscale=0), True, True, 0)
        desc_label_hbox.pack_start(desc_label, False, False, 0)
        #sub_table.attach(desc_label_hbox, 0, 1, 1, 2, gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL)
        sub_grid.attach(desc_label_hbox, 0, 1, 1, 1)

        desc_entry_hbox = gtk.HBox()
        desc_entry_hbox.pack_start(self.desc_entry, False, False, 0)
        #sub_table.attach(desc_entry_hbox, 1, 2, 1, 2, gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL, ypadding=3) #ypadding adds some space between bottom of entry and bottom of frame border
        sub_grid.attach(desc_entry_hbox, 1, 1, 1, 1)

        props_frame.add(sub_grid)

        return props_frame

    def _validate(self):
        return self.name_entry.get_text() != '' #only name field is required, desc field is optional

    def _create_output(self, filters_frame, options_frame):
        if options_frame.validate() and self._validate():
            name = self.name_entry.get_text()
            desc = self.desc_entry.get_text()
            filters = filters_frame.get_filters()
            calc = options_frame.get_output_calc()
            chained = options_frame.get_seg_linkage()

            output = Output(name, desc, filters, calc, chained)

            self.action_callback(output)
            self.window.destroy()
        
        else:
            UIUtils.show_empty_form_dialog()

class OptionsFrame(gtk.Frame):
    def __init__(self, edit_output=None, label='Options'):
        super(OptionsFrame, self).__init__(label=label)
        self.edit_output = edit_output
        
        #The 'seg_linkage' entry is a 2-tuple of the form:
        #(lambda: True if valid else False, lambda: True if linked else False)
        #The 'calc_type' entry is a 2-tuple of the form:
        #(lambda: True if valid else False, lambda: selected value from DBConstants.COMBO_OPTIONS)
        #Entries in the 'calc_inputs' dictionary should be arrays of the form:
        #[(lambda: True if valid else False, lambda: returns value of corresponding OutputCalc constructer arg), ...]
        self.inputs_dict = {'seg_linkage': None,
                            'calc_type': None,
                            'calc_inputs': [],
                            }
        self._build()

    def get_output_calc(self):
        options = DBConstants.COMBO_OPTIONS[DBConstants.COMBO_GROUPS.OUTPUT_CALC_TYPES]
        calc_type = self.inputs_dict['calc_type'][1]()

        calc_cls = {options.COUNT: CountOutputCalc,
                    options.RATE: RateOutputCalc,
                    options.TIME_PERIOD: TimePeriodOutputCalc,
                    options.BREAKDOWN: BreakdownOutputCalc,
                    options.LIST: ListOutputCalc,
            }[calc_type]
        
        args = []
        for arg_tuple in self.inputs_dict['calc_inputs']:
            args.append(arg_tuple[1]())
            
        return calc_cls(*args)

    def get_seg_linkage(self):
        return self.inputs_dict['seg_linkage'][1]()

    def validate(self):
        is_valid = True
        inputs = [self.inputs_dict['seg_linkage'], self.inputs_dict['calc_type']] + self.inputs_dict['calc_inputs']
        
        i = 0
        while is_valid and i < len(inputs):
            is_valid = inputs[i][0]()
            i += 1

        return is_valid

    def _build(self):
        vbox = gtk.VBox(spacing=5)
        
        linkage_label = gtk.Label('Segment Linkage:')
        linkage_combo = UIUtils.build_options_combo(
            DBConstants.COMBO_GROUPS.FILTER_LINKAGE_OPTIONS,
            include_empty_option=False,
            active_index=(0 if self.edit_output and self.edit_output.chained else 1)
            )
        
        self.inputs_dict['seg_linkage'] = (lambda: linkage_combo.get_active() >= 0, #Note: there is no "empty" option in this combo (hence >=)
                                           lambda: linkage_combo.get_model()[linkage_combo.get_active()][1] == DBConstants.COMBO_OPTIONS[DBConstants.COMBO_GROUPS.FILTER_LINKAGE_OPTIONS].LINKED)
        linkage_hbox = gtk.HBox()
        linkage_hbox.pack_start(linkage_label, True, True, 0)
        linkage_hbox.pack_start(linkage_combo, True, True, 0)
        vbox.pack_start(linkage_hbox, False, False, 0)
        
        #table = gtk.Table(2, 2)
        grid = gtk.Grid()
        grid.set_row_spacing(5)

        cell_matrix = []
        n_rows = 2 #table.get_property('n-rows')
        n_cols = 2 #table.get_property('n-columns')
        for row in range(n_rows):
            for col in range(n_cols):
                cell_hbox = gtk.HBox()
                if col == 0:
                    cell_matrix.append([cell_hbox])
                else:
                    cell_matrix[row].append(cell_hbox)
                    
                #table.attach(cell_matrix[row][col], col, col + 1, row, row + 1, gtk.EXPAND, gtk.EXPAND)
                grid.attach(cell_matrix[row][col], col, row, 1, 1)

        output_type_label = gtk.Label('Output Type:')
        
        active_index = 0
        if self.edit_output:
            active_index = self._get_output_type_combo_index()
            
        output_type_combo = UIUtils.build_options_combo(DBConstants.COMBO_GROUPS.OUTPUT_CALC_TYPES, active_index)
        output_type_combo.connect( 'changed', lambda w: self._update_options_frame(cell_matrix, n_rows, n_cols, w.get_model().get(w.get_active_iter(), 1)[0]) )
        if self.edit_output:
            self._update_options_frame( cell_matrix, n_rows, n_cols, output_type_combo.get_model().get(output_type_combo.get_active_iter(), 1)[0] )
        
        self.inputs_dict['calc_type'] = (lambda: output_type_combo.get_active() > 0,
                                         lambda: output_type_combo.get_model()[output_type_combo.get_active()][1])
        output_type_hbox = gtk.HBox()
        output_type_hbox.pack_start(output_type_label, True, True, 0)
        output_type_hbox.pack_start(output_type_combo, True, True, 0)
        
        vbox.pack_start(output_type_hbox, False, False, 0)
        vbox.pack_start(gtk.HSeparator(), False, False, 0)
        vbox.pack_start(grid, True, True, 0)
        
        self.add(vbox)

    def _get_output_type_combo_index(self):
        active_index = 0
        
        calc_cls = self.edit_output.output_calc.__class__
        opts = DBConstants.COMBO_OPTIONS[DBConstants.COMBO_GROUPS.OUTPUT_CALC_TYPES]
        val = {CountOutputCalc: opts.COUNT,
               RateOutputCalc: opts.RATE,
               TimePeriodOutputCalc: opts.TIME_PERIOD,
               BreakdownOutputCalc: opts.BREAKDOWN,
               ListOutputCalc: opts.LIST,
               }[calc_cls]

        return self._get_combo_index(DBConstants.COMBO_GROUPS.OUTPUT_CALC_TYPES, val)

    def _get_combo_index(self, combo_group, combo_val):
        opts = DBConstants.COMBO_OPTIONS[combo_group]
        i = 0
        enum_vals = opts.get_ordered_vals()
        found_index = -1
        while found_index < 0 and i < len(enum_vals):
            if enum_vals[i] == combo_val:
                found_index = i
            i += 1

        if found_index > -1:
            active_index = found_index

        return active_index

    #sel_option_id is db_id from combo_options table
    def _update_options_frame(self, cell_matrix, n_rows, n_cols, sel_option_id):
        for row in range(n_rows):
            for col in range(n_cols):
                children = cell_matrix[row][col].get_children()
                for child in children:
                    cell_matrix[row][col].remove(child)
        self.inputs_dict['calc_inputs'] = [] #clear any previous inputs
        options = DBConstants.COMBO_OPTIONS[DBConstants.COMBO_GROUPS.OUTPUT_CALC_TYPES]
        
        if sel_option_id == options.COUNT:
            regex_label = gtk.Label('Search:')
            regex_entry = gtk.Entry()
            regex_entry.set_width_chars(30)
            if self.edit_output:
                regex_entry.set_text(self.edit_output.output_calc.search_term)

            regex_helper = UIUtils.build_regex_helper_combo(regex_entry)
            hbox = gtk.HBox()
            hbox.pack_start(regex_entry, False, False, 0)
            hbox.pack_start(regex_helper, False, False, 0)
                
            cell_matrix[0][0].pack_start(regex_label, False, False, 0)
            cell_matrix[0][1].pack_start(hbox, False, False, 0)
            cell_matrix[0][0].show_all()
            cell_matrix[0][1].show_all()

            combo_label = gtk.Label('Calc Type:')
            active_index = 0
            if self.edit_output:
                active_index = self._get_combo_index(DBConstants.COMBO_GROUPS.COUNT_OUTPUT_CALC_TYPES, self.edit_output.output_calc.count_type)

            combo = UIUtils.build_options_combo(DBConstants.COMBO_GROUPS.COUNT_OUTPUT_CALC_TYPES, active_index)
            cell_matrix[1][0].pack_start(combo_label, False, False, 0)
            cell_matrix[1][1].pack_start(combo, False, False, 0)
            cell_matrix[1][0].show_all()
            cell_matrix[1][1].show_all()

            self.inputs_dict['calc_inputs'].append( (lambda: True, #if no text, assume user is searching for '*'
                                                     lambda: regex_entry.get_text()) )
            self.inputs_dict['calc_inputs'].append( (lambda: combo.get_active() > 0,
                                                     lambda: combo.get_model()[combo.get_active()][1]) )
        
        elif sel_option_id == options.RATE:
            regex_label = gtk.Label('Search:')
            regex_entry = gtk.Entry()
            regex_entry.set_width_chars(30)
            if self.edit_output:
                regex_entry.set_text(self.edit_output.output_calc.search_term)

            regex_helper = UIUtils.build_regex_helper_combo(regex_entry)
            hbox = gtk.HBox()
            hbox.pack_start(regex_entry, False, False, 0)
            hbox.pack_start(regex_helper, False, False, 0)
                
            cell_matrix[0][0].pack_start(regex_label, False, False, 0)
            cell_matrix[0][1].pack_start(hbox, False, False, 0)
            cell_matrix[0][0].show_all()
            cell_matrix[0][1].show_all()
            
            combo_label = gtk.Label('Calc Type:')
            active_index = 0
            if self.edit_output:
                active_index = self._get_combo_index(DBConstants.COMBO_GROUPS.RATE_OUTPUT_CALC_TYPES, self.edit_output.output_calc.rate_type)

            combo = UIUtils.build_options_combo(DBConstants.COMBO_GROUPS.RATE_OUTPUT_CALC_TYPES, active_index)
            cell_matrix[1][0].pack_start(combo_label, False, False, 0)
            cell_matrix[1][1].pack_start(combo, False, False, 0)
            cell_matrix[1][0].show_all()
            cell_matrix[1][1].show_all()

            self.inputs_dict['calc_inputs'].append( (lambda: True,
                                                     lambda: regex_entry.get_text()) )
            self.inputs_dict['calc_inputs'].append( (lambda: combo.get_active() > 0,
                                                     lambda: combo.get_model()[combo.get_active()][1]) )
        
        elif sel_option_id == options.TIME_PERIOD:
            regex_label = gtk.Label('Search:')
            regex_entry = gtk.Entry()
            regex_entry.set_width_chars(30)
            if self.edit_output:
                regex_entry.set_text(self.edit_output.output_calc.search_term)

            regex_helper = UIUtils.build_regex_helper_combo(regex_entry)
            hbox = gtk.HBox()
            hbox.pack_start(regex_entry, False, False, 0)
            hbox.pack_start(regex_helper, False, False, 0)
            
            cell_matrix[0][0].pack_start(regex_label, False, False, 0)
            cell_matrix[0][1].pack_start(hbox, False, False, 0)
            cell_matrix[0][0].show_all()
            cell_matrix[0][1].show_all()

            self.inputs_dict['calc_inputs'].append( (lambda: True,
                                                     lambda: regex_entry.get_text()) )
        
        elif sel_option_id == options.BREAKDOWN:
            row_combo_label = gtk.Label('Row Criteria:')
            active_row_index = 0
            if self.edit_output:
                active_row_index = self._get_combo_index(DBConstants.COMBO_GROUPS.BREAKDOWN_OUTPUT_CALC_CRITERIA, self.edit_output.output_calc.row_criteria)

            row_combo = UIUtils.build_options_combo(DBConstants.COMBO_GROUPS.BREAKDOWN_OUTPUT_CALC_CRITERIA, active_row_index)
            cell_matrix[0][0].pack_start(row_combo_label, False, False, 0)
            cell_matrix[0][1].pack_start(row_combo, False, False, 0)
            cell_matrix[0][0].show_all()
            cell_matrix[0][1].show_all()

            col_combo_label = gtk.Label('Column Criteria:')
            active_col_index = 0
            if self.edit_output:
                active_col_index = self._get_combo_index(DBConstants.COMBO_GROUPS.BREAKDOWN_OUTPUT_CALC_CRITERIA, self.edit_output.output_calc.col_criteria)
            col_combo = UIUtils.build_options_combo(DBConstants.COMBO_GROUPS.BREAKDOWN_OUTPUT_CALC_CRITERIA, active_col_index)
            cell_matrix[1][0].pack_start(col_combo_label, False, False, 0)
            cell_matrix[1][1].pack_start(col_combo, False, False, 0)
            cell_matrix[1][0].show_all()
            cell_matrix[1][1].show_all()

            self.inputs_dict['calc_inputs'].append( (lambda: row_combo.get_active() > 0,
                                                     lambda: row_combo.get_model()[row_combo.get_active()][1]) )
            self.inputs_dict['calc_inputs'].append( (lambda: col_combo.get_active() > 0,
                                                     lambda: col_combo.get_model()[col_combo.get_active()][1]) )

        elif sel_option_id == options.LIST:
            regex_label = gtk.Label('Search:')
            regex_entry = gtk.Entry()
            regex_entry.set_width_chars(30)
            if self.edit_output:
                regex_entry.set_text(self.edit_output.output_calc.search_term)

            regex_helper = UIUtils.build_regex_helper_combo(regex_entry)
            hbox = gtk.HBox()
            hbox.pack_start(regex_entry, False, False, 0)
            hbox.pack_start(regex_helper, False, False, 0)
            
            cell_matrix[0][0].pack_start(regex_label, False, False, 0)
            cell_matrix[0][1].pack_start(hbox, False, False, 0)
            cell_matrix[0][0].show_all()
            cell_matrix[0][1].show_all()

            grouping_cat_label = gtk.Label("Grouping Category:")
            active_index = 0
            if self.edit_output:
                active_index = self._get_combo_index(DBConstants.COMBO_GROUPS.LIST_OUTPUT_CALC_CATS, self.edit_output.output_calc.cat)
            grouping_cat_combo = UIUtils.build_options_combo(DBConstants.COMBO_GROUPS.LIST_OUTPUT_CALC_CATS, active_index)
            cell_matrix[1][0].pack_start(grouping_cat_label, False, False, 0)
            cell_matrix[1][1].pack_start(grouping_cat_combo, False, False, 0)
            cell_matrix[1][0].show_all()
            cell_matrix[1][1].show_all()

            self.inputs_dict['calc_inputs'].append( (lambda: True,
                                                     lambda: regex_entry.get_text()) )
            self.inputs_dict['calc_inputs'].append( (lambda: grouping_cat_combo.get_active() > 0,
                                                     lambda: grouping_cat_combo.get_model()[grouping_cat_combo.get_active()][1]) )

        #Make sure we don't try to restore state on subsequent calls to this method
        #Note: outdated outputs will be removed from the database by create_config_window.py
        self.edit_output = None
