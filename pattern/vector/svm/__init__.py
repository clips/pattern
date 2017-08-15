from __future__ import absolute_import
from __future__ import division

LIBSVM = LIBLINEAR = True

try:
    from . import libsvm
    from . import libsvmutil
except ImportError as e:
    LIBSVM = False
    raise e

try:
    from . import liblinear
    from . import liblinearutil
except:
    LIBLINEAR = False
