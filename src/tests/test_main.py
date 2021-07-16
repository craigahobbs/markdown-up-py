# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up/blob/main/LICENSE

from io import StringIO
import unittest
from unittest.mock import patch

import markdown_up.__main__
from markdown_up.main import main


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
