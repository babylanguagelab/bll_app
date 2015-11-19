#!/usr/bin/python2
# This module is the main entry point for all bll applications.

from __future__ import print_function
import os
import imp
import sys

# include the common library in src
BLL_APP_ROOT_DIR = os.getcwd() + '/src'

# this will allow all modules to access bll scripts
sys.path.append(BLL_APP_ROOT_DIR)

if len(sys.argv) < 2:
    print("Launcher requires the name of module to run (from app/ directory).")
    print("Or use '-l' to show all scripts")
    exit(1)

para = sys.argv[1]

if para == "-l":
    print("CURRENT PROGRAMS:")
    app_list = [f for f in os.listdir(BLL_APP_ROOT_DIR+"/app")
                if (f[0] != '_')]
    for i in app_list:
        print(app_list.index(i), i)
    select = input("SELECT WHICH SCRIPT TO RUN (NUMBER): ")
    module_name = app_list[int(select)].split('.')[0]
else:
    # [Todo] Check module name exist
    module_name = para

# include all files in the specific app folder
sys.path.append(BLL_APP_ROOT_DIR + "/app/" + module_name)

module_path = '%s/app/%s/main.py' % (BLL_APP_ROOT_DIR, module_name)
# attempt to dynamically import the module corresponding to
# the app we are launching
module = imp.load_source("main", module_path)

app = getattr(module, "main")
mApp = app()
mApp.run()
