## @package launcher
# This module is the main entry point for all bll applications.
# It must be launched with a single command-line arg, the name of the module
# from the app/ directory that is to be run (i.e. which application to run).

import os
import imp
import sys
from app.app import App

BLL_APP_ROOT_DIR = os.getcwd() + '/'

# this will allow all modules to access bll classes
sys.path.append(BLL_APP_ROOT_DIR)

if len(sys.argv) != 2:
    print 'Launcher requires name of module to run (from app/ directory).'
    exit(1)

module_name = sys.argv[1]
module_path = '%sapp/%s.py' % (BLL_APP_ROOT_DIR, module_name)
#the name of the class we will instantiate is the module name, with underscores removed, in camel-case
cls_name = reduce(lambda accum, word: accum + word.capitalize(), module_name.split('_'), '')

#attempt to dynamically import the module corresponding to the app we are launching
try:
    print module_path
    module = imp.load_source(module_name, module_path)
    
except Exception as err:
    print 'Error loading launch module "%s": %s' % (module_name, err)
    exit(2)

#instantiate the app class, and call a few methods to get the app running
cls = getattr(module, cls_name)
cur_app = cls()
#do any required setup for the app
cur_app.start()

if cur_app.app_type == App.APP_TYPES.GUI:
    #start the UI (gtk+) event loop to accept input from the keyboard, mouse, etc.
    cur_app.event_loop()

