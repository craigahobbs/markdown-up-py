# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

import json
import unittest
import unittest.mock

from markdown_up.app import MarkdownUpApplication

from .test_app import create_test_files


class TestMarkdownUpAPI(unittest.TestCase):

    def test_api(self):
        test_files = [
            ('test.smd', '''\
action sumNumbers
    urls
        GET

    query
        float[] values

    output
        float result
'''),
            ('test.bare', '''\
function sumNumbers(request):
    result = 0
    for value in objectGet(request, 'values'):
        result = result + value
    endfor
    return objectNew('result', result)
endfunction
''')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, {}, {
                'schemas': ['test.smd'],
                'scripts': ['test.bare'],
                'apis': [
                    {'name': 'sumNumbers'}
                ]
            })
            status, headers, content_bytes = app.request('GET', '/sumNumbers', query_string='values.0=1&values.1=2.5')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertDictEqual(json.loads(content_bytes.decode('utf-8')), {'result': 3.5})


    def test_api_wsgi(self):
        test_files = [
            ('test.smd', '''\
action sumNumbers
    urls
        GET

    query
        float[] values
'''),
            ('test.bare', '''\
function sumNumbers(request):
    result = 0
    for value in objectGet(request, 'values'):
        result = result + value
    endfor
    return arrayNew( \
        '200 OK', \
        arrayNew(arrayNew('Content-Type', 'text/plain')), \
        'The result is ' + result \
    )
endfunction
''')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, {}, {
                'schemas': ['test.smd'],
                'scripts': ['test.bare'],
                'apis': [
                    {'name': 'sumNumbers', 'wsgi': True}
                ]
            })
            status, headers, content_bytes = app.request('GET', '/sumNumbers', query_string='values.0=1&values.1=2.5')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'text/plain')])
            self.assertEqual(content_bytes, b'The result is 3.5')


    def test_api_globals(self):
        test_files = [
            ('test.smd', '''\
action testGlobals
    urls
        GET
'''),
            ('test.bare', '''\
function testGlobals(request):
    return arrayNew( \
        '200 OK', \
        arrayNew(arrayNew('Content-Type', 'text/plain')), \
        vName1 + ' and ' + vName2 \
    )
endfunction
''')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(
                temp_dir,
                {
                    'globals': {'vName1': 'Tom', 'vName2': 'Jerry'}
                },
                {
                    'schemas': ['test.smd'],
                    'scripts': ['test.bare'],
                    'apis': [
                        {'name': 'testGlobals', 'wsgi': True}
                    ]
                }
            )
            status, headers, content_bytes = app.request('GET', '/testGlobals')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'text/plain')])
            self.assertEqual(content_bytes, b'Tom and Jerry')


    def test_api_error(self):
        test_files = [
            ('test.smd', '''\
action testError
    urls
        GET

    errors
        TestError
'''),
            ('test.bare', '''\
function testError(request):
    backendError('TestError')
endfunction
''')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, {}, {
                'schemas': ['test.smd'],
                'scripts': ['test.bare'],
                'apis': [
                    {'name': 'testError'}
                ]
            })
            status, headers, content_bytes = app.request('GET', '/testError')
            self.assertEqual(status, '400 Bad Request')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertEqual(json.loads(content_bytes.decode('utf-8')), {'error': 'TestError'})


    def test_api_headers(self):
        test_files = [
            ('test.smd', '''\
action testError
    urls
        GET
'''),
            ('test.bare', '''\
function testError(request):
    backendHeader('X-Foobar', 'TestFoobar')
endfunction
''')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, {}, {
                'schemas': ['test.smd'],
                'scripts': ['test.bare'],
                'apis': [
                    {'name': 'testError'}
                ]
            })
            status, headers, content_bytes = app.request('GET', '/testError')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'application/json'), ('X-Foobar', 'TestFoobar')])
            self.assertEqual(json.loads(content_bytes.decode('utf-8')), {})
