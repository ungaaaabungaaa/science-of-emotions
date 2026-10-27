from http.client import HTTPConnection
from pathlib import Path
import threading
import unittest

from emotion_lab.server import make_server


class ServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = make_server(port=0)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join()

    def request(self, path, method='GET', host=None):
        conn = HTTPConnection('127.0.0.1', self.server.server_port, timeout=5)
        self.addCleanup(conn.close)
        conn.request(method, path, headers={'Host': host} if host else {})
        response = conn.getresponse()
        body = response.read()
        return response.status, dict(response.getheaders()), body

    def test_allowlisted_viewer_and_security_headers(self):
        code, headers, body = self.request('/')
        self.assertEqual(code, 200)
        self.assertIn(b'The Science of Emotions', body)
        self.assertIn("default-src 'self'", headers['Content-Security-Policy'])
        self.assertEqual(headers['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(headers['Cache-Control'], 'no-store')
        for path in ['/styles.css', '/app.mjs', '/model.mjs', '/assets/report.json']:
            self.assertEqual(self.request(path)[0], 200)

    def test_private_paths_and_host_rebinding_fail(self):
        for path in ['/.git/config', '/data-source.json', '/data/train.tsv', '/..%2FREADME.md', '/assets/', '//evil.example/']:
            self.assertNotEqual(self.request(path)[0], 200, path)
        self.assertEqual(self.request('/', host='evil.example')[0], 403)

    def test_head_has_length_without_body_and_post_is_not_supported(self):
        code, headers, body = self.request('/assets/report.json', 'HEAD')
        self.assertEqual(code, 200)
        self.assertGreater(int(headers['Content-Length']), 100)
        self.assertEqual(body, b'')
        self.assertEqual(self.request('/', 'POST')[0], 501)


if __name__ == '__main__':
    unittest.main()
