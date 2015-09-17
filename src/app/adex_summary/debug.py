# compatible API between python2 and python3

from __future__ import print_function
import sys


def check_version():
    return sys.version[0]


def my_print(*args, **kwargs):
    print(args, kwargs)
