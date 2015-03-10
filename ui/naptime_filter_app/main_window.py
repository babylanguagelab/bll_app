from gi.repository import Gtk as gtk
from ui.naptime_filter_app.filter_window import FilterWindow
from ui.naptime_filter_app.db_window import DBWindow
from utils.ui_utils import UIUtils

class MainWindow():
    def __init__(self):
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Naptime Filter')
        self.window.connect('destroy', lambda x: gtk.main_quit())
        self.window.set_border_width(10)
        self.window.set_default_size(210, 150)
                                         
        box = gtk.VBox(False, 5)
        update_button = UIUtils.create_button('Update Database', UIUtils.BUTTON_ICONS.UPDATE)
        update_button.connect('clicked', lambda widget, data=None: DBWindow())
        box.pack_start(update_button, False, False, 0)
        update_button.show()

        filter_file_button = UIUtils.create_button('Filter File', UIUtils.BUTTON_ICONS.CREATE)
        filter_file_button.connect('clicked', lambda widget, data=None: self._filter_file())
        box.pack_start(filter_file_button, False, False, 0)
        filter_file_button.show()

        filter_folder_button = UIUtils.create_button('Filter Folder', UIUtils.BUTTON_ICONS.OPEN)
        filter_folder_button.connect('clicked', lambda widget, data=None: self._filter_folder())
        box.pack_start(filter_folder_button, False, False, 0)
        filter_folder_button.show()

        exit_button = UIUtils.create_button('Exit', UIUtils.BUTTON_ICONS.EXIT)
        exit_button.connect('clicked', lambda widget: gtk.main_quit())
        box.pack_start(exit_button, False, False, 0)
        exit_button.show()

        self.window.add(box)
        box.show()
        self.window.show()

    def _filter_file(self):
        FilterWindow(FilterWindow.FILTER_TYPES.FILE)

    def _filter_folder(self):
        FilterWindow(FilterWindow.FILTER_TYPES.FOLDER)
