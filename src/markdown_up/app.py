# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up/blob/main/LICENSE

from http import HTTPStatus
from io import StringIO
import os

import chisel
from schema_markdown import encode_query_string


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
        self.add_request(index_html)
        self.add_request(index_md)

    def __call__(self, environ, start_response):

        # Determine the content type
        path_info = environ['PATH_INFO']
        _, path_ext = os.path.splitext(path_info)
        content_type = STATIC_EXT_TO_CONTENT_TYPE.get(path_ext)

        # Handle markdown static requests
        if content_type is not None and path_info != '/index.md':
            path = os.path.normpath(os.path.join(self.root, *path_info.split('/')))
            with open(path, 'rb') as path_file:
                start_response('OK', [('Content-Type', content_type)])
                return [path_file.read()]

        # Run the chisel application...
        return super().__call__(environ, start_response)


@chisel.action(wsgi_response=True, spec='''\
group "markdown-up"

# The markdown-up HTML page
action index_html
    urls
        GET /
    query
        # The markdown file name. If not provided, the markdown index is displayed.
        optional string(len > 0) file

        # The relative path of the sub-directory. If not provided, the root directory is used.
        optional string(len > 0) subdir
''')
def index_html(ctx, req):
    # Compute the markdown URL
    if 'file' in req and 'subdir' in req:
        markdown_url = f'{req["subdir"]}/{req["file"]}'
    elif 'file' in req:
        markdown_url = req['file']
    elif 'subdir' in req:
        query_string = encode_query_string({'subdir': req['subdir']})
        markdown_url = f'index.md?{query_string}'
    else:
        markdown_url = 'index.md'

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
action index_md
    urls
        GET /index.md
    query
        # The relative path of the sub-directory. If not provided, the root directory is used.
        optional string(len > 0) subdir
''')
def index_md(ctx, req):
    # Compute the sub-directory path
    path = os.path.join(ctx.app.root, req.get('subdir', ''))

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
        parent_subdir = os.path.dirname(req['subdir'])
        if parent_subdir == '':
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
            if 'subdir' in req:
                subdir = f'{req["subdir"]}/{dir_name}'
            else:
                subdir = dir_name
            print('', file=response)
            print(f'[{dir_name}](?{encode_query_string(dict(subdir=subdir))})', file=response)

    return ctx.response_text(HTTPStatus.OK, response.getvalue())
