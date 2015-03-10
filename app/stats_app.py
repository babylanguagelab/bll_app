## @package app.stats_app

from app.app import App
from ui.stats_app.view_configs_window import ViewConfigsWindow

## Handles startup for the statistics app.
class StatsApp(App):
    ## Constructor
    # @param self
    def __init__(self):
        super(StatsApp, self).__init__(
            'stats_app',
            App.APP_TYPES.GUI,
            'icons/open_icon_library-standard/icons/png/64x64/apps/gnumeric.png'
            )

    ## See superclass description.
    def start(self):
        ViewConfigsWindow()
