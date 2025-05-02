# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

from contextlib import contextmanager
import json
import os
from tempfile import TemporaryDirectory
import unittest
import unittest.mock

import chisel.app
from markdown_up.app import MarkdownUpApplication, MarkdownUpStaticRequest


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
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', 'd26ad180babc57df8a633cfe06676fb8')]
            )
            self.assertEqual(content, [MarkdownUpStaticRequest.create_markdown_up_stub('README.md').encode('utf-8')])

            # Get a raw markdown file
            environ = chisel.Context.create_environ('GET', '/README.md', query_string='raw=true')
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
            environ['HTTP_IF_NONE_MATCH'] = 'd26ad180babc57df8a633cfe06676fb8'
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '304 Not Modified')
            self.assertEqual(start_response.headers, [])
            self.assertEqual(content, [])

            # Get an unmodified raw markdown file
            environ = chisel.Context.create_environ('GET', '/README.md', query_string='raw=true')
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
                [('Content-Type', 'image/svg+xml; charset=utf-8'), ('ETag', '7b56e1eab00ec8000da9331a4888cb35')]
            )
            self.assertEqual(content, [b'<svg></svg>'])

            # Get a not-found file - Markdown
            environ = chisel.Context.create_environ('GET', '/not-found.md')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '404 Not Found')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])
            self.assertEqual(content, [b'Not Found'])

            # Get a not-found file - raw Markdown
            environ = chisel.Context.create_environ('GET', '/not-found.md', query_string='raw=true')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '404 Not Found')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])
            self.assertEqual(content, [b'Not Found'])

            # Get a not-found file - non-Markdown
            environ = chisel.Context.create_environ('GET', '/not-found.txt')
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

            # Verify no requests were added
            self.assertTrue('/README.md' not in app.requests)
            self.assertTrue('/images/image.svg' not in app.requests)
            self.assertTrue('/not-found.md' not in app.requests)
            self.assertTrue('/file.unk' not in app.requests)

            # Verify redirect requests
            self.assertListEqual(
                [
                    (redirect.urls, redirect.doc) for _, redirect in sorted(app.requests.items())
                    if isinstance(redirect, chisel.RedirectRequest)
                ],
                [
                    ((('GET', '/doc'),), 'Redirect to /doc/')
                ]
            )


    def test_static_markdown_release(self):
        test_files = [
            ('README.md', '# Title'),
            (('sub', 'index.md'), '# Index'),
            (('sub', 'test.md'), '# Test'),
            ('test.txt', 'Title')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, True)

            # Get "/README.md"
            environ = chisel.Context.create_environ('GET', '/README.md')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', 'd26ad180babc57df8a633cfe06676fb8')]
            )
            expected_content = MarkdownUpStaticRequest.create_markdown_up_stub('README.md')
            self.assertEqual(content, [expected_content.encode('utf-8')])

            # Get "/sub/"
            environ = chisel.Context.create_environ('GET', '/sub/')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', '2979cf7462fcf85e5c1f7257d7efbbc0')]
            )
            expected_content = MarkdownUpStaticRequest.create_markdown_up_stub('index.md')
            self.assertEqual(content, [expected_content.encode('utf-8')])

            # Get "/sub/test.md"
            environ = chisel.Context.create_environ('GET', '/sub/test.md')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', '78c893f60fceca53eb8cde1fcc3a87db')]
            )
            expected_content = MarkdownUpStaticRequest.create_markdown_up_stub('test.md')
            self.assertEqual(content, [expected_content.encode('utf-8')])

            # Get "/test.txt"
            environ = chisel.Context.create_environ('GET', '/test.txt')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/plain; charset=utf-8'), ('ETag', 'b78a3223503896721cca1303f776159b')]
            )
            self.assertEqual(content, [b'Title'])

            # Verify "/README.md" request
            request = app.requests.get('/README.md')
            self.assertTrue(request is not None)
            self.assertEqual(request.name, '/README.md')
            self.assertEqual(request.doc, 'The static resource "/README.md". Use `?raw=true` to get the raw content.')
            self.assertEqual(request.urls, (('GET', '/'), ('GET', '/README.md')))
            self.assertEqual(request.headers, [
                ('Content-Type', 'text/markdown; charset=utf-8'),
                ('ETag', '38cdd67987afb67a4af89ea02044a00e')
            ])
            self.assertEqual(request.content, b'# Title')
            self.assertEqual(request.etag, '38cdd67987afb67a4af89ea02044a00e')

            # Verify "/sub/" request
            request = app.requests.get('/sub/index.md')
            redirect_request = app.requests.get('/sub/')
            self.assertTrue(request is not None)
            self.assertTrue(redirect_request is not None)
            self.assertEqual(request.name, '/sub/index.md')
            self.assertEqual(request.doc, 'The static resource "/sub/index.md". Use `?raw=true` to get the raw content.')
            self.assertEqual(request.urls, (('GET', '/sub/'), ('GET', '/sub/index.md')))
            self.assertEqual(request.headers, [
                ('Content-Type', 'text/markdown; charset=utf-8'),
                ('ETag', 'df6b2237aef04199008203d333637579')
            ])
            self.assertEqual(request.content, b'# Index')
            self.assertEqual(request.etag, 'df6b2237aef04199008203d333637579')
            self.assertEqual(redirect_request.doc, 'Redirect to /sub/')
            self.assertEqual(redirect_request.urls, (('GET', '/sub'),))

            # Verify "/sub/test.md" request
            request = app.requests.get('/sub/test.md')
            self.assertTrue(request is not None)
            self.assertEqual(request.name, '/sub/test.md')
            self.assertEqual(request.doc, 'The static resource "/sub/test.md". Use `?raw=true` to get the raw content.')
            self.assertEqual(request.urls, (('GET', '/sub/test.md'),))
            self.assertEqual(request.headers, [
                ('Content-Type', 'text/markdown; charset=utf-8'),
                ('ETag', '7ba5401b897f966b4ba7c258c37a8732')
            ])
            self.assertEqual(request.content, b'# Test')
            self.assertEqual(request.etag, '7ba5401b897f966b4ba7c258c37a8732')

            # Verify "/test.txt" request
            request = app.requests.get('/test.txt')
            self.assertTrue(request is not None)
            self.assertEqual(request.name, '/test.txt')
            self.assertEqual(request.doc, 'The static resource "/test.txt"')
            self.assertEqual(request.urls, (('GET', '/test.txt'),))
            self.assertEqual(request.headers, [('Content-Type', 'text/plain; charset=utf-8'), ('ETag', 'b78a3223503896721cca1303f776159b')])
            self.assertEqual(request.content, b'Title')
            self.assertEqual(request.etag, 'b78a3223503896721cca1303f776159b')

            # Verify redirect requests
            self.assertListEqual(
                [
                    (redirect.urls, redirect.doc) for _, redirect in sorted(app.requests.items())
                    if isinstance(redirect, chisel.RedirectRequest)
                ],
                [
                    ((('GET', '/sub'),), 'Redirect to /sub/')
                ]
            )


    def test_static_markdown_release_multiple_indexes(self):
        test_files = [
            (('sub', 'index.md'), '# Title'),
            (('sub', 'README.md'), '# Title')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, True)

            # Get "/sub/index.md"
            environ = chisel.Context.create_environ('GET', '/sub/index.md')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', '2979cf7462fcf85e5c1f7257d7efbbc0')]
            )
            expected_content = MarkdownUpStaticRequest.create_markdown_up_stub('index.md')
            self.assertEqual(content, [expected_content.encode('utf-8')])

            # Get "/sub/README.md"
            environ = chisel.Context.create_environ('GET', '/sub/README.md')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', 'd26ad180babc57df8a633cfe06676fb8')]
            )
            expected_content = MarkdownUpStaticRequest.create_markdown_up_stub('README.md')
            self.assertEqual(content, [expected_content.encode('utf-8')])

            # Verify "/sub/index.md" request
            request = app.requests.get('/sub/index.md')
            self.assertTrue(request is not None)
            self.assertEqual(request.name, '/sub/index.md')
            self.assertEqual(request.doc, 'The static resource "/sub/index.md". Use `?raw=true` to get the raw content.')
            self.assertEqual(request.urls, (('GET', '/sub/'), ('GET', '/sub/index.md')))
            self.assertEqual(request.headers, [
                ('Content-Type', 'text/markdown; charset=utf-8'),
                ('ETag', '38cdd67987afb67a4af89ea02044a00e')
            ])
            self.assertEqual(request.content, b'# Title')
            self.assertEqual(request.etag, '38cdd67987afb67a4af89ea02044a00e')

            # Verify "/sub/README.md" request
            request = app.requests.get('/sub/README.md')
            self.assertTrue(request is not None)
            self.assertEqual(request.name, '/sub/README.md')
            self.assertEqual(request.doc, 'The static resource "/sub/README.md". Use `?raw=true` to get the raw content.')
            self.assertEqual(request.urls, (('GET', '/sub/README.md'),))
            self.assertEqual(request.headers, [
                ('Content-Type', 'text/markdown; charset=utf-8'),
                ('ETag', '38cdd67987afb67a4af89ea02044a00e')
            ])
            self.assertEqual(request.content, b'# Title')
            self.assertEqual(request.etag, '38cdd67987afb67a4af89ea02044a00e')

            # Verify redirect requests
            self.assertListEqual(
                [
                    (redirect.urls, redirect.doc) for _, redirect in sorted(app.requests.items())
                    if isinstance(redirect, chisel.RedirectRequest)
                ],
                [
                    ((('GET', '/sub'),), 'Redirect to /sub/')
                ]
            )


    def test_static_markdown_release_multiple_indexes_reversed(self):
        test_files = [
            (('sub', 'index.md'), '# Title'),
            (('sub', 'README.md'), '# Title')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir, True)

            # Get "/sub/README.md"
            environ = chisel.Context.create_environ('GET', '/sub/README.md')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', 'd26ad180babc57df8a633cfe06676fb8')]
            )
            expected_content = MarkdownUpStaticRequest.create_markdown_up_stub('README.md')
            self.assertEqual(content, [expected_content.encode('utf-8')])

            # Get "/sub/index.md"
            environ = chisel.Context.create_environ('GET', '/sub/index.md')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', '2979cf7462fcf85e5c1f7257d7efbbc0')]
            )
            expected_content = MarkdownUpStaticRequest.create_markdown_up_stub('index.md')
            self.assertEqual(content, [expected_content.encode('utf-8')])

            # Verify "/sub/index.md" request
            request = app.requests.get('/sub/index.md')
            self.assertTrue(request is not None)
            self.assertEqual(request.name, '/sub/index.md')
            self.assertEqual(request.doc, 'The static resource "/sub/index.md". Use `?raw=true` to get the raw content.')
            self.assertEqual(request.urls, (('GET', '/sub/'), ('GET', '/sub/index.md')))
            self.assertEqual(request.headers, [
                ('Content-Type', 'text/markdown; charset=utf-8'),
                ('ETag', '38cdd67987afb67a4af89ea02044a00e')
            ])
            self.assertEqual(request.content, b'# Title')
            self.assertEqual(request.etag, '38cdd67987afb67a4af89ea02044a00e')

            # Verify "/sub/README.md" request
            request = app.requests.get('/sub/README.md')
            self.assertTrue(request is not None)
            self.assertEqual(request.name, '/sub/README.md')
            self.assertEqual(request.doc, 'The static resource "/sub/README.md". Use `?raw=true` to get the raw content.')
            self.assertEqual(request.urls, (('GET', '/sub/README.md'),))
            self.assertEqual(request.headers, [
                ('Content-Type', 'text/markdown; charset=utf-8'),
                ('ETag', '38cdd67987afb67a4af89ea02044a00e')
            ])
            self.assertEqual(request.content, b'# Title')
            self.assertEqual(request.etag, '38cdd67987afb67a4af89ea02044a00e')

            # Verify redirect requests
            self.assertListEqual(
                [
                    (redirect.urls, redirect.doc) for _, redirect in sorted(app.requests.items())
                    if isinstance(redirect, chisel.RedirectRequest)
                ],
                [
                    ((('GET', '/sub'),), 'Redirect to /sub/')
                ]
            )


    def test_static_markdown_escape(self):
        test_files = [
            ('md file.md', '# Title'),
            ('txt file.txt', 'Text')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir)

            # Get a markdown file
            environ = chisel.Context.create_environ('GET', '/md file.md')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', 'f82390e20c67d23084eb766122bb7ea6')]
            )
            expected_content = MarkdownUpStaticRequest.create_markdown_up_stub('md file.md')
            self.assertEqual(content, [expected_content.encode('utf-8')])
            self.assertTrue("'md%20file.md?raw=true'" in expected_content)


    def test_static_markdown_invalid_query(self):
        test_files = [
            ('test.md', '# Title'),
            ('test.txt', 'Title')
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir)

            # Get a markdown file
            environ = chisel.Context.create_environ('GET', '/test.md', query_string='raw=1')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/html; charset=utf-8'), ('ETag', '78c893f60fceca53eb8cde1fcc3a87db')]
            )
            expected_content = MarkdownUpStaticRequest.create_markdown_up_stub('test.md')
            self.assertEqual(content, [expected_content.encode('utf-8')])

            # Get a markdown file
            environ = chisel.Context.create_environ('GET', '/test.txt', query_string='raw=1')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '200 OK')
            self.assertEqual(
                start_response.headers,
                [('Content-Type', 'text/plain; charset=utf-8'), ('ETag', 'b78a3223503896721cca1303f776159b')]
            )
            self.assertEqual(content, [b'Title'])


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
            self.assertEqual(start_response.status, '301 Moved Permanently')
            self.assertEqual(start_response.headers, [('Location', '/html/')])
            self.assertEqual(content, [])


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
            self.assertEqual(start_response.status, '301 Moved Permanently')
            self.assertEqual(start_response.headers, [('Location', '/html/')])
            self.assertEqual(content, [])


    def test_static_index_none(self):
        test_files = [
            (('sub', 'page.md'), '# Title'),
        ]
        with create_test_files(test_files) as temp_dir:
            app = MarkdownUpApplication(temp_dir)

            # Get the index file
            environ = chisel.Context.create_environ('GET', '/sub/')
            start_response = chisel.app.StartResponse()
            content = app(environ, start_response)
            self.assertEqual(start_response.status, '404 Not Found')
            self.assertEqual(start_response.headers, [('Content-Type', 'text/plain; charset=utf-8')])
            self.assertEqual(content, [b'Not Found'])

            # Get the index file (alternate)
            environ = chisel.Context.create_environ('GET', '/sub')
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
                'files': ['README.md', 'index.html'],
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
                'files': ['README.md'],
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
                'files': ['README.md'],
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
