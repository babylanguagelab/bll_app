## @package app.reliability2_app

from app.app import App
from ui.reliability2_app.main_window import MainWindow

## Handles startup for the reliability2 app.
class Reliability2App(App):
    ## Constructor
    # @param self
    def __init__(self):
        super(Reliability2App, self).__init__(
            'reliability2_app',
            App.APP_TYPES.GUI,
            'icons/open_icon_library-standard/icons/png/64x64/apps/achilles.png'
            )

    ## See superclass description.
    def start(self):
        MainWindow()
