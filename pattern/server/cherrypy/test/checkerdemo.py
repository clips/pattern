"""Demonstration app for cherrypy.checker.

This application is intentionally broken and badly designed.
To demonstrate the output of the CherryPy Checker, simply execute
this module.
"""

import os
import cherrypy
thisdir = os.path.dirname(os.path.abspath(__file__))

class Root:
    pass

if __name__ == '__main__':
    conf = {'/base': {'tools.staticdir.root': thisdir,
                      # Obsolete key.
                      'throw_errors': True,
                      },
            # This entry should be OK.
            '/base/static': {'tools.staticdir.on': True,
                        'tools.staticdir.dir': 'static'},
            # Warn on missing folder.
            '/base/js': {'tools.staticdir.on': True,
                    'tools.staticdir.dir': 'js'},
            # Warn on dir with an abs path even though we provide root.
            '/base/static2': {'tools.staticdir.on': True,
                         'tools.staticdir.dir': '/static'},
            # Warn on dir with a relative path with no root.
            '/static3': {'tools.staticdir.on': True,
                         'tools.staticdir.dir': 'static'},
            # Warn on unknown namespace
            '/unknown': {'toobles.gzip.on': True},
            # Warn special on cherrypy.<known ns>.*
            '/cpknown': {'cherrypy.tools.encode.on': True},
            # Warn on mismatched types
            '/conftype': {'request.show_tracebacks': 14},
            # Warn on unknown tool.
            '/web': {'tools.unknown.on': True},
            # Warn on server.* in app config.
            '/app1': {'server.socket_host': '0.0.0.0'},
            # Warn on 'localhost'
            'global': {'server.socket_host': 'localhost'},
            # Warn on '[name]'
            '[/extra_brackets]': {},
            }
    cherrypy.quickstart(Root(), config=conf)
