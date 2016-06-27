# Description: main entry point
# Author: zhangh15@myumanitoba.ca
# Date: 2015-11-17

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
# import logging as lg


class MainWindow(object):
    def __init__(self, controller):
        self.con = controller

        builder = Gtk.Builder()
        builder.add_from_file("UI.glade")
        self.window = builder.get_object("win_main")

        self.adex = ADEXDialog(builder, self.con)
        self.comt = CommentDialog(builder, self.con)

        self.connect_signals(builder)

    def connect_signals(self, gbuilder):
        signal_handlers = {
            "quit_main": Gtk.main_quit,
            "check_ADEX_toggled_cb": self.toggle_ADEX,
            "check_CMT_toggled_cb": self.toggle_CMT,
            "show_ADEX_dialog": self.adex.show,
            "show_CMT_dialog": self.comt.show,
            "run": self.run
        }

        signal_handlers.update(self.adex.get_signals_handlers())
        signal_handlers.update(self.comt.get_signals_handlers())

        gbuilder.connect_signals(signal_handlers)

    def toggle_ADEX(self, button):
        self.con.config['ADEX'] = button.get_active()

    def toggle_CMT(self, button):
        self.con.config['Comment'] = button.get_active()

    def run(self, button):
        #self.con.ADEX_folders=['/home/hao/Develop/projects/bll/bll_app/test/sample']
        if self.con.config['ADEX']:
            if len(self.con.adex.config['adex_dirs']) == 0:
                self.con.adex.config['adex_dirs'] = self.adex.choose_folders()

        if self.con.config['Comment']:
            if len(self.con.com.config['filename']) == 0:
                self.con.com.config['filename'] = self.comt.choose_file()

        if len(self.con.config['output_file']) == 0:
            save_dialog = Gtk.FileChooserDialog("Please choose where to save output",
                                                self.window,
                                                Gtk.FileChooserAction.SAVE,
                                                (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT,
                                                 Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
            save_dialog.set_local_only(True)
            response = save_dialog.run()

            if response == Gtk.ResponseType.ACCEPT:
                self.con.config['output_file'] = save_dialog.get_filename()

            save_dialog.destroy()

        self.con.run()

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
        column_toogle = Gtk.TreeViewColumn("Choose", render_toggle, active=1)
        treeview_adex_switch.append_column(column_toogle)

        self.combo_time = gbuilder.get_object("combo_ADEX_time")
        list_time_interval = gbuilder.get_object("list_ADEX_time")
        list_time_interval.append(["5 minutes"])
        list_time_interval.append(["10 minutes"])
        list_time_interval.append(["30 minutes"])
        list_time_interval.append(["60 minutes"])

        renderer_text = Gtk.CellRendererText()
        self.combo_time.pack_start(renderer_text, True)
        self.combo_time.add_attribute(renderer_text, "text", 0)

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
            "combo_ADEX_time_changed_cb": self.change_partial_time
        }
        return handlers

    # hide the window instead of deleting
    def stop_delete_window(self, widget, data):
        Gtk.Widget.hide(widget)
        return True

    # change ADEX configurations
    def toggle_switches(self, widget, path):
        self.list_adex_switch[path][1] = not self.list_adex_switch[path][1]
        self.control.adex.switches[int(path)][1] = self.list_adex_switch[path][1]

    def toggle_naptime(self, button):
        self.control.adex.config['naptime'] = button.get_active()

    def toggle_adex_f30mins(self, button):
        self.control.adex.config['f30mins'] = button.get_active()

    def toggle_partial_records(self, button):
        self.control.adex.config['partial_records'] = button.get_active()

    def change_partial_time(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter != None:
            model = combo.get_model()
            ptime = int(model[tree_iter][0].split(' ')[0])
            self.control.adex.config['time_interval'] = ptime * 60

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
        return result

    # ADEX configuration dialog
    def show(self, button):
        if len(self.control.adex.config['adex_dirs']) == 0:
            self.control.adex.config['adex_dirs'] = self.choose_folders()

        # sync data
        self.list_adex_switch.clear()
        for i in self.control.adex.switches:
            self.list_adex_switch.append(i)

        self.f30mins_toggle.set_active(self.control.adex.config['f30mins'])
        self.partial_toggle.set_active(self.control.adex.config['partial_records'])
        self.naptime_toggle.set_active(self.control.adex.config['naptime'])
        self.last2r_toggle.set_active(self.control.adex.config['last2rows'])

        time_interval = self.control.adex.config['time_interval']
        if time_interval == 300:
            self.combo_time.set_active(0)
        elif time_interval == 600:
            self.combo_time.set_active(1)
        elif time_interval == 1800:
            self.combo_time.set_active(2)
        elif time_interval == 3600:
            self.combo_time.set_active(3)

        self.mdialog.show()

    def hide(self, button):
        Gtk.Widget.hide(self.mdialog)


class CommentDialog(object):
    def __init__(self, gbuilder, controller):
        self.contro = controller

        self.main_dialog = gbuilder.get_object("dialog_comment")
        self.configs_store = gbuilder.get_object("liststore_comment")
        self.configs_view = gbuilder.get_object("treeview_comment")

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

        return comment_file

    def show(self, button):
        if len(self.contro.com.config['filename']) == 0:
            # # for test
            # self.contro.com.config['filename'] = "/home/hao/Develop/bll/bll_app/test/Special Cases Tab 2016.01.28.xlsx"
            self.contro.com.config['filename'] = self.choose_file()
            self.contro.com.open_comment_file()

            for item in self.contro.com.content['head']:
                self.configs_store.append([self.contro.com.switch[item][0], item])

            renderer_toggle = Gtk.CellRendererToggle()
            renderer_toggle.connect("toggled", self.update_rows)
            column_toggle = Gtk.TreeViewColumn("Enable", renderer_toggle, active=0)
            self.configs_view.append_column(column_toggle)

            renderer_text = Gtk.CellRendererText()
            column_text = Gtk.TreeViewColumn("Name", renderer_text, text=1)
            self.configs_view.append_column(column_text)

        self.main_dialog.show()

    def hide(self, button):
        Gtk.Widget.hide(self.main_dialog)

    def update_rows(self, widget, path):
        self.configs_store[path][0] = not self.configs_store[path][0]

        # for the specific item: name, enable, list, inverse)
        self.configs = []
        entry_name = self.contro.com.content["head"][int(path)]
        entry_list = self.contro.com.content["column"][entry_name]

        if self.configs_store[path][0]:
            entry_dialog = self.create_entry_dialog(entry_name, entry_list)
            entry_dialog.run()
            result_list = []
            treeiter = self.entry_liststore.get_iter_first()
            while treeiter != None:
                if self.entry_liststore[treeiter][0]:
                    result_list.append(self.entry_liststore[treeiter][1])
                treeiter = self.entry_liststore.iter_next(treeiter)
            self.contro.com.update_switch(entry_name, True, result_list, self.entry_inverse)
            entry_dialog.destroy()
        else:
            self.contro.com.update_switch(entry_name, False, "")

    def create_entry_dialog(self, entry_name, entry_list):
        entry_dialog = Gtk.Dialog("Config Dialog", self.main_dialog,
                                   0, (Gtk.STOCK_OK, Gtk.ResponseType.OK))

        vbox = entry_dialog.get_content_area()

        l2_box = Gtk.Box(Gtk.Orientation.HORIZONTAL)
        vbox.pack_start(l2_box, False, False, 0)

        label = Gtk.Label("Entry Name:" + entry_name)
        l2_box.pack_start(label, True, True, 10)

        inverse_button = Gtk.ToggleButton("Inverse")
        inverse_button.connect("toggled", self.update_entry_inverse, "1")
        l2_box.pack_start(inverse_button, False, False, 0)
        self.entry_inverse = False

        tmp_list = list(zip([True] * len(entry_list), entry_list))
        self.entry_liststore = Gtk.ListStore(bool, str)
        for i in tmp_list:
            self.entry_liststore.append(list(i))

        config_treeview = Gtk.TreeView(model=self.entry_liststore)

        renderer_toggle = Gtk.CellRendererToggle()
        renderer_toggle.connect("toggled", self.update_entry_config)
        column_toggle = Gtk.TreeViewColumn("Enable", renderer_toggle, active=0)
        column_toggle = Gtk.TreeViewColumn("Toggle", renderer_toggle, active=0)
        config_treeview.append_column(column_toggle)

        renderer_text = Gtk.CellRendererText()
        column_text = Gtk.TreeViewColumn("Text", renderer_text, text=1)
        config_treeview.append_column(column_text)

        scrolled_window = Gtk.ScrolledWindow()
        scrolled_window.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scrolled_window.add_with_viewport(config_treeview)

        vbox.pack_start(scrolled_window, True, True, 0)
        vbox.show_all()

        return entry_dialog

    def update_entry_config(self, widget, path):
        self.entry_liststore[path][0] = not self.entry_liststore[path][0]

    def update_entry_inverse(self, button, name):
        if button.get_active():
            self.entry_inverse = True
        else:
            self.entry_inverse = False
