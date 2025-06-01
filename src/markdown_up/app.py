# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

"""
The MarkdownUp launcher back-end application
"""

import hashlib
from http import HTTPStatus
import importlib.resources
import os
from pathlib import PurePosixPath

import chisel


class MarkdownUpApplication(chisel.Application):
    """
    The markdown-up back-end API WSGI application class
    """

    __slots__ = ('root',)


    def __init__(self, root):
        super().__init__()
        self.root = root

        # Add the chisel documentation application
        self.add_requests(chisel.create_doc_requests())

        # Add the markdown-up APIs
        self.add_request(markdown_up_index)

        # Add the markdown-up statics
        self.add_static('index.html', urls=(('GET', '/'),))
        self.add_static('markdownUpIndex.bare')


    def add_static(self, filename, urls=(('GET', None),), doc_group='MarkdownUp Index Statics'):
        content_type = _CONTENT_TYPES.get(os.path.splitext(filename)[1], 'text/plain; charset=utf-8')
        with importlib.resources.files('markdown_up.static').joinpath(filename).open('rb') as fh:
            self.add_request(chisel.StaticRequest(filename, fh.read(), content_type, urls, doc_group=doc_group))


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
                content = path_file.read()

            # Compute the etag
            md5 = hashlib.md5()
            md5.update(content)
            etag = md5.hexdigest()

            # Check the etag - is the resource modified?
            if etag == environ.get('HTTP_IF_NONE_MATCH'):
                status = HTTPStatus.NOT_MODIFIED
                start_response(f'{status.value} {status.phrase}', [])
                return []

            # Respond with static content
            status = HTTPStatus.OK
            start_response(f'{status.value} {status.phrase}', [('Content-Type', content_type), ('ETag', etag)])
            return [content]

        except: # pylint: disable=bare-except
            status = HTTPStatus.NOT_FOUND
            start_response(f'{status.value} {status.phrase}', [('Content-Type', 'text/plain; charset=utf-8')])
            return [status.phrase.encode(encoding='utf-8')]


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
    '.png': 'image/png',
    '.smd': 'text/plain; charset=utf-8',
    '.svg': 'image/svg+xml',
    '.tif': 'image/tiff',
    '.tiff': 'image/tiff',
    '.txt': 'text/plain; charset=utf-8',
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
