## @package utils.filters_frame

from gi.repository import Gtk as gtk
from gi.repository import GObject as gobject

from utils.add_filter_window import AddFilterWindow
from utils.ui_utils import UIUtils
from data_structs.seg_filters import *

## This is frame that you can embed in a window to allow the user to create segment filters.
# The frame contains a treeview with rows for each of the filters that have been added so far.
# Each row contains an English description of an existing filter.
# Two buttons just below the treeview allow the user to add and remove filters.
# A list of SegFilter objects can be retrieved using the get_filters() method.
# The machinery for adding and removing filters is provided by the utils.add_filter_window.AddFilterWindow class.
# Here is a screenshot of what this class looks like in the UI:
# <img src="../images/filters_frame.png">
class FiltersFrame(gtk.Frame):
    ## Constructor
    # @param self
    # @param label (string='Filters') a title string to display along the top of the frame
    # @param existing_filters (list=[]) a list of SegFilter objects that should be programatically added to the list upon creation
    def __init__(self, label='Filters', existing_filters=[]):
        super(FiltersFrame, self).__init__(label=label)

        vbox = gtk.VBox()
        #build the treeview (list of current filters)
        list_store = gtk.ListStore(gobject.TYPE_STRING,
                                   gobject.TYPE_STRING,
                                   gobject.TYPE_PYOBJECT)
        
        self.treeview = gtk.TreeView(list_store)
        
        col_names = ['Type', 'Description']
        for i in range(len(col_names)):
            col = gtk.TreeViewColumn(col_names[i], gtk.CellRendererText(), text=i)
            col.set_resizable(True)
            self.treeview.append_column(col)

        #if we have any already-existing filters, add them to the treeview model so that they are displayed
        model = self.treeview.get_model()
        for cur_filter in existing_filters:
            model.append([cur_filter.get_filter_type_str(), cur_filter.get_filter_desc_str(), cur_filter])

        vbox.pack_start(self.treeview, True, True, 0)

        #create buttons for adding and removing filters
        button_box = gtk.HButtonBox()
        add_button = UIUtils.create_button('Add Filter', UIUtils.BUTTON_ICONS.ADD, UIUtils.BUTTON_ICON_SIZES.PX22)
        add_button.connect('clicked', lambda w: AddFilterWindow(self._add_filter))
        remove_button = UIUtils.create_button('Remove Filter', UIUtils.BUTTON_ICONS.REMOVE, UIUtils.BUTTON_ICON_SIZES.PX22)
        remove_button.connect('clicked', lambda w: self._remove_filter())
        button_box.add(add_button)
        button_box.add(remove_button)

        vbox.pack_start(button_box, False, False, 0)
        self.add(vbox)

    ## Retrieves a list of SegFilter objects that represent the filters the user has created.
    # @param self
    # @returns (list) list of SegFilter objects - empty list if user has not created any
    def get_filters(self):
        tree_model = self.treeview.get_model()
        filters_iter = tree_model.get_iter_first()
        filters = []
        while filters_iter:
            filters.append(tree_model.get_value(filters_iter, 2))
            filters_iter = tree_model.iter_next(filters_iter)
            
        return filters

    ## Internal method to add a new filter to the treeview model. This makes the UI display a list row for the filter.
    # @param self
    # @param new_filter (SegFilter) a SegFilter object representing the newly created filter to add to the UI list.
    def _add_filter(self, new_filter):
        filter_list_store = self.treeview.get_model()
        filter_list_store.append([new_filter.get_filter_type_str(), new_filter.get_filter_desc_str(), new_filter])

    ## Internal method to remove the currently selected filter from the list. This effectively removes all record of the filter from this instance's memory (i.e. it will no longer be
    # returned by get_filters()). If no UI row is selected, nothing happens.
    # @param self
    def _remove_filter(self):
        model, it = self.treeview.get_selection().get_selected()
        if it:
            model.remove(it)
