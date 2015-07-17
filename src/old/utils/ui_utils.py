## @package utils.ui_utils

from gi.repository import Gtk as gtk, Pango
from gi.repository import GObject as gobject
from gi.repository import GdkPixbuf as pixbuf

import os
import re

from datetime import datetime
from dateutil import tz
from db.bll_database import DBConstants, BLLDatabase
from utils.backend_utils import BackendUtils
from utils.enum import Enum

## A collection of static methods and constants for common UI-related tasks.
# This class should never be instantiated.
class UIUtils(object):
    #stores the last directory accessed by the user from a filechooser dialog (see the show_file_dialog() and show_file_dialog_with_checks() methods)
    last_filechooser_location = None

    #These static members store gtk.FileFilter constants created by the _get_constants method() of the ui_utils module. They are populated when this file is processed by the Python iterpreter.
    WAV_FILE_FILTER = None
    TRS_FILE_FILTER = None 
    ITS_FILE_FILTER = None 
    ALL_FILE_FILTER = None
    CSV_FILE_FILTER = None
    TRS_CSV_FILE_FILTER = None

    #this is a date-time format string (of the type accepted by the Python datetime.strptime() method - see Python docs) that corresponds to the format in which timestamps come out of the database.
    DB_DT_OUTPUT_FMT = '%Y-%m-%d %H:%M:%S'
    #this is a date-time format string that corresponds to the format in which timestamps should be shown in the UI. Timestamps coming out of the database are converted to this format by get_db_timestamp_str().
    DT_DISPLAY_FMT = '%b %d, %Y %I:%M %p'

    #The UI contains lots of buttons that perform common actions. This is a lookup structure (an Enum) that maps actions to (the file path to) descriptive icons. You can use it to create buttons with icons on them.
    #See the create_button() method for more info. The '%s' placeholder will be filled with the name of the directory corresponding to the desired size of the icon - this is done in create_button().
    BUTTON_ICONS = Enum.from_dict({
         'CREATE': 'icons/open_icon_library-standard/icons/png/%s/actions/document-new-8.png',
         'OPEN': 'icons/open_icon_library-standard/icons/png/%s/actions/document-open-8.png',
         'ADD': 'icons/open_icon_library-standard/icons/png/%s/actions/list-add-5.png',
         'EDIT': 'icons/open_icon_library-standard/icons/png/%s/actions/edit.png',
         'REMOVE': 'icons/open_icon_library-standard/icons/png/%s/actions/list-remove-5.png',
         'DELETE': 'icons/open_icon_library-standard/icons/png/%s/actions/edit-delete-3.png',
         'RUN': 'icons/open_icon_library-standard/icons/png/%s/actions/system-run-2.png',
         'CLOSE': 'icons/open_icon_library-standard/icons/png/%s/actions/application-exit-4.png',
         'EXIT': 'icons/open_icon_library-standard/icons/png/%s/actions/application-exit.png',
         'EXPAND': 'icons/open_icon_library-standard/icons/png/%s/actions/edit-add-3.png',
         'COLLAPSE': 'icons/open_icon_library-standard/icons/png/%s/actions/edit-remove-2.png',
         'REFRESH': 'icons/open_icon_library-standard/icons/png/%s/actions/view-refresh-6.png',
         'PLAY': 'icons/open_icon_library-standard/icons/png/%s/apps/exaile-2.png',
         'FLAG': 'icons/open_icon_library-standard/icons/png/%s/actions/flag.png',
         'EXPORT': 'icons/open_icon_library-standard/icons/png/%s/actions/document-export.png',
         'SPLIT': 'icons/open_icon_library-standard/icons/png/%s/actions/edit-copy-9.png',
         'MERGE': 'icons/open_icon_library-standard/icons/png/%s/actions/edit-text-frame-update.png',
         'CLEAR': 'icons/open_icon_library-standard/icons/png/%s/actions/edit-clear-2.png',
         'FILTER': 'icons/open_icon_library-standard/icons/png/%s/actions/filter.png',
         'PRAAT': 'icons/open_icon_library-standard/icons/png/%s/apps/praat.png',
         'SAVE': 'icons/open_icon_library-standard/icons/png/%s/actions/document-save-as-6.png',
         'UPDATE': 'icons/open_icon_library-standard/icons/png/%s/apps/system-software-update-4.png',
         'VOLUME_OFF': 'icons/open_icon_library-standard/icons/png/%s/status/volume-0.png',
        'VOLUME_ON': 'icons/open_icon_library-standard/icons/png/%s/status/audio-volume-high-5.png',
         })

    #This enum allows you to select the size of the image you want for your button (see create_button()). The values correspond to the names of subdirectories in the 'bll_app/icons/png/' directory.
    #The selected value is interpolated into the value from the BUTTON_ICONS enum (above) within the create_button() method.
    BUTTON_ICON_SIZES = Enum.from_dict({
            'PX8': '8x8',
            'PX16': '16x16',
            'PX22': '22x22',
            'PX24': '24x24',
            'PX32': '32x32',
            'PX48': '48x48',
            'PX64': '64x64',
            'PX128': '128x128',
            })

    ## Sets some common GTK properties that all of the apps use. This only needs to be called once at appliation startup.
    # @param app_icon_filename (string) path to an image file. This icons will be used as the default application icon (appears in the top left-hand corner of all windows)
    @staticmethod
    def setup_gtk(app_icon_filename):
        #allow images to appear on buttons
        gtk.Settings.get_default().set_long_property('gtk-button-images', True, 'main')
        #set default program icon
        gtk.Window.set_default_icon_list([pixbuf.Pixbuf.new_from_file(app_icon_filename)])

    ## Sets the font size for a given widget
    # @param widget (Gtk Container) the widget whose font size you'd like to set
    # @param pt_size (int, possibly float too?) the font size (pt)
    # @param bold (boolean=False) Set to True to make font bold
    @staticmethod
    def set_font_size(widget, pt_size, bold=False):
        font = widget.get_style_context().get_font(gtk.StateFlags.NORMAL)
        font.set_size(pt_size * Pango.SCALE)
        if bold:
            font.set_weight(Pango.Weight.BOLD)
        widget.override_font(font)

    ## Constructs the full path to an icon, given a value from the BUTTON_ICONS enum, and a value from the BUTTON_ICON_SIZES enum.
    # @param img_path (string) this must be a value from the BUTTON_ICONS enum
    # @param icon_size_dir (string=BUTTON_ICON_SIZES.PX32) this must be a value from the BUTTON_ICON_SIZES enum. Size defaults to 32x32 pixels.
    # @returns (string) the full path to the icon file
    @staticmethod
    def get_icon_path(img_path, icon_size_dir=BUTTON_ICON_SIZES.PX32):
        return img_path % (icon_size_dir)

    ## Creates a gtk.Button with an icon on it. You can create predefined types of buttons (corresponding to common actions) of any given size by passing in parameters from this class' button enums.
    # Note: in order for this to work, you must first tell gtk to allow images on button - this is done in the setup_gtk() method, so you should call that first.
    # @param label (string) the text to display on the button.
    # @param img_path (string) a value from the BUTTON_ICONS enum (indicates the button action)
    # @param icon_size_dir (string=BUTTON_ICON_SIZES.PX32) a value from the BUTTON_ICON_SIZES enum, indicating the size of the icon that will be placed on the button. Default is 32x32 pixels.
    # @returns (gtk.Button) a gtk.Button object with the specified text and image.
    @staticmethod
    def create_button(label, img_path, icon_size_dir=BUTTON_ICON_SIZES.PX32): #use BUTTON_ICONS enum for 2nd param, BUTTON_ICON_SIZES enum for 3rd param
        button = gtk.Button(label)
        img = gtk.Image()
        full_path = UIUtils.get_icon_path(img_path, icon_size_dir)
        img.set_from_file(full_path)
        button.set_image(img)

        return button

    ## Displays a popup confirmation dialog with yes/no buttons. This method will block until one of the buttons is clicked, at which point it will return a boolean value (indicating which button was clicked) and the dialog will auto-destruct.
    # @param msg (string) the confirmation message to display (should be a yes/no question so the buttons make sense)
    # @returns (boolean) True if "yes" was clicked, False otherwise.
    @staticmethod
    def show_confirm_dialog(msg):
        dialog = gtk.MessageDialog(buttons=gtk.ButtonsType.YES_NO,
                                   type=gtk.MessageType.INFO,
                                   message_format=msg)
        response = dialog.run()
        dialog.destroy()

        return response == gtk.ResponseType.YES

    ## Displays a popup dialog (with an ok button) that tells the user to select a row (presumably in some type of UI list).
    # This method blocks until the user clicks ok.
    # @param alt_msg (string=None) alternate text to display in place of the default. The default is 'Please select a row.'
    @staticmethod
    def show_no_sel_dialog(alt_msg=None):
        default_msg = 'Please select a row.'
        UIUtils.show_message_dialog(default_msg or alt_msg)

    ## Displays a popup dialog (with an ok button) that tells the user to make sure all options in a form have been filled out.
    # This method blocks until the user clicks ok.
    # @param alt_msg (string=None) alternate text to display in place of the default. The default is 'Please make sure that all options have been filled out.'
    @staticmethod
    def show_empty_form_dialog(alt_msg=None):
        default_msg = 'Please make sure that all options have been filled out.'
        UIUtils.show_message_dialog(default_msg or alt_msg)

    ## Displays a popup dialog (with an ok button) that presents a textual message.
    # This method blocks until the user clicks ok.
    # @param message (string) the text to display in the dialog box.
    # @param dialog_type (int) one of the gtk message type constants (see gtk docs for the MessageDialog class), indicating the type of icon to display in the dialog. This icon indicates whether the
    # dialog is an info/question/warning/error message. Possible values are gtk.MESSAGE_INFO, gtk.MESSAGE_WARNING, gtk.MESSAGE_QUESTION, or gtk.MESSAGE_ERROR.
    @staticmethod
    def show_message_dialog(message, dialog_type=gtk.MessageType.INFO):
        dialog = gtk.MessageDialog(buttons=gtk.ButtonsType.OK,
                                   message_format=message,
                                   type=dialog_type)
        
        #this call blocks until the OK button is clicked
        dialog.run()
        dialog.destroy()

    ## Creates a set of gtk.SpinButton inputs to allow the user to input a time in the format hh:mm:ss.
    # These entries are packing into a horizontal gtk.HBox container, which is fitted with a label.
    # Here's what the container looks like when it's displayed in the UI:
    # <img src="../images/time_spinners.png">
    # @param label (string=None) an optional label to pack at the left side of the container
    # @param hours (int=0) value to default the hours spinbutton to
    # @param mins (int=0) value to default the minutes spinbutton to
    # @param secs (int=0) value to default the seconds spinbutton to
    # @returns (tuple) returns a tuple of 4 items: (hbox_container, hours_spinbutton, mins_spinbutton, secs_spinbutton). The spinbuttons are already packed into the hbox container. They are returned individually as well just for convenience
    # (so the caller can easily hook up signals without having to extract them from the container first).
    @staticmethod
    def get_time_spinners(label=None, hours=0, mins=0, secs=0):
        entry_box = gtk.HBox()
        entry_box.pack_start(gtk.Alignment(xalign=0.25, yalign=0), False, False, 0)

        if label:
            entry_box.pack_start(label, False, False, 0)
        
        hours_adj = gtk.Adjustment(value=0, lower=0, upper=1000, step_incr=1, page_incr=5) #note: upper is a required param - set it to something that won't be exceeded
        hours_spinner = gtk.SpinButton()
        hours_spinner.set_adjustment(hours_adj)
        hours_spinner.set_value(hours)
        entry_box.pack_start(hours_spinner, False, False, 0)
        entry_box.pack_start(gtk.Label(':'), False, False, 0)

        mins_adj = gtk.Adjustment(value=0, lower=0, upper=59, step_incr=1, page_incr=5)
        mins_spinner = gtk.SpinButton()
        mins_spinner.set_adjustment(mins_adj)
        mins_spinner.set_value(mins)
        entry_box.pack_start(mins_spinner, False, False, 0)
        entry_box.pack_start(gtk.Label(':'), False, False, 0)

        secs_adj = gtk.Adjustment(value=0, lower=0, upper=59, step_incr=1, page_incr=5)
        secs_spinner = gtk.SpinButton()
        secs_spinner.set_adjustment(secs_adj)
        secs_spinner.set_value(secs)
        entry_box.pack_start(secs_spinner, False, False, 0)
        entry_box.pack_start(gtk.Alignment(xalign=0.25, yalign=0), False, False, 0)

        return entry_box, hours_spinner, mins_spinner, secs_spinner

    ## Returns a string containing the current date and time.
    # @returns (string) the current timestamp, formatted according to the UIUtils.DT_DISPLAY_FMT pattern.
    @staticmethod
    def get_cur_timestamp_str():
        return datetime.now().strftime(UIUtils.DT_DISPLAY_FMT)

    ## Accepts a string representing a datetime that was retrieved from the database, and converts it into a format suitable for display in the UI.
    # @param timestamp (string) a timestamp string (retrieved from the DB) in the format UIUtils.DB_DT_OUTPUT_FMT
    # @returns (string) a timestamp string in the format UIUtils.DT_DISPLAY_FMT
    @staticmethod
    def get_db_timestamp_str(timestamp):
        return datetime.strptime(timestamp, UIUtils.DB_DT_OUTPUT_FMT).strftime(UIUtils.DT_DISPLAY_FMT)

    @staticmethod
    def utc_to_local_str(utc_timestamp):
        from_zone = tz.tzutc()
        to_zone = tz.tzlocal()

        # utc = datetime.utcnow()
        utc = datetime.strptime(utc_timestamp, UIUtils.DB_DT_OUTPUT_FMT)

        # Tell the datetime object that it's in UTC time zone since 
        # datetime objects are 'naive' by default
        utc = utc.replace(tzinfo=from_zone)

        # Convert time zone
        local = utc.astimezone(to_zone)

        return local.strftime(UIUtils.DT_DISPLAY_FMT)

    ## Constructs a gtk.FileFilter object for a set of file extensions.
    # @param title (string) the title for this filer. This title is displayed in the dropdown combobox of file types in filechooser dialogs
    # @param patterns (list) a list of strings, where each is a shell-expandible file extension (like '*.wav' or '*.trs')
    # @return (gtk.FileFilter) a gtk.FileFilter object that can be passed to a filechooser dialog
    @staticmethod
    def build_file_filter(title, patterns):
        file_filter = gtk.FileFilter()
        file_filter.set_name(title)
        map(file_filter.add_pattern, patterns)

        return file_filter

    ## Builds a simple combo box. Each entry has a title and a value.
    # The title is displayed, the value is hidden to the user. Here's what it looks like:
    # <img src="../images/simple_combo.png">
    # By default, the first option is selected. Note: You can make this a row with a label that is an empty string (and value None) if you want it to appear as though nothing is selected by default (as in the above image).
    # @param types (tuple) a 2-tuple of type functions (e.g. int, float, str). The
    # first element is the type of the label, and the second is the type of the value.
    # In most cases, the type of the label should be string, so you should pass the the str function as the first element.
    # Alternatively, you can also use the type constants from the gobject module (gobject.TYPE_STRING, gobject.TYPE_FLOAT, etc.).
    # @param labels (list) a list of strings - these will be the options made available for the user to select.
    # @param vals (list) a list of anything - the length must be equal to the length of the labels param. These are the values that
    # the labels will be given in the combobox model (assigned in the same order as the elements in the labels list appear).
    # These values can be retrieved when you query the combobox selection state.
    # @returns (gtk.ComboBox) a gtk.ComboBox object that can be used in the UI
    @staticmethod
    def build_simple_combo(types, labels, vals):
        model = gtk.ListStore(*types)
        map(model.append, zip(labels, vals))

        combobox = gtk.ComboBox(model=model)
        renderer = gtk.CellRendererText()
        combobox.pack_start(renderer, True, False, 0)
        combobox.add_attribute(renderer, 'text', 0)
        combobox.set_active(0)

        return combobox

    ## Builds a simple gtk.ListStore. This is the data store backing for a combobox or treeview.
    # @param labels (list) list of strings that will be displayed in the list of treeview
    # @param vals (list) list of objects, must be same length as labels list. These values are assigned to the rows/options in the widget, and
    # can be retrieved when the widget's selection state is queried.
    # @param val_type (function pointer) this is function pointer corresponding to a type (like str, int, float, etc.) or it is a type constant from the gobject module (eg. gobject.TYPE_STRING, gobject.TYPE_FLOAT, etc.).
    # It indicates the type of the elements in the vals array.
    # @returns (gtk.ListStore) a liststore object for use in the creation of a combobox or treeview (or potentially other types of widgets).
    @staticmethod
    def build_simple_liststore(labels, vals, val_type):
        list_store = gtk.ListStore(gobject.TYPE_STRING,
                                   val_type)

        for i in range(len(labels)):
            list_store.append([labels[i], vals[i]])

        return list_store

    ## Builds a treeview (a grid with selectable rows) with a single column. The user may select multiple rows at once.
    # The treeview has a hidden 'ID' column appended to it - you can use this to track the indices of the selected rows (or you can use the vals parameter).
    # See the gtk docs for more info on treeviews. Here is what the treeview looks like:
    # <img src="../images/multiselect_treeview.png">
    # @param labels (list) list of strings. These are the values to display in the rows (one element per row).
    # @param vals (list) list of anything. These values will be assigned to the rows in the same order as the labels list (therefore it must be of the same length). You can retrieve the values of selected rows when
    # querying the treeview widget's selection state.
    # @param val_type (function pointer) this is function pointer corresponding to a type (like str, int, float, etc.) or it is a type constant from the gobject module (eg. gobject.TYPE_STRING, gobject.TYPE_FLOAT, etc.).
    # It indicates the type of the elements in the vals array.
    # @param header_text (string) text to display at the top of the single column.
    # @returns (gtk.TreeView) a gtk.TreeView object that's set up and ready to embed in the UI
    @staticmethod
    def build_multiselect_treeview(labels, vals, val_type, header_text):
        list_store = UIUtils.build_simple_liststore(labels, vals, val_type)
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

    ## Builds a gtk.ListStore that contains a group of common combo options stored in the  DBConstants.COMBO_OPTIONS enum (these ultimately come from the database).
    # For example, you could create a liststore of all LENA speaker codes, then display them in a treeview - this is what was done to create the screenshot below:
    # <img src="../images/multiselect_treeview.png">
    # You could just as easily use this liststore to create a combobox, or something else.
    # @param group_id (int) a value from the DBConstants.COMBO_GROUPS enum, indicating which group of options to insert into the liststore. Combo options are grouped according to their type.
    # For example, passing a group_id of DBConstants.COMBO_GROUPS.SPEAKER_CODES would create a liststore like the one used in the screenshot shown above.
    # @param include_empty_option (boolean=True) if True, an option with an empty string label will be pre-pended to the liststore. This can be used as a "nothing-selected" option.
    # @returns (gtk.ListStore) a liststore object that contains all of the options from the specified group. This object can be used as a data-store backing for other widgets.
    @staticmethod
    def build_options_liststore(group_id, include_empty_option=True):
        list_store = gtk.ListStore(gobject.TYPE_STRING,
                                   gobject.TYPE_INT)

        group_keys_enum = DBConstants.COMBO_OPTIONS[group_id]
        for i in range(int(not include_empty_option), len(group_keys_enum)):
            group_option_key = group_keys_enum[i]
            option = DBConstants.COMBOS[group_id][group_option_key]
            if not option.hidden:
                list_store.append([option.disp_desc, option.db_id])

        return list_store

    ## Computes the minimum number of pixels (width) needed to show a treeview column with the specified title text.
    # This is an approximation that was emperically determined, and uses magic numbers. It is not guarenteed to work, and
    # should probably be removed. But you can try it if you feel frustrated.
    # @param col_name (string) the text that will be displayed in the column header
    # @returns (int) an approximation of the number of pixel you will need to applocate for the width of the treeview column, in order for the whole col_name header string to be displayed.
    @staticmethod
    def calc_treeview_col_min_width(col_name):
        return 90 + (len(col_name) / 15) * 50

    ## Builds a gtk.ComboBox widget that contains a group of common combo options stored in the  DBConstants.COMBO_OPTIONS enum (these ultimately come from the database).
    # For example, you could create a combobox that allows you to select one of the LENA speaker codes.
    # @param group_id (int) a value from the DBConstants.COMBO_GROUPS enum, indicating which group of options to insert into the liststore.
    # @param active_index (int=0) the row index of the entry to auto-select. If include_empty_option is True, and this is zero, then the empty entry will be selected.
    # @param include_empty_option (boolean=True) if True, an option with an empty string label will be pre-pended to the list of options. This can be used as a "nothing-selected" option.
    # @returns (gtk.ComboBox) a combobox widget containing all of the options for the specified group.
    @staticmethod
    def build_options_combo(group_id, active_index=0, include_empty_option=True):
        list_store = UIUtils.build_options_liststore(group_id, include_empty_option)

        combobox = gtk.ComboBox(model=list_store)
        renderer = gtk.CellRendererText()
        combobox.pack_start(renderer, True, False, 0)
        combobox.add_attribute(renderer, 'text', 0)
        
        combobox.set_active(active_index)

        return combobox

    ## Builds a gtk.ComboBox containing options for "common regexs" (COMBO_GROUPS.COMMON_REGEXS).
    # When the selected option changes, a text entry box is populated with the regex string.
    # (This is just a wrapper around the build_options_combo() method for common regexs, to add the ability to connect
    # the 'changed' signal.)
    # @param entry (gtk.Entry) a text entry box that will be populated with a regular expression string when the selection changes
    # @returns (gtk.ComboBox) a combobox with the 'changed' signal set up
    @staticmethod
    def build_regex_helper_combo(entry):
        combo = UIUtils.build_options_combo(DBConstants.COMBO_GROUPS.COMMON_REGEXS)
        combo.connect('changed', UIUtils._fill_entry, entry)

        return combo

    ## This is an internal helper method for build_regex_helper_combo(). It populates a text entry with a regex string corresponding to the
    # selected option in the combobox. It is called every time the combobox selection changes.
    # @param combo (gtk.ComboBox) this is a combobox created with the options for the DBConstants.COMBO_GROUPS.COMMON_REGEXS group
    # @param entry (gtk.Entry) a text entry to populate with the regex string for the selected combobox option
    @staticmethod
    def _fill_entry(combo, entry):
        opt_id = combo.get_model()[combo.get_active()][1]
        db = BLLDatabase()
        # Ideally, the regex info should come out of an enum in the DBConstants class (such as DBConstants.COMMON_REGEXS).
        # However, we only have the combobox option id of the selected option, and this isn't enough to figure out which enum value we need.
        # To solve this problem, I've reverted to a database query here, but this should really be fixed in the future...we need something other
        # than the option id to identify the selected combo option.
        rows = db.select('common_regexs', 'regex'.split(), 'combo_option_id=?', [opt_id])
        if rows and rows[0]:
            regex = rows[0][0]
            highlight_start = regex.find('\<')
            highlight_end = regex.find('\>')

            entry.set_text(regex.replace('\<', '<').replace('\>', '>'))

            entry.grab_focus()
            if highlight_start > -1 and highlight_end > -1:
                entry.select_region(highlight_start, highlight_end)

            db.close()

    ## This method opens an "open file" dialog, and populates a text entry widget with the resulting path.
    # It's useful to hook up to a "browse" button in the UI. This method blocks until the user clicks ok.
    # @param title (string) text to display in the titlebar of the "open file" dialog
    # @param entry (gtk.Entry) an entry widget to populate with the path name after the user clicks ok in the "open file" dialog
    # @param filters (list=[]) list of gtk.FileFilter objects. A dropdown list of file types displaying these is shown in the "open file" dialog.
    # You can use the constants in this class to build a list (UIUtils.ALL_FILE_FILTER, UIUtils.WAV_FILE_FILTER, UIUtils.TRS_FILE_FILTER, etc.)
    # @param auto_fill_entry (gtk.Entry=None) an optional gtk entry. It is possible to automatically locate another file with the same name as the one the user selects, but a different file extension.
    # This is useful, for example, when the user is locating a trs file, and you want to automatically locate the corresponding wav file. If this param is not None, an automatic search will be done
    # for the corresponding wav file and, if it is found, the entry will be populated with the path. The search encompasses the current directory (the one the user's selected file is in) and the parent directory.
    # @param auto_fill_file_extension (string='wav') an optional file extension string, used together with auto_fill_entry. This dictates the type of file extension that the search described in
    # the auto_fill_entry parameter documentation.
    @staticmethod
    def browse_file(title, entry, filters=[], auto_fill_entry=None, auto_fill_file_extension='wav'):
        filename = UIUtils.open_file(title, filters, save_last_location=True)
        if filename:
            entry.set_text(filename)
            search_name = filename[:-3] + auto_fill_file_extension
            #try to automatically find a corresponding wav file in the current or parent directories (in that order)
            #if one is found, and auto_fill_entry is not None, then the gtk.Entry pointed to be auto_fill_entry will be populated with the path of the found wav file
            try:
                if auto_fill_entry and auto_fill_entry.get_text() == '':
                    if os.path.exists(search_name):
                        auto_fill_entry.set_text(search_name)
                    else:
                        parent_dir = os.path.abspath( os.path.dirname(filename) + os.path.sep + os.path.pardir) #find absolute name of directory 'filename_dir/../'
                        search_name = parent_dir + os.path.sep + os.path.basename(search_name) #search for file in parent directory
                        if os.path.exists(search_name):
                            auto_fill_entry.set_text(search_name)
            except Exception as e:
                print 'Unable to find matching %s file: %s' % (auto_fill_file_extension, e)

    ## This method opens an "open folder" dialog, and populates a text entry widget with the resulting path.
    # It's useful to hook up to a "browse" button in the UI. This method blocks until the user clicks ok.
    # @param title (string) text to display in the titlebar of the "open folder" dialog
    # @param entry (gtk.Entry) an entry widget to populate with the path name after the user clicks ok in the "open folder" dialog
    # @param filters (list=[]) list of gtk.FileFilter objects. This specifies the types of files (via their extensions) that will be visible in the "open folder" dialog.
    # Since the dialog doesn't let you select files (only folders), any visible files will appear "greyed out", and this param really just affects with the user can see, not what they can do.
    # In general, it is probably most useful to either leave this empty or set it to UIUtils.ALL_FILE_FILTER.
    @staticmethod
    def browse_folder(title, entry, filters=[]):
        foldername = UIUtils.open_folder(title, filters, save_last_location=True)
        if foldername:
            entry.set_text(foldername)

    ## Shows an "open file" dialog, returning a user-selected filename (if any). This method blocks until the user clicks ok.
    # @param title (string='Open File') string to display in the dialog box titlebar
    # @param filters (list=[]) list of gtk.FileFilter objects for the dialog to use. A combobox is displayed listing these filters (generally file extensions). Only files matching the pattern will be viewable in the browse pane.
    # If no filters are specified, all files will be visible.
    # @param save_last_location (boolean=False) if True, the directory containing the selected file will be saved (to UIUtils.last_filechoose_location), and the next "open" or "save" dialog will use it as the current directory
    # @param cur_location (string=None) if this is non-None, it specifies the path to the folder to use as the current directory - this is the directory initially displayed when the dialog pops up
    # @returns (string) the path to the user-selected file. If the user did not select a file, and instead clicked the cancel button or closed the dialog, this method will return None.
    @staticmethod
    def open_file(title='Open File', filters=[], save_last_location=False, cur_location=None):
        if not filters:
            filters = [UIUtils.ALL_FILE_FILTER]
        filename, open_now = UIUtils.show_file_dialog(title, filters, gtk.FileChooserAction.OPEN, gtk.STOCK_OPEN, save_last_location=save_last_location, cur_location=cur_location)

        return filename

    ## Shows an "open folder" dialog, returning a user-selected foldername (if any). This method blocks until the user clicks ok.
    # @param title (string='Open Folder') string to display in the dialog box titlebar
    # @param filters (list=[]) list of gtk.FileFilter objects. This specifies the types of files (via their extensions) that will be visible in the "open folder" dialog.
    # Since the dialog doesn't let you select files (only folders), any visible files will appear "greyed out", and this param really just affects with the user can see, not what they can do.
    # In general, it is probably most useful to either leave this empty or set it to UIUtils.ALL_FILE_FILTER.
    # @param save_last_location (boolean=False) if True, the directory containing the selected file will be saved (to UIUtils.last_filechoose_location), and the next "open" dialog will use it as the current directory
    # @param cur_location (string=None) if this is non-None, it specifies the path to the folder to use as the current directory - this is the directory initially displayed when the dialog pops up
    # @returns (string) the path to the user-selected folder. If the user did not select a folder, and instead clicked the cancel button or closed the dialog, this method will return None.
    @staticmethod
    def open_folder(title='Select Folder', filters=[], save_last_location=False, cur_location=None):
        if not filters:
            filters = [UIUtils.ALL_FILE_FILTER]
        foldername, open_now = UIUtils.show_file_dialog(title, filters, gtk.FileChooserAction.SELECT_FOLDER, gtk.STOCK_OPEN, save_last_location=save_last_location, cur_location=cur_location)

        return foldername

    ## Shows a "Save file" dialog, returning the path to a user-selected location. This method blocks until the user clicks ok.
    # @param title (string="Save File") text to display in the dialog box titlebar
    # @param filters (list=[]) list of gtk.FileFilter objects. This specifies the types of files (via their extensions) that will be visible in the "save" dialog.
    # @param open_now_opt (boolean=False) if True, a checkbox will be displayed along the bottom of the save dialog box that allows the use to open the saved file as soon as it is finished being written to disk (opened in Excel).
    # @param save_last_location (boolean=False) if True, the directory containing the selected file will be saved (to UIUtils.last_filechoose_location), and the next "open" or "save" dialog will use it as the current directory
    # @param cur_location (string=None) a path to a folder to set the dialog to show when it opens. If None, this will display whatever directory GTK feels like.
    # @returns (string) the save path. If the user did not enter one, and instead clicked the cancel button or closed the dialog, this method will return None.
    @staticmethod
    def save_file(title='Save File', filters=[], open_now_opt=False, save_last_location=False, cur_location=None):
        if not filters:
            filters = [UIUtils.ALL_FILE_FILTER]
        return UIUtils.show_file_dialog(title, filters, gtk.FileChooserAction.SAVE, gtk.STOCK_SAVE, open_now_opt, save_last_location=save_last_location, cur_location=cur_location)

    ## Shows a dialog box with a message, a single text entry, and a set of buttons (e.g. ok/cancel). This allows the user to enter a string value. This method blocks until the user clicks ok.
    # Here is what the dialog looks like, (the red message at the bottom is shown only if the user clicks ok after entering invalid text/no text).
    # <img src="../images/entry_dialog.png">
    # @param msg (string) message to display above the entry. This is generally some instructions about what to type in the entry.
    # @param entry_title (string) This text will be displayed directly to the left of the entry. Usually it is some text with a colon that acts as a title for the entry.
    # @param default_text (string='') The entry will be prepopulated with this text when the dialog box opens.
    # @param validate_regex (string=r'^.+$') a regular expression that will be used to validate the text in the entry when the user clicks ok. If the regex does not match the text, invalid_msg will be displayed and the dialog will remain open.
    # The default value for this parameter is a regex that matches any text except the empty string (this just makes sure the user enters something).
    # @param invalid_msg (string='Please enter a value') this text will be shown below the dialog, in red, if the user clicks ok and the text they entered does not match validate_regex. In this case, the dialog will not close.
    # @returns (string) The string that the user typed into the entry, or None if they clicked the cancel button or closed the dialog.
    @staticmethod
    def show_entry_dialog(msg, entry_title, default_text='', validate_regex=r'^.+$', invalid_msg='Please enter a value.'):
        dialog = gtk.MessageDialog(buttons=gtk.ButtonsType.OK_CANCEL,
                                   message_format=msg,
                                   type=gtk.MessageType.QUESTION)

        message_area = dialog.get_message_area()
        
        vbox = gtk.VBox()

        entry_label = gtk.Label(entry_title)
        entry = gtk.Entry()
        entry.set_text(default_text)
        invalid_label = gtk.Label('')
        
        hbox = gtk.HBox()
        hbox.pack_start(entry_label, False, False, 0)
        hbox.pack_start(entry, False, False, 0)
        vbox.pack_start(hbox, False, False, 0)
        vbox.pack_start(invalid_label, False, False, 0)
        
        message_area.pack_end(vbox, False, False, 0)
        vbox.show_all()

        done = False
        text = None
        while text == None and dialog.run() == gtk.ResponseType.OK:
            entry_input = entry.get_text()
            if re.match(validate_regex, entry_input):
                text = entry_input
            else:
                invalid_label.set_markup('<span foreground="red">%s</span>' % (invalid_msg))
        
        dialog.destroy()

        return text

    ## This method shows a a file dialog box (for "open" or "save") that (in addition to its regular buttons and controls) contains one or more checkboxes that the user can toggle.
    # The checkboxes' states are returned, along with the user-specified path string (corresponding to the filesystem location they chose). This method blocks until the user clicks ok.
    # @param title (string) text to display in the dialog box titlebar
    # @param filters (list=[]) list of gtk.FileFilter objects. This specifies the types of files (via their extensions) that will be visible in the dialog.
    # @param action (int) This is a gtk filechooser action constant (one of gtk.FILE_CHOOSER_ACTION_OPEN, gtk.FILE_CHOOSER_ACTION_SAVE, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER or gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER),
    # indicating the type of dialog to display.
    # @param confirm_button_stock (int) a gtk stock icon constant (e.g. gtk.STOCK_OK, gtk.STOCK_OPEN), indicating what type of text and icon to display on the "ok" button. For a complete list of stock constants, see
    # <a href="http://www.pygtk.org/docs/pygtk/gtk-stock-items.html">the PyGTK docs here</a>.
    # @param checkbuttons (list) a list of gtk.CheckButton objects (i.e. checkboxes) to display in the dialog. See return value description for how to obtain their state when the ok button is pressed.
    # @param save_last_location (boolean=False) if True, the directory containing the selected file will be saved (to UIUtils.last_filechoose_location), and the next "open" or "save" dialog will use it as the current directory
    # @returns (string, list) a 2-tuple. The first element is the path the user has selected using the dialog controls (for example, the path to the file to open). The second element is a list of boolean values. Each value corresponds to one checkbutton.
    # A value of True indicates that the checkbox was checked when the user clicked ok - False indicates it was unchecked.
    @staticmethod
    def show_file_dialog_with_checks(title, filters, action, confirm_button_stock, checkbuttons, save_last_location=False):
        filename = None
        check_results = []
        
        dialog = gtk.FileChooserDialog(title=title,
                                       action=action,
                                       buttons=(gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL, confirm_button_stock, gtk.ResponseType.OK))
        dialog.set_default_response(gtk.ResponseType.OK)
        if save_last_location and UIUtils.last_filechooser_location:
            dialog.set_current_folder(UIUtils.last_filechooser_location)

        for cur_filter in filters:
            dialog.add_filter(cur_filter)

        if checkbuttons:
            content_area = dialog.get_content_area()
            vbox = gtk.VBox()
            for button in checkbuttons:
                align = gtk.Alignment(xalign=1.0, yalign=1.0)
                align.add(button)
                vbox.pack_start(align, False, False, 0)
                
            content_area.pack_end(vbox, False, False, 0)
            vbox.show_all()
        
        response = dialog.run()
        if response == gtk.ResponseType.OK:
            filename = dialog.get_filename()
            for button in checkbuttons:
                check_results.append(button.get_active())
            
        dialog.destroy()

        if save_last_location and filename:
            UIUtils.last_filechooser_location = os.path.dirname(filename)
        
        return filename, check_results

    ## This method shows a a file dialog box (for "open" or "save") with controls that allow the user to select a file. This method blocks until the user clicks ok.
    # @param title (string) text to display in the dialog box titlebar
    # @param filters (list=[]) list of gtk.FileFilter objects. This specifies the types of files (via their extensions) that will be visible in the dialog.
    # @param action (int) This is a gtk filechooser action constant (one of gtk.FILE_CHOOSER_ACTION_OPEN, gtk.FILE_CHOOSER_ACTION_SAVE, gtk.FILE_CHOOSER_ACTION_SELECT_FOLDER or gtk.FILE_CHOOSER_ACTION_CREATE_FOLDER),
    # indicating the type of dialog to display.
    # @param confirm_button_stock (int) a gtk stock icon constant (e.g. gtk.STOCK_OK, gtk.STOCK_OPEN), indicating what type of text and icon to display on the "ok" button. For a complete list of stock constants, see
    # <a href="http://www.pygtk.org/docs/pygtk/gtk-stock-items.html">the PyGTK docs here</a>.
    # @param open_now_opt (boolean=False) if True, a checkbox will be displayed in the dialog with the title "Open Immediately". Its value (True=checked, False=unchecked) is returned along with the path when this method returns. Typically this is used
    # in save dialogs to allow the user to indicate that they would like to open a file immediately after it is saved to disk.
    # @param save_last_location (boolean=False) if True, the directory containing the selected file will be saved (to UIUtils.last_filechoose_location), and the next "open" or "save" dialog will use it as the current directory
    # @param cur_location (string=None) a path to a folder to set the dialog to show when it opens. If None, this will display whatever directory GTK feels like.
    # @returns (string, list) a 2-tuple. The first element is the path the user has selected using the dialog controls (for example, the path to the file to open). The second element is a boolean value indicating the status of the "open now" checkbox (if present).
    # A value of True indicates that the checkbox was checked when the user clicked ok - False indicates it was unchecked (or that the checkbox is not being shown).
    @staticmethod
    def show_file_dialog(title, filters, action, confirm_button_stock, open_now_opt=False, save_last_location=False, cur_location=None):
        filename = None
        open_now_checkbox = None
        open_now = False
        
        dialog = gtk.FileChooserDialog(title=title,
                                       action=action,
                                       buttons=(gtk.STOCK_CANCEL, gtk.ResponseType.CANCEL, confirm_button_stock, gtk.ResponseType.OK))
        dialog.set_default_response(gtk.ResponseType.OK)
        if cur_location:
            dialog.set_current_folder(cur_location)
        elif save_last_location and UIUtils.last_filechooser_location:
            dialog.set_current_folder(UIUtils.last_filechooser_location)

        map(lambda f: dialog.add_filter(f), filters)

        if open_now_opt:
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
        if response == gtk.ResponseType.OK:
            filename = dialog.get_filename()
            if open_now_opt:
                open_now = open_now_checkbox.get_active()
            
        dialog.destroy()

        if save_last_location and filename:
            UIUtils.last_filechooser_location = os.path.dirname(filename)
        
        return filename, open_now

## This function is executed (by the call directly below it in the code) when the Python iterpreter reads this file for the first time.
# It populates all of the static constants in the UIUtils class. We cannot do this at class creation time (or in the class constructor)
# because it involves calling static UIUtils methods, and UIUtils has not yet been defined in either of those cases.
def _get_constants():
    #Create some static common filter objects that can be passed to the dialog box methods in the UIUtils class.
    #These are provided only for convenience. Calling code is free to create filter for other types of files/folders.
    UIUtils.WAV_FILE_FILTER = UIUtils.build_file_filter('WAV Files', ['*.wav'])
    UIUtils.TRS_FILE_FILTER = UIUtils.build_file_filter('TRS Files', ['*.trs'])
    UIUtils.ITS_FILE_FILTER = UIUtils.build_file_filter('ITS Files', ['*.its'])
    UIUtils.ALL_FILE_FILTER = UIUtils.build_file_filter('All Files', ['*'])
    UIUtils.CSV_FILE_FILTER = UIUtils.build_file_filter('CSV Files', ['*.csv'])
    UIUtils.TRS_CSV_FILE_FILTER = UIUtils.build_file_filter('TRS/CSV Files', ['*.trs', '*.csv'])

_get_constants()
