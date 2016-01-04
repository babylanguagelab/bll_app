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

        # adex switches tree view
        treeview_adex_conf = self.builder.get_object("treeview_adex_conf")
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Name", renderer, text=0)
        treeview_adex_conf.append_column(column)

        render_toggle = Gtk.CellRendererToggle()
        render_toggle.connect("toggled", self.toggle_adex_conf)
        column_toogle = Gtk.TreeViewColumn("Choose", render_toggle, active=1)
        treeview_adex_conf.append_column(column_toogle)

        self.run_dialog = self.builder.get_object("g_run_dialog")
        self.connect_signals()

        self.controller = Controller()

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
            "g_run_finish": self.run_finish,
            "g_run_configs": self.run_configs
        }
        self.builder.connect_signals(handlers)

    # ADEX configuration dialog
    def config_adex(self, button):
        adex_head_name_list = ['File_Name', 'Number_Recordings', 'File_Hours',
                               'Child_ChildID', 'Child_Age', 'Child_Gender',
                               'AWC', 'Turn_Count', 'Child_Voc_Duration',
                               'FAN_Word_Count', 'FAN', 'MAN_Word_Count', 'MAN',
                               'CXN', 'OLN', 'TVN', 'NON', 'SIL', 'Clock_Time_TZAdj',
                               'Audio_Duration']

        # sync with controller
        self.list_adex_conf.clear()
        configs = zip(adex_head_name_list,
                      self.controller.adex_control.switches)
        for i in configs:
            self.list_adex_conf.append(list(i))

        self.dia_adex.run()

        result = []
        for row in self.list_adex_conf:
            result.append(row[1])
        self.controller.adex_control.switches = result

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
            self.controller.ADEX_folders = dialog.get_filenames()

        dialog.destroy()

    # change ADEX configurations
    def toggle_adex_conf(self, widget, path):
        self.list_adex_conf[path][1] = not self.list_adex_conf[path][1]

    def adex_use_naptime(self, button):
        if button.get_active():
            self.controller.adex_control.set_use_naptime(True)
        else:
            self.controller.adex_control.set_use_naptime(False)

    def adex_remove_5mins(self, button):
         if button.get_active():
            self.controller.adex_control.set_remove_5mins(True)
         else:
            self.controller.adex_control.set_remove_5mins(False)

    # run on all configurations
    def run_configs(self, button):
        if (len(self.controller.ADEX_folders) == 0):
            dialog = Gtk.MessageDialog(self.window,
                                       Gtk.DialogFlags.DESTROY_WITH_PARENT,
                                       Gtk.MessageType.INFO, Gtk.ButtonsType.OK,
                                       "Please choose ADEX folders first!")
            dialog.run()
            dialog.destroy()
            return

        save_dialog = Gtk.FileChooserDialog("Please choose where to save output",
                                       self.window,
                                       Gtk.FileChooserAction.SAVE,
                                       (Gtk.STOCK_OK, Gtk.ResponseType.ACCEPT,
                                        Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL))
        save_dialog.set_local_only(True)
        response = save_dialog.run()

        if response == Gtk.ResponseType.ACCEPT:
            self.controller.output_file = save_dialog.get_filename()

        save_dialog.destroy()
        if not self.controller.output_file:
            lg.error("You haven't choose the place for output yet!")
            return

        self.run_dialog.show_all()
        while(Gtk.events_pending()):
            Gtk.main_iteration()

        self.controller.run()
        self.emit("start-task", 0)

    def run_finish(self, button):
        self.run_dialog.hide()

    def show(self):
        self.window.show_all()
        Gtk.main()

mMain = MainWindow()
mMain.show()
