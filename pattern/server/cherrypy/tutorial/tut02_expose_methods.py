"""
Tutorial - Multiple methods

This tutorial shows you how to link to other methods of your request
handler.
"""

import cherrypy

class HelloWorld:

    def index(self):
        # Let's link to another method here.
        return 'We have an <a href="showMessage">important message</a> for you!'
    index.exposed = True

    def showMessage(self):
        # Here's the important message!
        return "Hello world!"
    showMessage.exposed = True

import os.path
tutconf = os.path.join(os.path.dirname(__file__), 'tutorial.conf')

if __name__ == '__main__':
    # CherryPy always starts with app.root when trying to map request URIs
    # to objects, so we need to mount a request handler root. A request
    # to '/' will be mapped to HelloWorld().index().
    cherrypy.quickstart(HelloWorld(), config=tutconf)
else:
    # This branch is for the test suite; you can ignore it.
    cherrypy.tree.mount(HelloWorld(), config=tutconf)
