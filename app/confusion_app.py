## @package app.custom_app

from app.app import App

import custom_scripts.reliability.rel_conf_mat.confusion as confusion
import custom_scripts.reliability.rel_conf_mat.matrix_adder as adder
import custom_scripts.reliability.rel_conf_mat.matrix_spacer as spacer

## Handles startup for the custom command line scripts (such as thos contained in the bll_app/custom_scripts/ folder).
# Using this class as an entry point for command line scripts gives them access to all of the bll_app classes.
# So for example, you can use the TRSParser class in your command line scripts to read TRS files.
class ConfusionApp(App):
    def __init__(self):
        super(ConfusionApp, self).__init__(
            'confusion_app',
            App.APP_TYPES.CMD_LINE #this will prevent the superclass from starting up PyGTK
            )

    ## See superclass description. Calling this will start your command line script (if it contains a method called "run").
    def start(self):
        print 'Running confusion.py'
        confusion.run()
        
        # print '\nRunning matrix_adder.py'
        # adder.run()

        # print '\nRunning matrix_spacer.py'
        # spacer.run()
