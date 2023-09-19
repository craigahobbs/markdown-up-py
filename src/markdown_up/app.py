# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

"""
The MarkdownUp launcher back-end application
"""

from http import HTTPStatus
import os
from pathlib import PurePosixPath

import chisel


# The map of static file extension to content-type
STATIC_EXT_TO_CONTENT_TYPE = {
    '.bare': 'text/plain; charset=utf-8',
    '.csv': 'text/csv',
    '.gif': 'image/gif',
    '.jpeg': 'image/jpeg',
    '.jpg': 'image/jpeg',
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

        # Add the markdown-up application
        self.add_request(MARKDOWN_UP_HTML)
        self.add_request(markdown_up_index)

    def __call__(self, environ, start_response):

        # Handle markdown static requests
        path_info = PurePosixPath(environ['PATH_INFO'])
        content_type = STATIC_EXT_TO_CONTENT_TYPE.get(path_info.suffix)
        if content_type is not None:
            try:
                # Read the static file
                path = os.path.join(self.root, *path_info.parts[1:])
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

        # Run the chisel application...
        return super().__call__(environ, start_response)


MARKDOWN_UP_HTML = chisel.StaticRequest(
    'markdown_up_html',
    b'''\
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>MarkdownUp</title>
        <meta charset="UTF-8">
        <meta name="description" content="MarkdownUp is a Markdown viewer">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="https://craigahobbs.github.io/markdown-up/app.css">
    </head>
    <body>
    </body>
    <script type="module">
        import {MarkdownUp} from 'https://craigahobbs.github.io/markdown-up/lib/app.js';
        const app = new MarkdownUp(window, {
            'markdownText': `\\
~~~ markdown-script
include 'https://craigahobbs.github.io/markdown-up/launcher/app.mds'
markdownUpIndex()
~~~
`
        });
        app.run();
    </script>
</html>
''',
    content_type='text/html; charset=utf-8',
    urls=(('GET', '/'),),
    doc='The MarkdownUp launcher index application',
    doc_group='MarkdownUp'
)


@chisel.action(spec='''\
group "MarkdownUp"

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
    directories = []
    for entry in os.scandir(path):
        if entry.is_dir() and not entry.name.startswith('.'):
            directories.append(entry.name)
        elif entry.is_file() and entry.name.endswith(MARKDOWN_EXTS):
            files.append(entry.name)

    # Return the response
    response = {'path': path}
    if parent_path is not None and parent_path != '.':
        response['parent'] = parent_path
    if files:
        response['files'] = sorted(files)
    if directories:
        response['directories'] = sorted(directories)
    return response
