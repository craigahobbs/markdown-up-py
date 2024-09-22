# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

from io import StringIO
import os
import unittest
from unittest.mock import ANY, patch

import chisel

import markdown_up.__main__
from markdown_up.main import main


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
            self.assertEqual(stdout.getvalue().splitlines()[0], 'usage: markdown-up [-h] [-p N] [-n] [-q] [path]')
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
            mock_isfile.assert_called_once_with(os.path.join('missing', 'README.md'))


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
            mock_isdir.assert_called_once_with('missing')


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
            mock_isfile.assert_not_called()
            mock_thread.assert_called_once_with(target=ANY, args=('http://127.0.0.1:8080/',))
            thread_fn = mock_thread.call_args.kwargs['target']
            self.assertTrue(callable(thread_fn))
            mock_waitress_serve.assert_called_once_with(ANY, port=8080)
            wsgiapp = mock_waitress_serve.call_args[0][0]
            self.assertTrue(callable(wsgiapp))

            # Test calling the WSGI application
            environ = chisel.Context.create_environ('GET', '/doc')
            start_response = chisel.app.StartResponse()
            content = wsgiapp(environ, start_response)
            self.assertEqual(start_response.status, '301 Moved Permanently')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain'), ('Location', '/doc/')])
            self.assertEqual(content, [b'/doc/'])
            self.assertEqual(stdout.getvalue(), 'markdown-up: Serving at http://127.0.0.1:8080/ ...\nmarkdown-up: 301 GET /doc \n')
            self.assertEqual(stderr.getvalue(), '')


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
            mock_isfile.assert_not_called()
            mock_thread.assert_not_called()
            mock_waitress_serve.assert_called_once_with(ANY, port=8080)
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
            mock_isfile.assert_not_called()
            mock_waitress_serve.assert_called_once_with(ANY, port=8080)
            wsgiapp = mock_waitress_serve.call_args[0][0]
            self.assertTrue(callable(wsgiapp))

            # Test calling the WSGI application
            environ = chisel.Context.create_environ('GET', '/doc')
            start_response = chisel.app.StartResponse()
            content = wsgiapp(environ, start_response)
            self.assertEqual(start_response.status, '301 Moved Permanently')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain'), ('Location', '/doc/')])
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
            mock_isfile.assert_not_called()
            mock_waitress_serve.assert_called_once_with(ANY, port=8081)
            wsgiapp = mock_waitress_serve.call_args[0][0]
            self.assertTrue(callable(wsgiapp))


    def test_main_run_file(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=False) as mock_isdir, \
             patch('os.path.isfile', return_value=True) as mock_isfile, \
             patch('waitress.serve') as mock_waitress_serve:
            main(['-n', 'README.md'])

            self.assertEqual(stdout.getvalue(), 'markdown-up: Serving at http://127.0.0.1:8080/#url=README.md ...\n')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_called_once_with('README.md')
            mock_isfile.assert_called_once_with('README.md')
            mock_waitress_serve.assert_called_once_with(ANY, port=8080)
            wsgiapp = mock_waitress_serve.call_args[0][0]
            self.assertTrue(callable(wsgiapp))


    def test_main_run_file_html(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=False) as mock_isdir, \
             patch('os.path.isfile', return_value=True) as mock_isfile, \
             patch('waitress.serve') as mock_waitress_serve:
            main(['-n', 'index.html'])

            self.assertEqual(stdout.getvalue(), 'markdown-up: Serving at http://127.0.0.1:8080/index.html ...\n')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_called_once_with('index.html')
            mock_isfile.assert_called_once_with('index.html')
            mock_waitress_serve.assert_called_once_with(ANY, port=8080)
            wsgiapp = mock_waitress_serve.call_args[0][0]
            self.assertTrue(callable(wsgiapp))


    def test_main_run_file_subdir(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=False) as mock_isdir, \
             patch('os.path.isfile', return_value=True) as mock_isfile, \
             patch('waitress.serve') as mock_waitress_serve:
            main(['-n', 'subdir/README.md'])

            self.assertEqual(stdout.getvalue(), 'markdown-up: Serving at http://127.0.0.1:8080/#url=README.md ...\n')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_called_once_with('subdir/README.md')
            mock_isfile.assert_called_once_with('subdir/README.md')
            mock_waitress_serve.assert_called_once_with(ANY, port=8080)
            wsgiapp = mock_waitress_serve.call_args[0][0]
            self.assertTrue(callable(wsgiapp))


    def test_main_run_file_html_subdir(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=False) as mock_isdir, \
             patch('os.path.isfile', return_value=True) as mock_isfile, \
             patch('waitress.serve') as mock_waitress_serve:
            main(['-n', 'subdir/index.html'])

            self.assertEqual(stdout.getvalue(), 'markdown-up: Serving at http://127.0.0.1:8080/index.html ...\n')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_called_once_with('subdir/index.html')
            mock_isfile.assert_called_once_with('subdir/index.html')
            mock_waitress_serve.assert_called_once_with(ANY, port=8080)
            wsgiapp = mock_waitress_serve.call_args[0][0]
            self.assertTrue(callable(wsgiapp))
