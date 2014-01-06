"""
Tutorial - Sessions

Storing session data in CherryPy applications is very easy: cherrypy
provides a dictionary called "session" that represents the session
data for the current user. If you use RAM based sessions, you can store
any kind of object into that dictionary; otherwise, you are limited to
objects that can be pickled.
"""

import cherrypy


class HitCounter:

    _cp_config = {'tools.sessions.on': True}

    def index(self):
        # Increase the silly hit counter
        count = cherrypy.session.get('count', 0) + 1

        # Store the new value in the session dictionary
        cherrypy.session['count'] = count

        # And display a silly hit count message!
        return '''
            During your current session, you've viewed this
            page %s times! Your life is a patio of fun!
        ''' % count
    index.exposed = True


import os.path
tutconf = os.path.join(os.path.dirname(__file__), 'tutorial.conf')

if __name__ == '__main__':
    # CherryPy always starts with app.root when trying to map request URIs
    # to objects, so we need to mount a request handler root. A request
    # to '/' will be mapped to HelloWorld().index().
    cherrypy.quickstart(HitCounter(), config=tutconf)
else:
    # This branch is for the test suite; you can ignore it.
    cherrypy.tree.mount(HitCounter(), config=tutconf)

