## @package app.acrp_combine_app

from app.app import App
#you will need to import the module that contains your custom script below:
from custom_scripts.elizabeth.combine import *

## Handles startup for the custom command line scripts (such as thos contained in the bll_app/custom_scripts/ folder).
# Using this class as an entry point for command line scripts gives them access to all of the bll_app classes.
# So for example, you can use the TRSParser class in your command line scripts to read TRS files.
class AcrpCombineApp(App):
    def __init__(self):
        super(AcrpCombineApp, self).__init__(
            'acrp_combine_app',
            App.APP_TYPES.CMD_LINE #this will prevent the superclass from starting up PyGTK
            )

    ## See superclass description. Calling this will start your command line script (if it contains a method called "run").
    def start(self):
        run()
