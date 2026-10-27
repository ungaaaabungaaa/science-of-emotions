"""Small loopback-only viewer server with a fixed public-file allowlist."""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ('index.html', 'styles.css', 'app.mjs', 'model.mjs', 'assets/report.json')
MIME = {'.html': 'text/html; charset=utf-8', '.css': 'text/css; charset=utf-8',
        '.mjs': 'text/javascript; charset=utf-8', '.json': 'application/json; charset=utf-8'}


def make_server(port=8787, web_root=None):
    directory = Path(web_root or ROOT / 'web').resolve()

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def do_GET(self):
            self.send_file(False)

        def do_HEAD(self):
            self.send_file(True)

        def send_file(self, head):
            host = self.headers.get('Host', '')
            if host not in {f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}'}:
                self.send_error(403)
                return
            parsed = urlsplit(self.path)
            path = 'index.html' if parsed.path == '/' else parsed.path.removeprefix('/')
            if parsed.scheme or parsed.netloc or path not in PUBLIC:
                self.send_error(404)
                return
            target = directory / path
            try:
                if target.is_symlink() or not target.is_file() or target.resolve().parent not in {directory, directory / 'assets'}:
                    raise FileNotFoundError
                data = target.read_bytes()
                if len(data) > 1_000_000:
                    raise OSError('Public file too large')
            except OSError:
                self.send_error(404)
                return
            self.send_response(200)
            self.send_header('Content-Type', MIME[target.suffix])
            self.send_header('Content-Length', str(len(data)))
            self.send_header('Cache-Control', 'no-store')
            self.send_header('X-Content-Type-Options', 'nosniff')
            self.send_header('Referrer-Policy', 'no-referrer')
            self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'none'")
            self.end_headers()
            if not head:
                self.wfile.write(data)

    return ThreadingHTTPServer(('127.0.0.1', port), Handler)
