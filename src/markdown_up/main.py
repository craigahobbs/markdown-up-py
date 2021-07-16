# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up/blob/main/LICENSE

import argparse
import webbrowser

import gunicorn.app.base

from .app import MarkdownUpApplication


def main(argv=None):

    # Command line parsing
    parser = argparse.ArgumentParser(prog='markdown-up')
    parser.add_argument('dir', nargs='?', default='.',
                        help='The directory of markdown files to host (default is ".")')
    parser.add_argument('-p', metavar='N', dest='port', type=int, default=8080,
                        help='The application port (default is 8080)')
    parser.add_argument('-w', metavar='N', dest='workers', type=int, default=2,
                        help='The number of application workers (default is 2)')
    args = parser.parse_args(args=argv)

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
            webbrowser.open(f'http://{host}:{port}/')

        # When ready, open the web broswer
        self.cfg.set('when_ready', load_browser)

    def load(self):
        return MarkdownUpApplication(self.args.dir)
