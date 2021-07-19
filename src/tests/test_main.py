# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up/blob/main/LICENSE

import argparse
from io import StringIO
import unittest
from unittest.mock import patch

import markdown_up.__main__
from markdown_up.app import MarkdownUpApplication
from markdown_up.main import GunicornApplication, main


class TestMain(unittest.TestCase):

    def test_main_submodule(self):
        self.assertTrue(markdown_up.__main__)

    def test_main_help(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr:
            with self.assertRaises(SystemExit) as cm_exc:
                main(['-h'])
        self.assertEqual(cm_exc.exception.code, 0)
        self.assertEqual(stdout.getvalue().splitlines()[0], 'usage: markdown-up [-h] [-p N] [-w N] [dir]')
        self.assertEqual(stderr.getvalue(), '')

    def test_main_run(self):
        with patch('sys.stdout', StringIO()) as stdout, \
             patch('sys.stderr', StringIO()) as stderr, \
             patch('gunicorn.app.base.BaseApplication.run') as mock_run:
            main([])
        self.assertEqual(stdout.getvalue(), '')
        self.assertEqual(stderr.getvalue(), '')
        self.assertEqual(mock_run.call_count, 1)
        mock_run.assert_called_with()

    def test_main_app(self):
        server = GunicornApplication(argparse.Namespace(dir='.', port=8080, workers=2))

        # Load the config
        server.load_config()
        self.assertEqual(server.cfg.settings['bind'].value, ['127.0.0.1:8080'])
        self.assertTrue(callable(server.cfg.settings['when_ready'].value))
        self.assertEqual(server.cfg.settings['workers'].value, 2)

        # Load the application
        app = server.load()
        self.assertIsInstance(app, MarkdownUpApplication)
        self.assertEqual(app.root, '.')

        # Open the web browser
        with patch('webbrowser.open') as mock_open:
            server.cfg.settings['when_ready'].value(argparse.Namespace(address=[('127.0.0.1', '8080')]))
            self.assertEqual(mock_open.call_count, 1)
            mock_open.assert_called_with('http://127.0.0.1:8080/')
