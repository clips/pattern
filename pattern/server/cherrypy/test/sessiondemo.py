#!/usr/bin/python
"""A session demonstration app."""

import calendar
from datetime import datetime
import sys
import cherrypy
from cherrypy.lib import sessions
from cherrypy._cpcompat import copyitems


page = """
<html>
<head>
<style type='text/css'>
table { border-collapse: collapse; border: 1px solid #663333; }
th { text-align: right; background-color: #663333; color: white; padding: 0.5em; }
td { white-space: pre-wrap; font-family: monospace; padding: 0.5em;
     border: 1px solid #663333; }
.warn { font-family: serif; color: #990000; }
</style>
<script type="text/javascript">
<!--
function twodigit(d) { return d < 10 ? "0" + d : d; }
function formattime(t) {
    var month = t.getUTCMonth() + 1;
    var day = t.getUTCDate();
    var year = t.getUTCFullYear();
    var hours = t.getUTCHours();
    var minutes = t.getUTCMinutes();
    return (year + "/" + twodigit(month) + "/" + twodigit(day) + " " +
            hours + ":" + twodigit(minutes) + " UTC");
}

function interval(s) {
    // Return the given interval (in seconds) as an English phrase
    var seconds = s %% 60;
    s = Math.floor(s / 60);
    var minutes = s %% 60;
    s = Math.floor(s / 60);
    var hours = s %% 24;
    var v = twodigit(hours) + ":" + twodigit(minutes) + ":" + twodigit(seconds);
    var days = Math.floor(s / 24);
    if (days != 0) v = days + ' days, ' + v;
    return v;
}

var fudge_seconds = 5;

function init() {
    // Set the content of the 'btime' cell.
    var currentTime = new Date();
    var bunixtime = Math.floor(currentTime.getTime() / 1000);

    var v = formattime(currentTime);
    v += " (Unix time: " + bunixtime + ")";

    var diff = Math.abs(%(serverunixtime)s - bunixtime);
    if (diff > fudge_seconds) v += "<p class='warn'>Browser and Server times disagree.</p>";

    document.getElementById('btime').innerHTML = v;

    // Warn if response cookie expires is not close to one hour in the future.
    // Yes, we want this to happen when wit hit the 'Expire' link, too.
    var expires = Date.parse("%(expires)s") / 1000;
    var onehour = (60 * 60);
    if (Math.abs(expires - (bunixtime + onehour)) > fudge_seconds) {
        diff = Math.floor(expires - bunixtime);
        if (expires > (bunixtime + onehour)) {
            var msg = "Response cookie 'expires' date is " + interval(diff) + " in the future.";
        } else {
            var msg = "Response cookie 'expires' date is " + interval(0 - diff) + " in the past.";
        }
        document.getElementById('respcookiewarn').innerHTML = msg;
    }
}
//-->
</script>
</head>

<body onload='init()'>
<h2>Session Demo</h2>
<p>Reload this page. The session ID should not change from one reload to the next</p>
<p><a href='../'>Index</a> | <a href='expire'>Expire</a> | <a href='regen'>Regenerate</a></p>
<table>
    <tr><th>Session ID:</th><td>%(sessionid)s<p class='warn'>%(changemsg)s</p></td></tr>
    <tr><th>Request Cookie</th><td>%(reqcookie)s</td></tr>
    <tr><th>Response Cookie</th><td>%(respcookie)s<p id='respcookiewarn' class='warn'></p></td></tr>
    <tr><th>Session Data</th><td>%(sessiondata)s</td></tr>
    <tr><th>Server Time</th><td id='stime'>%(servertime)s (Unix time: %(serverunixtime)s)</td></tr>
    <tr><th>Browser Time</th><td id='btime'>&nbsp;</td></tr>
    <tr><th>Cherrypy Version:</th><td>%(cpversion)s</td></tr>
    <tr><th>Python Version:</th><td>%(pyversion)s</td></tr>
</table>
</body></html>
"""

class Root(object):

    def page(self):
        changemsg = []
        if cherrypy.session.id != cherrypy.session.originalid:
            if cherrypy.session.originalid is None:
                changemsg.append('Created new session because no session id was given.')
            if cherrypy.session.missing:
                changemsg.append('Created new session due to missing (expired or malicious) session.')
            if cherrypy.session.regenerated:
                changemsg.append('Application generated a new session.')

        try:
            expires = cherrypy.response.cookie['session_id']['expires']
        except KeyError:
            expires = ''

        return page % {
            'sessionid': cherrypy.session.id,
            'changemsg': '<br>'.join(changemsg),
            'respcookie': cherrypy.response.cookie.output(),
            'reqcookie': cherrypy.request.cookie.output(),
            'sessiondata': copyitems(cherrypy.session),
            'servertime': datetime.utcnow().strftime("%Y/%m/%d %H:%M") + " UTC",
            'serverunixtime': calendar.timegm(datetime.utcnow().timetuple()),
            'cpversion': cherrypy.__version__,
            'pyversion': sys.version,
            'expires': expires,
            }

    def index(self):
        # Must modify data or the session will not be saved.
        cherrypy.session['color'] = 'green'
        return self.page()
    index.exposed = True

    def expire(self):
        sessions.expire()
        return self.page()
    expire.exposed = True

    def regen(self):
        cherrypy.session.regenerate()
        # Must modify data or the session will not be saved.
        cherrypy.session['color'] = 'yellow'
        return self.page()
    regen.exposed = True

if __name__ == '__main__':
    cherrypy.config.update({
        #'environment': 'production',
        'log.screen': True,
        'tools.sessions.on': True,
        })
    cherrypy.quickstart(Root())

