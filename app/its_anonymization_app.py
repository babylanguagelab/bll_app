## @package app.verifier_app

from app.app import App
from ui.its_anonymization_app.main_window import MainWindow

## Handles startup for the transcription verifier app.
class ItsAnonymizationApp(App):
    ## Constructor
    # @param self
    def __init__(self):
        super(ItsAnonymizationApp, self).__init__(
            'its_anonymization_app',
            App.APP_TYPES.GUI,
            'icons/open_icon_library-standard/icons/png/64x64/apps/kaddressbook-4.png'
            )

    ## See superclass description.
    def start(self):
        MainWindow()
