# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

from http import HTTPStatus
from io import StringIO
import os
from pathlib import PurePosixPath
import re

import chisel
from schema_markdown import encode_query_string


# The map of static file extension to content-type
STATIC_EXT_TO_CONTENT_TYPE = {
    '.gif': 'image/gif',
    '.jpeg': 'image/jpeg',
    '.jpg': 'image/jpeg',
    '.md': 'text/markdown; charset=utf-8',
    '.png': 'image/png',
    '.svg': 'image/svg+xml',
    '.tif': 'image/tiff',
    '.tiff': 'image/tiff',
    '.webp': 'image/webp'
}


class MarkdownUpApplication(chisel.Application):
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
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="https://craigahobbs.github.io/markdown-up/markdown-model.css">
        <link rel="stylesheet" href="https://craigahobbs.github.io/markdown-up/schema-markdown-doc.css">
    </head>
    <body>
    </body>
    <script type="module">
        import {MarkdownUp} from 'https://craigahobbs.github.io/markdown-up/markdown-up/index.js';
        MarkdownUp.run(window, 'markdown_up_index');
    </script>
</html>
''',
    content_type='text/html; charset=utf-8',
    urls=(('GET', '/'),),
    doc='The markdown-up HTML application stub',
    doc_group='markdown-up'
)


@chisel.action(wsgi_response=True, spec='''\
group "markdown-up"

# The markdown-up index markdown
action markdown_up_index
    urls
        GET

    query
        # The relative sub-directory path
        optional string(len > 0) path

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

    # Get the list of markdown files and sub-directories from the current sub-directory
    files = []
    directories = []
    for entry in os.scandir(path):
        if entry.is_dir() and not entry.name.startswith('.'):
            directories.append(entry.name)
        elif entry.is_file() and entry.name.endswith('.md'):
            files.append(entry.name)

    # Build the index markdown response
    response = StringIO()
    print('## [markdown-up](https://github.com/craigahobbs/markdown-up-py#readme)', file=response)

    # Sub-directory? If so, report...
    if 'path' in req:
        print('', file=response)
        print(f'You are in the sub-directory, "**{escape_markdown_span(req["path"])}**".', file=response)

    # Empty?
    if not files and not directories:
        print('', file=response)
        print('No markdown files or sub-directories found.', file=response)

    # Back-link to parent sub-directory
    if 'path' in req:
        parent_path = str(posix_path.parent)
        if parent_path == '.':
            parent_url = '#'
        else:
            markdown_url = f'markdown_up_index?{encode_query_string(dict(path=parent_path))}'
            parent_url = f'#{encode_query_string(dict(url=markdown_url))}'
        print('', file=response)
        print(f'[Back to parent]({parent_url})', file=response)

    # Add the markdown file links
    if files:
        print('', file=response)
        print('### Markdown Files', file=response)
        for file_name in sorted(files):
            file_url = f'#{encode_query_string(dict(url=str(posix_path.joinpath(file_name))))}'
            print('', file=response)
            print(f'[{escape_markdown_span(file_name)}]({file_url})', file=response)

    # Add the sub-directory links
    if directories:
        print('', file=response)
        print('### Directories', file=response)
        for dir_name in sorted(directories):
            markdown_url = f'markdown_up_index?{encode_query_string(dict(path=posix_path.joinpath(dir_name)))}'
            dir_url = f'#{encode_query_string(dict(url=markdown_url))}'
            print('', file=response)
            print(f'[{escape_markdown_span(dir_name)}]({dir_url})', file=response)

    return ctx.response_text(HTTPStatus.OK, response.getvalue(), content_type='text/markdown; charset=utf-8')


# Helper function to escape Markdown span characters
def escape_markdown_span(text):
    return re_escape_markdown_span.sub(r'\\\1', text)

re_escape_markdown_span = re.compile(r'([\\\[\]()*])')
