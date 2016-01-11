import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from gi.repository import GObject
import logging as lg
from debug import init_debug
from controller import Controller


class MainWindow(GObject.GObject):
    __gsignals__ = {"start_task": (GObject.SIGNAL_RUN_FIRST, None, (int,)),
                    "stop_task": (GObject.SIGNAL_RUN_FIRST, None, (int,))}

    def __init__(self):
        GObject.GObject.__init__(self)
        init_debug()
        self.builder = Gtk.Builder()
        self.builder.add_from_file("UI.glade")
        self.window = self.builder.get_object("win_main")
        self.dia_adex = self.builder.get_object("dia_adex")

        self.list_adex_conf = self.builder.get_object("list_adex_conf")
        treeview_adex_conf = self.builder.get_object("treeview_adex_conf")
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Name", renderer, text=0)
        treeview_adex_conf.append_column(column)

        render_toggle = Gtk.CellRendererToggle()
        render_toggle.connect("toggled", self.toggle_adex_conf)
        column_toogle = Gtk.TreeViewColumn("Choose", render_toggle, active=1)
        treeview_adex_conf.append_column(column_toogle)
        self.adex_naptime_toggle = self.builder.get_object("adex_naptime_check")
        self.adex_5mins_toggle = self.builder.get_object("adex_5mins_check")

        self.initCMT()

        self.run_dialog = self.builder.get_object("g_run_dialog")
        self.connect_signals()

        self.con = Controller()

    def initCMT(self):
        self.CMT_dialog = self.builder.get_object("dialog_comment")
        self.list_CMT_conf = self.builder.get_object("list_comments_conf")
        treeview_conf = self.builder.get_object("treeview_comment_conf")

        text_render = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Name", text_render, text=0)
        treeview_conf.append_column(column)

        toggle_render = Gtk.CellRendererToggle()
        toggle_render.connect("toggled", self.CMT_toggle_conf)
        column_toggle = Gtk.TreeViewColumn("Choose", toggle_render, active=1)
        treeview_conf.append_column(column_toggle)

    def do_start_task(self, data):
        self.emit("stop_task", 0)

    def do_stop_task(self, data):
        self.run_dialog.hide()

    def connect_signals(self):
        handlers = {
            "quit_main": Gtk.main_quit,
            "config_adex": self.config_adex,
            "add_adex_folders": self.add_adex_files,
            "adex_use_naptime": self.adex_use_naptime,
            "adex_remove_5mins": self.adex_remove_5mins,
            "show_comment_dialog": self.CMT_show_dialog,
            "add_comment_file": self.CMT_add_file,
            "g_run_configs": self.run
        }
        self.builder.connect_signals(handlers)

    # ADEX configuration dialog
    def config_adex(self, button):

        self.list_adex_conf.clear()

        # sync with controller
        for i in self.con.ADEX_proc.switches:
            self.list_adex_conf.append(i)

        if self.con.ADEX_proc.removeNaptime:
            self.adex_naptime_toggle.set_active(True)

        if self.con.ADEX_proc.remove5mins:
            self.adex_5mins_toggle.set_active(True)

        self.dia_adex.run()

        # sync with controller
        switches = []
        for row in self.list_adex_conf:
            switches.append(row[1])
        self.con.ADEX_proc.setSwitches(switches)

        Gtk.Widget.hide(self.dia_adex)

    # ADEX folders choose dialog
    def add_adex_files(self, button):
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
    def toggle_adex_conf(self, widget, path):
        self.list_adex_conf[path][1] = not self.list_adex_conf[path][1]

    def adex_use_naptime(self, button):
        self.con.ADEX_proc.removeNaptime = button.get_active()

    def adex_remove_5mins(self, button):
        self.con.ADEX_proc.remove5mins = button.get_active()

    def CMT_show_dialog(self, button):
        self.list_CMT_conf.clear()

        # sync with controller
        for i in self.con.CMT_proc.switches:
            self.list_CMT_conf.append(i)

        self.CMT_dialog.run()

        switches = []

        for row in self.list_CMT_conf:
            switches.append(row[1])
        self.con.CMT_proc.setSwitches(switches)

        Gtk.Widget.hide(self.CMT_dialog)

    def CMT_add_file(self, button):
        file_dialog = Gtk.FileChooserDialog("Please choose special case file",
                                            self.window,
                                            Gtk.FileChooserAction.SAVE,
                                            (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT,
                                             Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        file_dialog.set_local_only(True)
        response = file_dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            self.con.CMT_proc.openCommentFile(file_dialog.get_filename())

        file_dialog.destroy()

    def CMT_toggle_conf(self, widget, path):
        self.list_CMT_conf[path][1] = not self.list_CMT_conf[path][1]

    # run on all configurations
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
            self.con.saveOutput(save_dialog.get_filename())

        save_dialog.destroy()
        #self.con.saveOutput('/home/hao/Develop/projects/bll/bll_app/test/sample/output.xlsx')

    def show(self):
        self.window.show_all()
        Gtk.main()

mMain = MainWindow()
mMain.show()
