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
        self.dialog_adex = ADEXDialog(builder, self.con)
        self.dialog_comment = CommentDialog(builder, self.con)

        #self.init_CMT_dialog(builder)
        #self.init_config_dialog(builder)

        self.connect_signals(builder)

    def init_config_dialog(self, gbuilder):
        self.dialog_config = gbuilder.get_object("save_config_dialog")
        self.config_title = gbuilder.get_object("save_config_titile")
        self.config_desc = gbuilder.get_object("save_config_desc")

        self.list_configs = gbuilder.get_object("list_conf")
        treeview_conf = gbuilder.get_object("treeview_conf")

        text_render = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("ID", text_render, text=0)
        treeview_conf.append_column(column)

        text_render = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Title", text_render, text=1)
        treeview_conf.append_column(column)

        text_render = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Description", text_render, text=2)
        treeview_conf.append_column(column)

        self.list_configs.append((1, "Adex's config", "Sample Description"))


    def connect_signals(self, gbuilder):
        adex_handlers = self.dialog_adex.get_signals_handlers()

        mHandlers = {
            "quit_main": Gtk.main_quit,
            "show_ADEX_dialog": self.dialog_adex.show,
            "show_CMT_dialog": self.dialog_comment.show,
            "show_config_dialog": self.show_config_dialog,
            "run": self.run
        }

        mHandlers.update(adex_handlers)
        gbuilder.connect_signals(mHandlers)


    def toggle_CMT(self, button):
        self.con.enable_CMT = button.get_active()

    def show_CMT_dialog(self, button):
        if len(self.con.CMT_file) == 0:
            self.add_CMT_file()

        self.list_CMT_conf.clear()

        options = self.con.CMT_proc.get_options()
        self.liststore_CMT_all = []

        for key in self.con.CMT_proc.heads:
            self.list_CMT_conf.append([key, options[key][0]])
            liststore_CMT_one = Gtk.ListStore(str)
            for item in options[key]:
                liststore_CMT_one.append([item])
            self.liststore_CMT_all.append(liststore_CMT_one)

        self.dialog_CMT.run()

        Gtk.Widget.hide(self.dialog_CMT)

    def change_CMT_cursor(self, widget):
        path = int(widget.get_cursor()[0].to_string())
        self.CMT_combo_render2.set_property("model",
                                            self.liststore_CMT_all[path])

    def on_CMT_combo_changed(self, widget, path, text):
        self.list_CMT_conf[path][1] = text

    def add_CMT_file(self):
        file_dialog = Gtk.FileChooserDialog("Please choose special case file",
                                            self.window,
                                            Gtk.FileChooserAction.SAVE,
                                            (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT,
                                             Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        file_dialog.set_local_only(True)
        response = file_dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            self.con.CMT_file = file_dialog.get_filename()
            self.con.CMT_proc.open_comment_file(self.con.CMT_file)

        file_dialog.destroy()

    def show_config_dialog(self, button):
        self.dialog_config.run()
        Gtk.Widget.hide(self.dialog_config)

    def run(self, button):
        #self.con.ADEX_folders=['/home/hao/Develop/projects/bll/bll_app/test/sample']
        if (len(self.con.ADEX_folders) == 0):
            dialog = Gtk.MessageDialog(self.window,
                                       Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                       Gtk.MessageType.INFO, Gtk.ButtonsType.OK,
                                       "Please choose ADEX folders first!")
            dialog.run()
            dialog.destroy()
            return

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
        self.mCon = controller

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
            "toggle_ADEX_30mins": self.toggle_adex_f30mins,
            "toggle_ADEX_partial": self.toggle_partial_records,
            "toggle_ADEX_naptime": self.toggle_naptime,
            "toggle_ADEX_last2": self.toggle_last2,
            "stop_ADEX_delete": self.stop_delete,
            "hidex_adex_dialog": self.hide,
            "combo_ADEX_time_changed_cb": self.change_partial_time
        }
        return handlers

    # change ADEX configurations
    def toggle_switches(self, widget, path):
        self.list_adex_switch[path][1] = not self.list_adex_switch[path][1]
        self.mCon.adex.switches[int(path)][1] = self.list_adex_switch[path][1]

    def toggle_naptime(self, button):
        self.mCon.adex.config['naptime'] = button.get_active()

    def toggle_adex_f30mins(self, button):
        self.mCon.adex.config['f30mins'] = button.get_active()

    def toggle_partial_records(self, button):
        self.mCon.adex.config['partial_records'] = button.get_active()

    def change_partial_time(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter != None:
            model = combo.get_model()
            ptime = int(model[tree_iter][0].split(' ')[0])
            self.mCon.adex.config['time_interval'] = ptime * 60

    def toggle_last2(self, button):
        self.mCon.adex.config['last2rows'] = button.get_active()

    def stop_delete(self, widget, data):
        return True

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
        if len(self.mCon.adex.config['adex_dirs']) == 0:
            self.mCon.adex.config['adex_dirs'] = self.choose_folders()

        # sync data
        self.list_adex_switch.clear()
        for i in self.mCon.adex.switches:
            self.list_adex_switch.append(i)

        self.f30mins_toggle.set_active(self.mCon.adex.config['f30mins'])
        self.partial_toggle.set_active(self.mCon.adex.config['partial_records'])
        self.naptime_toggle.set_active(self.mCon.adex.config['naptime'])
        self.last2r_toggle.set_active(self.mCon.adex.config['last2rows'])

        time_interval = self.mCon.adex.config['time_interval']
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
        self.mDialog = gbuilder.get_object("dialog_comment")
        self.mCon = controller

        self.record_type = gbuilder.get_object("checkbutton1")
        self.record_type_toggle = gbuilder.get_object("comboboxtext1")

        self.its = gbuilder.get_object("checkbutton2")

        self.notes_in = gbuilder.get_object("checkbutton4")
        self.notes_in_toggle = gbuilder.get_object("comboboxtext8")

        self.PRecord = gbuilder.get_object("checkbutton5")
        self.PRecord_toggle = gbuilder.get_object("comboboxtext6")

        self.language = gbuilder.get_object("checkbutton6")
        self.language_toggle = gbuilder.get_object("comboboxtext2")

        self.sick = gbuilder.get_object("checkbutton7")
        self.sick_toggle = gbuilder.get_object("comboboxtext3")

        self.develop = gbuilder.get_object("checkbutton8")
        self.develop_toggle = gbuilder.get_object("comboboxtext4")

        self.withdraw = gbuilder.get_object("checkbutton9")
        self.withdraw_toggle = gbuilder.get_object("comboboxtext5")


    def show(self, button):
        if len(self.mCon.com.config['filename']) == 0:
            file_dialog = Gtk.FileChooserDialog("Please choose special case file",
                                                self.mDialog,
                                                Gtk.FileChooserAction.SAVE,
                                                (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT,
                                                 Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
            file_dialog.set_local_only(True)
            response = file_dialog.run()

            if response == Gtk.ResponseType.ACCEPT:
                self.mCon.com.config['filename'] = file_dialog.get_filename()
                self.mCon.com.open_comment_file()

            options = self.mCon.com.get_options_from_title("Recording Type")
            for x in options:
                self.record_type_toggle.append(None, x)

            options = self.mCon.com.get_options_from_title("Recording Notes/Errors?")
            for x in options:
                self.notes_in_toggle.append(None, x)

            options = self.mCon.com.get_options_from_title("Paired Recording")
            for x in options:
                self.PRecord_toggle.append(None, x)

            options = self.mCon.com.get_options_from_title("Language Other than English")
            for x in options:
                self.language_toggle.append(None, x)

            options = self.mCon.com.get_options_from_title("Child Sick")
            for x in options:
                self.sick_toggle.append(None, x)

            options = self.mCon.com.get_options_from_title("Child Development Concern")
            for x in options:
                self.develop_toggle.append(None, x)

            options = self.mCon.com.get_options_from_title("Withdrew from Study")
            for x in options:
                self.withdraw_toggle.append(None, x)

            file_dialog.destroy()

        self.record_type_toggle.set_active(0)
        self.notes_in_toggle.set_active(0)
        self.PRecord_toggle.set_active(0)
        self.language_toggle.set_active(0)
        self.sick_toggle.set_active(0)
        self.develop_toggle.set_active(0)
        self.withdraw_toggle.set_active(0)

        self.mDialog.show()
