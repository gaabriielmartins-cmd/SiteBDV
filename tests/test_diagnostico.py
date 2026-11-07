import concurrent.futures
import gzip
import sys
import threading
import unittest
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import diagnostico as d

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        code, body = 200, b'<title>Batata Das Vargens</title>'
        if self.path == '/static/logo.png': body = b'\x89PNG\r\n\x1a\n'
        elif self.path == '/api/cardapio': body = b'{"Combos": []}'
        elif self.path == '/error': code, body = 503, b'Unavailable'
        elif self.path == '/login': code, body = 302, b''
        elif self.path == '/bad-gzip': body = b'not a gzip file'
        elif self.path == '/invalid-json': body = b'not json'
        compressed = self.headers.get('Accept-Encoding') == 'gzip'
        if compressed and self.path != '/bad-gzip': body = gzip.compress(body)
        self.send_response(code)
        if code == 302: self.send_header('Location', '/')
        if compressed: self.send_header('Content-Encoding', 'gzip')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self, *args): pass

class DiagnosticTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = 'http://127.0.0.1:' + str(cls.server.server_port)
    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown(); cls.server.server_close(); cls.thread.join()

    def test_loopback_skips_proxy_discovery(self):
        with patch.object(urllib.request, 'getproxies', side_effect=AssertionError('Proxy discovery')):
            for url in [self.url, 'http://localhost:5000', 'http://[::1]:5000']:
                d.criar_cliente(url)
            self.assertFalse(d.consultar(self.url, '/')['erro'])

    def test_external_preserves_proxy(self):
        with patch.object(urllib.request, 'getproxies', return_value={'https': 'http://proxy.example:8080'}) as discovery:
            client = d.criar_cliente('https://example.com')
            discovery.assert_called_once()
            proxy = next(h for h in client.handlers if isinstance(h, urllib.request.ProxyHandler))
            self.assertEqual(proxy.proxies['https'], 'http://proxy.example:8080')

    def test_client_reused(self):
        client = d.criar_cliente(self.url)
        with patch.object(urllib.request, 'build_opener', side_effect=AssertionError('Rebuilt')):
            for path in ('/', '/static/logo.png', '/api/cardapio'):
                self.assertFalse(d.consultar(self.url, path, client)['erro'])

    def test_gzip_validated_and_counted(self):
        for path in ('/', '/static/logo.png', '/api/cardapio'):
            r = d.consultar(self.url, path, comprimir=True)
            self.assertEqual(r['status'], 200)
            self.assertFalse(r['erro'])
            self.assertEqual(r['headers']['content-encoding'], 'gzip')
            self.assertGreater(r['bytes_recebidos'], 0)

    def test_corrupt_gzip(self):
        self.assertIn('Gzip invalido', d.consultar(self.url, '/bad-gzip', comprimir=True)['erro'])

    def test_redirect_and_server_error(self):
        self.assertEqual(d.consultar(self.url, '/login')['status'], 302)
        r = d.consultar(self.url, '/error')
        self.assertEqual(r['status'], 503)
        self.assertIn('HTTP 503', ' '.join(d.analisar([r])))

    def test_concurrency_and_reporting(self):
        result = d.executar(self.url, 4, 1, comprimir=True)
        self.assertEqual(result['resumo']['falhas'], 0)
        self.assertEqual(result['resumo']['requisicoes'], 7)
        self.assertEqual(result['versao_diagnostico'], '1.1')
        self.assertTrue(result['gzip_solicitado'])
        self.assertLess(result['duracao_real_s'], 4)

if __name__ == '__main__': unittest.main()
