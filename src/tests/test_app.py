# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

from contextlib import contextmanager
from io import StringIO
import json
import os
import re
from tempfile import TemporaryDirectory
import unittest
import unittest.mock

import chisel.app
from markdown_up.app import MarkdownUpApplication, create_markdown_up_stub


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


class TestMarkdownUp(unittest.TestCase):

    def test_init(self):
        app = MarkdownUpApplication('.')
        self.assertEqual(app.root, '.')
        self.assertTrue('index.html' in (request.name for request in app.requests.values()))
        self.assertTrue('markdownUpIndex.bare' in (request.name for request in app.requests.values()))
        self.assertTrue('markdown_up_index' in (request.name for request in app.requests.values()))
        self.assertTrue('chisel_doc' in (request.name for request in app.requests.values()))
        self.assertTrue('markdown-up/VERSION.txt' in (request.name for request in app.requests.values()))


    def test_init_release(self):
        app = MarkdownUpApplication('.', True)
        self.assertEqual(app.root, '.')
        self.assertFalse('index.html' in (request.name for request in app.requests.values()))
        self.assertFalse('markdownUpIndex.bare' in (request.name for request in app.requests.values()))
        self.assertFalse('markdown_up_index' in (request.name for request in app.requests.values()))
        self.assertFalse('chisel_doc' in (request.name for request in app.requests.values()))
        self.assertTrue('markdown-up/VERSION.txt' in (request.name for request in app.requests.values()))


    def test_static(self):
        test_files = [
            ('README.md', '# Title'),
            (('sub', 'index.md'), '# index.md'),
            (('sub2', 'index.html'), '<html></html>'),
            (('sub3', 'test.txt'), 'test')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir)

            # Root
            environ = chisel.Context.create_environ('GET', '/')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', '85ffc95b1d8b8f87ac29f80e07cac2d0')]
            )
            self.assertTrue(b'<title>MarkdownUp</title>' in b''.join(content))

            # Root subdir reloc
            environ = chisel.Context.create_environ('GET', '/sub')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '301 Moved Permanently')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/plain; charset=utf-8'), ('Location', '/sub/')]
            )
            self.assertEqual(content, [b'/sub/'])

            # Root subdir autostub
            environ = chisel.Context.create_environ('GET', '/sub/')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', '0658c1a8597e87ba9829f9b7e13fe5be')]
            )
            self.assertTrue(content, [create_markdown_up_stub('index.md')])

            # Root subdir HTML
            environ = chisel.Context.create_environ('GET', '/sub2/')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', 'c83301425b2ad1d496473a5ff3d9ecca')]
            )
            self.assertEqual(content, [b'<html></html>'])

            # Root subdir not found
            environ = chisel.Context.create_environ('GET', '/sub3/')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '404 Not Found')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/plain; charset=utf-8')]
            )
            self.assertEqual(content, [b'Not Found'])

            # File
            environ = chisel.Context.create_environ('GET', '/README.md')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/markdown; charset=utf-8'), ('ETag', '38cdd67987afb67a4af89ea02044a00e')]
            )
            self.assertEqual(content, [b'# Title'])

            # File unmodified
            environ = chisel.Context.create_environ('GET', '/README.md')
            environ['HTTP_IF_NONE_MATCH'] = '38cdd67987afb67a4af89ea02044a00e'
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '304 Not Modified')
            self.assertEqual(start_response.headers, [])
            self.assertEqual(content, [])

            # Auto HTML stub
            environ = chisel.Context.create_environ('GET', '/README.html')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', 'e4fad7593460a7af69f2708f6563898b')]
            )
            self.assertEqual(content, [create_markdown_up_stub('README.md')])

            # Auto HTML stub unmodified
            environ = chisel.Context.create_environ('GET', '/README.html')
            environ['HTTP_IF_NONE_MATCH'] = 'e4fad7593460a7af69f2708f6563898b'
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '304 Not Modified')
            self.assertEqual(start_response.headers, [])
            self.assertEqual(content, [])

            # Not found
            environ = chisel.Context.create_environ('GET', '/not-found.md')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '404 Not Found')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])
            self.assertEqual(content, [b'Not Found'])

            # Not found HTML
            environ = chisel.Context.create_environ('GET', '/not-found.html')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '404 Not Found')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])
            self.assertEqual(content, [b'Not Found'])

            # Bad method
            environ = chisel.Context.create_environ('POST', '/README.md')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '405 Method Not Allowed')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])
            self.assertEqual(content, [b'Method Not Allowed'])

            # Verify no requests were added
            self.assertFalse('/' in app.requests)
            self.assertFalse('/sub' in app.requests)
            self.assertFalse('/sub/' in app.requests)
            self.assertFalse('/sub2/' in app.requests)
            self.assertFalse('/sub3/' in app.requests)
            self.assertFalse('/README.html' in app.requests)
            self.assertFalse('/README.md' in app.requests)
            self.assertFalse('/not-found.html' in app.requests)
            self.assertFalse('/not-found.md' in app.requests)


    def test_static_release(self):
        test_files = [
            ('README.md', '# Title'),
            (('sub', 'index.md'), '# index.md'),
            (('sub2', 'index.html'), '<html></html>'),
            (('sub3', 'test.txt'), 'test')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, True)

            # Root
            environ = chisel.Context.create_environ('GET', '/')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', 'e4fad7593460a7af69f2708f6563898b')]
            )
            self.assertTrue(content, [create_markdown_up_stub('README.md')])

            # Root subdir reloc
            environ = chisel.Context.create_environ('GET', '/sub')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '301 Moved Permanently')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/plain; charset=utf-8'), ('Location', '/sub/')]
            )
            self.assertEqual(content, [b'/sub/'])

            # Root subdir autostub
            environ = chisel.Context.create_environ('GET', '/sub/')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', '0658c1a8597e87ba9829f9b7e13fe5be')]
            )
            self.assertTrue(content, [create_markdown_up_stub('index.md')])

            # Root subdir HTML
            environ = chisel.Context.create_environ('GET', '/sub2/')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', 'c83301425b2ad1d496473a5ff3d9ecca')]
            )
            self.assertEqual(content, [b'<html></html>'])

            # Root subdir not found
            environ = chisel.Context.create_environ('GET', '/sub3/')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '404 Not Found')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/plain; charset=utf-8')]
            )
            self.assertEqual(content, [b'Not Found'])

            # File
            environ = chisel.Context.create_environ('GET', '/README.md')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/markdown; charset=utf-8'), ('ETag', '38cdd67987afb67a4af89ea02044a00e')]
            )
            self.assertEqual(content, [b'# Title'])

            # File unmodified
            environ = chisel.Context.create_environ('GET', '/README.md')
            environ['HTTP_IF_NONE_MATCH'] = '38cdd67987afb67a4af89ea02044a00e'
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '304 Not Modified')
            self.assertEqual(start_response.headers, [])
            self.assertEqual(content, [])

            # Auto HTML stub
            environ = chisel.Context.create_environ('GET', '/README.html')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', 'e4fad7593460a7af69f2708f6563898b')]
            )
            self.assertEqual(content, [create_markdown_up_stub('README.md')])

            # Auto HTML stub unmodified
            environ = chisel.Context.create_environ('GET', '/README.html')
            environ['HTTP_IF_NONE_MATCH'] = 'e4fad7593460a7af69f2708f6563898b'
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '304 Not Modified')
            self.assertEqual(start_response.headers, [])
            self.assertEqual(content, [])

            # Not found
            environ = chisel.Context.create_environ('GET', '/not-found.md')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '404 Not Found')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])
            self.assertEqual(content, [b'Not Found'])

            # Not found HTML
            environ = chisel.Context.create_environ('GET', '/not-found.html')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '404 Not Found')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])
            self.assertEqual(content, [b'Not Found'])

            # Bad method
            environ = chisel.Context.create_environ('POST', '/README.md')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '405 Method Not Allowed')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])
            self.assertEqual(content, [b'Method Not Allowed'])

            # Verify no requests were added
            self.assertTrue('/' in app.requests)
            self.assertTrue('/sub' in app.requests)
            self.assertTrue('/sub/' in app.requests)
            self.assertTrue('/sub2/' in app.requests)
            self.assertFalse('/sub3/' in app.requests)
            self.assertTrue('/README.html' in app.requests)
            self.assertTrue('/README.md' in app.requests)
            self.assertFalse('/not-found.md' in app.requests)


    def test_static_unknown_extension(self):
        test_files = [
            ('test.unk', '')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, True)
            wsgi_errors = StringIO()
            environ = chisel.Context.create_environ('GET', '/test.unk', environ={'wsgi.errors': wsgi_errors})
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '404 Not Found')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])
            self.assertEqual(content, [b'Not Found'])
            self.assertTrue(re.match(
                r'^WARNING \[\d+ / \d+\] Unknown content type for static resource "/test.unk"',
                wsgi_errors.getvalue()
            ), wsgi_errors.getvalue())


    def test_static_unknown_extension_not_found(self):
        test_files = []
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, True)
            environ = chisel.Context.create_environ('GET', '/test.unk')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '404 Not Found')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])
            self.assertEqual(content, [b'Not Found'])


class TestMarkdownUpAPI(unittest.TestCase):

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
                'files': [{'name': 'README.html', 'display': 'README.md'}, {'name': 'index.html'}],
                'directories': ['dir', 'dir2']
            })


    def test_markdown_up_index_empty(self):
        with create_test_files([]) as temp_dir:
            app = MarkdownUpApplication(temp_dir)
            status, headers, content_bytes = app.request('GET', '/markdown_up_index')
            self.assertEqual(status, '200 OK')
            self.assertEqual(headers, [('Content-Type', 'application/json')])
            self.assertDictEqual(json.loads(content_bytes.decode('utf-8')), {
                'path': temp_dir,
                'files': [],
                'directories': []
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
                'files': [{'name': 'README.html', 'display': 'README.md'}],
                'directories': []
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
                'files': [{'name': 'README.html', 'display': 'README.md'}],
                'directories': []
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
                'files': [{'name': 'file()[].html', 'display': 'file()[].md'}],
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
