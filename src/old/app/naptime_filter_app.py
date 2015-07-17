## @package app.naptime_filter_app

from app.app import App
from ui.naptime_filter_app.main_window import MainWindow

## Handles startup for the Naptime Filter app.
class NaptimeFilterApp(App):
    ## Constructor
    # @param self
    def __init__(self):
        super(NaptimeFilterApp, self).__init__(
            'naptime_filter_app',
            App.APP_TYPES.GUI,
            'icons/open_icon_library-standard/icons/png/64x64/apps/kalarm-3.png'
            )

    ## See superclass description.
    def start(self):
        MainWindow()
