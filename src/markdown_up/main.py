# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up/blob/main/LICENSE

import argparse
import os
import webbrowser

import gunicorn.app.base
from schema_markdown import encode_query_string

from .app import MarkdownUpApplication, is_markdown_file


def main(argv=None):

    # Command line parsing
    parser = argparse.ArgumentParser(prog='markdown-up')
    parser.add_argument('path', nargs='?', default='.',
                        help='The markdown file or directory to view (default is ".")')
    parser.add_argument('-p', metavar='N', dest='port', type=int, default=8080,
                        help='The application port (default is 8080)')
    parser.add_argument('-w', metavar='N', dest='workers', type=int, default=2,
                        help='The number of application workers (default is 2)')
    args = parser.parse_args(args=argv)

    # Verify the path exists
    is_file = is_markdown_file(args.path)
    if (is_file and not os.path.isfile(args.path)) or (not is_file and not os.path.isdir(args.path)):
        parser.exit(message=f'"{args.path}" does not exist!\n', status=2)

    # Run the application
    GunicornApplication(args).run()


class GunicornApplication(gunicorn.app.base.BaseApplication):
    # pylint: disable=abstract-method

    def __init__(self, args):
        self.args = args
        super().__init__()

    def load_config(self):
        self.cfg.set('bind', f'127.0.0.1:{self.args.port}')
        self.cfg.set('workers', self.args.workers)
        self.cfg.set('accesslog', '-')
        self.cfg.set('errorlog', '-')
        self.cfg.set('loglevel', 'warning')

        # Helper function to load the web browser
        def load_browser(server):
            host, port = server.address[0]
            url = f'http://{host}:{port}/'

            # Opening a file?
            if is_markdown_file(self.args.path):
                url += f'?{encode_query_string(dict(path=os.path.basename(self.args.path)))}'

            webbrowser.open(url)

        # When ready, open the web broswer
        self.cfg.set('when_ready', load_browser)

    def load(self):
        # Determine the root
        if is_markdown_file(self.args.path):
            root = os.path.dirname(self.args.path)
        else:
            root = self.args.path

        # Root must be a directory
        if root == '':
            root = '.'

        return MarkdownUpApplication(root)
