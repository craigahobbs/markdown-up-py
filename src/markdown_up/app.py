# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

"""
The MarkdownUp launcher back-end application
"""

import hashlib
import importlib.resources
import os
from pathlib import PurePosixPath
import threading
import urllib.parse

import chisel
import schema_markdown


class MarkdownUpApplication(chisel.Application):
    """
    The markdown-up back-end API WSGI application class
    """

    __slots__ = ('root', 'cache_statics', 'add_request_lock')


    def __init__(self, root, cache_statics=False):
        super().__init__()
        self.root = root
        self.cache_statics = cache_statics
        self.add_request_lock = threading.Lock()

        # Add the chisel documentation application
        self.add_requests(chisel.create_doc_requests())

        # Add the markdown-up APIs
        self.add_request(markdown_up_index)

        # Add the markdown-up statics
        self.add_static('index.html', urls=(('GET', '/'),))
        self.add_static('markdownUpIndex.bare')


    def add_static(self, filename, urls=(('GET', None),), doc_group='MarkdownUp Index Statics'):
        content_type = STATIC_EXT_TO_CONTENT_TYPE.get(os.path.splitext(filename)[1], STATIC_EXT_TO_CONTENT_TYPE['.txt'])
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
                    # Redirect?
                    if not path_info.endswith('/'):
                        start_response('301 Moved Permanently', [('Location', path_info + '/')])
                        return []

                    # Update the index path
                    posix_path_info = index_posix_path
                    path = index_path
                    break

        try:
            # Unknown method or content type?
            content_type = STATIC_EXT_TO_CONTENT_TYPE.get(posix_path_info.suffix)
            if request_method != 'GET' or content_type is None or not os.path.isfile(path):
                raise FileNotFoundError(path)

            # Get the static content
            with open(path, 'rb') as path_file:
                content = path_file.read()

            # Create the static content request
            request = MarkdownUpStaticRequest(posix_path_info, content, content_type)

            # Add the request, if caching of statics is enabled
            if self.cache_statics:
                with self.add_request_lock:
                    request_lock, _ = self.match_request(request_method, path_info)
                    if request_lock is None: # pragma: no branch
                        self.add_request(request)

                        # Add the index redirect, if not at the root
                        parent_path_str = str(posix_path_info.parent)
                        if parent_path_str != '/' and posix_path_info.name in INDEX_FILES:
                            self.add_request(chisel.RedirectRequest(
                                (('GET', parent_path_str),),
                                parent_path_str + '/',
                                name=parent_path_str + '/'
                            ))

            return request(environ, start_response)
        except: # pylint: disable=bare-except
            start_response('404 Not Found', [('Content-Type', STATIC_EXT_TO_CONTENT_TYPE['.txt'])])
            return [b'Not Found']


