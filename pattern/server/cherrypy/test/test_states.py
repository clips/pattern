from cherrypy._cpcompat import BadStatusLine, ntob
import os
import sys
import time
import signal
import unittest
import socket

import cherrypy
import cherrypy.process.servers
from cherrypy.test import helper

engine = cherrypy.engine
thisdir = os.path.join(os.getcwd(), os.path.dirname(__file__))


class Dependency:

    def __init__(self, bus):
        self.bus = bus
        self.running = False
        self.startcount = 0
        self.gracecount = 0
        self.threads = {}

    def subscribe(self):
        self.bus.subscribe('start', self.start)
        self.bus.subscribe('stop', self.stop)
        self.bus.subscribe('graceful', self.graceful)
        self.bus.subscribe('start_thread', self.startthread)
        self.bus.subscribe('stop_thread', self.stopthread)

    def start(self):
        self.running = True
        self.startcount += 1

    def stop(self):
        self.running = False

    def graceful(self):
        self.gracecount += 1

    def startthread(self, thread_id):
        self.threads[thread_id] = None

    def stopthread(self, thread_id):
        del self.threads[thread_id]

db_connection = Dependency(engine)

def setup_server():
    class Root:
        def index(self):
            return "Hello World"
        index.exposed = True

        def ctrlc(self):
            raise KeyboardInterrupt()
        ctrlc.exposed = True

        def graceful(self):
            engine.graceful()
            return "app was (gracefully) restarted succesfully"
        graceful.exposed = True

        def block_explicit(self):
            while True:
                if cherrypy.response.timed_out:
                    cherrypy.response.timed_out = False
                    return "broken!"
                time.sleep(0.01)
        block_explicit.exposed = True

        def block_implicit(self):
            time.sleep(0.5)
            return "response.timeout = %s" % cherrypy.response.timeout
        block_implicit.exposed = True

    cherrypy.tree.mount(Root())
    cherrypy.config.update({
        'environment': 'test_suite',
        'engine.deadlock_poll_freq': 0.1,
        })

    db_connection.subscribe()

# ------------ Enough helpers. Time for real live test cases. ------------ #

