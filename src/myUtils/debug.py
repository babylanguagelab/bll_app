# compatible API between python2 and python3
from __future__ import print_function
import sys
import logging


def check_version():
    logging.info("python version: " + sys.version[:6])

def log_init(lFile=None):
    if (lFile):
        logging.basicConfig(filename=lFile,
                            level=logging.WARNING,
                            format='%(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(levelname)s|m:%(module)s|l:%(lineno)d|msg:%(message)s')

def debug_init(level=1):
    # for release
    if level == 0:
        log_init('BLL.log')
    # for development
    else:
        log_init()

    check_version()
