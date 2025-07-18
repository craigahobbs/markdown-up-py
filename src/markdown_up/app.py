# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

"""
The MarkdownUp launcher back-end application
"""

import importlib.resources
import os
from pathlib import PurePosixPath
import threading
import urllib.parse

import chisel


class MarkdownUpApplication(chisel.Application):
    """
    The markdown-up back-end API WSGI application class
    """

    __slots__ = ('root', 'release', 'add_request_lock')


    def __init__(self, root, release=False):
        super().__init__()
        self.root = root
        self.release = release
        self.add_request_lock = threading.Lock()

        if release:
            # Add the MarkdownUp application
            self.add_requests(chisel.create_doc_requests(api=False, app=False, markdown_up=True))
        else:
            # Add the chisel documentation application (and the MarkdownUp application)
            self.add_requests(chisel.create_doc_requests())

            # Add the markdown-up APIs
            self.add_request(markdown_up_index)

            # Add the markdown-up statics
            self.add_static('index.html', content_type='text/html; charset=utf-8', urls=(('GET', '/'),))
            self.add_static('markdownUpIndex.bare')


    def add_static(self, filename, content_type=None, urls=(('GET', None),), doc_group='MarkdownUp Index Statics'):
        with importlib.resources.files('markdown_up.static').joinpath(filename).open('rb') as fh:
            self.add_request(chisel.StaticRequest(filename, fh.read(), content_type=content_type, urls=urls, doc_group=doc_group))


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

        # Directory path?
        request = None
        if os.path.isdir(path):

            # Directory redirect?
            if not path_info.endswith('/'):
                request = chisel.RedirectRequest(((None, path_info),), path_info + '/', name=path_info)

            # HTML index file exist?
            if request is None:
                for index_file in INDEX_FILES:
                    index_posix_path = posix_path_info.joinpath(index_file)
                    index_path = os.path.join(self.root, *index_posix_path.parts[1:])
                    if os.path.isfile(index_path):
                        with open(index_path, 'rb') as index_file:
                            request = chisel.StaticRequest(
                                path_info,
                                index_file.read(),
                                content_type='text/html; charset=utf-8',
                                urls=(('GET', path_info),)
                            )
                        break

            # No HTML index file - does a Markdown index file exist?
            if request is None:
                for index_markdown in INDEX_MARKDOWN:
                    markdown_posix_path = posix_path_info.joinpath(index_markdown)
                    markdown_path = os.path.join(self.root, *markdown_posix_path.parts[1:])
                    if os.path.isfile(markdown_path):
                        request = chisel.StaticRequest(
                            path_info,
                            create_markdown_up_stub(markdown_posix_path.name),
                            content_type='text/html; charset=utf-8',
                            urls=(('GET', path_info),)
                        )
                        break

        # File path?
        elif os.path.isfile(path):
            try:
                with open(path, 'rb') as path_file:
                    request = chisel.StaticRequest(path_info, path_file.read(), urls=(('GET', path_info),))
            except AssertionError as exc:
                ctx = chisel.Context(self, environ, start_response)
                ctx.log.warning(str(exc))

        # Auto-generate MarkdownUp HTML stub?
        elif posix_path_info.suffix == HTML_EXTS[0]:
            for markdown_ext in MARKDOWN_EXTS:
                markdown_posix_path = posix_path_info.with_suffix(markdown_ext)
                markdown_path = os.path.join(self.root, *markdown_posix_path.parts[1:])
                if os.path.isfile(markdown_path):
                    request = chisel.StaticRequest(
                        path_info,
                        create_markdown_up_stub(markdown_posix_path.name),
                        content_type='text/html; charset=utf-8',
                        urls=(('GET', path_info),)
                    )
                    break

        # Not found?
        if not request:
            start_response('404 Not Found', [('Content-Type', 'text/plain; charset=utf-8')])
            return [b'Not Found']

        # Add the request, if caching of statics is enabled
        if self.release:
            with self.add_request_lock:
                request_lock, _ = self.match_request('GET', path_info)
                if request_lock is None:
                    self.add_request(request)

        # Bad method?
        if isinstance(request, chisel.StaticRequest) and request_method != 'GET':
            start_response('405 Method Not Allowed', [('Content-Type', 'text/plain; charset=utf-8')])
            return [b'Method Not Allowed']

        # Handle the request
        return request(environ, start_response)


