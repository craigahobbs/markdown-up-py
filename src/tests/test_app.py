# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

# pylint: disable=missing-class-docstring, missing-function-docstring, missing-module-docstring

from contextlib import contextmanager
import os
from tempfile import TemporaryDirectory
import unittest
import unittest.mock

import chisel.app
from markdown_up.app import MarkdownUpApplication


# Helper context manager to create a list of files in a temporary directory
@contextmanager
def create_test_files(file_defs):
    tempdir = TemporaryDirectory() # pylint: disable=consider-using-with
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
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain')])
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
            self.assertEqual(headers, [('Content-Type', 'text/html; charset=utf-8'), ('ETag', 'b8c619152efa3ec038331ed7accbbf7e')])
            self.assertEqual(content_bytes, b'''\
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
''')

    def test_markdown_up_index(self):
        with create_test_files([
                ('README.md', '# Title'),
                ('text.txt', 'Text'),
                ('image.svg', '<svg>'),
                (('dir', 'info.md'), '# Info'),
                (('dir2', 'info2.md'), '# Info 2')
        ]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)
            status, headers, content_bytes = app.request('GET', '/markdown_up_index')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'text/markdown; charset=utf-8')])
            self.assertEqual(content_bytes, b'''\
## [markdown-up](https://github.com/craigahobbs/markdown-up-py#readme)

### Markdown Files

[README.md](#url=README.md)

### Directories

[dir](#url=markdown_up_index%3Fpath%3Ddir)

[dir2](#url=markdown_up_index%3Fpath%3Ddir2)
''')

    def test_markdown_up_index_empty(self):
        with create_test_files([]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)
            status, headers, content_bytes = app.request('GET', '/markdown_up_index')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'text/markdown; charset=utf-8')])
            self.assertEqual(content_bytes, b'''\
## [markdown-up](https://github.com/craigahobbs/markdown-up-py#readme)

No markdown files or sub-directories found.
''')

    def test_markdown_up_index_path(self):
        with create_test_files([
                (('dir', 'README.md'), '# Info')
        ]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)
            status, headers, content_bytes = app.request('GET', '/markdown_up_index', query_string='path=dir')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'text/markdown; charset=utf-8')])
            self.assertEqual(content_bytes, b'''\
## [markdown-up](https://github.com/craigahobbs/markdown-up-py#readme)

You are in the sub-directory, "**dir**".

[Back to parent](#)

### Markdown Files

[README.md](#url=dir/README.md)
''')

    def test_markdown_up_index_path_dir(self):
        with create_test_files([
                (('dir', 'dir2', 'README.md'), '# Info')
        ]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)
            status, headers, content_bytes = app.request('GET', '/markdown_up_index', query_string='path=dir/dir2')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'text/markdown; charset=utf-8')])
            self.assertEqual(content_bytes, b'''\
## [markdown-up](https://github.com/craigahobbs/markdown-up-py#readme)

You are in the sub-directory, "**dir/dir2**".

[Back to parent](#url=markdown_up_index%3Fpath%3Ddir)

### Markdown Files

[README.md](#url=dir/dir2/README.md)
''')

    def test_markdown_up_index_escape(self):
        with create_test_files([
                (('dir()[]\\*', 'dir2()[]\\*', 'file()[]\\*.md'), '# File'),
                (('dir()[]\\*', 'dir2()[]\\*', 'dir3()[]\\*', 'file2()[]\\*.md'), '# File 2')
        ]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)
            status, headers, content_bytes = app.request('GET', '/markdown_up_index', query_string='path=dir()[]\\*/dir2()[]\\*')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'text/markdown; charset=utf-8')])
            self.assertEqual(content_bytes.decode(), r'''## [markdown-up](https://github.com/craigahobbs/markdown-up-py#readme)

You are in the sub-directory, "**dir\(\)\[\]\\\*/dir2\(\)\[\]\\\***".

[Back to parent](#url=markdown_up_index%3Fpath%3Ddir%2528%2529%255B%255D%255C%252A)

### Markdown Files

[file\(\)\[\]\\\*.md](#url=dir%28%29%5B%5D%5C%2A/dir2%28%29%5B%5D%5C%2A/file%28%29%5B%5D%5C%2A.md)

### Directories

[dir3\(\)\[\]\\\*](#url=markdown_up_index%3Fpath%3Ddir%2528%2529%255B%255D%255C%252A/dir2%2528%2529%255B%255D%255C%252A/dir3%2528%2529%255B%255D%255C%252A)
''')

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
