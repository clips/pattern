LIBSVM = LIBLINEAR = True

try:
    import libsvm
    import libsvmutil
except ImportError, e:
    LIBSVM = False
    raise e
    
try:
    import liblinear
    import liblinearutil
except:
    LIBLINEAR = False