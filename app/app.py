## @package app.app

from gi.repository import Gtk as gtk
from utils.backend_utils import BackendUtils
from utils.ui_utils import UIUtils
from utils.enum import Enum

## This is the "abstract" superclass of all _app classes.
# There is one subclass for each bll application. The launcher
# module instantiates the appropriate subclass to start the application.
# This provides a single entry point (the launcher module) for
# all applications. Subclasses should override the start method to do
# whatever they need to do to start the app.


class App(object):
    APP_TYPES = Enum('GUI CMD_LINE'.split())

    ## Constructor
    # @param self
    # @param app_name (string) module name (name of a file from the app/ directory) of the app being started
    # @param app_type (int) a value from the static enum App.APP_TYPES, indicating whether or not to initialize GUI stuff.
    # @param app_icon_filename (string=None) path to the icon to use for this application (pass None if this is not a GUI-based app). This icon will be shown in the upper left corner of the title bar of all windows. The path may be absolute, or may be relative to the directory from which launcher.py is being called (typically this is the same directory that is specified by the BLL_APP_ROOT_DIR constant in launcher.py).
    def __init__(self, app_name, app_type, app_icon_filename=None):
        self.app_type = app_type

        BackendUtils.setup_logging(
            'logs/%s.log' % (app_name)
            )

        if app_type == App.APP_TYPES.GUI:
            # this sets some project-wide GTK settings and
            # sets the app-specific window icon
            UIUtils.setup_gtk(app_icon_filename)

    ## This method must be overridden by subclasses to
    # launch their main startup code.
    # @param self
    def start(self):
        pass

    ## This method starts the gtk+ event loop. This causes the app to start accepting input from input devices like the keyboard and mouse. launcher.py only calls this if the app instance is App.APP_TYPES.GUI
    def event_loop(self):
        gtk.main()
