# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

"""
The MarkdownUp launcher command-line application
"""

import argparse
from functools import partial
import os
import threading
import webbrowser

import waitress

from .app import HTML_EXTS, MARKDOWN_EXTS, MarkdownUpApplication


def main(argv=None):
    """
    markdown-up command-line script main entry point
    """

    # Command line arguments
    parser = argparse.ArgumentParser(prog='markdown-up')
    parser.add_argument('path', nargs='?', default='.',
                        help='the file or directory to view (default is ".")')
    parser.add_argument('-p', metavar='N', dest='port', type=int, default=8080,
                        help='the application port (default is 8080)')
    parser.add_argument('-t', metavar='N', dest='threads', type=int, default=8,
                        help='the number of web server threads (default is 8)')
    parser.add_argument('-n', dest='no_browser', action='store_true',
                        help="don't open a web browser")
    parser.add_argument('-r', dest='release', action='store_true',
                        help="release mode (cache statics, remove documentation and index)")
    parser.add_argument('-q', dest='quiet', action='store_true',
                        help="don't display access logging")
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

    # Construct the URL
    host = '127.0.0.1'
    if is_file:
        path_base = os.path.basename(args.path)
        path_root, path_ext = os.path.splitext(path_base)
        if path_ext in MARKDOWN_EXTS:
            url = f'http://{host}:{args.port}/{path_root}{HTML_EXTS[0]}'
        else:
            url = f'http://{host}:{args.port}/{path_base}'
    else:
        url = f'http://{host}:{args.port}/'

    # Launch the web browser on a thread so the WSGI application can startup first
    if not args.no_browser:
        webbrowser_thread = threading.Thread(target=webbrowser.open, args=(url,))
        webbrowser_thread.daemon = True
        webbrowser_thread.start()

    # Create the WSGI application
    wsgiapp = MarkdownUpApplication(root, args.release)
    wsgiapp_wrap = wsgiapp if args.quiet else partial(_wsgiapp_log_access, wsgiapp)

    # Host the application
    if not args.quiet:
        print(f'markdown-up: Serving at {url} ...')
    waitress.serve(wsgiapp_wrap, port=args.port, threads=max(args.threads, 1))


# WSGI application wrapper and the start_response function so we can log status and environ
def _wsgiapp_log_access(wsgiapp, environ, start_response):
    def log_start_response(status, response_headers):
        print(f'markdown-up: {status[0:3]} {environ["REQUEST_METHOD"]} {environ["PATH_INFO"]} {environ["QUERY_STRING"]}')
        return start_response(status, response_headers)
    return wsgiapp(environ, log_start_response)
