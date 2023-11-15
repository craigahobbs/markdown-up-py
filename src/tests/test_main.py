# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

from io import StringIO
import os
import unittest
from unittest.mock import ANY, patch

import markdown_up.__main__
from markdown_up.app import MarkdownUpApplication
from markdown_up.main import GunicornServer, main


class TestMain(unittest.TestCase):

    def test_main_submodule(self):
        self.assertTrue(markdown_up.__main__)

    def test_main_help(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isfile', False):
            with self.assertRaises(SystemExit) as cm_exc:
                main(['-h'])
        self.assertEqual(cm_exc.exception.code, 0)
        self.assertEqual(stdout.getvalue().splitlines()[0], 'usage: markdown-up [-h] [-p N] [-n] [path]')
        self.assertEqual(stderr.getvalue(), '')

    def test_main_file_not_found(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isfile', return_value=False) as mock_isfile:
            with self.assertRaises(SystemExit) as cm_exc:
                main([os.path.join('missing', 'README.md')])
        self.assertEqual(cm_exc.exception.code, 2)
        self.assertEqual(stdout.getvalue(), '')
        self.assertTrue(stderr.getvalue(), '"missing/README.md" does not exist!\n')
        mock_isfile.assert_called_with('missing/README.md')

    def test_main_dir_not_found(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=False) as mock_isdir:
            with self.assertRaises(SystemExit) as cm_exc:
                main(['missing'])
        self.assertEqual(cm_exc.exception.code, 2)
        self.assertEqual(stdout.getvalue(), '')
        self.assertEqual(stderr.getvalue(), '"missing" does not exist!\n')
        mock_isdir.assert_called_with('missing')

    def test_main_run(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=True) as mock_isfile, \
             patch('threading.Thread') as mock_thread, \
             patch('markdown_up.main.GunicornServer.make_server') as mock_make_server:
            main([])
        self.assertEqual(stdout.getvalue(), '')
        self.assertEqual(stderr.getvalue(), '')
        mock_isfile.assert_called_with('.')
        self.assertEqual(mock_thread.call_count, 1)
        mock_thread.assert_called_with(target=ANY, args=('http://127.0.0.1:8080/',))
        self.assertEqual(mock_make_server.call_count, 1)
        mock_make_server.assert_called_once_with('127.0.0.1', 8080, ANY)
        self.assertIsInstance(mock_make_server.mock_calls[0].args[2], MarkdownUpApplication)
        self.assertEqual(mock_make_server.mock_calls[0].args[2].root, '.')

    def test_main_run_port(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=True) as mock_isfile, \
             patch('threading.Thread') as mock_thread, \
             patch('markdown_up.main.GunicornServer.make_server') as mock_make_server:
            main(['-p', '8081'])
        self.assertEqual(stdout.getvalue(), '')
        self.assertEqual(stderr.getvalue(), '')
        mock_isfile.assert_called_with('.')
        self.assertEqual(mock_thread.call_count, 1)
        mock_thread.assert_called_with(target=ANY, args=('http://127.0.0.1:8081/',))
        self.assertEqual(mock_make_server.call_count, 1)
        mock_make_server.assert_called_once_with('127.0.0.1', 8081, ANY)
        self.assertIsInstance(mock_make_server.mock_calls[0].args[2], MarkdownUpApplication)
        self.assertEqual(mock_make_server.mock_calls[0].args[2].root, '.')

    def test_main_run_file(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isfile', return_value=True) as mock_isfile, \
             patch('threading.Thread') as mock_thread, \
             patch('markdown_up.main.GunicornServer.make_server') as mock_make_server:
            main(['README.md'])
        self.assertEqual(stdout.getvalue(), '')
        self.assertEqual(stderr.getvalue(), '')
        mock_isfile.assert_called_with('README.md')
        self.assertEqual(mock_thread.call_count, 1)
        mock_thread.assert_called_with(target=ANY, args=('http://127.0.0.1:8080/#url=README.md',))
        self.assertEqual(mock_make_server.call_count, 1)
        mock_make_server.assert_called_once_with('127.0.0.1', 8080, ANY)
        self.assertIsInstance(mock_make_server.mock_calls[0].args[2], MarkdownUpApplication)
        self.assertEqual(mock_make_server.mock_calls[0].args[2].root, '.')

    def test_main_run_file_subdir(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isfile', return_value=True) as mock_isfile, \
             patch('threading.Thread') as mock_thread, \
             patch('markdown_up.main.GunicornServer.make_server') as mock_make_server:
            main(['subdir/README.md'])
        self.assertEqual(stdout.getvalue(), '')
        self.assertEqual(stderr.getvalue(), '')
        mock_isfile.assert_called_with('subdir/README.md')
        self.assertEqual(mock_thread.call_count, 1)
        mock_thread.assert_called_with(target=ANY, args=('http://127.0.0.1:8080/#url=README.md',))
        self.assertEqual(mock_make_server.call_count, 1)
        mock_make_server.assert_called_once_with('127.0.0.1', 8080, ANY)
        self.assertIsInstance(mock_make_server.mock_calls[0].args[2], MarkdownUpApplication)
        self.assertEqual(mock_make_server.mock_calls[0].args[2].root, 'subdir')

    def test_main_run_no_browser(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=True) as mock_isfile, \
             patch('threading.Thread') as mock_thread, \
             patch('markdown_up.main.GunicornServer.make_server') as mock_make_server:
            main(['-n'])
        self.assertEqual(stdout.getvalue(), '')
        self.assertEqual(stderr.getvalue(), '')
        mock_isfile.assert_called_with('.')
        self.assertEqual(mock_thread.call_count, 0)
        self.assertEqual(mock_make_server.call_count, 1)
        mock_make_server.assert_called_once_with('127.0.0.1', 8080, ANY)
        self.assertIsInstance(mock_make_server.mock_calls[0].args[2], MarkdownUpApplication)
        self.assertEqual(mock_make_server.mock_calls[0].args[2].root, '.')

    def test_make_server(self):
        class TestServer(GunicornServer):
            # pylint: disable=abstract-method
            def run(self):
                testcase.assertIsInstance(self, GunicornServer)
                testcase.assertIs(self.callable, app)
                testcase.assertDictEqual(self.options, {
                    'accesslog': '-',
                    'errorlog': '-',
                    'bind': '127.0.0.1:8080',
                    'workers': 2
                })
                testcase.assertEqual(self.cfg.accesslog, '-')
                testcase.assertEqual(self.cfg.errorlog, '-')
                testcase.assertListEqual(self.cfg.bind, ['127.0.0.1:8080'])
                testcase.assertEqual(self.cfg.workers, 2)

        testcase = self
        app = MarkdownUpApplication('.')
        TestServer.make_server('127.0.0.1', 8080, app)
