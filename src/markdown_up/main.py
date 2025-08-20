# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

"""
The MarkdownUp backend command-line application
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
    parser.add_argument('-p', '--port', metavar='N', type=int, default=8080,
                        help='the application port (default is 8080)')
    parser.add_argument('-t', '--threads', metavar='N', type=int,
                        help='the number of web server threads (default is 8)')
    parser.add_argument('-n', '--no-browser', action='store_true',
                        help="don't open a web browser")
    parser.add_argument('-r', '--release', action='store_true', default=None,
                        help="release mode (cache statics, remove documentation and index)")
    parser.add_argument('-q', '--quiet', action='store_true',
                        help="hide access logging")
    parser.add_argument('-d', '--debug', action='store_true', default=None,
                        help='backend debug mode')
    parser.add_argument('-v', '--var', nargs=2, action='append', metavar=('VAR', 'EXPR'), default = [],
                        help='set a backend global variable')
    parser.add_argument('-c', '--config', metavar='FILE', default='markdown-up.json',
                        help='the application config filename (default is "markdown-up.json")')
    parser.add_argument('-a', '--api', metavar='FILE', default='markdown-up-api.json',
                        help='the API config filename (default is "markdown-up-api.json")')
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

    # Load and validate the configuration file
    config_path = os.path.normpath(os.path.join(root, args.config))
    if os.path.isfile(config_path):
        with open(config_path, 'r', encoding='utf-8') as config_file:
            config = schema_markdown.validate_type(CONFIG_TYPES, 'MarkdownUpConfig', json.load(config_file))
    else:
        config = {}

    # Load and validate the API configuration file
    api_path = os.path.normpath(os.path.join(root, args.api))
    if os.path.isfile(api_path):
        with open(api_path, 'r', encoding='utf-8') as api_file:
            api_config = schema_markdown.validate_type(CONFIG_TYPES, 'MarkdownUpAPIConfig', json.load(api_file))
    else:
        api_config = None

    # Add argumentsg to the config
    config['debug'] = args.debug if args.debug is not None else config.get('debug', False)
    config['release'] = args.release if args.release is not None else config.get('release', False)
    config['threads'] = max(1, args.threads if args.threads is not None else config.get('threads', 8))
    if args.var:
        if 'globals' not in config:
            config['globals'] = {}
        for key, value in args.var:
            config['globals'][key] = value

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
    if not config['release'] and not args.no_browser:
        webbrowser_thread = threading.Thread(target=webbrowser.open, args=(url,))
        webbrowser_thread.daemon = True
        webbrowser_thread.start()

    # Create the WSGI application
    wsgiapp = MarkdownUpApplication(root, config, api_config)
    wsgiapp_wrap = wsgiapp if args.quiet else partial(_wsgiapp_log_access, wsgiapp)

    # Host the application
    if not args.quiet:
        print(f'markdown-up: Serving at {url} ...')
    waitress.serve(wsgiapp_wrap, port=args.port, threads=config['threads'])


# WSGI application wrapper and the start_response function so we can log status and environ
def _wsgiapp_log_access(wsgiapp, environ, start_response):
    def log_start_response(status, response_headers):
        query_string = f' {environ["QUERY_STRING"]}' if environ['QUERY_STRING'] else ''
        print(f'markdown-up: {status[0:3]} {environ["REQUEST_METHOD"]} {environ["PATH_INFO"]}{query_string}')
        return start_response(status, response_headers)
    return wsgiapp(environ, log_start_response)


# The backend configuration schema
CONFIG_TYPES = schema_markdown.parse_schema_markdown('''\
group "Application Configuration"


# The MarkdownUp application configuration (e.g. `markdown-up.json`)
struct MarkdownUpConfig

    # If true, run in release mode. Default is false.
    optional bool release

    # If true, run in debug mode. Default is false.
    optional bool debug

    # The number of backend server threads. Default is 8.
    optional int threads

    # Global variables
    optional string{} globals


group "API Configuration"


# The MarkdownUp API configuration (e.g. `markdown-up-api.json`)
struct MarkdownUpAPIConfig

    # The API schema markdown POSIX file paths
    string[] schemas

    # The API BareScript POSIX file paths
    string[] scripts

    # The APIs
    MarkdownUpAPI[] apis


group


# An API
struct MarkdownUpAPI

    # The schema action name
    string name

    # The script function name. If unspecified, use the schema action name.
    optional string function

    # If true, the API function has a WSGI respone (e.g. `["200 Status", [["Content-Type": "text/plain"]], "Hello!"]`)
    # Default is false.
    optional bool wsgi
''')
