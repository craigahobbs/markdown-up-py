# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up/blob/main/LICENSE

from http import HTTPStatus
from io import StringIO
import os
from pathlib import PurePosixPath

import chisel
from schema_markdown import encode_query_string


# The map of static file extension to content-type
STATIC_EXT_TO_CONTENT_TYPE = {
    '.gif': 'image/gif',
    '.jpeg': 'image/jpeg',
    '.jpg': 'image/jpeg',
    '.md': 'text/plain',
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
        self.add_request(markdown_up_html)
        self.add_request(markdown_up_index)

    def __call__(self, environ, start_response):

        # Handle markdown static requests
        path_info = PurePosixPath(environ['PATH_INFO'])
        content_type = STATIC_EXT_TO_CONTENT_TYPE.get(path_info.suffix)
        if content_type is not None:
            try:
                path = os.path.join(self.root, *path_info.parts[1:])
                with open(path, 'rb') as path_file:
                    status = HTTPStatus.OK
                    start_response(f'{status.value} {status.phrase}', [('Content-Type', content_type)])
                    return [path_file.read()]
            except Exception as exc: # pylint: disable=broad-except
                if isinstance(exc, FileNotFoundError):
                    status = HTTPStatus.NOT_FOUND
                else:
                    status = HTTPStatus.INTERNAL_SERVER_ERROR
                start_response(f'{status.value} {status.phrase}', [('Content-Type', 'text/plain')])
                return [status.phrase.encode()]

        # Run the chisel application...
        return super().__call__(environ, start_response)


@chisel.action(wsgi_response=True, spec='''\
group "markdown-up"

# The markdown-up HTML page
action markdown_up_html
    urls
        GET /
    query
        # The markdown file name. If not provided, the markdown index is displayed.
        optional string(len > 0) file

        # The relative path of the sub-directory. If not provided, the root directory is used.
        optional string(len > 0) subdir
''')
def markdown_up_html(ctx, req):
    # Compute the markdown URL
    if 'file' in req:
        markdown_url = PurePosixPath(req.get('subdir', '')).joinpath(req['file'])
    elif 'subdir' in req:
        query_string = encode_query_string({'subdir': req['subdir']})
        markdown_url = f'markdown_up_index?{query_string}'
    else:
        markdown_url = 'markdown_up_index'

    # Return the customized markdown-up application stub
    return ctx.response_text(
        HTTPStatus.OK,
        f'''\
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
        import {{MarkdownUp}} from 'https://craigahobbs.github.io/markdown-up/markdown-up/index.js';
        MarkdownUp.run(window, '{markdown_url}');
    </script>
</html>
''',
        content_type='text/html'
        )


@chisel.action(wsgi_response=True, spec='''\
group "markdown-up"

# The markdown-up index markdown
action markdown_up_index
    urls
        GET
    query
        # The relative path of the sub-directory. If not provided, the root directory is used.
        optional string(len > 0) subdir
''')
def markdown_up_index(ctx, req):
    # Compute the sub-directory path
    subdir = PurePosixPath(req.get('subdir', ''))
    path = os.path.join(ctx.app.root, *subdir.parts)

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
    if 'subdir' in req:
        parent_subdir = str(subdir.parent)
        if parent_subdir == '.':
            parent_url = '?'
        else:
            parent_url = f'?{encode_query_string(dict(subdir=parent_subdir))}'

        print('', file=response)
        print(f'You are in the sub-directory, "**{req["subdir"]}**".', file=response)
        print('', file=response)
        print(f'[Back to parent]({parent_url})', file=response)

    # Add the markdown file links
    if files:
        print('', file=response)
        print('### Markdown Files', file=response)
        for file_name in sorted(files):
            print('', file=response)
            print(f'[{file_name}](?{encode_query_string(dict(req, file=file_name))})', file=response)

    # Add the sub-directory links
    if directories:
        print('', file=response)
        print('### Directories', file=response)
        for dir_name in sorted(directories):
            print('', file=response)
            print(f'[{dir_name}](?{encode_query_string(dict(subdir=subdir.joinpath(dir_name)))})', file=response)

    return ctx.response_text(HTTPStatus.OK, response.getvalue())
