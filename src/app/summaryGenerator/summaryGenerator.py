# Description: main entry point
# Author: zhangh15@myumanitoba.ca
# Date: 2016-07-17

import logging as lg
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from myUtils.debug import init_debug
from controller import controller


class mainWindow(object):
    def __init__(self):
        self.con = controller()

        builder = Gtk.Builder()
        builder.add_from_file("UI.glade")
        self.window = builder.get_object("win_main")

        self.init_ADEX_dialog(builder)
        self.init_CMT_dialog(builder)
        self.init_config_dialog(builder)

        self.run_dialog = builder.get_object("g_run_dialog")
        self.connect_signals(builder)

    def init_ADEX_dialog(self, gbuilder):
        self.dialog_ADEX = gbuilder.get_object("dialog_ADEX")

        self.list_ADEX_switch = gbuilder.get_object("list_ADEX_switch")
        treeview_ADEX_switch = gbuilder.get_object("treeview_ADEX_switch")

        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Name", renderer, text=0)
        treeview_ADEX_switch.append_column(column)

        render_toggle = Gtk.CellRendererToggle()
        render_toggle.connect("toggled", self.toggle_ADEX_switches)
        column_toogle = Gtk.TreeViewColumn("Choose", render_toggle, active=1)
        treeview_ADEX_switch.append_column(column_toogle)

        self.combo_time = gbuilder.get_object("combo_ADEX_time")
        list_time_interval = gbuilder.get_object("list_ADEX_time")
        list_time_interval.append(["5 minutes"])
        list_time_interval.append(["10 minutes"])
        list_time_interval.append(["30 minutes"])
        list_time_interval.append(["60 minutes"])
        renderer_text = Gtk.CellRendererText()
        self.combo_time.pack_start(renderer_text, True)
        self.combo_time.add_attribute(renderer_text, "text", 0)
        self.combo_time.set_active(0)

        self.adex_30mins_toggle = gbuilder.get_object("adex_30mins_check")
        self.adex_partial_toggle = gbuilder.get_object("adex_partial_check")
        self.adex_naptime_toggle = gbuilder.get_object("adex_naptime_check")
        self.adex_last2_toggle = gbuilder.get_object("adex_last2_check")

    def init_CMT_dialog(self, gbuilder):
        self.dialog_CMT = gbuilder.get_object("dialog_comment")
        self.list_CMT_conf = gbuilder.get_object("list_comments_conf")
        treeview_conf = gbuilder.get_object("treeview_comment_conf")

        text_render = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Name", text_render, text=0)
        treeview_conf.append_column(column)

        toggle_render = Gtk.CellRendererToggle()
        toggle_render.connect("toggled", self.toggle_CMT_switches)
        column_toggle = Gtk.TreeViewColumn("Choose", toggle_render, active=1)
        treeview_conf.append_column(column_toggle)

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
        handlers = {
            "quit_main": Gtk.main_quit,
            "show_ADEX_dialog": self.show_ADEX_dialog,
            "add_ADEX_folders": self.add_ADEX_folders,
            "toggle_ADEX_naptime": self.toggle_ADEX_naptime,
            "toggle_ADEX_partial": self.toggle_partial_records,
            "toggle_ADEX_30mins": self.toggle_ADEX_30mins,
            "toggle_ADEX_last2": self.toggle_ADEX_last2,
            "combo_ADEX_time_changed_cb": self.change_ADEX_time,
            "check_CMT_toggled_cb": self.toggle_CMT,
            "show_CMT_dialog": self.show_CMT_dialog,
            "add_CMT_file": self.add_CMT_file,
            "show_config_dialog": self.show_config_dialog,
            "run": self.run
        }
        gbuilder.connect_signals(handlers)

    # ADEX configuration dialog
    def show_ADEX_dialog(self, button):

        self.list_ADEX_switch.clear()
        # sync with controller
        for i in self.con.ADEX_proc.switches:
            self.list_ADEX_switch.append(i)

        if self.con.ADEX_proc.no_naptime:
            self.adex_naptime_toggle.set_active(True)

        if self.con.ADEX_proc.no_30mins:
            self.adex_30mins_toggle.set_active(True)

        self.dialog_ADEX.run()

        # sync with controller
        switches = []
        for row in self.list_ADEX_switch:
            switches.append(row[1])
        self.con.ADEX_proc.set_switches(switches)

        Gtk.Widget.hide(self.dialog_ADEX)

    # ADEX folders choose dialog
    def add_ADEX_folders(self, button):
        dialog = Gtk.FileChooserDialog("Please choose ADEX folders",
                                       self.window,
                                       Gtk.FileChooserAction.SELECT_FOLDER,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        dialog.set_select_multiple(True)
        dialog.set_local_only(True)
        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            self.con.ADEX_folders = dialog.get_filenames()

        dialog.destroy()

    # change ADEX configurations
    def toggle_ADEX_switches(self, widget, path):
        self.list_ADEX_switch[path][1] = not self.list_adex_conf[path][1]

    def change_ADEX_time(self, combo):
        tree_iter = combo.get_active_iter()
        if tree_iter != None:
            model = combo.get_model()
            select = model[tree_iter][0]
            self.con.ADEX_proc.time_interval = select

    def toggle_ADEX_30mins(self, button):
        self.con.ADEX_proc.no_30mins = button.get_active()

    def toggle_partial_records(self, button):
        self.con.ADEX_proc.no_partial = button.get_active()

    def toggle_ADEX_naptime(self, button):
        self.con.ADEX_proc.no_naptime = button.get_active()

    def toggle_ADEX_last2(self, button):
        self.con.ADEX_proc.no_last2rows = button.get_active()

    def toggle_CMT(self, button):
        self.con.enable_CMT = button.get_active()

    def show_CMT_dialog(self, button):
        self.list_CMT_conf.clear()

        # sync with controller
        for i in self.con.CMT_proc.switches:
            self.list_CMT_conf.append(i)

        self.dialog_CMT.run()

        switches = []

        for row in self.list_CMT_conf:
            switches.append(row[1])
        self.con.CMT_proc.set_switches(switches)

        Gtk.Widget.hide(self.dialog_CMT)

    def add_CMT_file(self, button):
        file_dialog = Gtk.FileChooserDialog("Please choose special case file",
                                            self.window,
                                            Gtk.FileChooserAction.SAVE,
                                            (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT,
                                             Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        file_dialog.set_local_only(True)
        response = file_dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            self.con.CMT_proc.open_comment_file(file_dialog.get_filename())

        file_dialog.destroy()

    def toggle_CMT_switches(self, widget, path):
        self.list_CMT_conf[path][1] = not self.list_CMT_conf[path][1]

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

        self.run_dialog.show_all()
        while(Gtk.events_pending()):
            Gtk.main_iteration()

        self.con.run()
        self.run_dialog.hide()

        save_dialog = Gtk.FileChooserDialog("Please choose where to save output",
                                            self.window,
                                            Gtk.FileChooserAction.SAVE,
                                            (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT,
                                             Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        save_dialog.set_local_only(True)
        response = save_dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            self.con.save_output(save_dialog.get_filename())

        save_dialog.destroy()
        #self.con.saveOutput('/home/hao/Develop/projects/bll/bll_app/test/sample/output.xlsx')

    def show(self):
        self.window.show_all()
        Gtk.main()

class main(object):
    def __init__(self):
        init_debug()
        self.mWin = mainWindow()

    def run(self):
        self.mWin.show()
