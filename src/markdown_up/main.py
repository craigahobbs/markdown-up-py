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
import waitress

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
        if args.path.endswith(HTML_EXTS):
            url = f'http://{host}:{args.port}/{os.path.basename(args.path)}'
        else:
            hash_args = encode_query_string({'url': os.path.basename(args.path)})
            url = f'http://{host}:{args.port}/#{hash_args}'
    else:
        url = f'http://{host}:{args.port}/'

    # Launch the web browser on a thread so the WSGI application can startup first
    if not args.no_browser:
        webbrowser_thread = threading.Thread(target=webbrowser.open, args=(url,))
        webbrowser_thread.daemon = True
        webbrowser_thread.start()

    # Create the WSGI application
    wsgiapp = MarkdownUpApplication(root)
    def wsgiapp_wrap(environ, start_response):
        if not args.quiet:
            print(f'markdown-up: {environ["REQUEST_METHOD"]} {environ["PATH_INFO"]} {environ["QUERY_STRING"]}')
        return wsgiapp(environ, start_response)

    # Host the application
    if not args.quiet:
        print(f'markdown-up: Serving at {url} ...')
    waitress.serve(wsgiapp_wrap, port=args.port)
