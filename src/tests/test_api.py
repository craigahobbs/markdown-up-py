# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

from io import StringIO
import json
import re
import unittest
import unittest.mock

from bare_script import BareScriptParserError
from schema_markdown import SchemaMarkdownParserError

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

    def test_api_posix(self):
        test_files = [
            (('sub', 'test.smd'), '''\
action sumNumbers
    urls
        GET

    query
        float[] values

    output
        float result
'''),
            (('sub', 'test.bare'), '''\
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
            # Relative POSIX paths
            app = MarkdownUpApplication(temp_dir, {}, {
                'schemas': ['sub/test.smd'],
                'scripts': ['sub/test.bare'],
                'apis': [
                    {'name': 'sumNumbers'}
                ]
            })
            status, headers, content_bytes = app.request('GET', '/sumNumbers', query_string='values.0=1&values.1=2.5')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertDictEqual(json.loads(content_bytes.decode('utf-8')), {'result': 3.5})

            # Absolute POSIX paths
            app = MarkdownUpApplication(temp_dir, {}, {
                'schemas': ['/sub/test.smd'],
                'scripts': ['/sub/test.bare'],
                'apis': [
                    {'name': 'sumNumbers'}
                ]
            })
            status, headers, content_bytes = app.request('GET', '/sumNumbers', query_string='values.0=1&values.1=2.5')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertDictEqual(json.loads(content_bytes.decode('utf-8')), {'result': 3.5})


    def test_api_named_fn(self):
        test_files = [
            ('test.smd', '''\
action test
    urls
        GET
'''),
            ('test.bare', '''\
function testx(request):
    return objectNew()
endfunction
''')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, {}, {
                'schemas': ['test.smd'],
                'scripts': ['test.bare'],
                'apis': [
                    {'name': 'test', 'function': 'testx'}
                ]
            })
            status, headers, content_bytes = app.request('GET', '/test')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertEqual(content_bytes, b'{}')


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


    def test_api_bad_method(self):
        test_files = [
            ('test.smd', '''\
action test
    urls
        POST
'''),
            ('test.bare', '''\
function test(request):
endfunction
''')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, {}, {
                'schemas': ['test.smd'],
                'scripts': ['test.bare'],
                'apis': [
                    {'name': 'test'}
                ]
            })
            status, headers, content_bytes = app.request('GET', '/test')
            self.assertEqual(status, '405 Method Not Allowed')
            self.assertEqual(headers, [('Content-Type', 'text/plain')])
            self.assertEqual(content_bytes, b'Method Not Allowed')


    def test_api_schema_error(self):
        test_files = [
            ('test.smd', '''\
asdf
'''),
            ('test.bare', '''\
function test(request):
    return objectNew()
endfunction
''')
        ]
        with create_test_files(test_files) as temp_dir:
            with self.assertRaises(SchemaMarkdownParserError) as cm_exc:
                MarkdownUpApplication(
                    temp_dir,
                    {},
                    {
                        'schemas': ['test.smd'],
                        'scripts': ['test.bare'],
                        'apis': [
                            {'name': 'test'}
                        ]
                    }
                )
            self.assertEqual(str(cm_exc.exception), 'test.smd:1: error: Syntax error')


    def test_api_script_error(self):
        test_files = [
            ('test.smd', '''\
action test
    urls
        GET
'''),
            ('test.bare', '''\
asdf-
''')
        ]
        with create_test_files(test_files) as temp_dir:
            with self.assertRaises(BareScriptParserError) as cm_exc:
                MarkdownUpApplication(
                    temp_dir,
                    {},
                    {
                        'schemas': ['test.smd'],
                        'scripts': ['test.bare'],
                        'apis': [
                            {'name': 'test'}
                        ]
                    }
                )
            self.assertEqual(str(cm_exc.exception), '''\
Syntax error, line number 1:
asdf-
     ^
''')


    def test_api_unknown_function(self):
        test_files = [
            ('test.smd', '''\
action test
    urls
        GET
'''),
            ('test.bare', '''\
function test():
    return objectNew()
endfunction
''')
        ]
        with create_test_files(test_files) as temp_dir:
            with self.assertRaises(NameError) as cm_exc:
                MarkdownUpApplication(
                    temp_dir,
                    {},
                    {
                        'schemas': ['test.smd'],
                        'scripts': ['test.bare'],
                        'apis': [
                            {'name': 'unknown'}
                        ]
                    }
                )
            self.assertEqual(str(cm_exc.exception), 'Unknown API function "unknown"')


    def test_api_invalid_function(self):
        test_files = [
            ('test.smd', '''\
action test
    urls
        GET
'''),
            ('test.bare', '''\
test = null
''')
        ]
        with create_test_files(test_files) as temp_dir:
            with self.assertRaises(NameError) as cm_exc:
                MarkdownUpApplication(
                    temp_dir,
                    {},
                    {
                        'schemas': ['test.smd'],
                        'scripts': ['test.bare'],
                        'apis': [
                            {'name': 'test'}
                        ]
                    }
                )
            self.assertEqual(str(cm_exc.exception), 'Unknown API function "test"')


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
    apiError('TestError')
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


    def test_api_error_status(self):
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
    apiError('TestError', '500 Internal Server Error')
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
            self.assertEqual(status, '500 Internal Server Error')
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
    apiHeader('X-Foobar', 'TestFoobar')
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


    def test_api_null_response(self):
        test_files = [
            ('test.smd', '''\
action test
    urls
        GET
'''),
            ('test.bare', '''\
function test(request):
endfunction
''')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, {}, {
                'schemas': ['test.smd'],
                'scripts': ['test.bare'],
                'apis': [
                    {'name': 'test'}
                ]
            })
            status, headers, content_bytes = app.request('GET', '/test')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertEqual(json.loads(content_bytes.decode('utf-8')), {})


    def test_api_invalid_response(self):
        test_files = [
            ('test.smd', '''\
action test
    urls
        GET
'''),
            ('test.bare', '''\
function test(request):
    return 'asdf'
endfunction
''')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, {}, {
                'schemas': ['test.smd'],
                'scripts': ['test.bare'],
                'apis': [
                    {'name': 'test'}
                ]
            })
            wsgi_errors = StringIO()
            status, headers, content_bytes = app.request('GET', '/test', environ={'wsgi.errors': wsgi_errors})
            self.assertEqual(status, '500 Internal Server Error')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertEqual(json.loads(content_bytes.decode('utf-8')), {
                'error': 'InvalidOutput',
                'message': "Invalid value 'asdf' (type 'str'), expected type 'test_output'"
            })
            self.assertTrue(re.match(
                r"ERROR \[\d+ / \d+\] Invalid output returned from action 'test': "
                    r"Invalid value 'asdf' \(type 'str'\), expected type 'test_output'",
                wsgi_errors.getvalue()
            ), wsgi_errors.getvalue())


    def test_api_wsgi_invalid_response_empty(self):
        test_files = [
            ('test.smd', '''\
action test
    urls
        GET
'''),
            ('test.bare', '''\
function test(request):
    return arrayNew()
endfunction
''')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, {}, {
                'schemas': ['test.smd'],
                'scripts': ['test.bare'],
                'apis': [
                    {'name': 'test', 'wsgi': True}
                ]
            })
            wsgi_errors = StringIO()
            status, headers, content_bytes = app.request('GET', '/test', environ={'wsgi.errors': wsgi_errors})
            self.assertEqual(status, '500 Internal Server Error')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertEqual(json.loads(content_bytes.decode('utf-8')), {
                'error': 'InvalidOutput',
                'message': 'WSGI API function "test" invalid return value'
            })
            self.assertTrue(re.match(
                r'ERROR \[\d+ / \d+\] WSGI API function "test" invalid return value',
                wsgi_errors.getvalue()
            ), wsgi_errors.getvalue())


    def test_api_wsgi_invalid_response_status(self):
        test_files = [
            ('test.smd', '''\
action test
    urls
        GET
'''),
            ('test.bare', '''\
function test(request):
    return arrayNew(200, arrayNew(), 'Hello')
endfunction
''')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, {}, {
                'schemas': ['test.smd'],
                'scripts': ['test.bare'],
                'apis': [
                    {'name': 'test', 'wsgi': True}
                ]
            })
            status, headers, content_bytes = app.request('GET', '/test')
            self.assertEqual(status, '500 Internal Server Error')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertEqual(json.loads(content_bytes.decode('utf-8')), {
                'error': 'InvalidOutput',
                'message': 'WSGI API function "test" invalid return value'
            })


    def test_api_wsgi_invalid_response_headers(self):
        test_files = [
            ('test.smd', '''\
action test
    urls
        GET
'''),
            ('test.bare', '''\
function test(request):
    return arrayNew('200 OK', 'text/plain', 'Hello')
endfunction
''')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, {}, {
                'schemas': ['test.smd'],
                'scripts': ['test.bare'],
                'apis': [
                    {'name': 'test', 'wsgi': True}
                ]
            })
            status, headers, content_bytes = app.request('GET', '/test')
            self.assertEqual(status, '500 Internal Server Error')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertEqual(json.loads(content_bytes.decode('utf-8')), {
                'error': 'InvalidOutput',
                'message': 'WSGI API function "test" invalid return value'
            })


    def test_api_wsgi_invalid_response_header_item(self):
        test_files = [
            ('test.smd', '''\
action test
    urls
        GET
'''),
            ('test.bare', '''\
function test(request):
    return arrayNew('200 OK', arrayNew('text/plain'), 'Hello')
endfunction
''')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, {}, {
                'schemas': ['test.smd'],
                'scripts': ['test.bare'],
                'apis': [
                    {'name': 'test', 'wsgi': True}
                ]
            })
            status, headers, content_bytes = app.request('GET', '/test')
            self.assertEqual(status, '500 Internal Server Error')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertEqual(json.loads(content_bytes.decode('utf-8')), {
                'error': 'InvalidOutput',
                'message': 'WSGI API function "test" invalid return value'
            })


    def test_api_wsgi_invalid_response_header_empty(self):
        test_files = [
            ('test.smd', '''\
action test
    urls
        GET
'''),
            ('test.bare', '''\
function test(request):
    return arrayNew('200 OK', arrayNew(arrayNew()), 'Hello')
endfunction
''')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, {}, {
                'schemas': ['test.smd'],
                'scripts': ['test.bare'],
                'apis': [
                    {'name': 'test', 'wsgi': True}
                ]
            })
            status, headers, content_bytes = app.request('GET', '/test')
            self.assertEqual(status, '500 Internal Server Error')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertEqual(json.loads(content_bytes.decode('utf-8')), {
                'error': 'InvalidOutput',
                'message': 'WSGI API function "test" invalid return value'
            })


    def test_api_wsgi_invalid_response_header_key(self):
        test_files = [
            ('test.smd', '''\
action test
    urls
        GET
'''),
            ('test.bare', '''\
function test(request):
    return arrayNew('200 OK', arrayNew(arrayNew(null, 'Value')), 'Hello')
endfunction
''')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, {}, {
                'schemas': ['test.smd'],
                'scripts': ['test.bare'],
                'apis': [
                    {'name': 'test', 'wsgi': True}
                ]
            })
            status, headers, content_bytes = app.request('GET', '/test')
            self.assertEqual(status, '500 Internal Server Error')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertEqual(json.loads(content_bytes.decode('utf-8')), {
                'error': 'InvalidOutput',
                'message': 'WSGI API function "test" invalid return value'
            })


    def test_api_wsgi_invalid_response_header_value(self):
        test_files = [
            ('test.smd', '''\
action test
    urls
        GET
'''),
            ('test.bare', '''\
function test(request):
    return arrayNew('200 OK', arrayNew(arrayNew('Key', null)), 'Hello')
endfunction
''')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, {}, {
                'schemas': ['test.smd'],
                'scripts': ['test.bare'],
                'apis': [
                    {'name': 'test', 'wsgi': True}
                ]
            })
            status, headers, content_bytes = app.request('GET', '/test')
            self.assertEqual(status, '500 Internal Server Error')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertEqual(json.loads(content_bytes.decode('utf-8')), {
                'error': 'InvalidOutput',
                'message': 'WSGI API function "test" invalid return value'
            })


    def test_api_wsgi_invalid_response_content(self):
        test_files = [
            ('test.smd', '''\
action test
    urls
        GET
'''),
            ('test.bare', '''\
function test(request):
    return arrayNew('200 OK', arrayNew(arrayNew('Content-Type', 'text/plain')), null)
endfunction
''')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, {}, {
                'schemas': ['test.smd'],
                'scripts': ['test.bare'],
                'apis': [
                    {'name': 'test', 'wsgi': True}
                ]
            })
            status, headers, content_bytes = app.request('GET', '/test')
            self.assertEqual(status, '500 Internal Server Error')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertEqual(json.loads(content_bytes.decode('utf-8')), {
                'error': 'InvalidOutput',
                'message': 'WSGI API function "test" invalid return value'
            })
