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


# Helper function to validate path argument
def validate_path(ctx, req, allow_files=False):

    # Validate the path
    posix_path = PurePosixPath(req.get('path', ''))
    if posix_path.is_absolute() or any(part in ('.', '..') for part in posix_path.parts):
        raise chisel.ActionError('InvalidPath')
    path = os.path.join(ctx.app.root, *posix_path.parts)

    # Are markdown files allowed?
    is_file = is_markdown_file(path)
    if not allow_files and is_file:
        raise chisel.ActionError('InvalidPath')

    # Verify that the path exists
    if (is_file and not os.path.isfile(path)) or (not is_file and not os.path.isdir(path)):
        raise chisel.ActionError('FileNotFound', status=HTTPStatus.NOT_FOUND)

    return posix_path, path


# Helper function to determine if a path is a markdown file
def is_markdown_file(path):
    return path.endswith('.md')


@chisel.action(wsgi_response=True, spec='''\
group "markdown-up"

# The markdown-up HTML page
action markdown_up_html
    urls
        GET /

    query
        # The relative sub-directory or markdown file path. If path is a directory or not provided,
        # display the markdown index. Otherwise, display the markdown file.
        optional string(len > 0) path

    errors
        # The path is invalid
        InvalidPath

        # The path does not exist
        FileNotFound
''')
def markdown_up_html(ctx, req):
    validate_path(ctx, req, allow_files=True)

    # Compute the markdown URL
    if 'path' in req:
        if is_markdown_file(req['path']):
            markdown_url = req['path']
        else:
            query_string = encode_query_string({'path': req['path']})
            markdown_url = f'markdown_up_index?{query_string}'
    else:
        markdown_url = 'markdown_up_index'

    # Return the customized markdown-up application stub
    markdown_url_escaped = markdown_url.replace('\\', '\\\\').replace("'", "\\'")
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
        MarkdownUp.run(window, '{markdown_url_escaped}');
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
        # The relative sub-directory path
        optional string(len > 0) path

    errors
        # The path is invalid
        InvalidPath

        # The path does not exist
        FileNotFound
''')
def markdown_up_index(ctx, req):
    posix_path, path = validate_path(ctx, req)

    # Get the list of markdown files and sub-directories from the current sub-directory
    files = []
    directories = []
    for entry in os.scandir(path):
        if entry.is_dir() and not entry.name.startswith('.'):
            directories.append(entry.name)
        elif entry.is_file() and is_markdown_file(entry.name):
            files.append(entry.name)

    # Build the index markdown response
    response = StringIO()
    print('## [markdown-up](https://github.com/craigahobbs/markdown-up-py#readme)', file=response)

    # Sub-directory? If so, report...
    if 'path' in req:
        parent_path = str(posix_path.parent)
        if parent_path == '.':
            parent_url = '?'
        else:
            parent_url = f'?{encode_query_string(dict(path=parent_path))}'

        print('', file=response)
        print(f'You are in the sub-directory, "**{req["path"]}**".', file=response)
        print('', file=response)
        print(f'[Back to parent]({parent_url})', file=response)

    # Add the markdown file links
    if files:
        print('', file=response)
        print('### Markdown Files', file=response)
        for file_name in sorted(files):
            file_url = encode_query_string(dict(path=str(posix_path.joinpath(file_name))))
            print('', file=response)
            print(f'[{file_name}](?{file_url})', file=response)

    # Add the sub-directory links
    if directories:
        print('', file=response)
        print('### Directories', file=response)
        for dir_name in sorted(directories):
            dir_url = encode_query_string(dict(path=posix_path.joinpath(dir_name)))
            print('', file=response)
            print(f'[{dir_name}](?{dir_url})', file=response)

    return ctx.response_text(HTTPStatus.OK, response.getvalue())
