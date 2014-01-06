import os
import sys
import time
starttime = time.time()

import cherrypy


class Root:

    def index(self):
        return "Hello World"
    index.exposed = True

    def mtimes(self):
        return repr(cherrypy.engine.publish("Autoreloader", "mtimes"))
    mtimes.exposed = True

    def pid(self):
        return str(os.getpid())
    pid.exposed = True

    def start(self):
        return repr(starttime)
    start.exposed = True

    def exit(self):
        # This handler might be called before the engine is STARTED if an
        # HTTP worker thread handles it before the HTTP server returns
        # control to engine.start. We avoid that race condition here
        # by waiting for the Bus to be STARTED.
        cherrypy.engine.wait(state=cherrypy.engine.states.STARTED)
        cherrypy.engine.exit()
    exit.exposed = True


def unsub_sig():
    cherrypy.log("unsubsig: %s" % cherrypy.config.get('unsubsig', False))
    if cherrypy.config.get('unsubsig', False):
        cherrypy.log("Unsubscribing the default cherrypy signal handler")
        cherrypy.engine.signal_handler.unsubscribe()
    try:
        from signal import signal, SIGTERM
    except ImportError:
        pass
    else:
        def old_term_handler(signum=None, frame=None):
            cherrypy.log("I am an old SIGTERM handler.")
            sys.exit(0)
        cherrypy.log("Subscribing the new one.")
        signal(SIGTERM, old_term_handler)
cherrypy.engine.subscribe('start', unsub_sig, priority=100)


def starterror():
    if cherrypy.config.get('starterror', False):
        zerodiv = 1 / 0
cherrypy.engine.subscribe('start', starterror, priority=6)

def log_test_case_name():
    if cherrypy.config.get('test_case_name', False):
        cherrypy.log("STARTED FROM: %s" % cherrypy.config.get('test_case_name'))
cherrypy.engine.subscribe('start', log_test_case_name, priority=6)


cherrypy.tree.mount(Root(), '/', {'/': {}})
