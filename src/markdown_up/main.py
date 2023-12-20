# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

"""
The MarkdownUp launcher command-line application
"""

import argparse
import os
import webbrowser

from schema_markdown import encode_query_string
import gunicorn.app.base

from .app import HTML_EXTS, MarkdownUpApplication


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
    is_dir = os.path.isdir(args.path)
    is_file = not is_dir and os.path.isfile(args.path)
    if not is_file and not is_dir:
        parser.exit(message=f'"{args.path}" does not exist!\n', status=2)

    # Determine the root
    if is_file:
        root = os.path.dirname(args.path)
    else:
        root = args.path

    # Root must be a directory
    if root == '':
        root = '.'

    # Define the server's when_ready function
    host = '127.0.0.1'
    def when_ready(_):
        # Do nothing?
        if args.no_browser:
            return

        # Construct the URL
        if is_file:
            if args.path.endswith(HTML_EXTS):
                url = f'http://{host}:{args.port}/{os.path.basename(args.path)}'
            else:
                hash_args = encode_query_string({'url': os.path.basename(args.path)})
                url = f'http://{host}:{args.port}/#{hash_args}'
        else:
            url = f'http://{host}:{args.port}/'

        # Launch the web browser
        webbrowser.open(url)

    # Host the application
    StandaloneApplication(MarkdownUpApplication(root), {
        'access_log_format': '%(h)s %(l)s "%(r)s" %(s)s %(b)s',
        'accesslog': '-',
        'errorlog': '-',
        'bind': f'{host}:{args.port}',
        'workers': 2,
        'when_ready': when_ready
    }).run()


# A stand-alone WSGI server using Gunicorn - see https://docs.gunicorn.org/en/stable/custom.html
class StandaloneApplication(gunicorn.app.base.BaseApplication):
    # pylint: disable=abstract-method

    def __init__(self, application, options): # pragma: no cover
        self.options = options
        self.application = application
        super().__init__()

    def load_config(self): # pragma: no cover
        for key, value in self.options.items():
            self.cfg.set(key, value)

    def load(self): # pragma: no cover
        return self.application
