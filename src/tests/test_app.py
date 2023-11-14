# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

from contextlib import contextmanager
import json
import os
from tempfile import TemporaryDirectory
import unittest
import unittest.mock

import chisel.app
from markdown_up.app import MarkdownUpApplication


# Helper context manager to create a list of files in a temporary directory
@contextmanager
def create_test_files(file_defs):
    tempdir = TemporaryDirectory()
    try:
        for path_parts, content in file_defs:
            if isinstance(path_parts, str):
                path_parts = [path_parts]
            path = os.path.join(tempdir.name, *path_parts)
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, 'w', encoding='utf-8') as file_:
                file_.write(content)
        yield tempdir.name
    finally:
        tempdir.cleanup()


class TestMarkdownUpApplication(unittest.TestCase):

    def test_init(self):
        app = MarkdownUpApplication('.')
        self.assertEqual(app.root, '.')
        self.assertListEqual(sorted(app.requests.keys()), [
            'chisel_doc',
            'chisel_doc_index',
            'chisel_doc_request',
            'markdown_up_html',
            'markdown_up_index',
            'redirect_doc'
        ])

    def test_static(self):
        with create_test_files([
                ('README.md', '# Title'),
                (('images', 'image.svg'), '<svg></svg>')
        ]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)

            # Get a markdown file
            environ = chisel.Context.create_environ('GET', '/README.md')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/markdown; charset=utf-8')])
            self.assertEqual(content, [b'# Title'])

            # Get an image file
            environ = chisel.Context.create_environ('GET', '/images/image.svg')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(start_response.headers, [('Content-Type', 'image/svg+xml')])
            self.assertEqual(content, [b'<svg></svg>'])

            # Get a not-found file
            environ = chisel.Context.create_environ('GET', '/not-found.md')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '404 Not Found')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])
            self.assertEqual(content, [b'Not Found'])

            # Get an file of unknown content type
            environ = chisel.Context.create_environ('GET', '/file.unk')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '404 Not Found')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])
            self.assertEqual(content, [b'Not Found'])

    def test_static_index(self):
        with create_test_files([
                (('html', 'index.html'), '<html></html>'),
        ]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)

            # Get the index file directly
            environ = chisel.Context.create_environ('GET', '/html/index.html')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/html; charset=utf-8')])
            self.assertEqual(content, [b'<html></html>'])

            # Get the index file
            environ = chisel.Context.create_environ('GET', '/html/')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/html; charset=utf-8')])
            self.assertEqual(content, [b'<html></html>'])

            # Get the index file (alternate)
            environ = chisel.Context.create_environ('GET', '/html')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/html; charset=utf-8')])
            self.assertEqual(content, [b'<html></html>'])

    def test_static_index_other(self):
        with create_test_files([
                (('html', 'index.htm'), '<html></html>'),
        ]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)

            # Get the index file directly
            environ = chisel.Context.create_environ('GET', '/html/index.htm')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/html; charset=utf-8')])
            self.assertEqual(content, [b'<html></html>'])

            # Get the index file
            environ = chisel.Context.create_environ('GET', '/html/')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/html; charset=utf-8')])
            self.assertEqual(content, [b'<html></html>'])

            # Get the index file (alternate)
            environ = chisel.Context.create_environ('GET', '/html')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/html; charset=utf-8')])
            self.assertEqual(content, [b'<html></html>'])

    def test_static_index_none(self):
        with create_test_files([
                (('html', 'README.md'), '# Title'),
        ]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)

            # Get the index file
            environ = chisel.Context.create_environ('GET', '/html/')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '404 Not Found')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])
            self.assertEqual(content, [b'Not Found'])

            # Get the index file (alternate)
            environ = chisel.Context.create_environ('GET', '/html')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '404 Not Found')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])
            self.assertEqual(content, [b'Not Found'])

    def test_static_internal_server_error(self):
        with unittest.mock.patch('markdown_up.app.open') as mock_open:
            mock_open.side_effect = Exception('BAD')

            with create_test_files([]) as temp_dir:
                app = MarkdownUpApplication(temp_dir)

                # Get a markdown file - fail
                environ = chisel.Context.create_environ('GET', '/README.md')
                start_response = chisel.app.StartResponse()
                content = app(environ, start_response)
                self.assertEqual(start_response.status, '500 Internal Server Error')
                self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])
                self.assertEqual(content, [b'Internal Server Error'])

    def test_markdown_up_html(self):
        with create_test_files([]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)
            status, headers, content_bytes = app.request('GET', '/')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'text/html; charset=utf-8'), ('ETag', '06aa8f8893b669112370c8ff1a08df74')])
            self.assertEqual(content_bytes.decode('utf-8'), '''\
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
''')

    def test_markdown_up_index(self):
        with create_test_files([
                ('README.md', '# Title'),
                ('index.html', '<html>'),
                ('image.svg', '<svg>'),
                ('text.txt', 'Text'),
                (('dir', 'info.md'), '# Info'),
                (('dir2', 'info2.md'), '# Info 2')
        ]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)
            status, headers, content_bytes = app.request('GET', '/markdown_up_index')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertDictEqual(json.loads(content_bytes.decode('utf-8')), {
                'path': temp_dir,
                'files': ['README.md'],
                'htmlFiles': ['index.html'],
                'directories': ['dir', 'dir2']
            })

    def test_markdown_up_index_empty(self):
        with create_test_files([]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)
            status, headers, content_bytes = app.request('GET', '/markdown_up_index')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertDictEqual(json.loads(content_bytes.decode('utf-8')), {
                'path': temp_dir
            })

    def test_markdown_up_index_path(self):
        with create_test_files([
                (('dir', 'README.md'), '# Info')
        ]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)
            status, headers, content_bytes = app.request('GET', '/markdown_up_index', query_string='path=dir')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertDictEqual(json.loads(content_bytes.decode('utf-8')), {
                'path': temp_dir + '/dir',
                'files': ['README.md']
            })

    def test_markdown_up_index_path_dir(self):
        with create_test_files([
                (('dir', 'dir2', 'README.md'), '# Info')
        ]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)
            status, headers, content_bytes = app.request('GET', '/markdown_up_index', query_string='path=dir/dir2')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertDictEqual(json.loads(content_bytes.decode('utf-8')), {
                'path': temp_dir + '/dir/dir2',
                'parent': 'dir',
                'files': ['README.md']
            })

    def test_markdown_up_index_escape(self):
        with create_test_files([
                (('dir()[]\\*', 'dir2()[]\\*', 'file()[]\\*.md'), '# File'),
                (('dir()[]\\*', 'dir2()[]\\*', 'dir3()[]\\*', 'file2()[]\\*.md'), '# File 2')
        ]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)
            status, headers, content_bytes = app.request('GET', '/markdown_up_index', query_string='path=dir()[]\\*/dir2()[]\\*')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertDictEqual(json.loads(content_bytes.decode('utf-8')), {
                'path': temp_dir + '/dir()[]\\*/dir2()[]\\*',
                'parent': 'dir()[]\\*',
                'files': ['file()[]\\*.md'],
                'directories': ['dir3()[]\\*']
            })

    def test_markdown_up_index_invalid_path(self):
        with create_test_files([]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)
            status, headers, content_bytes = app.request('GET', '/markdown_up_index', query_string='path=../dir')
            self.assertEqual(status, '400 Bad Request')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertEqual(content_bytes, b'{"error":"InvalidPath"}')

    def test_markdown_up_index_file_path(self):
        with create_test_files([
                ('README.md', '# Title')
        ]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)
            status, headers, content_bytes = app.request('GET', '/markdown_up_index', query_string='path=README.md')
            self.assertEqual(status, '400 Bad Request')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertEqual(content_bytes, b'{"error":"InvalidPath"}')

    def test_markdown_up_index_file_not_found(self):
        with create_test_files([]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)
            status, headers, content_bytes = app.request('GET', '/markdown_up_index', query_string='path=dir')
            self.assertEqual(status, '400 Bad Request')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertEqual(content_bytes, b'{"error":"InvalidPath"}')
