# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

"""
The MarkdownUp launcher command-line application
"""

import argparse
from functools import partial
import json
import os
import threading
import webbrowser

import schema_markdown
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
    parser.add_argument('-t', metavar='N', dest='threads', type=int,
                        help='the number of web server threads (default is 8)')
    parser.add_argument('-n', dest='no_browser', action='store_true',
                        help="don't open a web browser")
    parser.add_argument('-r', dest='release', action='store_true',
                        help="release mode (cache statics, remove documentation and index)")
    parser.add_argument('-q', dest='quiet', action='store_true',
                        help="don't display access logging")
    parser.add_argument('-d', dest='debug', action='store_true', default=False,
                        help='backend debug mode')
    args = parser.parse_args(args=argv)

    # Load and validate the configuration file
    config_path = 'markdown-up.json'
    if os.path.isfile(config_path):
        with open(config_path, 'r', encoding='utf-8') as config_file:
            config = schema_markdown.validate_type(CONFIG_TYPES, 'MarkdownUpConfig', json.load(config_file))
    else:
        config = {}
    config['debug'] = args.debug if args.debug is not None else config.get('debug', False)
    config['release'] = args.release if args.release is not None else config.get('release', False)
    config['threads'] = max(1, args.threads if args.threads is not None else config.get('threads', 8))

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
    wsgiapp = MarkdownUpApplication(root, config)
    wsgiapp_wrap = wsgiapp if args.quiet else partial(_wsgiapp_log_access, wsgiapp)

    # Host the application
    if not args.quiet:
        print(f'markdown-up: Serving at {url} ...')
    waitress.serve(wsgiapp_wrap, port=args.port, threads=config['threads'])


# WSGI application wrapper and the start_response function so we can log status and environ
def _wsgiapp_log_access(wsgiapp, environ, start_response):
    def log_start_response(status, response_headers):
        print(f'markdown-up: {status[0:3]} {environ["REQUEST_METHOD"]} {environ["PATH_INFO"]} {environ["QUERY_STRING"]}')
        return start_response(status, response_headers)
    return wsgiapp(environ, log_start_response)


# The backend configuration schema
CONFIG_TYPES = schema_markdown.parse_schema_markdown('''\
# The MarkdownUp configuration file
struct MarkdownUpConfig

    # If true, run in release mode. Default is false.
    optional bool release

    # If true, run in debug mode. Default is false.
    optional bool debug

    # The number of backend server threads. Default is 8.
    optional int threads

    # The backend schema markdown files
    optional string[len > 0] schemas

    # The backend BareScript files
    optional string[len > 0] scripts

    # The backend APIs
    optional BackendAPI[len > 0] apis


# A backend API
struct BackendAPI

    # The schema action name
    string name

    # The script function name. If unspecified, use the schema action name.
    optional string function
''')