class ServerStateTests(helper.CPWebCase):
    setup_server = staticmethod(setup_server)

    def setUp(self):
        cherrypy.server.socket_timeout = 0.1
        self.do_gc_test = False

    def test_0_NormalStateFlow(self):
        engine.stop()
        # Our db_connection should not be running
        self.assertEqual(db_connection.running, False)
        self.assertEqual(db_connection.startcount, 1)
        self.assertEqual(len(db_connection.threads), 0)

        # Test server start
        engine.start()
        self.assertEqual(engine.state, engine.states.STARTED)

        host = cherrypy.server.socket_host
        port = cherrypy.server.socket_port
        self.assertRaises(IOError, cherrypy._cpserver.check_port, host, port)

        # The db_connection should be running now
        self.assertEqual(db_connection.running, True)
        self.assertEqual(db_connection.startcount, 2)
        self.assertEqual(len(db_connection.threads), 0)

        self.getPage("/")
        self.assertBody("Hello World")
        self.assertEqual(len(db_connection.threads), 1)

        # Test engine stop. This will also stop the HTTP server.
        engine.stop()
        self.assertEqual(engine.state, engine.states.STOPPED)

        # Verify that our custom stop function was called
        self.assertEqual(db_connection.running, False)
        self.assertEqual(len(db_connection.threads), 0)

        # Block the main thread now and verify that exit() works.
        def exittest():
            self.getPage("/")
            self.assertBody("Hello World")
            engine.exit()
        cherrypy.server.start()
        engine.start_with_callback(exittest)
        engine.block()
        self.assertEqual(engine.state, engine.states.EXITING)

    def test_1_Restart(self):
        cherrypy.server.start()
        engine.start()

        # The db_connection should be running now
        self.assertEqual(db_connection.running, True)
        grace = db_connection.gracecount

        self.getPage("/")
        self.assertBody("Hello World")
        self.assertEqual(len(db_connection.threads), 1)

        # Test server restart from this thread
        engine.graceful()
        self.assertEqual(engine.state, engine.states.STARTED)
        self.getPage("/")
        self.assertBody("Hello World")
        self.assertEqual(db_connection.running, True)
        self.assertEqual(db_connection.gracecount, grace + 1)
        self.assertEqual(len(db_connection.threads), 1)

        # Test server restart from inside a page handler
        self.getPage("/graceful")
        self.assertEqual(engine.state, engine.states.STARTED)
        self.assertBody("app was (gracefully) restarted succesfully")
        self.assertEqual(db_connection.running, True)
        self.assertEqual(db_connection.gracecount, grace + 2)
        # Since we are requesting synchronously, is only one thread used?
        # Note that the "/graceful" request has been flushed.
        self.assertEqual(len(db_connection.threads), 0)

        engine.stop()
        self.assertEqual(engine.state, engine.states.STOPPED)
        self.assertEqual(db_connection.running, False)
        self.assertEqual(len(db_connection.threads), 0)

    def test_2_KeyboardInterrupt(self):
        # Raise a keyboard interrupt in the HTTP server's main thread.
        # We must start the server in this, the main thread
        engine.start()
        cherrypy.server.start()

        self.persistent = True
        try:
            # Make the first request and assert there's no "Connection: close".
            self.getPage("/")
            self.assertStatus('200 OK')
            self.assertBody("Hello World")
            self.assertNoHeader("Connection")

            cherrypy.server.httpserver.interrupt = KeyboardInterrupt
            engine.block()

            self.assertEqual(db_connection.running, False)
            self.assertEqual(len(db_connection.threads), 0)
            self.assertEqual(engine.state, engine.states.EXITING)
        finally:
            self.persistent = False

        # Raise a keyboard interrupt in a page handler; on multithreaded
        # servers, this should occur in one of the worker threads.
        # This should raise a BadStatusLine error, since the worker
        # thread will just die without writing a response.
        engine.start()
        cherrypy.server.start()

        try:
            self.getPage("/ctrlc")
        except BadStatusLine:
            pass
        else:
            print(self.body)
            self.fail("AssertionError: BadStatusLine not raised")

        engine.block()
        self.assertEqual(db_connection.running, False)
        self.assertEqual(len(db_connection.threads), 0)

    def test_3_Deadlocks(self):
        cherrypy.config.update({'response.timeout': 0.2})

        engine.start()
        cherrypy.server.start()
        try:
            self.assertNotEqual(engine.timeout_monitor.thread, None)

            # Request a "normal" page.
            self.assertEqual(engine.timeout_monitor.servings, [])
            self.getPage("/")
            self.assertBody("Hello World")
            # request.close is called async.
            while engine.timeout_monitor.servings:
                sys.stdout.write(".")
                time.sleep(0.01)

            # Request a page that explicitly checks itself for deadlock.
            # The deadlock_timeout should be 2 secs.
            self.getPage("/block_explicit")
            self.assertBody("broken!")

            # Request a page that implicitly breaks deadlock.
            # If we deadlock, we want to touch as little code as possible,
            # so we won't even call handle_error, just bail ASAP.
            self.getPage("/block_implicit")
            self.assertStatus(500)
            self.assertInBody("raise cherrypy.TimeoutError()")
        finally:
            engine.exit()

    def test_4_Autoreload(self):
        # Start the demo script in a new process
        p = helper.CPProcess(ssl=(self.scheme.lower()=='https'))
        p.write_conf(extra='test_case_name: "test_4_Autoreload"')
        p.start(imports='cherrypy.test._test_states_demo')
        try:
            self.getPage("/start")
            start = float(self.body)

            # Give the autoreloader time to cache the file time.
            time.sleep(2)

            # Touch the file
            os.utime(os.path.join(thisdir, "_test_states_demo.py"), None)

            # Give the autoreloader time to re-exec the process
            time.sleep(2)
            host = cherrypy.server.socket_host
            port = cherrypy.server.socket_port
            cherrypy._cpserver.wait_for_occupied_port(host, port)

            self.getPage("/start")
            if not (float(self.body) > start):
                raise AssertionError("start time %s not greater than %s" %
                                     (float(self.body), start))
        finally:
            # Shut down the spawned process
            self.getPage("/exit")
        p.join()

    def test_5_Start_Error(self):
        # If a process errors during start, it should stop the engine
        # and exit with a non-zero exit code.
        p = helper.CPProcess(ssl=(self.scheme.lower()=='https'),
                             wait=True)
        p.write_conf(
                extra="""starterror: True
test_case_name: "test_5_Start_Error"
"""
        )
        p.start(imports='cherrypy.test._test_states_demo')
        if p.exit_code == 0:
            self.fail("Process failed to return nonzero exit code.")


