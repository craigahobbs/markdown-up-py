# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

"""
The MarkdownUp launcher command-line application
"""

import argparse
import os
import threading
import webbrowser

from schema_markdown import encode_query_string
import gunicorn.app.base

from .app import MarkdownUpApplication


def main(argv=None):
    """
    markdown-up command-line script main entry point
    """

    # Command line arguments
    parser = argparse.ArgumentParser(prog='markdown-up')
    parser.add_argument('path', nargs='?', default='.',
                        help='the markdown file or directory to view (default is ".")')
    parser.add_argument('-p', metavar='N', dest='port', type=int, default=8080,
                        help='the application port (default is 8080)')
    parser.add_argument('-n', dest='no_browser', action='store_true',
                        help="don't open a web browser")
    args = parser.parse_args(args=argv)

    # Verify the path exists
    is_file = args.path.endswith('.md')
    if (is_file and not os.path.isfile(args.path)) or (not is_file and not os.path.isdir(args.path)):
        parser.exit(message=f'"{args.path}" does not exist!\n', status=2)

    # Determine the root
    if is_file:
        root = os.path.dirname(args.path)
    else:
        root = args.path

    # Root must be a directory
    if root == '':
        root = '.'

    # Construct the URL
    host = '127.0.0.1'
    url = f'http://{host}:{args.port}/'
    if is_file:
        # pylint: disable=use-dict-literal
        url += f'#{encode_query_string(dict(url=os.path.basename(args.path)))}'

    # Launch the web browser on a thread as webbrowser.open may block
    if not args.no_browser:
        webbrowser_thread = threading.Thread(target=webbrowser.open, args=(url,))
        webbrowser_thread.daemon = True
        webbrowser_thread.start()

    # Host
    GunicornServer.make_server(host, args.port, MarkdownUpApplication(root))



# A stand-alone WSGI application using Gunicorn
class GunicornServer(gunicorn.app.base.BaseApplication):
    # pylint: disable=abstract-method

    def __init__(self, host, port, app):
        self.options = {
            'accesslog': '-',
            'errorlog': '-',
            'bind': f'{host}:{port}',
            'workers': 2
        }
        super().__init__()
        self.callable = app

    def load_config(self):
        for key, value in self.options.items():
            self.cfg.set(key, value)

    @classmethod
    def make_server(cls, host, port, app):
        cls(host, port, app).run()
