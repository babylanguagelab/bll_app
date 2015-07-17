## @package launcher
# This module is the main entry point for all bll applications.
# It must be launched with a single command-line arg, the name of the module
# from the app/ directory that is to be run (i.e. which application to run).

import os
import imp
import sys
from functools import reduce
from utils.debug import myDebug

BLL_APP_ROOT_DIR = os.getcwd() + '/'

# this will allow all modules to access bll classes
sys.path.append(BLL_APP_ROOT_DIR)

if len(sys.argv) != 2:
    myDebug('Launcher requires name of module to run (from app/ directory).')
    exit(1)

para = sys.argv[1]

if para == "list":
    myDebug("current programs:")
    app_list = [f for f in os.listdir(BLL_APP_ROOT_DIR + 'app')
                if not f.endswith(".py")]
    for i in app_list:
        myDebug(app_list.index(i), i)
    select = input("select script to run:")
    module_name = app_list[int(select)]
else:
    module_name = para

module_path = '%sapp/%s.py' % (BLL_APP_ROOT_DIR, module_name)
myDebug(module_path)
exit(0)

# attempt to dynamically import the module corresponding to
# the app we are launching
try:
    module = imp.load_source(module_name, module_path)

except Exception as err:
    myDebug('Error loading launch module', module_name, ':', err)
    exit(2)

# the name of the class we will instantiate is the module name,
# with underscores removed, in camel-case
cls_name = reduce(lambda accum, word: accum + word.capitalize(),
                  module_name.split('_'), '')

# instantiate the app class, and call a few methods to get the app running
cls = getattr(module, cls_name)
cur_app = cls()
# do any required setup for the app
cur_app.start()

if cur_app.app_type == App.APP_TYPES.GUI:
    # start the UI (gtk+) event loop.
    cur_app.event_loop()
