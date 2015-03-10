## @package app.reliability_app

from app.app import App
from ui.data_viewer_app.main_window import MainWindow

## Handles startup for the data viewer app.
class DataViewerApp(App):
    ## Constructor
    # @param self
    def __init__(self):
        super(DataViewerApp, self).__init__(
            'data_viewer_app',
            App.APP_TYPES.GUI,
            'icons/open_icon_library-standard/icons/png/64x64/categories/applications-office-4.png'
            )

    ## See superclass description.
    def start(self):
        MainWindow()
