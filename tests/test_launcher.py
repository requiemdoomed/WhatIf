import socket
import tempfile
import unittest
import urllib.request
from pathlib import Path
from app import create_app
from launcher import LocalServer, start_server, stop_server


class LauncherTests(unittest.TestCase):
    def test_start_rerun_http_stop_restart(self):
        with tempfile.TemporaryDirectory() as folder:
            app=create_app(Path(folder)/'test.sqlite3',testing=True)
            first=start_server(0,app)
            try:
                self.assertIs(first,start_server(0,app))
                with urllib.request.urlopen(f'http://127.0.0.1:{first.port}/') as r:self.assertEqual(r.status,200)
            finally:stop_server()
            self.assertFalse(first.thread.is_alive())
            second=start_server(0,app)
            self.assertIsNot(first,second);stop_server()

    def test_occupied_port(self):
        with tempfile.TemporaryDirectory() as folder, socket.socket() as sock:
            sock.bind(('127.0.0.1',0));sock.listen()
            app=create_app(Path(folder)/'test.sqlite3',testing=True)
            with self.assertRaises(RuntimeError):LocalServer(app,sock.getsockname()[1])

    def test_invalid_port(self):
        for port in [-1,65536,'5050',True]:
            with self.subTest(port=port),self.assertRaises(ValueError):start_server(port)
