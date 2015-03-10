from gi.repository import Gtk as gtk

from utils.ui_utils import UIUtils
from ui.reliability2_app.create_check_window import CreateCheckWindow
from ui.reliability2_app.load_window import LoadWindow

class MainWindow():
    def __init__(self):
        self.window = gtk.Window(gtk.WindowType.TOPLEVEL)
        self.window.set_title('Reliability App 2')
        self.window.connect('destroy', lambda x: gtk.main_quit())
        self.window.set_border_width(10)
        self.window.set_default_size(210, 100)
                                         
        box = gtk.VBox(False, 5)

        create_button = UIUtils.create_button('New', UIUtils.BUTTON_ICONS.CREATE)
        create_button.connect('clicked', lambda w: CreateCheckWindow())
        box.pack_start(create_button, False, False, 0)

        load_button = UIUtils.create_button('Load', UIUtils.BUTTON_ICONS.OPEN)
        load_button.connect('clicked', lambda w: LoadWindow())
        box.pack_start(load_button, False, False, 0)

        exit_button = UIUtils.create_button('Exit', UIUtils.BUTTON_ICONS.EXIT)
        exit_button.connect('clicked', lambda widget: gtk.main_quit())
        box.pack_start(exit_button, False, False, 0)

        self.window.add(box)
        self.window.show_all()
