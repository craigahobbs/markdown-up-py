# markdown-up

[![PyPI - Status](https://img.shields.io/pypi/status/markdown-up)](https://pypi.org/project/markdown-up/)
[![PyPI](https://img.shields.io/pypi/v/markdown-up)](https://pypi.org/project/markdown-up/)
[![GitHub](https://img.shields.io/github/license/craigahobbs/markdown-up-py)](https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/markdown-up)](https://pypi.org/project/markdown-up/)

**markdown-up** is a Markdown viewer application. To launch markdown-up, run it from the command line:

```
$ markdown-up
```

The markdown-up service starts and then opens the web browser to the current directory index by default. You can also
open a specific file or directory:

```
$ markdown-up README.md
```


## How it works

markdown-up first starts a [chisel](https://pypi.org/project/chisel/) back-end API server to host the
[markdown-up JavaScript application](https://www.npmjs.com/package/markdown-up)
and host the Markdown static files (it only hosts statics below the root directory). Once the API service has
started, the markdown-up application opens the desired directory (index) or Markdown file for viewing.

To view the markdown-up back-end API documentation, open the Chisel documentation application at "/doc".


## Development

This project is developed using [python-build](https://github.com/craigahobbs/python-build#readme). It was started
using [python-template](https://github.com/craigahobbs/python-template#readme) as follows:

```
template-specialize python-template/template/ markdown-up-py/ -k package markdown-up -k name 'Craig A. Hobbs' -k email 'craigahobbs@gmail.com' -k github 'craigahobbs' -k noapi 1
```
