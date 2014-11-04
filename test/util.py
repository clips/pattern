# -*- coding: utf-8 -*-
import codecs
import datetime
import math
import os
import random
import re
import subprocess
import sys
import time
import warnings

try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO
try:
    import unittest2 as unittest
except ImportError:
    import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from pattern import nl

try:
    PATH = os.path.dirname(os.path.realpath(__file__))
except:
    PATH = ""