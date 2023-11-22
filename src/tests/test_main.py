# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

from io import StringIO
import os
import unittest
from unittest.mock import ANY, patch

import markdown_up.__main__
from markdown_up.app import MarkdownUpApplication
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
            self.assertEqual(stdout.getvalue().splitlines()[0], 'usage: markdown-up [-h] [-p N] [-n] [path]')
            self.assertEqual(stderr.getvalue(), '')

    def test_main_file_not_found(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=False) as mock_isdir, \
             patch('os.path.isfile', return_value=False) as mock_isfile:
            with self.assertRaises(SystemExit) as cm_exc:
                main([os.path.join('missing', 'README.md')])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '"missing/README.md" does not exist!\n')
            mock_isdir.assert_called_once_with('missing/README.md')
            mock_isfile.assert_called_once_with('missing/README.md')
            self.assertEqual(cm_exc.exception.code, 2)
            self.assertEqual(stdout.getvalue(), '')
            self.assertTrue(stderr.getvalue(), '"missing/README.md" does not exist!\n')
            mock_isfile.assert_called_once_with('missing/README.md')

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
             patch('webbrowser.open') as mock_webbrowser_open, \
             patch('markdown_up.main.StandaloneApplication') as mock_server:
            main([])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_called_once_with('.')
            mock_isfile.assert_not_called()
            mock_webbrowser_open.assert_not_called()
            mock_server.assert_called_once_with(ANY, {
                'access_log_format': '%(h)s %(l)s "%(r)s" %(s)s %(b)s',
                'accesslog': '-',
                'errorlog': '-',
                'bind': '127.0.0.1:8080',
                'workers': 2,
                'when_ready': ANY
            })
            mock_server.return_value.run.assert_called_once_with()
            self.assertIsInstance(mock_server.mock_calls[0].args[0], MarkdownUpApplication)
            self.assertEqual(mock_server.mock_calls[0].args[0].root, '.')
            when_ready = mock_server.mock_calls[0].args[1]['when_ready']
            self.assertTrue(callable(when_ready))
            when_ready(None)
            mock_webbrowser_open.assert_called_once_with('http://127.0.0.1:8080/')

    def test_main_run_port(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=True) as mock_isdir, \
             patch('os.path.isfile', return_value=False) as mock_isfile, \
             patch('webbrowser.open') as mock_webbrowser_open, \
             patch('markdown_up.main.StandaloneApplication') as mock_server:
            main(['-p', '8081'])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_called_once_with('.')
            mock_isfile.assert_not_called()
            mock_webbrowser_open.assert_not_called()
            mock_server.assert_called_once_with(ANY, {
                'access_log_format': '%(h)s %(l)s "%(r)s" %(s)s %(b)s',
                'accesslog': '-',
                'errorlog': '-',
                'bind': '127.0.0.1:8081',
                'workers': 2,
                'when_ready': ANY
            })
            mock_server.return_value.run.assert_called_once_with()
            self.assertIsInstance(mock_server.mock_calls[0].args[0], MarkdownUpApplication)
            self.assertEqual(mock_server.mock_calls[0].args[0].root, '.')
            when_ready = mock_server.mock_calls[0].args[1]['when_ready']
            self.assertTrue(callable(when_ready))
            when_ready(None)
            mock_webbrowser_open.assert_called_once_with('http://127.0.0.1:8081/')

    def test_main_run_file(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=False) as mock_isdir, \
             patch('os.path.isfile', return_value=True) as mock_isfile, \
             patch('webbrowser.open') as mock_webbrowser_open, \
             patch('markdown_up.main.StandaloneApplication') as mock_server:
            main(['README.md'])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_called_once_with('README.md')
            mock_isfile.assert_called_once_with('README.md')
            mock_webbrowser_open.assert_not_called()
            mock_server.assert_called_once_with(ANY, {
                'access_log_format': '%(h)s %(l)s "%(r)s" %(s)s %(b)s',
                'accesslog': '-',
                'errorlog': '-',
                'bind': '127.0.0.1:8080',
                'workers': 2,
                'when_ready': ANY
            })
            mock_server.return_value.run.assert_called_once_with()
            self.assertIsInstance(mock_server.mock_calls[0].args[0], MarkdownUpApplication)
            self.assertEqual(mock_server.mock_calls[0].args[0].root, '.')
            when_ready = mock_server.mock_calls[0].args[1]['when_ready']
            self.assertTrue(callable(when_ready))
            when_ready(None)
            mock_webbrowser_open.assert_called_once_with('http://127.0.0.1:8080/#url=README.md')

    def test_main_run_file_subdir(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=False) as mock_isdir, \
             patch('os.path.isfile', return_value=True) as mock_isfile, \
             patch('webbrowser.open') as mock_webbrowser_open, \
             patch('markdown_up.main.StandaloneApplication') as mock_server:
            main(['subdir/README.md'])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_called_once_with('subdir/README.md')
            mock_isfile.assert_called_once_with('subdir/README.md')
            mock_webbrowser_open.assert_not_called()
            mock_server.assert_called_once_with(ANY, {
                'access_log_format': '%(h)s %(l)s "%(r)s" %(s)s %(b)s',
                'accesslog': '-',
                'errorlog': '-',
                'bind': '127.0.0.1:8080',
                'workers': 2,
                'when_ready': ANY
            })
            mock_server.return_value.run.assert_called_once_with()
            self.assertIsInstance(mock_server.mock_calls[0].args[0], MarkdownUpApplication)
            self.assertEqual(mock_server.mock_calls[0].args[0].root, 'subdir')
            when_ready = mock_server.mock_calls[0].args[1]['when_ready']
            self.assertTrue(callable(when_ready))
            when_ready(None)
            mock_webbrowser_open.assert_called_once_with('http://127.0.0.1:8080/#url=README.md')

    def test_main_run_no_browser(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=True) as mock_isdir, \
             patch('os.path.isfile', return_value=False) as mock_isfile, \
             patch('webbrowser.open') as mock_webbrowser_open, \
             patch('markdown_up.main.StandaloneApplication') as mock_server:
            main(['-n'])

            self.assertEqual(stdout.getvalue(), '')
            self.assertEqual(stderr.getvalue(), '')
            mock_isdir.assert_called_once_with('.')
            mock_isfile.assert_not_called()
            mock_webbrowser_open.assert_not_called()
            mock_server.assert_called_once_with(ANY, {
                'access_log_format': '%(h)s %(l)s "%(r)s" %(s)s %(b)s',
                'accesslog': '-',
                'errorlog': '-',
                'bind': '127.0.0.1:8080',
                'workers': 2,
                'when_ready': ANY
            })
            mock_server.return_value.run.assert_called_once_with()
            self.assertIsInstance(mock_server.mock_calls[0].args[0], MarkdownUpApplication)
            self.assertEqual(mock_server.mock_calls[0].args[0].root, '.')
            when_ready = mock_server.mock_calls[0].args[1]['when_ready']
            self.assertTrue(callable(when_ready))
            when_ready(None)
            mock_webbrowser_open.assert_not_called()