class PluginTests(helper.CPWebCase):
    def test_daemonize(self):
        if os.name not in ['posix']:
            return self.skip("skipped (not on posix) ")
        self.HOST = '127.0.0.1'
        self.PORT = 8081
        # Spawn the process and wait, when this returns, the original process
        # is finished.  If it daemonized properly, we should still be able
        # to access pages.
        p = helper.CPProcess(ssl=(self.scheme.lower()=='https'),
                             wait=True, daemonize=True,
                             socket_host='127.0.0.1',
                             socket_port=8081)
        p.write_conf(
             extra='test_case_name: "test_daemonize"')
        p.start(imports='cherrypy.test._test_states_demo')
        try:
            # Just get the pid of the daemonization process.
            self.getPage("/pid")
            self.assertStatus(200)
            page_pid = int(self.body)
            self.assertEqual(page_pid, p.get_pid())
        finally:
            # Shut down the spawned process
            self.getPage("/exit")
        p.join()

        # Wait until here to test the exit code because we want to ensure
        # that we wait for the daemon to finish running before we fail.
        if p.exit_code != 0:
            self.fail("Daemonized parent process failed to exit cleanly.")


class SignalHandlingTests(helper.CPWebCase):
    def test_SIGHUP_tty(self):
        # When not daemonized, SIGHUP should shut down the server.
        try:
            from signal import SIGHUP
        except ImportError:
            return self.skip("skipped (no SIGHUP) ")

        # Spawn the process.
        p = helper.CPProcess(ssl=(self.scheme.lower()=='https'))
        p.write_conf(
                extra='test_case_name: "test_SIGHUP_tty"')
        p.start(imports='cherrypy.test._test_states_demo')
        # Send a SIGHUP
        os.kill(p.get_pid(), SIGHUP)
        # This might hang if things aren't working right, but meh.
        p.join()

    def test_SIGHUP_daemonized(self):
        # When daemonized, SIGHUP should restart the server.
        try:
            from signal import SIGHUP
        except ImportError:
            return self.skip("skipped (no SIGHUP) ")

        if os.name not in ['posix']:
            return self.skip("skipped (not on posix) ")

        # Spawn the process and wait, when this returns, the original process
        # is finished.  If it daemonized properly, we should still be able
        # to access pages.
        p = helper.CPProcess(ssl=(self.scheme.lower()=='https'),
                             wait=True, daemonize=True)
        p.write_conf(
             extra='test_case_name: "test_SIGHUP_daemonized"')
        p.start(imports='cherrypy.test._test_states_demo')

        pid = p.get_pid()
        try:
            # Send a SIGHUP
            os.kill(pid, SIGHUP)
            # Give the server some time to restart
            time.sleep(2)
            self.getPage("/pid")
            self.assertStatus(200)
            new_pid = int(self.body)
            self.assertNotEqual(new_pid, pid)
        finally:
            # Shut down the spawned process
            self.getPage("/exit")
        p.join()

    def _require_signal_and_kill(self, signal_name):
        if not hasattr(signal, signal_name):
            self.skip("skipped (no %(signal_name)s)" % vars())

        if not hasattr(os, 'kill'):
            self.skip("skipped (no os.kill)")

    def test_SIGTERM(self):
        "SIGTERM should shut down the server whether daemonized or not."
        self._require_signal_and_kill('SIGTERM')

        # Spawn a normal, undaemonized process.
        p = helper.CPProcess(ssl=(self.scheme.lower()=='https'))
        p.write_conf(
                extra='test_case_name: "test_SIGTERM"')
        p.start(imports='cherrypy.test._test_states_demo')
        # Send a SIGTERM
        os.kill(p.get_pid(), signal.SIGTERM)
        # This might hang if things aren't working right, but meh.
        p.join()

        if os.name in ['posix']:
            # Spawn a daemonized process and test again.
            p = helper.CPProcess(ssl=(self.scheme.lower()=='https'),
                                 wait=True, daemonize=True)
            p.write_conf(
                 extra='test_case_name: "test_SIGTERM_2"')
            p.start(imports='cherrypy.test._test_states_demo')
            # Send a SIGTERM
            os.kill(p.get_pid(), signal.SIGTERM)
            # This might hang if things aren't working right, but meh.
            p.join()

    def test_signal_handler_unsubscribe(self):
        self._require_signal_and_kill('SIGTERM')

        # Although Windows has `os.kill` and SIGTERM is defined, the
        #  platform does not implement signals and sending SIGTERM
        #  will result in a forced termination of the process.
        #  Therefore, this test is not suitable for Windows.
        if os.name == 'nt':
            self.skip("SIGTERM not available")

        # Spawn a normal, undaemonized process.
        p = helper.CPProcess(ssl=(self.scheme.lower()=='https'))
        p.write_conf(
            extra="""unsubsig: True
test_case_name: "test_signal_handler_unsubscribe"
""")
        p.start(imports='cherrypy.test._test_states_demo')
        # Ask the process to quit
        os.kill(p.get_pid(), signal.SIGTERM)
        # This might hang if things aren't working right, but meh.
        p.join()

        # Assert the old handler ran.
        target_line = open(p.error_log, 'rb').readlines()[-10]
        if not ntob("I am an old SIGTERM handler.") in target_line:
            self.fail("Old SIGTERM handler did not run.\n%r" % target_line)

