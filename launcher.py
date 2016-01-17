# Description: This module is the main entry point for all bll applications.
# Author: zhangh15@myumanitoba.ca
# Date: 2016-01-17

from __future__ import print_function
import os
import sys

# include the common library in src
BLL_LIB_DIR = os.getcwd() + '/src/'

# this will allow all modules to access BLL libraries 
sys.path.append(BLL_LIB_DIR)

BLL_APP_ROOT_DIR = os.getcwd() + '/src'

if len(sys.argv) < 2:
    print("Launcher requires the name of module to run (in app/ directory).")
    print("Or use '-l' to show all scripts")
    exit(1)

para = sys.argv[1]

if para == "-l":
    print("CURRENT APPS:")
    app_list = [f for f in os.listdir(BLL_APP_ROOT_DIR+"/app")
                if (f[0] != '_')]
    for i in app_list:
        print(app_list.index(i), i)
    select = input("SELECT WHICH SCRIPT TO RUN (NUMBER): ")
    module_name = app_list[int(select)].split('.')[0]
else:
    module_name = para

# include all files in the specific app folder
sys.path.append(BLL_APP_ROOT_DIR + "/app/" + module_name)

module_path = '%s/app/%s/' % (BLL_APP_ROOT_DIR, module_name)
os.chdir(module_path)

# attempt to dynamically import the module corresponding to
# the app we are launching
module = __import__(module_name)
main_class = getattr(module, "main")
mApp = main_class()
mApp.run()
