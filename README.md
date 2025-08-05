# markdown-up

[![PyPI - Status](https://img.shields.io/pypi/status/markdown-up)](https://pypi.org/project/markdown-up/)
[![PyPI](https://img.shields.io/pypi/v/markdown-up)](https://pypi.org/project/markdown-up/)
[![GitHub](https://img.shields.io/github/license/craigahobbs/markdown-up-py)](https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/markdown-up)](https://pypi.org/project/markdown-up/)

MarkdownUp is a Markdown viewer.


## Install MarkdownUp

Use Python's `pip` to install MarkdownUp as follows:

~~~
pip install markdown-up
~~~


## View Markdown Files

To start MarkdownUp, open a terminal and run the `markdown-up` application:

~~~
markdown-up
~~~

The `markdown-up` application opens the web browser to the MarkdownUp file browser, which allows you
to view Markdown or HTML files and navigate directories. To view a file, click on its link.

You can view a specific file as follows:

~~~
markdown-up README.md
~~~

**Note:** MarkdownUp runs entirely offline. It does not use an external service to render Markdown
files.


## Running MarkdownUp

When you run the `markdown-up` application, in addition to opening the web browser, it starts a
[chisel](https://pypi.org/project/chisel/)
backend API application using
[waitress](https://pypi.org/project/waitress/).


### Automatic HTML for Markdown Files

When you run MarkdownUp and click on a Markdown file link, the link navigates to an HTML file that
renders the Markdown file. Every Markdown file hosted by MarkdownUp has a corresponding `.html` file
of the same name. For example, if you run MarkdownUp in a directory that has the following Markdown
files: "README.md" and "CHANGELOG.md". The MarkdownUp service automatically generates "README.html"
and "CHANGELOG.html" files.

The generated `.html` files are HTML stubs for the
[MarkdownUp Front-End Application](https://github.com/craigahobbs/markdown-up#readme).
All Markdown parsing and rendering are done on the client.


### Configuration File

The
[MarkdownUp Application Configuration File](https://craigahobbs.github.io/markdown-up-py/config.html#var.vName='MarkdownUpConfig'),
`markdown-up.json`, allows you to enable release mode, set the number of backend server threads, and more.


### Command-Line Arguments

The `markdown-up` application has the following command-line arguments:

```
usage: markdown-up [-h] [-p N] [-t N] [-n] [-r] [-q] [-d] [-v VAR EXPR] [-c FILE] [-a FILE] [path]

positional arguments:
  path                the file or directory to view (default is ".")

options:
  -h, --help          show this help message and exit
  -p, --port N        the application port (default is 8080)
  -t, --threads N     the number of web server threads (default is 8)
  -n, --no-browser    don't open a web browser
  -r, --release       release mode (cache statics, remove documentation and index)
  -q, --quiet         hide access logging
  -d, --debug         backend debug mode
  -v, --var VAR EXPR  set a backend global variable
  -c, --config FILE   the application config filename (default is "markdown-up.json")
  -a, --api FILE      the API config filename (default is "markdown-up-api.json")
  ```


## MarkdownUp Applications

[MarkdownUp Applications](https://github.com/craigahobbs/markdown-up?tab=readme-ov-file#dynamic-markdown-applications)
are front-end applications that run within the
[MarkdownUp Front-End Application](https://github.com/craigahobbs/markdown-up#readme)
using the
[BareScript](https://github.com/craigahobbs/bare-script#readme)
programming language. Markdown files viewed within MarkdownUp may contain `markdown-script` fenced
code blocks containing
[BareScript](https://github.com/craigahobbs/bare-script#readme)
that execute when the Markdown renders.


### Application Example

TODO


#### Frontend Application

TODO

MarkdownUp has libraries for dynamically generating and rendering Markdown text, drawing SVG images,
performing data analytics, parsing application arguments, and much more. See the
[MarkdownUp Library](https://craigahobbs.github.io/markdown-up/library/)
and
[MarkdownUp Include Library](https://craigahobbs.github.io/markdown-up/library/include.html)
for more information.


#### Backend APIs

TODO


### Other Examples

To see what's possible with MarkdownUp Applications, see the
[MarkdownUp Application Examples](https://craigahobbs.github.io/#var.vPage='MarkdownUp')
page.


## Development

This package is developed using [python-build](https://github.com/craigahobbs/python-build#readme).
It was started using [python-template](https://github.com/craigahobbs/python-template#readme) as follows:

~~~
template-specialize python-template/template/ markdown-up-py/ -k package markdown-up -k name 'Craig A. Hobbs' -k email 'craigahobbs@gmail.com' -k github 'craigahobbs' -k noapi 1
~~~
