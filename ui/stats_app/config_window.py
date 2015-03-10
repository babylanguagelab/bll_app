from gi.repository import Gtk as gtk
from gi.repository import GObject as gobject

from utils.ui_utils import UIUtils
from data_structs.output_config import OutputConfig
from ui.stats_app.output_window import OutputWindow
from db.bll_database import BLLDatabase

class ConfigWindow():
    def __init__(self, action_callback, edit_config=None):
        self.edit_config = edit_config
        self.action_callback = action_callback
        
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('%s Configuration' % ('Edit' if self.edit_config else 'Create'))
        self.window.set_border_width(10)
        self.window.set_default_size(500, 350)

        vbox = gtk.VBox()

        #properties frame
        props_frame = gtk.Frame(label='Properties')
        grid = gtk.Grid() #gtk.Table(3, 2)
        grid.set_column_spacing(3)
        name_label = gtk.Label('Name:')
        self.name_entry = gtk.Entry()
        self.name_entry.set_width_chars(50)
        if self.edit_config:
            self.name_entry.set_text(self.edit_config.name)

        #It appears that proper alignment can only be acheived with HBoxes here...
        name_label_hbox = gtk.HBox()
        align = gtk.Alignment()
        align.set(1, 0, 0, 0)
        name_label_hbox.pack_start(align, True, True, 0)
        name_label_hbox.pack_start(name_label, False, False, 0)
        #table.attach(name_label_hbox, 0, 1, 0, 1)
        grid.attach(name_label_hbox, 0, 0, 1, 1)

        name_entry_hbox = gtk.HBox()
        name_entry_hbox.pack_start(self.name_entry, False, False, 0)
        #table.attach(name_entry_hbox, 1, 2, 0, 1)
        grid.attach(name_entry_hbox, 1, 0, 1, 1)

        desc_label = gtk.Label('Description:')
        self.desc_entry = gtk.Entry()
        self.desc_entry.set_width_chars(50)
        if self.edit_config:
            self.desc_entry.set_text(self.edit_config.desc)

        desc_label_hbox = gtk.HBox()
        align = gtk.Alignment()
        align.set(1, 0, 0, 0)
        desc_label_hbox.pack_start(align, True, True, 0)
        desc_label_hbox.pack_start(desc_label, False, False, 0)
        #table.attach(desc_label_hbox, 0, 1, 1, 2)
        grid.attach(desc_label_hbox, 0, 1, 1, 1)

        desc_entry_hbox = gtk.HBox()
        desc_entry_hbox.pack_start(self.desc_entry, False, False, 0)
        #table.attach(desc_entry_hbox, 1, 2, 1, 2)#, ypadding=3) #ypadding adds some space between bottom of entry and bottom of frame border
        grid.attach(desc_entry_hbox, 1, 1, 1, 1)

        props_frame.add(grid)
        
        vbox.pack_start(props_frame, False, False, 0)

        #outputs frame
        outputs_frame = gtk.Frame(label='Outputs')
        outputs_vbox = gtk.VBox()
        existing_outputs = self.edit_config.outputs if self.edit_config else []
        self.outputs_treeview = self._build_outputs_treeview(existing_outputs)
        scrolled_win = gtk.ScrolledWindow()
        scrolled_win.set_policy(gtk.PolicyType.AUTOMATIC, gtk.PolicyType.AUTOMATIC)
        scrolled_win.add(self.outputs_treeview)
        outputs_vbox.pack_start(scrolled_win, True, True, 0)

        outputs_button_box = gtk.HButtonBox()
        outputs_button_box.set_layout(gtk.ButtonBoxStyle.EDGE)

        add_button = UIUtils.create_button('Add Output', UIUtils.BUTTON_ICONS.ADD, UIUtils.BUTTON_ICON_SIZES.PX22)
        add_button.connect('clicked', lambda w: OutputWindow(self._add_output_callback))
        outputs_button_box.pack_start(add_button, True, True, 0)

        edit_button = UIUtils.create_button('Edit Output', UIUtils.BUTTON_ICONS.EDIT, UIUtils.BUTTON_ICON_SIZES.PX22)
        edit_button.connect('clicked', lambda w: self._edit_output())
        outputs_button_box.pack_start(edit_button, True, True, 0)

        remove_button = UIUtils.create_button('Remove Output', UIUtils.BUTTON_ICONS.REMOVE, UIUtils.BUTTON_ICON_SIZES.PX22)
        remove_button.connect('clicked', lambda w: self._remove_output())
        outputs_button_box.pack_start(remove_button, True, True, 0)

        outputs_vbox.pack_start(outputs_button_box, False, False, 0)
        outputs_frame.add(outputs_vbox)
        
        vbox.pack_start(outputs_frame, True, True, 0)

        #buttons box
        button_box = gtk.HButtonBox()
        button_box.set_layout(gtk.ButtonBoxStyle.EDGE)
        cancel_button = gtk.Button(stock=gtk.STOCK_CANCEL)
        cancel_button.connect('clicked', lambda w: self.window.destroy())
        button_box.pack_start(cancel_button, False, False, 0)

        ok_button = gtk.Button(stock=gtk.STOCK_OK)
        ok_button.connect('clicked', lambda w: self._create_config())
        button_box.pack_start(ok_button, False, False, 0)

        vbox.pack_end(button_box, False, False, 0)
        
        self.window.add(vbox)
        self.window.show_all()

    def _validate(self):
        return self.name_entry.get_text() != '' # desc can be left blank

    def _create_config(self):
        if self._validate():
            #extract the output objects from the treeview model
            outputs = []
            model = self.outputs_treeview.get_model()
            row = 0
            while row < len(model):
                outputs.append(model[row][4])
                row += 1

            name = self.name_entry.get_text()
            desc = self.desc_entry.get_text()

            db = BLLDatabase()
            created = None
            #if editing, delete previous config from DB
            if self.edit_config:
                created = self.edit_config.created
                self.edit_config.db_delete(db) #this will also delete any associated outputs and entries in output_configs_to_outputs
                self.edit_config = None
                
            config = OutputConfig(name, desc, outputs, created)
            config.db_insert(db)
            db.close()

            self.window.destroy()
            self.action_callback(config)

        else:
            UIUtils.show_message_dialog('Please make sure that all of the fields have been filled out.', gtk.MessageType.WARNING)

    def _get_output_filters_str(self, output):
        filters_str = ''
        i = 0
        while i < len(output.filters):
            filters_str += output.filters[i].get_filter_desc_str()
            if i < len(output.filters) - 1:
                filters_str += ' and\n'
            i += 1

        if not filters_str:
            filters_str = '-'

        return filters_str
            
    def _add_output_callback(self, new_output):
        self.outputs_treeview.get_model().append([new_output.name,
                                                  new_output.desc,
                                                  'Linked' if new_output.chained else 'Unlinked',
                                                  self._get_output_filters_str(new_output),
                                                  new_output,
                                                  ])

    def _edit_output(self):
        model, it = self.outputs_treeview.get_selection().get_selected()
        if it:
            OutputWindow(lambda edited_output: self._edit_output_callback(edited_output, it), model.get(it, 4)[0])
            
        else:
            UIUtils.show_message_dialog('Please select a row.', gtk.MessageType.WARNING)
        
    def _edit_output_callback(self, edited_output, row_it):
        model = self.outputs_treeview.get_model()
        
        #update the treeview model with the edited properties
        model.set_value(row_it, 0, edited_output.name)
        model.set_value(row_it, 1, edited_output.desc)
        model.set_value(row_it, 2, 'Linked' if edited_output.chained else 'Unlinked')
        model.set_value(row_it, 3, self._get_output_filters_str(edited_output))
        model.set_value(row_it, 4, edited_output)

    def _remove_output(self):
        model, it = self.outputs_treeview.get_selection().get_selected()
        if it:
            if UIUtils.show_confirm_dialog('Are you sure you want to delete this output?'):
                model.remove(it)
        else:
            UIUtils.show_message_dialog('Please select a row.', gtk.MessageType.WARNING)

        #note: the actual delete from the DB is deferred until the user clicks ok
            
    def _build_list_store(self, existing_outputs=[]):
        list_store = gtk.ListStore(gobject.TYPE_STRING, #name
                                   gobject.TYPE_STRING, #desc
                                   gobject.TYPE_STRING, #linked
                                   gobject.TYPE_STRING, #filters
                                   gobject.TYPE_PYOBJECT, #output object
                                   )

        #for edit functionality
        for cur_output in existing_outputs:
            list_store.append([cur_output.name,
                               cur_output.desc,
                               'Linked' if cur_output.chained else 'Unlinked',
                               self._get_output_filters_str(cur_output),
                               cur_output,
                               ])

        return list_store
            
    def _build_outputs_treeview(self, existing_outputs=[]):
        list_store = self._build_list_store(existing_outputs)
        treeview = gtk.TreeView(list_store)

        #don't create any column for the PYOBJECT, which is the first element of the list_store rows
        col_names = ['Name', 'Description', 'Link Segs', 'Filters']
        for i in range(len(col_names)):
            col = gtk.TreeViewColumn(col_names[i], gtk.CellRendererText(), text=i)
            col.set_resizable(True)
            col.set_min_width( UIUtils.calc_treeview_col_min_width(col_names[i]) )
            treeview.append_column(col)

        return treeview
