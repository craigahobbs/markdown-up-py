# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

from io import StringIO
import os
import unittest
from unittest.mock import ANY, patch

import chisel

import markdown_up.__main__
from markdown_up.app import MarkdownUpApplication
from markdown_up.main import main

from .test_app import create_test_files


class TestMain(unittest.TestCase):

    def test_main_submodule(self):
        self.assertTrue(markdown_up.__main__)


    def test_main_help(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=False) as mock_isdir, \
             patch('os.path.isfile', return_value=False) as mock_isfile:
            with self.assertRaises(SystemExit) as cm_exc:
                main(['-h'])

            self.assertNotEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_not_called()
            mock_isfile.assert_not_called()
            self.assertEqual(cm_exc.exception.code, 0)
            self.assertTrue(stdout.getvalue().startswith('usage: markdown-up'))
            self.assertEqual(stderr.getvalue(), '')


    def test_main_file_not_found(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=False) as mock_isdir, \
             patch('os.path.isfile', return_value=False) as mock_isfile:
            with self.assertRaises(SystemExit) as cm_exc:
                main([os.path.join('missing', 'README.md')])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), f"\"{os.path.join('missing', 'README.md')}\" does not exist!\n")
            mock_isdir.assert_called_once_with(os.path.join('missing', 'README.md'))
            mock_isfile.assert_called_once_with(os.path.join('missing', 'README.md'))
            self.assertEqual(cm_exc.exception.code, 2)
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), f"\"{os.path.join('missing', 'README.md')}\" does not exist!\n")


    def test_main_dir_not_found(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=False) as mock_isdir, \
             patch('os.path.isfile', return_value=False) as mock_isfile:
            with self.assertRaises(SystemExit) as cm_exc:
                main(['missing'])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '"missing" does not exist!\n')
            mock_isdir.assert_called_once_with('missing')
            mock_isfile.assert_called_once_with('missing')
            self.assertEqual(cm_exc.exception.code, 2)
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '"missing" does not exist!\n')


    def test_main_run(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=True) as mock_isdir, \
             patch('os.path.isfile', return_value=False) as mock_isfile, \
             patch('threading.Thread') as mock_thread, \
             patch('waitress.serve') as mock_waitress_serve:
            main([])

            self.assertEqual(stdout.getvalue(), 'markdown-up: Serving at http://127.0.0.1:8080/ ...\n')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_called_once_with('.')
            self.assertEqual(mock_isfile.call_count, 2)
            mock_isfile.assert_has_calls([
                unittest.mock.call('markdown-up.json'),
                unittest.mock.call('markdown-up-api.json')
            ])
            mock_thread.assert_called_once_with(target=ANY, args=('http://127.0.0.1:8080/',))
            thread_fn = mock_thread.call_args.kwargs['target']
            self.assertTrue(callable(thread_fn))
            mock_waitress_serve.assert_called_once_with(ANY, port=8080, threads=8)
            wsgiapp = mock_waitress_serve.call_args[0][0]
            self.assertTrue(callable(wsgiapp))

            # Test calling the WSGI application
            environ = chisel.Context.create_environ('GET', '/doc')
            start_response = chisel.app.StartResponse()
            content = wsgiapp(environ, start_response)
            self.assertEqual(start_response.status, '301 Moved Permanently')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8'), ('Location', '/doc/')])
            self.assertEqual(content, [b'/doc/'])
            self.assertEqual(stdout.getvalue(), 'markdown-up: Serving at http://127.0.0.1:8080/ ...\nmarkdown-up: 301 GET /doc\n')
            self.assertEqual(stderr.getvalue(), '')


    def test_main_run_release(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=True) as mock_isdir, \
             patch('os.path.isfile', return_value=False) as mock_isfile, \
             patch('threading.Thread') as mock_thread, \
             patch('waitress.serve') as mock_waitress_serve:
            main(['-n', '-r', '-q'])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_called_once_with('.')
            self.assertEqual(mock_isfile.call_count, 2)
            mock_isfile.assert_has_calls([
                unittest.mock.call('markdown-up.json'),
                unittest.mock.call('markdown-up-api.json')
            ])
            mock_thread.assert_not_called()
            mock_waitress_serve.assert_called_once_with(ANY, port=8080, threads=8)
            wsgiapp = mock_waitress_serve.call_args[0][0]
            self.assertTrue(callable(wsgiapp))
            self.assertTrue(isinstance(wsgiapp, MarkdownUpApplication))
            self.assertTrue(wsgiapp.release)


    def test_main_run_no_browser(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=True) as mock_isdir, \
             patch('os.path.isfile', return_value=False) as mock_isfile, \
             patch('threading.Thread') as mock_thread, \
             patch('waitress.serve') as mock_waitress_serve:
            main(['-n'])

            self.assertEqual(stdout.getvalue(), 'markdown-up: Serving at http://127.0.0.1:8080/ ...\n')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_called_once_with('.')
            self.assertEqual(mock_isfile.call_count, 2)
            mock_isfile.assert_has_calls([
                unittest.mock.call('markdown-up.json'),
                unittest.mock.call('markdown-up-api.json')
            ])
            mock_thread.assert_not_called()
            mock_waitress_serve.assert_called_once_with(ANY, port=8080, threads=8)
            wsgiapp = mock_waitress_serve.call_args[0][0]
            self.assertTrue(callable(wsgiapp))


    def test_main_run_quiet(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=True) as mock_isdir, \
             patch('os.path.isfile', return_value=False) as mock_isfile, \
             patch('waitress.serve') as mock_waitress_serve:
            main(['-n', '-q'])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_called_once_with('.')
            self.assertEqual(mock_isfile.call_count, 2)
            mock_isfile.assert_has_calls([
                unittest.mock.call('markdown-up.json'),
                unittest.mock.call('markdown-up-api.json')
            ])
            mock_waitress_serve.assert_called_once_with(ANY, port=8080, threads=8)
            wsgiapp = mock_waitress_serve.call_args[0][0]
            self.assertTrue(callable(wsgiapp))
            self.assertTrue(isinstance(wsgiapp, MarkdownUpApplication))
            self.assertFalse(wsgiapp.release)

            # Test calling the WSGI application
            environ = chisel.Context.create_environ('GET', '/doc')
            start_response = chisel.app.StartResponse()
            content = wsgiapp(environ, start_response)
            self.assertEqual(start_response.status, '301 Moved Permanently')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8'), ('Location', '/doc/')])
            self.assertEqual(content, [b'/doc/'])
            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')


    def test_main_run_port(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=True) as mock_isdir, \
             patch('os.path.isfile', return_value=False) as mock_isfile, \
             patch('waitress.serve') as mock_waitress_serve:
            main(['-n', '-p', '8081'])

            self.assertEqual(stdout.getvalue(), 'markdown-up: Serving at http://127.0.0.1:8081/ ...\n')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_called_once_with('.')
            self.assertEqual(mock_isfile.call_count, 2)
            mock_isfile.assert_has_calls([
                unittest.mock.call('markdown-up.json'),
                unittest.mock.call('markdown-up-api.json')
            ])
            mock_waitress_serve.assert_called_once_with(ANY, port=8081, threads=8)
            wsgiapp = mock_waitress_serve.call_args[0][0]
            self.assertTrue(callable(wsgiapp))


    def test_main_run_threads(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=True) as mock_isdir, \
             patch('os.path.isfile', return_value=False) as mock_isfile, \
             patch('waitress.serve') as mock_waitress_serve:
            main(['-n', '-t', '16'])

            self.assertEqual(stdout.getvalue(), 'markdown-up: Serving at http://127.0.0.1:8080/ ...\n')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_called_once_with('.')
            self.assertEqual(mock_isfile.call_count, 2)
            mock_isfile.assert_has_calls([
                unittest.mock.call('markdown-up.json'),
                unittest.mock.call('markdown-up-api.json')
            ])
            mock_waitress_serve.assert_called_once_with(ANY, port=8080, threads=16)
            wsgiapp = mock_waitress_serve.call_args[0][0]
            self.assertTrue(callable(wsgiapp))


    def test_main_run_threads_negative(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=True) as mock_isdir, \
             patch('os.path.isfile', return_value=False) as mock_isfile, \
             patch('waitress.serve') as mock_waitress_serve:
            main(['-n', '-t', '-1'])

            self.assertEqual(stdout.getvalue(), 'markdown-up: Serving at http://127.0.0.1:8080/ ...\n')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_called_once_with('.')
            self.assertEqual(mock_isfile.call_count, 2)
            mock_isfile.assert_has_calls([
                unittest.mock.call('markdown-up.json'),
                unittest.mock.call('markdown-up-api.json')
            ])
            mock_waitress_serve.assert_called_once_with(ANY, port=8080, threads=1)
            wsgiapp = mock_waitress_serve.call_args[0][0]
            self.assertTrue(callable(wsgiapp))


    def test_main_run_globals(self):
        test_files = [
            ('test.smd', '''\
action testGlobals
    urls
        GET
'''),
            ('test.bare', '''\
function testGlobals(request):
    systemLog('The sum of ' + N1 + ' and ' + N2 + ' is ' + (numberParseInt(N1) + numberParseInt(N2)) + '.')
endfunction
'''),
            ('markdown-up-api.json', '''\
{
    "schemas": ["test.smd"],
    "scripts": ["test.bare"],
    "apis": [
        {"name": "testGlobals"}
    ]
}
''')
        ]
        with create_test_files(test_files) as temp_dir, \
             patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('waitress.serve') as mock_waitress_serve:
            main(['-n', '-v', 'N1', '1', '-v', 'N2', '2', temp_dir])

            mock_waitress_serve.assert_called_once_with(ANY, port=8080, threads=8)
            wsgiapp = mock_waitress_serve.call_args[0][0]
            self.assertTrue(callable(wsgiapp))

            wsgi_errors = StringIO()
            environ = chisel.Context.create_environ('GET', '/testGlobals', environ={'wsgi.errors': wsgi_errors})
            start_response_calls = []
            def start_response(status, headers):
                start_response_calls.append([status, headers])
            response = wsgiapp(environ, start_response)
            self.assertEqual(start_response_calls, [['200 OK', [('Content-Type', 'application/json')]]])
            self.assertEqual(response, [b'{}'])
            self.assertEqual(wsgi_errors.getvalue(), 'The sum of 1 and 2 is 3.\n')

            self.assertEqual(stdout.getvalue(), '''\
markdown-up: Serving at http://127.0.0.1:8080/ ...
markdown-up: 200 GET /testGlobals
''')
            self.assertEqual(stderr.getvalue(), '')


    def test_main_run_config(self):
        test_files = [
            ('test.smd', '''\
action testGlobals
    urls
        GET

    output
        int result
'''),
            ('test.bare', '''\
function testGlobals(request):
    return objectNew('result', numberParseInt(N1) + numberParseInt(N2))
endfunction
'''),
            ('markdown-up-api.json', '''\
{
    "schemas": ["test.smd"],
    "scripts": ["test.bare"],
    "apis": [
        {"name": "testGlobals"}
    ]
}
'''),
            ('markdown-up.json', '''\
{
    "release": true,
    "threads": 16,
    "globals": {"N1": "1", "N2": "2"}
}
''')
        ]
        with create_test_files(test_files) as temp_dir, \
             patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('waitress.serve') as mock_waitress_serve:
            main(['-n', '-v', 'N1', '1', '-v', 'N2', '2', temp_dir])

            mock_waitress_serve.assert_called_once_with(ANY, port=8080, threads=16)
            wsgiapp = mock_waitress_serve.call_args[0][0]
            self.assertTrue(callable(wsgiapp))

            wsgi_errors = StringIO()
            def start_response(status, headers):
                start_response_calls.append([status, headers])

            start_response_calls = []
            environ = chisel.Context.create_environ('GET', '/doc', environ={'wsgi.errors': wsgi_errors})
            response = wsgiapp(environ, start_response)
            self.assertEqual(start_response_calls, [['404 Not Found', [('Content-Type', 'text/plain')]]])
            self.assertEqual(response, [b'Not Found'])

            start_response_calls = []
            environ = chisel.Context.create_environ('GET', '/testGlobals', environ={'wsgi.errors': wsgi_errors})
            response = wsgiapp(environ, start_response)
            self.assertEqual(start_response_calls, [['200 OK', [('Content-Type', 'application/json')]]])
            self.assertEqual(response, [b'{"result":3}'])
            self.assertEqual(wsgi_errors.getvalue(), '')

            self.assertEqual(wsgi_errors.getvalue(), '')
            self.assertEqual(stdout.getvalue(), '''\
markdown-up: Serving at http://127.0.0.1:8080/ ...
markdown-up: 404 GET /doc
markdown-up: 200 GET /testGlobals
''')
            self.assertEqual(stderr.getvalue(), '')


    def test_main_run_file(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=False) as mock_isdir, \
             patch('os.path.isfile', side_effect=[True, False, False]) as mock_isfile, \
             patch('waitress.serve') as mock_waitress_serve:
            main(['-n', 'README.md'])

            self.assertEqual(stdout.getvalue(), 'markdown-up: Serving at http://127.0.0.1:8080/README.html ...\n')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_called_once_with('README.md')
            self.assertEqual(mock_isfile.call_count, 3)
            mock_isfile.assert_has_calls([
                unittest.mock.call('README.md'),
                unittest.mock.call('markdown-up.json'),
                unittest.mock.call('markdown-up-api.json')
            ])
            mock_waitress_serve.assert_called_once_with(ANY, port=8080, threads=8)
            wsgiapp = mock_waitress_serve.call_args[0][0]
            self.assertTrue(callable(wsgiapp))


    def test_main_run_file_html(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=False) as mock_isdir, \
             patch('os.path.isfile', side_effect=[True, False, False]) as mock_isfile, \
             patch('waitress.serve') as mock_waitress_serve:
            main(['-n', 'index.html'])

            self.assertEqual(stdout.getvalue(), 'markdown-up: Serving at http://127.0.0.1:8080/index.html ...\n')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_called_once_with('index.html')
            self.assertEqual(mock_isfile.call_count, 3)
            mock_isfile.assert_has_calls([
                unittest.mock.call('index.html'),
                unittest.mock.call('markdown-up.json'),
                unittest.mock.call('markdown-up-api.json')
            ])
            mock_waitress_serve.assert_called_once_with(ANY, port=8080, threads=8)
            wsgiapp = mock_waitress_serve.call_args[0][0]
            self.assertTrue(callable(wsgiapp))


    def test_main_run_file_subdir(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=False) as mock_isdir, \
             patch('os.path.isfile', side_effect=[True, False, False]) as mock_isfile, \
             patch('waitress.serve') as mock_waitress_serve:
            main(['-n', os.path.join('subdir', 'README.md')])

            self.assertEqual(stdout.getvalue(), 'markdown-up: Serving at http://127.0.0.1:8080/README.html ...\n')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_called_once_with(os.path.join('subdir', 'README.md'))
            self.assertEqual(mock_isfile.call_count, 3)
            mock_isfile.assert_has_calls([
                unittest.mock.call(os.path.join('subdir', 'README.md')),
                unittest.mock.call(os.path.join('subdir', 'markdown-up.json')),
                unittest.mock.call(os.path.join('subdir', 'markdown-up-api.json'))
            ])
            mock_waitress_serve.assert_called_once_with(ANY, port=8080, threads=8)
            wsgiapp = mock_waitress_serve.call_args[0][0]
            self.assertTrue(callable(wsgiapp))


    def test_main_run_file_html_subdir(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=False) as mock_isdir, \
             patch('os.path.isfile', side_effect=[True, False, False]) as mock_isfile, \
             patch('waitress.serve') as mock_waitress_serve:
            main(['-n', os.path.join('subdir', 'index.html')])

            self.assertEqual(stdout.getvalue(), 'markdown-up: Serving at http://127.0.0.1:8080/index.html ...\n')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_called_once_with(os.path.join('subdir', 'index.html'))
            self.assertEqual(mock_isfile.call_count, 3)
            mock_isfile.assert_has_calls([
                unittest.mock.call(os.path.join('subdir', 'index.html')),
                unittest.mock.call(os.path.join('subdir', 'markdown-up.json')),
                unittest.mock.call(os.path.join('subdir', 'markdown-up-api.json'))
            ])
            mock_waitress_serve.assert_called_once_with(ANY, port=8080, threads=8)
            wsgiapp = mock_waitress_serve.call_args[0][0]
            self.assertTrue(callable(wsgiapp))
