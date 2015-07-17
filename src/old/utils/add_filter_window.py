## @package utils.add_filter_window

from gi.repository import Gtk as gtk

from db.bll_database import DBConstants
from utils.ui_utils import UIUtils
from data_structs.seg_filters import *

## This class provides a window that allows the user to create various types of segment filters.
# When the window is closed (via the ok button), a callback function is invoked and passed a
# SegFilter object corresponding to the newly created filter.
# Here is a screenshot of what this class looks like in the UI:
# <img src="../images/add_filter_window.png">
class AddFilterWindow(object):
    ## Constructor
    # @param self
    # @param callback (function pointer) this callback function will be called with a SegFilter object when the window is closed via the OK button. If the window is closed in some other way (cancel button, x button),
    # the callback is not invoked. The callback function must accept a single parameter - a SegFilter object.
    def __init__(self, callback):
        self.callback = callback
        
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Add Filter')
        self.window.set_border_width(10)
        self.window.set_default_size(300, 350)

        self.inputs_dict = {'filter_type': None,
                            'negate': None,
                            'type_inputs': [],
                            }
        self._build()

    ## An internal method to construct all the UI widgets, hook up their signals, and place them in the window.
    # @param self
    def _build(self):
        #table = gtk.Table(3, 2)
        #table.set_row_spacings(5)
        #table.set_col_spacings(2)
        grid = gtk.Grid()
        grid.set_row_spacing(5)
        grid.set_column_spacing(2)
        
        type_label = gtk.Label('Filter Type:')
        #table.attach(type_label, 0, 1, 0, 1, gtk.EXPAND, gtk.EXPAND)
        grid.attach(type_label, 0, 0, 1, 1)

        filter_type_combo = UIUtils.build_options_combo(DBConstants.COMBO_GROUPS.SEG_FILTER_TYPES)
        #table.attach(filter_type_combo, 1, 2, 0, 1, gtk.EXPAND, gtk.EXPAND)
        grid.attach(filter_type_combo, 1, 0, 1, 1)
        self.inputs_dict['filter_type'] = (lambda: filter_type_combo.get_active() > 0,
                                           lambda: filter_type_combo.get_model()[filter_type_combo.get_active()][1])

        negate_label = gtk.Label('Negate:')
        #table.attach(negate_label, 0, 1, 1, 2, gtk.EXPAND, gtk.EXPAND)
        grid.attach(negate_label, 0, 1, 1, 1)

        negate_checkbox = gtk.CheckButton()
        negate_hbox = gtk.HBox()
        negate_hbox.pack_start(negate_checkbox, True, True, 0)
        negate_hbox.pack_start(gtk.Alignment(xalign=0, yalign=0), True, True, 0)
        #table.attach(negate_hbox, 1, 2, 1, 2, gtk.EXPAND|gtk.FILL, gtk.EXPAND|gtk.FILL)
        grid.attach(negate_hbox, 1, 1, 1, 1)
        self.inputs_dict['negate'] = (lambda: True,
                                      lambda: negate_checkbox.get_active())

        opts_vbox = gtk.VBox()
        #table.attach(opts_vbox, 0, 2, 2, 3)
        grid.attach(opts_vbox, 0, 2, 2, 1)
        filter_type_combo.connect('changed', lambda w: self._update_add_inputs(opts_vbox))

        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.ButtonBoxStyle.EDGE)
        cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel_button.connect('clicked', lambda w: self.window.destroy())
        button_box.pack_start(cancel_button, False, False, 0)
        
        ok_button = gtk.Button(stock=gtk.STOCK_OK)
        ok_button.connect('clicked', lambda w: self._create_filter())
        button_box.pack_start(ok_button, False, False, 0)
        
        vbox = gtk.VBox()
        vbox.pack_start(grid, False, False, 0)
        vbox.pack_end(button_box, False, False, 0)

        self.window.add(vbox)
        self.window.show_all()

    ## The window provides a combo box that allows the user to select the type of filter they want to create. When the selection in this combo box changes, this method is invoked. It updates the rest of the window
    # to show the necessary inputs for creating the selected type of filter.
    # @param self
    # @param vbox (gtk.VBox) a GTK vertical packing box to populate/purge of input widgets.
    def _update_add_inputs(self, vbox):
        #remove previous children
        map(lambda child: vbox.remove(child), vbox.get_children())
        self.inputs_dict['type_inputs'] = []

        #get new combo value
        sel_opt = self.inputs_dict['filter_type'][1]()
        options = DBConstants.COMBO_OPTIONS[DBConstants.COMBO_GROUPS.SEG_FILTER_TYPES]
        
        #add new children, based on new filter type
        if sel_opt == options.SPEAKER:
            treeview = self._build_codes_treeview(DBConstants.COMBO_GROUPS.SPEAKER_CODES, 'Select Speaker Codes:')
            vbox.pack_start(treeview, True, True, 0)
            self.inputs_dict['type_inputs'].append( (lambda: len(self._get_treeview_combo_opts(treeview, DBConstants.COMBO_GROUPS.SPEAKER_CODES)) > 0,
                                                     lambda: self._get_treeview_combo_opts(treeview, DBConstants.COMBO_GROUPS.SPEAKER_CODES)) )

        elif sel_opt == options.TIME:
            #table = gtk.Table(2, 2)
            grid = gtk.Grid()

            criteria_label = gtk.Label('Criteria:')
            #criteria_label.set_alignment(xalign=1.0, yalign=0.5)
            #table.attach(criteria_label, 0, 1, 0, 1)
            grid.attach(criteria_label, 0, 0, 1, 1)

            criteria_combo = UIUtils.build_options_combo(DBConstants.COMBO_GROUPS.SEG_FILTER_TIME)
            #table.attach(criteria_combo, 1, 2, 0, 1)
            grid.attach(criteria_combo, 1, 0, 1, 1)
            self.inputs_dict['type_inputs'].append( (lambda: criteria_combo.get_active() > 0,
                                                     lambda: criteria_combo.get_model()[criteria_combo.get_active()][1]) )
            
            time_label = gtk.Label('Time (h:m:s):')
            #time_label.set_alignment(xalign=1.0, yalign=0.5)
            #table.attach(time_label, 0, 1, 1, 2)
            grid.attach(time_label, 0, 1, 1, 1)
        
            time_inputs_box, hours_spinner, mins_spinner, secs_spinner = UIUtils.get_time_spinners()
            self.inputs_dict['type_inputs'].append(
                (lambda: hours_spinner.get_value_as_int() > 0 or mins_spinner.get_value_as_int() > 0 or secs_spinner.get_value_as_int() > 0,
                lambda: hours_spinner.get_value_as_int() * 60 * 60 + mins_spinner.get_value_as_int() * 60 + secs_spinner.get_value_as_int())
                )
            
            #table.attach(time_inputs_box, 1, 2, 1, 2)
            grid.attach(time_inputs_box, 1, 1, 1, 1)
            vbox.pack_start(grid, True, True, 0)

        elif sel_opt == options.SPEAKER_TYPE:
            treeview = self._build_codes_treeview(DBConstants.COMBO_GROUPS.SPEAKER_TYPES, 'Select Speaker Types:')
            vbox.pack_start(treeview, True, True, 0)
            self.inputs_dict['type_inputs'].append( (lambda: len(self._get_treeview_combo_opts(treeview, DBConstants.COMBO_GROUPS.SPEAKER_TYPES)) > 0,
                                                     lambda: self._get_treeview_combo_opts(treeview, DBConstants.COMBO_GROUPS.SPEAKER_TYPES)) )

        elif sel_opt == options.TARGET_LISTENER:
            treeview = self._build_codes_treeview(DBConstants.COMBO_GROUPS.TARGET_LISTENERS, 'Select Target Listeners:')
            vbox.pack_start(treeview, True, True, 0)
            self.inputs_dict['type_inputs'].append( (lambda: len(self._get_treeview_combo_opts(treeview, DBConstants.COMBO_GROUPS.TARGET_LISTENERS)) > 0,
                                                     lambda: self._get_treeview_combo_opts(treeview, DBConstants.COMBO_GROUPS.TARGET_LISTENERS)) )

        elif sel_opt == options.GRAMMATICALITY:
            treeview = self._build_codes_treeview(DBConstants.COMBO_GROUPS.GRAMMATICALITY, 'Select Grammaticality/Completeness options:')
            vbox.pack_start(treeview, True, True, 0)
            self.inputs_dict['type_inputs'].append( (lambda: len(self._get_treeview_combo_opts(treeview, DBConstants.COMBO_GROUPS.GRAMMATICALITY)) > 0,
                                                     lambda: self._get_treeview_combo_opts(treeview, DBConstants.COMBO_GROUPS.GRAMMATICALITY)) )

        elif sel_opt == options.UTTERANCE_TYPE:
            treeview = self._build_codes_treeview(DBConstants.COMBO_GROUPS.UTTERANCE_TYPES, 'Select Utterance Types:')
            vbox.pack_start(treeview, True, True, 0)
            self.inputs_dict['type_inputs'].append( (lambda: len(self._get_treeview_combo_opts(treeview, DBConstants.COMBO_GROUPS.UTTERANCE_TYPES)) > 0,
                                                     lambda: self._get_treeview_combo_opts(treeview, DBConstants.COMBO_GROUPS.UTTERANCE_TYPES)) )

        vbox.show_all()

    ## Retrieves the code names of the selected code options in a given treeview.
    # @param self
    # @param treeview (gtk.Treeview) the treeview whose rows we are examining
    # @param combo_group (int) value from the enum DBConstants.COMBO_GROUPS, indicating which option is selected in the filter types combo box (i.e. indicates what type of filter we're creating so that we can access the corresponding options).
    # @returns (list) a list of strings, one for each selected code option. For example, if we are working with a treeview that displays LENA speaker codes, we might get ['MAN', 'FAN']. In this case, the combo_group param (above) would have been set to
    # DBConstants.COMBO_GROUPS.SPEAKER_CODES.
    def _get_treeview_combo_opts(self, treeview, combo_group):
        code_names = []
        model, paths = treeview.get_selection().get_selected_rows()
        for cur_path in paths:
            #since the list is in the same order as the options in the enum, we can just use cur_path (the index of the selected item in the list) to access the corresponding combo_option. Note that we must add 1 to cur_path to adjust for the omission of the 'Empty' option (which is present in the enum, but not the list).
            combo_option = DBConstants.COMBO_OPTIONS[combo_group][cur_path[0] + 1]
            code_names.append(DBConstants.COMBOS[combo_group][combo_option].code_name) #note: this only works if the code name in combo_option corresponds exactly to the string code...

        return code_names

    ## Builds a treeview (a UI list) of code options for a given type of filter. The user can select multiple rows from this list at the same time.
    # @param self
    # @param combo_group (int) value from the enum DBConstants.COMBO_GROUPS, indicating which option is selected in the filter types combo box (i.e. indicates what type of filter we're creating so that we can access the corresponding options).
    # @param header_text (string) this text will be displayed at the very top of the treeview, as a title
    # @returns (gtk.Treeview) a Treeview object for the specified type of code
    def _build_codes_treeview(self, combo_group, header_text):
        list_store = UIUtils.build_options_liststore(combo_group, False)
        treeview = gtk.TreeView(list_store)
        treeview.get_selection().set_mode(gtk.SelectionMode.MULTIPLE)
        
        col = gtk.TreeViewColumn(header_text, gtk.CellRendererText(), text=0)
        treeview.append_column(col)
        col.set_sizing(gtk.TreeViewColumnSizing.AUTOSIZE)

        col = gtk.TreeViewColumn('ID', gtk.CellRendererText(), text=1)
        col.set_visible(False)
        col.set_sizing(gtk.TreeViewColumnSizing.AUTOSIZE)
        treeview.append_column(col)

        return treeview

    ## This method is called by _create_filter(). It makes sure all the inputs have been filled out (before the calling code creates the filter).
    # @param self
    # @returns (boolean) True if all inputs are filled out, False if one or more are empty
    def _validate(self):
        valid = self.inputs_dict['filter_type'][0]() and self.inputs_dict['negate'][0]()

        i = 0
        while valid and i < len(self.inputs_dict['type_inputs']):
            input_tuple = self.inputs_dict['type_inputs'][i]
            valid = input_tuple[0]()
            i += 1

        return valid

    ## This is called when the ok button is clicked. It creates a SegFilter object using the UI input values. The callback function is then invoked, passing the SegFilter object as its argument.
    # @param self
    def _create_filter(self):
        if self._validate():
            filter_type = self.inputs_dict['filter_type'][1]()
            options = DBConstants.COMBO_OPTIONS[DBConstants.COMBO_GROUPS.SEG_FILTER_TYPES]
            negate = self.inputs_dict['negate'][1]()
            
            args = []
            for arg_tuple in self.inputs_dict['type_inputs']:
                args.append(arg_tuple[1]())

            #instantiate the appropriate subclass based on the type of filter being created
            seg_filter = {
                options.SPEAKER: lambda: SpeakerCodeSegFilter(*args, negate=negate),
                options.TIME: lambda: TimeSegFilter(*args, inclusive=False, negate=negate), #my fault for breaking the pattern by defining the constructor in this way - unfortunately now it's too late to change it, as ordered args are stored in the database for some apps...
                options.SPEAKER_TYPE: lambda: SpeakerTypeSegFilter(*args, negate=negate),
                options.TARGET_LISTENER: lambda: TargetListenerSegFilter(*args, negate=negate),
                options.GRAMMATICALITY: lambda: GrammaticalitySegFilter(*args, negate=negate),
                options.UTTERANCE_TYPE: lambda: UtteranceTypeSegFilter(*args, negate=negate),
                options.OVERLAPPING_VOCALS: lambda: OverlappingVocalsSegFilter(*args, negate=negate),
            }[filter_type]()

            self.window.destroy()
            self.callback(seg_filter)
        
        else:
            UIUtils.show_empty_form_dialog()