class WaitTests(unittest.TestCase):
    def test_wait_for_occupied_port_INADDR_ANY(self):
        """
        Wait on INADDR_ANY should not raise IOError

        In cases where the loopback interface does not exist, CherryPy cannot
        effectively determine if a port binding to INADDR_ANY was effected.
        In this situation, CherryPy should assume that it failed to detect
        the binding (not that the binding failed) and only warn that it could
        not verify it.
        """
        # At such a time that CherryPy can reliably determine one or more
        #  viable IP addresses of the host, this test may be removed.

        # Simulate the behavior we observe when no loopback interface is
        #  present by: finding a port that's not occupied, then wait on it.

        free_port = self.find_free_port()

        servers = cherrypy.process.servers

        def with_shorter_timeouts(func):
            """
            A context where occupied_port_timeout is much smaller to speed
            test runs.
            """
            # When we have Python 2.5, simplify using the with_statement.
            orig_timeout = servers.occupied_port_timeout
            servers.occupied_port_timeout = .07
            try:
                func()
            finally:
                servers.occupied_port_timeout = orig_timeout

        def do_waiting():
            # Wait on the free port that's unbound
            servers.wait_for_occupied_port('0.0.0.0', free_port)
            # The wait should still raise an IO error if INADDR_ANY was
            #  not supplied.
            self.assertRaises(IOError, servers.wait_for_occupied_port,
                '127.0.0.1', free_port)

        with_shorter_timeouts(do_waiting)

    def find_free_port(self):
        "Find a free port by binding to port 0 then unbinding."
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('', 0))
        free_port = sock.getsockname()[1]
        sock.close()
        return free_port
