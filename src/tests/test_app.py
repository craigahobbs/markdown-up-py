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
        self.assertListEqual(
            sorted(request.name for request in app.requests.values() if request.doc_group.startswith('MarkdownUp Index ')),
            [
                'index.html',
                'markdownUpIndex.bare',
                'markdown_up_index'
            ]
        )


    def test_static(self):
        test_files = [
            ('README.md', '# Title'),
            (('images', 'image.svg'), '<svg></svg>')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir)

            # Get a markdown file
            environ = chisel.Context.create_environ('GET', '/README.md')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/markdown; charset=utf-8'), ('ETag', '38cdd67987afb67a4af89ea02044a00e')]
            )
            self.assertEqual(content, [b'# Title'])

            # Get an unmodified markdown file
            environ = chisel.Context.create_environ('GET', '/README.md')
            environ['HTTP_IF_NONE_MATCH'] = '38cdd67987afb67a4af89ea02044a00e'
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '304 Not Modified')
            self.assertEqual(start_response.headers, [])
            self.assertEqual(content, [])

            # Get an image file
            environ = chisel.Context.create_environ('GET', '/images/image.svg')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'image/svg+xml'), ('ETag', '7b56e1eab00ec8000da9331a4888cb35')]
            )
            self.assertEqual(content, [b'<svg></svg>'])

            # Get a not-found file
            environ = chisel.Context.create_environ('GET', '/not-found.md')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '404 Not Found')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])
            self.assertEqual(content, [b'Not Found'])

            # Get a file of unknown content type
            environ = chisel.Context.create_environ('GET', '/file.unk')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '404 Not Found')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])
            self.assertEqual(content, [b'Not Found'])


    def test_static_index(self):
        test_files = [
            (('html', 'index.html'), '<html></html>'),
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir)

            # Get the index file directly
            environ = chisel.Context.create_environ('GET', '/html/index.html')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', 'c83301425b2ad1d496473a5ff3d9ecca')]
            )
            self.assertEqual(content, [b'<html></html>'])

            # Get the index file
            environ = chisel.Context.create_environ('GET', '/html/')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', 'c83301425b2ad1d496473a5ff3d9ecca')]
            )
            self.assertEqual(content, [b'<html></html>'])

            # Get the index file (alternate)
            environ = chisel.Context.create_environ('GET', '/html')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', 'c83301425b2ad1d496473a5ff3d9ecca')]
            )
            self.assertEqual(content, [b'<html></html>'])


    def test_static_index_other(self):
        test_files = [
            (('html', 'index.htm'), '<html></html>'),
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir)

            # Get the index file directly
            environ = chisel.Context.create_environ('GET', '/html/index.htm')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', 'c83301425b2ad1d496473a5ff3d9ecca')]
            )
            self.assertEqual(content, [b'<html></html>'])

            # Get the index file
            environ = chisel.Context.create_environ('GET', '/html/')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', 'c83301425b2ad1d496473a5ff3d9ecca')]
            )
            self.assertEqual(content, [b'<html></html>'])

            # Get the index file (alternate)
            environ = chisel.Context.create_environ('GET', '/html')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', 'c83301425b2ad1d496473a5ff3d9ecca')]
            )
            self.assertEqual(content, [b'<html></html>'])


    def test_static_index_none(self):
        test_files = [
            (('html', 'README.md'), '# Title'),
        ]
        with create_test_files(test_files) as temp_dir:
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


    def test_markdown_up_html(self):
        with create_test_files([]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)
            status, headers, content_bytes = app.request('GET', '/')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'text/html; charset=utf-8'), ('ETag', 'abb5157ca009ed55bc9bb14813cdb6c7')])
            self.assertTrue(content_bytes.decode('utf-8').startswith('<!DOCTYPE html>'))


    def test_markdown_up_index(self):
        test_files = [
            ('README.md', '# Title'),
            ('index.html', '<html>'),
            ('image.svg', '<svg>'),
            ('text.txt', 'Text'),
            (('dir', 'info.md'), '# Info'),
            (('dir2', 'info2.md'), '# Info 2')
        ]
        with create_test_files(test_files) as temp_dir:
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
        test_files = [
            (('dir', 'README.md'), '# Info')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir)
            status, headers, content_bytes = app.request('GET', '/markdown_up_index', query_string='path=dir')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertDictEqual(json.loads(content_bytes.decode('utf-8')), {
                'path': os.path.join(temp_dir, 'dir'),
                'files': ['README.md']
            })


    def test_markdown_up_index_path_dir(self):
        test_files = [
            (('dir', 'dir2', 'README.md'), '# Info')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir)
            status, headers, content_bytes = app.request('GET', '/markdown_up_index', query_string='path=dir/dir2')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertDictEqual(json.loads(content_bytes.decode('utf-8')), {
                'path': os.path.join(temp_dir, 'dir', 'dir2'),
                'parent': 'dir',
                'files': ['README.md']
            })


    def test_markdown_up_index_escape(self):
        test_files = [
            (('dir()[]', 'dir2()[]', 'file()[].md'), '# File'),
            (('dir()[]', 'dir2()[]', 'dir3()[]', 'file2()[].md'), '# File 2')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir)
            status, headers, content_bytes = app.request('GET', '/markdown_up_index', query_string='path=dir()[]/dir2()[]')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertDictEqual(json.loads(content_bytes.decode('utf-8')), {
                'path': os.path.join(temp_dir, 'dir()[]', 'dir2()[]'),
                'parent': 'dir()[]',
                'files': ['file()[].md'],
                'directories': ['dir3()[]']
            })


    def test_markdown_up_index_invalid_path(self):
        with create_test_files([]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)
            status, headers, content_bytes = app.request('GET', '/markdown_up_index', query_string='path=../dir')
            self.assertEqual(status, '400 Bad Request')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertEqual(content_bytes, b'{"error":"InvalidPath"}')


    def test_markdown_up_index_file_path(self):
        test_files = [
            ('README.md', '# Title')
        ]
        with create_test_files(test_files) as temp_dir:
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
