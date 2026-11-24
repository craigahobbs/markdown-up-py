# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

"""
The MarkdownUp backend command-line application
"""

import argparse
from functools import partial
import os
import sys
import threading
import webbrowser

import waitress

from .app import HTML_EXTS, MARKDOWN_EXTS, MarkdownUpApplication


def main(argv=None):
    """
    markdown-up command-line script main entry point
    """

    # Command line arguments
    argument_parser_args = {'prog': 'markdown-up'}
    if sys.version_info >= (3, 14): # pragma: no cover
        argument_parser_args['color'] = False
    parser = argparse.ArgumentParser(**argument_parser_args)
    parser.add_argument('path', nargs='?', default='.',
                        help='the file or directory to view (default is ".")')
    parser.add_argument('--host', metavar='HOST',
                        help='the host address to bind (default is "127.0.0.1"; "0.0.0.0" in release mode)')
    parser.add_argument('-p', '--port', metavar='N', type=int, default=8080,
                        help='the application port (default is 8080)')
    parser.add_argument('-t', '--threads', metavar='N', type=int, default=8,
                        help='the number of web server threads (default is 8)')
    parser.add_argument('-n', '--no-browser', action='store_true',
                        help="don't open a web browser")
    parser.add_argument('-r', '--release', action='store_true',
                        help="release mode (cache statics, remove documentation and index)")
    parser.add_argument('-q', '--quiet', action='store_true',
                        help="hide access logging")
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

    # Determine the host address to bind. By default, only release mode is reachable from other machines.
    bind_host = args.host or ('0.0.0.0' if args.release else '127.0.0.1')

    # Construct the URL - an any-address bind is viewed at its loopback address
    host = {'0.0.0.0': '127.0.0.1', '::': '::1'}.get(bind_host, bind_host)
    if ':' in host:
        host = f'[{host}]'
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
    if not args.release and not args.no_browser:
        webbrowser_thread = threading.Thread(target=webbrowser.open, args=(url,))
        webbrowser_thread.daemon = True
        webbrowser_thread.start()

    # Create the WSGI application
    wsgiapp = MarkdownUpApplication(root, release=args.release)
    wsgiapp_wrap = wsgiapp if args.quiet else partial(_wsgiapp_log_access, wsgiapp)

    # Host the application
    if not args.quiet:
        print(f'markdown-up: Serving at {url} ...')
    waitress.serve(wsgiapp_wrap, host=bind_host, port=args.port, threads=max(1, args.threads))


# WSGI application wrapper and the start_response function so we can log status and environ
def _wsgiapp_log_access(wsgiapp, environ, start_response):
    def log_start_response(status, response_headers):
        query_string = f' {environ["QUERY_STRING"]}' if environ['QUERY_STRING'] else ''
        print(f'markdown-up: {status[0:3]} {environ["REQUEST_METHOD"]} {environ["PATH_INFO"]}{query_string}')
        return start_response(status, response_headers)
    return wsgiapp(environ, log_start_response)
