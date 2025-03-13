# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

"""
The MarkdownUp launcher back-end application
"""

from functools import partial
from http import HTTPStatus
import importlib.resources
import json
import os
from pathlib import PurePosixPath
import tarfile

import bare_script
import chisel
import schema_markdown


class MarkdownUpApplication(chisel.Application):
    """
    The markdown-up back-end API WSGI application class
    """

    __slots__ = ('root',)


    def __init__(self, root):
        super().__init__()
        self.root = root

        # Add the chisel documentation application
        self.add_requests(chisel.create_doc_requests(markdown_up='../markdown-up/'))

        # Add the markdown-up APIs
        self.add_request(markdown_up_index)

        # Add the markdown-up index statics
        self.add_static('index.html', urls=(('GET', '/'),))
        self.add_static('markdownUpIndex.bare')

        # Markdown-Up application statics
        with importlib.resources.files('markdown_up.static').joinpath('markdown-up.tar.gz').open('rb') as tgz:
            with tarfile.open(fileobj=tgz, mode='r:gz') as tar:
                for member in tar.getmembers():
                    if member.isfile():
                        self.add_request(chisel.StaticRequest(
                            member.name,
                            tar.extractfile(member).read(),
                            content_type=_CONTENT_TYPES.get(os.path.splitext(member.name)[1], 'text/plain; charset=utf-8'),
                            urls=(('GET', None),),
                            doc_group='MarkdownUp Statics'
                        ))

        # Add the backend APIs
        self.add_backend()


    def add_static(self, filename, urls=(('GET', None),), doc_group='MarkdownUp Index Statics'):
        content_type = _CONTENT_TYPES.get(os.path.splitext(filename)[1], 'text/plain; charset=utf-8')
        with importlib.resources.files('markdown_up.static').joinpath(filename).open('rb') as fh:
            self.add_request(chisel.StaticRequest(filename, fh.read(), content_type, urls, doc_group=doc_group))


    def add_backend(self):
        backend_path = 'markdown-up.json'

        # Read the "markdown-up.json" file - do nothing if it doesn't exist
        if not os.path.isfile(backend_path):
            return
        with open(backend_path, 'r', encoding='utf-8') as backend_file:
            backend = schema_markdown.validate_type(BACKEND_TYPES, 'BackendConfig', json.load(backend_file))

        # Load the schema markdown files
        types = {}
        for smd_path in backend['schemaFiles']:
            with open(smd_path, 'r', encoding='utf-8') as smd_file:
                schema_markdown.parse_schema_markdown(smd_file, types, filename=smd_path, validate=False)
        schema_markdown.validate_type_model(types)

        # Add an action for each backend API
        for api in backend['apis']:

            # Parse the script
            with open(api['script'], 'r', encoding='utf-8') as script_file:
                script = bare_script.parse_script(script_file)
            script_globals = {}
            script_options = {
                'fetchFn': bare_script.fetch_read_write,
                'globals': script_globals,
                'logFn': bare_script.log_stdout,
                'urlFile': bare_script.url_file_relative,
                'systemPrefix': 'https://craigahobbs.github.io/markdown-up/include/'
            }
            bare_script.execute_script(script, script_options)

            # Add the API action
            script_fn = script_globals[api['name']]
            action_fn = partial(_bare_script_action_fn, script_fn, script_options)
            self.add_request(chisel.Action(action_fn, name=api['name'], types=types))


    def __call__(self, environ, start_response):
        request_method = environ['REQUEST_METHOD']
        path_info = environ['PATH_INFO']

        # Chisel API request? Otherwise, its a static request...
        request, _ = self.match_request(request_method, path_info)
        if request is not None:
            return super().__call__(environ, start_response)

        # Compute the static file path
        posix_path_info = PurePosixPath(path_info)
        path = os.path.join(self.root, *posix_path_info.parts[1:])

        # Directory index file?
        if os.path.isdir(path):
            for index_file in INDEX_FILES:
                index_posix_path = posix_path_info.joinpath(index_file)
                index_path = os.path.join(self.root, *index_posix_path.parts[1:])
                if os.path.isfile(index_path):
                    posix_path_info = index_posix_path
                    path = index_path
                    break

        # Read the static file
        try:
            # Unknown method or content type?
            content_type = STATIC_EXT_TO_CONTENT_TYPE.get(posix_path_info.suffix)
            if request_method != 'GET' or content_type is None:
                raise FileNotFoundError(path)

            # Read the static file
            with open(path, 'rb') as path_file:
                status = HTTPStatus.OK
                content = path_file.read()
        except FileNotFoundError:
            status = HTTPStatus.NOT_FOUND
            content = status.phrase.encode(encoding='utf-8')
            content_type = 'text/plain; charset=utf-8'
        except: # pylint: disable=bare-except
            status = HTTPStatus.INTERNAL_SERVER_ERROR
            content = status.phrase.encode(encoding='utf-8')
            content_type = 'text/plain; charset=utf-8'

        # Static response
        start_response(f'{status.value} {status.phrase}', [('Content-Type', content_type)])
        return [content]


