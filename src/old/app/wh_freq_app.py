## @package app.wh_freq_app

from app.app import App
from ui.wh_freq_app.main_window import MainWindow

## Handles startup for the WH Question app.
class WhFreqApp(App):
    ## Constructor
    # @param self
    def __init__(self):
        super(WhFreqApp, self).__init__(
            'wh_freq_app',
            App.APP_TYPES.GUI,
            'icons/open_icon_library-standard/icons/png/64x64/actions/edit-find-5.png'
            )

    ## See superclass description.
    def start(self):
        MainWindow()