class MarkdownUpStaticRequest(chisel.Request):
    __slots__ = ('headers', 'content', 'etag', 'stub_headers', 'stub_content', 'stub_etag')


    def __init__(self, posix_path, content, content_type):
        is_stubbed = posix_path.suffix in MARKDOWN_EXTS
        posix_path_str = str(posix_path)
        parent_path_str = str(posix_path.parent)
        if is_stubbed:
            doc = f'The static resource "{posix_path_str}". Use `?raw=true` to get the raw content.'
        else:
            doc = f'The static resource "{posix_path_str}"'
        if parent_path_str != '/' and posix_path.name in INDEX_FILES:
            urls = (('GET', parent_path_str + '/'), ('GET', posix_path_str))
        else:
            urls = (('GET', posix_path_str),)
        super().__init__(name=posix_path_str, urls=urls, doc=doc, doc_group='Statics')

        # Compute the etag
        self.content = content
        md5 = hashlib.md5()
        md5.update(content)
        self.etag = md5.hexdigest()
        self.headers = [('Content-Type', content_type), ('ETag', self.etag)]

        # Compute the raw etag
        if is_stubbed:
            self.stub_content = self.create_markdown_up_stub(posix_path.name).encode('utf-8')
            md5 = hashlib.md5()
            md5.update(self.stub_content)
            self.stub_etag = md5.hexdigest()
            self.stub_headers = [('Content-Type', STATIC_EXT_TO_CONTENT_TYPE['.html']), ('ETag', self.stub_etag)]
        else:
            self.stub_content = None
            self.stub_etag = None
            self.stub_headers = None


    def __call__(self, environ, start_response):
        # Raw content request?
        if self.stub_content is None:
            is_raw = True
        else:
            try:
                query_args_raw = schema_markdown.decode_query_string(environ.get('QUERY_STRING', ''))
                query_args = schema_markdown.validate_type(self.QUERY_TYPES, 'MarkdownUpStaticQuery', query_args_raw)
                is_raw = query_args.get('raw', False)
            except: # pylint: disable=bare-except
                is_raw = False

        # Get the response content
        if is_raw:
            headers, content, etag = self.headers, self.content, self.etag
        else:
            headers, content, etag = self.stub_headers, self.stub_content, self.stub_etag

        # Check the etag - is the resource modified?
        if etag == environ.get('HTTP_IF_NONE_MATCH'):
            start_response('304 Not Modified', [])
            return []

        start_response('200 OK', headers)
        return [content]


    QUERY_TYPES = schema_markdown.parse_schema_markdown('''\
# The MarkdownUp application static query string arguments
struct MarkdownUpStaticQuery

    # If true, return the raw resource (default is `false`)
    optional bool raw
''')


    @staticmethod
    def create_markdown_up_stub(filename):
        return f'''\
<!DOCTYPE html>
<html lang="en">
    <head>
        <title>MarkdownUp</title>
        <meta charset="UTF-8">
        <meta name="description" content="MarkdownUp is a Markdown viewer">
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
        const app = new MarkdownUp(window, {{'url': '{urllib.parse.quote(filename)}?raw=true'}});
        app.run();
    </script>
</html>
'''


# The map of static file extension to content-type
STATIC_EXT_TO_CONTENT_TYPE = {
    '.bare': 'text/plain; charset=utf-8',
    '.css': 'text/css; charset=utf-8',
    '.csv': 'text/csv; charset=utf-8',
    '.gif': 'image/gif',
    '.htm': 'text/html; charset=utf-8',
    '.html': 'text/html; charset=utf-8',
    '.jpeg': 'image/jpeg',
    '.jpg': 'image/jpeg',
    '.js': 'application/javascript; charset=utf-8',
    '.json': 'application/json; charset=utf-8',
    '.markdown': 'text/markdown; charset=utf-8',
    '.md': 'text/markdown; charset=utf-8',
    '.mds': 'text/plain; charset=utf-8',
    '.png': 'image/png',
    '.smd': 'text/plain; charset=utf-8',
    '.svg': 'image/svg+xml; charset=utf-8',
    '.tif': 'image/tiff',
    '.tiff': 'image/tiff',
    '.txt': 'text/plain; charset=utf-8',
    '.webp': 'image/webp'
}
MARKDOWN_EXTS = ('.md', '.markdown')
HTML_EXTS = ('.html', '.htm')
INDEX_FILES = ('index.html', 'index.htm', 'index.md', 'README.md')


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
        string[] files

        # The path's sub-directories
        string[] directories

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

    # Get the list of files and sub-directories from the current sub-directory
    files = []
    directories = []
    for entry in os.scandir(path):
        if entry.is_dir() and not entry.name.startswith('.'):
            directories.append(entry.name)
        elif entry.is_file(): # pragma: no branch
            if entry.name.endswith(MARKDOWN_EXTS) or entry.name.endswith(HTML_EXTS):
                files.append(entry.name)

    # Return the response
    response = {
        'path': path,
        'files': sorted(files),
        'directories': sorted(directories)
    }
    if parent_path is not None and parent_path != '.':
        response['parent'] = parent_path
    return response
