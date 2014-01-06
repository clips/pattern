"""Regression test suite for CherryPy.

Run 'nosetests -s test/' to exercise all tests.

The '-s' flag instructs nose to output stdout messages, wihch is crucial to
the 'interactive' mode of webtest.py. If you run these tests without the '-s'
flag, don't be surprised if the test seems to hang: it's waiting for your
interactive input.
"""

import os
import sys

def newexit():
    os._exit(1)

def setup():
    # We want to monkey patch sys.exit so that we can get some
    # information about where exit is being called.
    newexit._old = sys.exit
    sys.exit = newexit

def teardown():
    try:
        sys.exit = sys.exit._old
    except AttributeError:
        sys.exit = sys._exit