# Render-able file extensions
MARKDOWN_EXTS = ('.md', '.markdown')
HTML_EXTS = ('.html', '.htm')


# Index file names
INDEX_FILES = ('index.html', 'index.htm')
INDEX_MARKDOWN = ('index.md', 'README.md')


def create_markdown_up_stub(filename):
    return f'''\
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>MarkdownUp</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <link rel="stylesheet" href="/markdown-up/app.css">

        <!-- Preloads -->
        <link rel="modulepreload" href="/markdown-up/bare-script/lib/data.js" as="script">
        <link rel="modulepreload" href="/markdown-up/bare-script/lib/library.js" as="script">
        <link rel="modulepreload" href="/markdown-up/bare-script/lib/model.js" as="script">
        <link rel="modulepreload" href="/markdown-up/bare-script/lib/options.js" as="script">
        <link rel="modulepreload" href="/markdown-up/bare-script/lib/parser.js" as="script">
        <link rel="modulepreload" href="/markdown-up/bare-script/lib/runtime.js" as="script">
        <link rel="modulepreload" href="/markdown-up/bare-script/lib/runtimeAsync.js" as="script">
        <link rel="modulepreload" href="/markdown-up/bare-script/lib/value.js" as="script">
        <link rel="modulepreload" href="/markdown-up/element-model/lib/elementModel.js" as="script">
        <link rel="modulepreload" href="/markdown-up/lib/app.js" as="script">
        <link rel="modulepreload" href="/markdown-up/lib/dataTable.js" as="script">
        <link rel="modulepreload" href="/markdown-up/lib/dataUtil.js" as="script">
        <link rel="modulepreload" href="/markdown-up/lib/lineChart.js" as="script">
        <link rel="modulepreload" href="/markdown-up/lib/script.js" as="script">
        <link rel="modulepreload" href="/markdown-up/lib/scriptLibrary.js" as="script">
        <link rel="modulepreload" href="/markdown-up/markdown-model/lib/elements.js" as="script">
        <link rel="modulepreload" href="/markdown-up/markdown-model/lib/highlight.js" as="script">
        <link rel="modulepreload" href="/markdown-up/markdown-model/lib/parser.js" as="script">
        <link rel="modulepreload" href="/markdown-up/schema-markdown-doc/lib/schemaMarkdownDoc.js" as="script">
        <link rel="modulepreload" href="/markdown-up/schema-markdown/lib/encode.js" as="script">
        <link rel="modulepreload" href="/markdown-up/schema-markdown/lib/parser.js" as="script">
        <link rel="modulepreload" href="/markdown-up/schema-markdown/lib/schema.js" as="script">
        <link rel="modulepreload" href="/markdown-up/schema-markdown/lib/schemaUtil.js" as="script">
        <link rel="modulepreload" href="/markdown-up/schema-markdown/lib/typeModel.js" as="script">
        <link rel="preload" href="/markdown-up/app.css" as="style">
        <link rel="preload" href="/markdown-up/markdown-model/static/markdown-model.css" as="style">
    </head>
    <body>
    </body>
    <script type="module">
        import {{MarkdownUp}} from '/markdown-up/lib/app.js';
        const app = new MarkdownUp(window, {{
            'systemPrefix': '/markdown-up/include/',
            'url': '{urllib.parse.quote(filename)}'
        }});
        app.run();
    </script>
</html>
'''.encode('utf-8')


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

        # The path's files
        IndexFile[] files

        # The path's sub-directories
        string[] directories

    errors
        # The path is invalid
        InvalidPath


# An index file
struct IndexFile

    # The file name
    string name

    # The file's display name
    optional string display
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

    # Get the list of files and sub-directories from the current sub-directory
    files = []
    directories = []
    for entry in os.scandir(path):
        if entry.is_file():
            # Markdown files are viewed using their generated MarkdownUp HTML stubs
            name_root, name_ext = os.path.splitext(entry.name)
            if name_ext in MARKDOWN_EXTS:
                files.append({'name': f'{name_root}{HTML_EXTS[0]}', 'display': entry.name})
            elif name_ext in HTML_EXTS:
                files.append({'name': entry.name})
        elif entry.is_dir(): # pragma: no branch
            directories.append(entry.name)

    # Return the response
    response = {
        'path': path,
        'files': sorted(files, key=lambda file_: file_.get('display', file_['name'])),
        'directories': sorted(directories)
    }
    if parent_path is not None and parent_path != '.':
        response['parent'] = parent_path
    return response
