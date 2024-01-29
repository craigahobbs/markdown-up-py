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
        request_method = environ['REQUEST_METHOD']
        path_info = environ['PATH_INFO']

        # Chisel API request? Otherwise, its a static request...
        if request_method == 'GET' and path_info in ('/', '/doc', '/doc/', '/doc/doc_index', '/doc/doc_request', '/markdown_up_index'):
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

        <!-- Preloads -->
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/bare-script/lib/data.js" as="script">
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/bare-script/lib/library.js" as="script">
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/bare-script/lib/model.js" as="script">
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/bare-script/lib/parser.js" as="script">
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/bare-script/lib/runtime.js" as="script">
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/bare-script/lib/runtimeAsync.js" as="script">
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/element-model/lib/elementModel.js" as="script">
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/lib/app.js" as="script">
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/lib/dataTable.js" as="script">
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/lib/dataUtil.js" as="script">
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/lib/lineChart.js" as="script">
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/lib/script.js" as="script">
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/lib/scriptLibrary.js" as="script">
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/markdown-model/lib/elements.js" as="script">
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/markdown-model/lib/parser.js" as="script">
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/schema-markdown-doc/lib/schemaMarkdownDoc.js" as="script">
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/schema-markdown/lib/encode.js" as="script">
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/schema-markdown/lib/parser.js" as="script">
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/schema-markdown/lib/schema.js" as="script">
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/schema-markdown/lib/schemaUtil.js" as="script">
        <link rel="modulepreload" href="https://craigahobbs.github.io/markdown-up/schema-markdown/lib/typeModel.js" as="script">
        <link rel="preload" href="https://craigahobbs.github.io/markdown-up/app.css" as="style">
        <link rel="preload" href="https://craigahobbs.github.io/markdown-up/markdown-model/static/markdown-model.css" as="style">
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
