"""Test module for the @-decorator syntax, which is version-specific"""

from cherrypy import expose, tools
from cherrypy._cpcompat import ntob


class ExposeExamples(object):

    @expose
    def no_call(self):
        return "Mr E. R. Bradshaw"

    @expose()
    def call_empty(self):
        return "Mrs. B.J. Smegma"

    @expose("call_alias")
    def nesbitt(self):
        return "Mr Nesbitt"

    @expose(["alias1", "alias2"])
    def andrews(self):
        return "Mr Ken Andrews"

    @expose(alias="alias3")
    def watson(self):
        return "Mr. and Mrs. Watson"


class ToolExamples(object):

    @expose
    @tools.response_headers(headers=[('Content-Type', 'application/data')])
    def blah(self):
        yield ntob("blah")
    # This is here to demonstrate that _cp_config = {...} overwrites
    # the _cp_config attribute added by the Tool decorator. You have
    # to write _cp_config[k] = v or _cp_config.update(...) instead.
    blah._cp_config['response.stream'] = True


