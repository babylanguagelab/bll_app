## @package app.splitter_app

from app.app import App
from ui.splitter_app.main_window import MainWindow

## Handles startup for the TRS file splitting app.
class SplitterApp(App):
        ## Constructor
        # @param self
        def __init__(self):
                super(SplitterApp, self).__init__(
                        'splitter_app',
                        App.APP_TYPES.GUI,
                        'icons/open_icon_library-standard/icons/png/64x64/actions/edit-destroy.png'
                        )

        ## See superclass description
        def start(self):
                MainWindow()
