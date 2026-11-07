import concurrent.futures
import gzip
import unittest
from unittest.mock import patch
import banco_de_dados as optimized


class PerformanceTests(unittest.TestCase):
    def setUp(self):
        optimized.app.debug = False
        self.client = optimized.app.test_client()

    def test_content_matches_original_and_compression(self):
        for path in ('/', '/api/cardapio'):
            with optimized.app.app_context():
                expected = (optimized._render_home().encode("utf-8") if path == "/"
                            else optimized.jsonify(optimized.MENU).get_data())
            plain = self.client.get(path)
            compressed = self.client.get(path, headers={'Accept-Encoding': 'gzip'})
            self.assertEqual(plain.data, expected)
            self.assertEqual(gzip.decompress(compressed.data), expected)
            self.assertEqual(compressed.headers['Content-Encoding'], 'gzip')
            self.assertNotEqual(plain.headers['ETag'], compressed.headers['ETag'])
            if path.endswith('cardapio'):
                self.assertEqual(plain.json, optimized.MENU)

    def test_conditional_get_head_and_vary(self):
        for path in ('/', '/api/cardapio'):
            for accept in ('identity', 'gzip'):
                headers = {'Accept-Encoding': accept}
                initial = self.client.get(path, headers=headers)
                cached = self.client.get(path, headers={**headers, 'If-None-Match': initial.headers['ETag']})
                self.assertEqual(cached.status_code, 304)
                self.assertEqual(cached.data, b'')
                self.assertIn('Accept-Encoding', cached.headers['Vary'])
                self.assertIn('no-cache', initial.headers['Cache-Control'])
                head = self.client.head(path, headers=headers)
                self.assertEqual(head.data, b'')
                self.assertEqual(head.content_length, len(initial.data))
                self.assertEqual(self.client.get(path, headers={**headers, 'If-None-Match': '"stale"'}).status_code, 200)

    def test_encoding_negotiation(self):
        cases = {'gzip': 'gzip', 'br': None, 'gzip;q=0': None,
                 'gzip;q=0.5, identity;q=1': None, '*': 'gzip',
                 'gzip;q=1, identity;q=0': 'gzip', '*;q=0': 406,
                 'gzip;q=0, identity;q=0': 406}
        for header, expected in cases.items():
            r = self.client.get('/', headers={'Accept-Encoding': header})
            if expected == 406:
                self.assertEqual(r.status_code, 406)
            else:
                self.assertEqual(r.status_code, 200)
                self.assertEqual(r.headers.get('Content-Encoding'), expected)

    def test_no_per_request_render_or_serialization(self):
        with patch.object(optimized, 'render_template', side_effect=AssertionError('rendered again')), patch.object(optimized, 'jsonify', side_effect=AssertionError('serialized again')):
            self.assertEqual(self.client.get('/').status_code, 200)
            self.assertEqual(self.client.get('/api/cardapio').status_code, 200)

    def test_debug_updates_data(self):
        optimized.app.debug = True
        try:
            with patch.object(optimized, 'NOME_LOJA', 'Novo nome'):
                self.assertIn(b'Novo nome', self.client.get('/').data)
        finally:
            optimized.app.debug = False

    def test_concurrent_response_isolation(self):
        def visit(i):
            with optimized.app.test_client() as client:
                compressed = i % 2 == 0
                r = client.get('/', headers={'Accept-Encoding': 'gzip' if compressed else 'identity'})
                return gzip.decompress(r.data) if compressed else r.data
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
            bodies = list(pool.map(visit, range(100)))
        self.assertTrue(all(body == bodies[0] for body in bodies))



if __name__ == "__main__":
    unittest.main()
