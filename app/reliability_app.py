## @package app.reliability_app

from app.app import App
from ui.reliability_app.main_window import MainWindow

## Handles startup for the reliability app.
class ReliabilityApp(App):
    ## Constructor
    # @param self
    def __init__(self):
        super(ReliabilityApp, self).__init__(
            'reliability_app',
            App.APP_TYPES.GUI,
            'icons/open_icon_library-standard/icons/png/64x64/apps/education-science.png'
            )

    ## See superclass description.
    def start(self):
        MainWindow()
