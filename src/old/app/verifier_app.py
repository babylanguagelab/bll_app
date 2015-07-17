## @package app.verifier_app

from app.app import App
from ui.verifier_app.main_window import MainWindow

## Handles startup for the transcription verifier app.
class VerifierApp(App):
    ## Constructor
    # @param self
    def __init__(self):
        super(VerifierApp, self).__init__(
            'verifier_app',
            App.APP_TYPES.GUI,
            'icons/open_icon_library-standard/icons/png/64x64/apps/kaddressbook-4.png'
            )

    ## See superclass description.
    def start(self):
        MainWindow()
