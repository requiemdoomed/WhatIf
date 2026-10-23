"""A notebook-friendly server with a real stop button and one live instance."""
import threading
from werkzeug.serving import make_server

_active = None

class LocalServer:
    def __init__(self, app, port):
        try:
            self.httpd = make_server('127.0.0.1', port, app, threaded=True)
        except (SystemExit, OSError) as error:
            raise RuntimeError(f'Port {port} is unavailable. Stop the other server or choose another PORT.') from error
        self.port = self.httpd.server_port
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

    def stop(self):
        if self.thread.is_alive():
            self.httpd.shutdown()
            self.thread.join(timeout=5)
            self.httpd.server_close()
        print('WhatIf stopped. Saved journeys remain in the database.')


def start_server(port=5050, app=None):
    global _active
    if type(port) is not int or not 0 <= port <= 65535:
        raise ValueError('Choose an integer port between 1 and 65535 (0 selects a free port).')
    if _active and _active.thread.is_alive():
        print(f'WhatIf is already running at http://127.0.0.1:{_active.port}')
        return _active
    if app is None:
        from app import create_app
        app = create_app()
    _active = LocalServer(app, port)
    print(f'Open http://127.0.0.1:{_active.port} in your browser.')
    return _active


def stop_server():
    if _active:
        _active.stop()
    else:
        print('No notebook server is running.')
