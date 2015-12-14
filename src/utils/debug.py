# compatible API between python2 and python3
from __future__ import print_function
import sys
import logging


def check_version():
    logging.info("python version: " + sys.version[:6])

def init_log(lFile=None):
    if (lFile):
        logging.basicConfig(filename=lFile,
                            level=logging.WARNING,
                            format='%(levelname)s - %(message)s')
    else:
        logging.basicConfig(level=logging.DEBUG,
                            format='%(levelname)s|m:%(module)s|l:%(lineno)d|msg:%(message)s')

def init_debug(level=1):
    # for release
    if level == 0:
        init_log('log')
    # for development
    else:
        init_log()

    check_version()
