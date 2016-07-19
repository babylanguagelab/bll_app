import logging as lg
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk


class MainWindow(object):
    def __init__(self, controller):
        self.con = controller

        builder = Gtk.Builder()
        builder.add_from_file("UI.glade")
        self.window = builder.get_object("win_main")

        self.adex = ADEXDialog(builder, self.con)
        self.comt = CommentDialog(builder, self.con)
        self.trans = TransDialog(builder, self.con)

        self.connect_signals(builder)

        ADEX_toggle = builder.get_object("toggle_ADEX")
        if self.con.config['ADEX']:
            ADEX_toggle.set_active(True)

        Comment_toggle= builder.get_object("toggle_COM")
        if self.con.config['comment']:
            Comment_toggle.set_active(True)

        Trans_toggle = builder.get_object("toggle_TRANS")
        if self.con.config['transcribed']:
            Trans_toggle.set_active(True)

    def connect_signals(self, gbuilder):
        signal_handlers = {
            "quit_main": Gtk.main_quit,
            "check_ADEX_toggled_cb": self.toggle_ADEX,
            "check_CMT_toggled_cb": self.toggle_CMT,
            "check_Trans_toggle_cb": self.toggle_Trans,
            "save_preliminary": self.save_preliminary,
            "run": self.run
        }

        signal_handlers.update(self.adex.get_signals_handlers())
        signal_handlers.update(self.comt.get_signals_handlers())
        signal_handlers.update(self.trans.get_signals_handlers())

        gbuilder.connect_signals(signal_handlers)

    def toggle_ADEX(self, button):
        self.con.config['ADEX'] = button.get_active()

        if self.con.config['ADEX']:
            self.adex.show()

    def toggle_CMT(self, button):
        self.con.config['comment'] = button.get_active()

        if self.con.config['comment']:
            self.comt.show()

    def toggle_Trans(self, button):
        self.con.config['transcribed'] = button.get_active()

        if self.con.config['transcribed']:
            self.trans.show()

    def save_preliminary(self, button):
        self.con.set_preliminary(button.get_active())

    def run(self, button):
        if self.con.config['ADEX'] and len(self.con.config['ADEX_folders']) == 0:
            self.adex.choose_folders()

        if self.con.config['comment'] and len(self.con.config['special_case_file']) == 0:
            self.comt.choose_file()

        if self.con.config['transcribed'] and len(self.con.config['transcribed_file']) == 0:
            self.trans.choose_file()

        if len(self.con.config['output']) == 0:
            save_dialog = Gtk.FileChooserDialog("Please choose where to save output",
                                                self.window,
                                                Gtk.FileChooserAction.SELECT_FOLDER,
                                                (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT,
                                                 Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
            save_dialog.set_local_only(True)
            response = save_dialog.run()

            if response == Gtk.ResponseType.ACCEPT:
                self.con.set_output(save_dialog.get_filename())

            save_dialog.destroy()

        self.con.run()

        info_dialog = Gtk.MessageDialog(self.window, Gtk.DialogFlags.MODAL,
                                        Gtk.MessageType.WARNING,
                                        (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT),
                                        message_format="Job Complete!")
        info_dialog.run()
        info_dialog.destroy()

    def show(self):
        self.window.show_all()
        Gtk.main()


class ADEXDialog(object):
    def __init__(self, gbuilder, controller):
        self.mdialog = gbuilder.get_object("dialog_ADEX")
        self.control = controller

        self.list_adex_switch = gbuilder.get_object("list_ADEX_switch")

        treeview_adex_switch = gbuilder.get_object("treeview_ADEX_switch")

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Name", renderer, text=0)
        treeview_adex_switch.append_column(column)

        render_toggle = Gtk.CellRendererToggle()
        render_toggle.connect("toggled", self.toggle_switches)
        column_toggle = Gtk.TreeViewColumn("Choose", render_toggle, active=1)
        treeview_adex_switch.append_column(column_toggle)

        self.f30mins_toggle = gbuilder.get_object("adex_30mins_check")
        self.partial_toggle = gbuilder.get_object("adex_partial_check")
        self.naptime_toggle = gbuilder.get_object("adex_naptime_check")
        self.last2r_toggle = gbuilder.get_object("adex_last2_check")

    def get_signals_handlers(self):
        handlers = {
            "stop_delete_window": self.stop_delete_window,
            "toggle_ADEX_30mins": self.toggle_adex_f30mins,
            "toggle_ADEX_partial": self.toggle_partial_records,
            "toggle_ADEX_naptime": self.toggle_naptime,
            "toggle_ADEX_last2": self.toggle_last2,
            "hidex_adex_dialog": self.hide,
        }
        return handlers

    # hide the window instead of deleting
    def stop_delete_window(self, widget, data):
        Gtk.Widget.hide(widget)
        return True

    def toggle_switches(self, widget, path):
        self.list_adex_switch[path][1] = not self.list_adex_switch[path][1]

    def toggle_naptime(self, button):
        self.control.adex.config['naptime'] = button.get_active()

    def toggle_adex_f30mins(self, button):
        self.control.adex.config['f30mins'] = button.get_active()

    def toggle_partial_records(self, button):
        self.control.adex.config['partial_records'] = button.get_active()

    def toggle_last2(self, button):
        self.control.adex.config['last2rows'] = button.get_active()

    # ADEX folders choose dialog
    def choose_folders(self):
        result = []
        dialog = Gtk.FileChooserDialog("Please choose ADEX folders",
                                       self.mdialog,
                                       Gtk.FileChooserAction.SELECT_FOLDER,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_select_multiple(True)
        dialog.set_local_only(True)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            result = dialog.get_filenames()

        dialog.destroy()

        self.control.config['ADEX_folders'] = result

    # ADEX configuration dialog
    def show(self):
        self.choose_folders()

        # sync data
        self.list_adex_switch.clear()
        for i in self.control.adex.switches:
            self.list_adex_switch.append((i, True))

        self.f30mins_toggle.set_active(self.control.adex.config['f30mins'])
        self.partial_toggle.set_active(self.control.adex.config['partial_records'])
        self.naptime_toggle.set_active(self.control.adex.config['naptime'])
        self.last2r_toggle.set_active(self.control.adex.config['last2rows'])

        self.mdialog.show()

    def hide(self, button):
        # update switches with ADEX processor
        valid_options = []
        treeiter = self.list_adex_switch.get_iter_first()
        while treeiter  is not None:
            if self.list_adex_switch[treeiter][1]:
                valid_options.append(self.list_adex_switch[treeiter][0])
            treeiter = self.list_adex_switch.iter_next(treeiter)

        Gtk.Widget.hide(self.mdialog)


class CommentDialog(object):
    def __init__(self, gbuilder, controller):
        self.control = controller

        self.main_dialog = gbuilder.get_object("dialog_comment")
        self.configs_store = gbuilder.get_object("liststore_comment")
        self.configs_view = gbuilder.get_object("treeview_comment")
        self.configs = []

    def get_signals_handlers(self):
        handlers = {
            "stop_delete_window": self.stop_delete_window,
            "hide_dialog_comment": self.hide
        }
        return handlers

    def stop_delete_window(self, widget, data):
        Gtk.Widget.hide(widget)
        return True

    def choose_file(self):
        file_dialog = Gtk.FileChooserDialog("Please choose the special case file",
                                            self.main_dialog,
                                            Gtk.FileChooserAction.SAVE,
                                            (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT,
                                             Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        file_dialog.set_local_only(True)
        response = file_dialog.run()

        comment_file = ""
        if response == Gtk.ResponseType.ACCEPT:
            comment_file = file_dialog.get_filename()

        file_dialog.destroy()

        self.control.config['special_case_file'] = comment_file
        self.control.com.open_comment_file(comment_file)

    def show(self):
        if len(self.control.config['special_case_file'])  == 0:
            self.choose_file()

            for item in self.control.com.content['head']:
                self.configs_store.append([self.control.com.switch[item][0],
                                           item,
                                           False])

            renderer_toggle = Gtk.CellRendererToggle()
            renderer_toggle.connect("toggled", self.update_rows)
            column_toggle = Gtk.TreeViewColumn("Enable", renderer_toggle, active=0)
            self.configs_view.append_column(column_toggle)

            renderer_text = Gtk.CellRendererText()
            column_text = Gtk.TreeViewColumn("Name", renderer_text, text=1)
            self.configs_view.append_column(column_text)

            renderer_toggle2 = Gtk.CellRendererToggle()
            column_toggle2 = Gtk.TreeViewColumn("Details", renderer_toggle2, active=2)
            renderer_toggle2.connect("toggled", self.update_details)
            self.configs_view.append_column(column_toggle2)

        self.main_dialog.show()

    def hide(self, button):
        Gtk.Widget.hide(self.main_dialog)

    # update categories
    def update_rows(self, widget, path):
        self.configs_store[path][0] = not self.configs_store[path][0]

    # update details
    def update_details(self, widget, path):
        # for the specific item: name, enable, list, inverse)
        self.configs = []
        entry_name = self.control.com.content["head"][int(path)]
        entry_list = list(self.control.com.content["column"][entry_name])
        entry_list.sort()

        if not self.configs_store[path][0]:
            self.configs_store[path][0] = not self.configs_store[path][0]

        entry_dialog = self.create_entry_dialog(entry_name, entry_list)
        entry_dialog.run()
        Gtk.Widget.hide(entry_dialog)

        if self.entry_all:
            self.control.com.update_switch(entry_name, True, "all")
            return

        result_list = []
        treeiter = self.entry_liststore.get_iter_first()
        while treeiter != None:
            if self.entry_liststore[treeiter][0]:
                result_list.append(self.entry_liststore[treeiter][1])
            treeiter = self.entry_liststore.iter_next(treeiter)

        entry_dialog.destroy()
        self.control.com.update_switch(entry_name, True, result_list, self.entry_inverse)

    # create details dialog
    def create_entry_dialog(self, entry_name, entry_list):
        entry_dialog = Gtk.Dialog("Config Dialog", self.main_dialog,
                                   Gtk.DialogFlags.MODAL,
                                  (Gtk.STOCK_OK, Gtk.ResponseType.OK))
        entry_dialog.resize(480, 640)

        vbox = entry_dialog.get_content_area()

        l2_box = Gtk.Box(Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(l2_box, False, False, 0)

        label = Gtk.Label("Entry Name:" + entry_name)
        l2_box.pack_start(label, True, True, 10)

        self.entry_all = True
        all_button = Gtk.ToggleButton("All")
        all_button.connect("toggled", self.update_entry_all, "1")
        l2_box.pack_start(all_button, False, False, 0)

        self.entry_inverse = False
        inverse_button = Gtk.ToggleButton("Inverse")
        inverse_button.connect("toggled", self.update_entry_inverse, "1")
        l2_box.pack_start(inverse_button, False, False, 0)

        tmp_list = list(zip([True] * len(entry_list), entry_list))
        self.entry_liststore = Gtk.ListStore(bool, str)
        for i in tmp_list:
            self.entry_liststore.append(list(i))

        self.config_treeview = Gtk.TreeView(model=self.entry_liststore)

        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.connect("toggled", self.update_entry_config)
        column_toggle = Gtk.TreeViewColumn("Enable", renderer_toggle, active=0)
        column_toggle = Gtk.TreeViewColumn("Toggle", renderer_toggle, active=0)
        self.config_treeview.append_column(column_toggle)

        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn("Text", renderer_text, text=1)
        self.config_treeview.append_column(column_text)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add_with_viewport(self.config_treeview)

        vbox.pack_start(scrolled_window, True, True, 0)
        vbox.show_all()

        all_button.set_active(True)

        return entry_dialog

    def update_entry_config(self, widget, path):
        self.entry_liststore[path][0] = not self.entry_liststore[path][0]

    def update_entry_all(self, button, name):
        if button.get_active():
            self.entry_all = True
            self.config_treeview.set_sensitive(False)
        else:
            self.entry_all = False
            self.config_treeview.set_sensitive(True)

    def update_entry_inverse(self, button, name):
        if button.get_active():
            self.entry_inverse = True
        else:
            self.entry_inverse = False


class TransDialog(object):
    def __init__(self, gbuilder, controller):
        self.control = controller
        self.main_dialog= gbuilder.get_object("dialog_transcribed")

        self.average_button = gbuilder.get_object("transcribed_average_button")
        self.average_button.connect("toggled", self.button_toggled, "1")

        self.sum_button = gbuilder.get_object("transcribed_sum_button")
        self.sum_button.connect("toggled", self.button_toggled, "2")

    def get_signals_handlers(self):
        handlers = {"stop_delete_window": self.stop_delete_window,
                    "hide_dialog": self.hide}
        return handlers

    def stop_delete_window(self, widget, data):
        Gtk.Widget.hide(widget)
        return True

    def choose_file(self):
        file_dialog = Gtk.FileChooserDialog("Please choose the transcribed file",
                                            self.main_dialog,
                                            Gtk.FileChooserAction.SAVE,
                                            (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT,
                                             Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        file_dialog.set_local_only(True)
        response = file_dialog.run()

        trans_file = ""
        if response == Gtk.ResponseType.ACCEPT:
            trans_file = file_dialog.get_filename()

        file_dialog.destroy()
        self.control.config['transcribed_file'] = trans_file

    def button_toggled(self, button, name):
        if button.get_active():
            if name == "1":
                self.control.trans.config['calc_type'] = 1
            else:
                self.control.trans.config['calc_type'] = 2

    def hide(self, button):
        Gtk.Widget.hide(self.main_dialog)

    def show(self):
        if len(self.control.config['transcribed_file']) == 0:
            self.choose_file()

        self.main_dialog.show()
