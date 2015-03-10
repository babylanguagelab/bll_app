from gi.repository import Gtk as gtk
from ui.reliability_app.create_window import CreateWindow
from ui.reliability_app.load_window import LoadWindow
from utils.ui_utils import UIUtils

class MainWindow():
    def __init__(self):
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Reliability App')
        self.window.connect('destroy', lambda x: gtk.main_quit())
        self.window.set_border_width(10)
        self.window.set_default_size(210, 150)
                                         
        box = gtk.VBox(False, 5)
        create_button = UIUtils.create_button('Create Check', UIUtils.BUTTON_ICONS.CREATE)
        create_button.connect('clicked', lambda widget, data=None: CreateWindow())
        box.pack_start(create_button, False, False, 0)
        create_button.show()

        load_button = UIUtils.create_button('Load Check', UIUtils.BUTTON_ICONS.RUN)
        load_button.connect('clicked', lambda widget, data=None: LoadWindow())
        box.pack_start(load_button, False, False, 0)
        load_button.show()

        exit_button = UIUtils.create_button('Exit', UIUtils.BUTTON_ICONS.EXIT)
        exit_button.connect('clicked', lambda widget: gtk.main_quit())
        box.pack_start(exit_button, False, False, 0)
        exit_button.show()

        self.window.add(box)
        box.show()
        self.window.show()