# Action function wrapper for a MarkdownUp backend API function
def _bare_script_action_fn(script_fn, script_options, _ctx, req):
    return script_fn([req], script_options)


# The backend configuration schema
BACKEND_TYPES = schema_markdown.parse_schema_markdown('''\
# The MarkdownUp backend API configuration file schemax
struct BackendConfig

    # The list of schema markdown files
    string[] schemaFiles

    # The list of APIs
    BackendAPI[] apis


# The backend API model
struct BackendAPI

    # The API name
    string name

    # The BareScript file containing the API function
    string script
''')


_CONTENT_TYPES = {
    '.css': 'text/css; charset=utf-8',
    '.js': 'text/javascript; charset=utf-8',
    '.html': 'text/html; charset=utf-8'
}


# The map of static file extension to content-type
STATIC_EXT_TO_CONTENT_TYPE = {
    '.bare': 'text/plain; charset=utf-8',
    '.css': 'text/css',
    '.csv': 'text/csv',
    '.gif': 'image/gif',
    '.htm': 'text/html; charset=utf-8',
    '.html': 'text/html; charset=utf-8',
    '.jpeg': 'image/jpeg',
    '.jpg': 'image/jpeg',
    '.js': 'application/javascript',
    '.json': 'application/json',
    '.markdown': 'text/markdown; charset=utf-8',
    '.md': 'text/markdown; charset=utf-8',
    '.mds': 'text/plain; charset=utf-8',
    '.png': 'image/png',
    '.smd': 'text/plain; charset=utf-8',
    '.svg': 'image/svg+xml',
    '.tif': 'image/tiff',
    '.tiff': 'image/tiff',
    '.webp': 'image/webp'
}
MARKDOWN_EXTS = ('.md', '.markdown')
HTML_EXTS = ('.html', '.htm')
INDEX_FILES = ('index.html', 'index.htm')


@chisel.action(spec='''\
group "MarkdownUp Index API"

# The MarkdownUp launcher index API
action markdown_up_index
    urls
        GET

    query
        # The relative sub-directory path
        optional string(len > 0) path

    output
        # The index path
        string path

        # The parent path
        optional string parent

        # The path's Markdown files
        optional string[len > 0] files

        # The path's HTML files
        optional string[len > 0] htmlFiles

        # The path's sub-directories
        optional string[len > 0] directories

    errors
        # The path is invalid
        InvalidPath
''')
def markdown_up_index(ctx, req):

    # Validate the path
    posix_path = PurePosixPath(req['path'] if 'path' in req else '')
    if posix_path.is_absolute() or any(part == '..' for part in posix_path.parts):
        raise chisel.ActionError('InvalidPath')

    # Verify that the path exists
    path = os.path.join(ctx.app.root, *posix_path.parts)
    if not os.path.isdir(path):
        raise chisel.ActionError('InvalidPath')

    # Compute parent path
    parent_path = str(posix_path.parent) if 'path' in req else None

    # Get the list of markdown files and sub-directories from the current sub-directory
    files = []
    html_files = []
    directories = []
    for entry in os.scandir(path):
        if entry.is_dir() and not entry.name.startswith('.'):
            directories.append(entry.name)
        elif entry.is_file(): # pragma: no branch
            if entry.name.endswith(MARKDOWN_EXTS):
                files.append(entry.name)
            if entry.name.endswith(HTML_EXTS):
                html_files.append(entry.name)

    # Return the response
    response = {'path': path}
    if parent_path is not None and parent_path != '.':
        response['parent'] = parent_path
    if files:
        response['files'] = sorted(files)
    if html_files:
        response['htmlFiles'] = sorted(html_files)
    if directories:
        response['directories'] = sorted(directories)
    return response
