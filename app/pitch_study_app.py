## @package app.pitch_study_app

from app.app import App
from ui.pitch_study_app.main_window import MainWindow

## Handles startup for the mel_testing app.
class PitchStudyApp(App):
    ## Constructor
    # @param self
    def __init__(self):
        super(PitchStudyApp, self).__init__(
            'pitch_study_app',
            App.APP_TYPES.GUI,
            'icons/open_icon_library-standard/icons/png/48x48/apps/soundconverter.png'
            )

    ## See superclass description.
    def start(self):
        MainWindow()
