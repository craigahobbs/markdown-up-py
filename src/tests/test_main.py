# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

from io import StringIO
import os
import unittest
from unittest.mock import ANY, patch

import markdown_up.__main__
from markdown_up.main import main


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
             patch('wsgiref.simple_server.make_server') as mock_make_server:
            main([])
        self.assertEqual(stdout.getvalue(), 'Serving at http://127.0.0.1:8080/ ...\n')
        self.assertEqual(stderr.getvalue(), '')
        mock_isfile.assert_called_with('.')
        self.assertEqual(mock_thread.call_count, 1)
        mock_thread.assert_called_with(target=ANY, args=('http://127.0.0.1:8080/',))
        self.assertEqual(mock_make_server.call_count, 1)
        mock_make_server.assert_called_with('127.0.0.1', 8080, ANY)

    def test_main_run_file(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isfile', return_value=True) as mock_isfile, \
             patch('threading.Thread') as mock_thread, \
             patch('wsgiref.simple_server.make_server') as mock_make_server:
            main(['README.md'])
        self.assertEqual(stdout.getvalue(), 'Serving at http://127.0.0.1:8080/#url=README.md ...\n')
        self.assertEqual(stderr.getvalue(), '')
        mock_isfile.assert_called_with('README.md')
        self.assertEqual(mock_thread.call_count, 1)
        mock_thread.assert_called_with(target=ANY, args=('http://127.0.0.1:8080/#url=README.md',))
        self.assertEqual(mock_make_server.call_count, 1)
        mock_make_server.assert_called_with('127.0.0.1', 8080, ANY)

    def test_main_run_no_browser(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('os.path.isdir', return_value=True) as mock_isfile, \
             patch('threading.Thread') as mock_thread, \
             patch('wsgiref.simple_server.make_server') as mock_make_server:
            main(['-n'])
        self.assertEqual(stdout.getvalue(), 'Serving at http://127.0.0.1:8080/ ...\n')
        self.assertEqual(stderr.getvalue(), '')
        mock_isfile.assert_called_with('.')
        self.assertEqual(mock_thread.call_count, 0)
        self.assertEqual(mock_make_server.call_count, 1)
        mock_make_server.assert_called_with('127.0.0.1', 8080, ANY)
