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
of the same name. For example, if you run Markdown up in a directory that has the following Markdown
files: "README.md" and "CHANGELOG.md". The MarkdownUp service automatically generates "README.html"
and "CHANGELOG.html" files.

The generated `.html` files are HTML stubs for the
[MarkdownUp Front-End Application](https://github.com/craigahobbs/markdown-up#readme).
All Markdown parsing and rendering are done on the client to minimize server costs.


### Command-Line Arguments

The `markdown-up` application has the following command-line arguments:

```
usage: markdown-up [-h] [-p N] [-t N] [-n] [-r] [-q] [path]

positional arguments:
  path        the file or directory to view (default is ".")

options:
  -h, --help  show this help message and exit
  -p N        the application port (default is 8080)
  -t N        the number of web server threads (default is 8)
  -n          don't open a web browser
  -r          release mode (cache statics, remove documentation and index)
  -q          don't display access logging
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

MarkdownUp has libraries for dynamically generating and rendering Markdown text, drawing SVG images,
performing data analytics, parsing application arguments, and much more. See the
[MarkdownUp Library](https://craigahobbs.github.io/markdown-up/library/)
and
[MarkdownUp Include Library](https://craigahobbs.github.io/markdown-up/library/include.html)
for more information.

Here's an example of a simple MarkdownUp application:

~~~markdown
# The First Ten Numbers

Here are the first ten numbers:

```markdown-script
i = 1
while i <= 10:
    markdownPrint('', stringNew(i))
    i = i + 1
endwhile
```
~~~


### MarkdownUp Application Examples

To see what's possible with MarkdownUp Applications, see the
[MarkdownUp Application Examples](https://craigahobbs.github.io/#var.vPage='MarkdownUp')
page.


## Development

This package is developed using [python-build](https://github.com/craigahobbs/python-build#readme).
It was started using [python-template](https://github.com/craigahobbs/python-template#readme) as follows:

~~~
template-specialize python-template/template/ markdown-up-py/ -k package markdown-up -k name 'Craig A. Hobbs' -k email 'craigahobbs@gmail.com' -k github 'craigahobbs' -k noapi 1
~~~
