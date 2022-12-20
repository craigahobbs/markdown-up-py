# markdown-up

[![PyPI - Status](https://img.shields.io/pypi/status/markdown-up)](https://pypi.org/project/markdown-up/)
[![PyPI](https://img.shields.io/pypi/v/markdown-up)](https://pypi.org/project/markdown-up/)
[![GitHub](https://img.shields.io/github/license/craigahobbs/markdown-up-py)](https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/markdown-up)](https://pypi.org/project/markdown-up/)

**markdown-up** is the
[MarkdownUp](https://craigahobbs.github.io/markdown-up/)
launcher.
[MarkdownUp](https://craigahobbs.github.io/markdown-up/)
is a Markdown viewer.


## Links

- [Source code](https://github.com/craigahobbs/markdown-up-py)


## View Local Markdown Files

To view local Markdown files, run the markdown-up command-line application from a terminal prompt:

~~~
pip install markdown-up
markdown-up
~~~

You can also open a specific file or directory:

~~~
markdown-up README.md
~~~


## Development

This package is developed using [python-build](https://github.com/craigahobbs/python-build#readme).
It was started using [python-template](https://github.com/craigahobbs/python-template#readme) as follows:

~~~
template-specialize python-template/template/ markdown-up-py/ -k package markdown-up -k name 'Craig A. Hobbs' -k email 'craigahobbs@gmail.com' -k github 'craigahobbs' -k noapi 1
~~~
