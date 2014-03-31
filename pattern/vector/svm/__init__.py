LIBSVM = LIBLINEAR = True

try:
    import libsvm
    import libsvmutil
except ImportError as e:
    LIBSVM = False
    raise e
    
try:
    import liblinear
    import liblinearutil
except:
    LIBLINEAR = False