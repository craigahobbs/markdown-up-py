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
[MarkdownUp frontend application](https://github.com/craigahobbs/markdown-up#readme).
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

With MarkdownUp, you can write client-rendered frontend applications and backend APIs using
[BareScript](https://craigahobbs.github.io/bare-script/language/).


### MarkdownUp Frontend Applications

MarkdownUp frontend applications are created by adding `markdown-script` fenced code blocks containing
[BareScript](https://craigahobbs.github.io/bare-script/language/)
to a Markdown file and viewing it with the MarkdownUp frontend application. When the Markdown file
is rendered, the BareScript is executed and its results are rendered in place. For example:

~~~markdown
# Frontend Hello World

```markdown-script
markdownPrint('Hello, **World**!!')
```
~~~


#### MarkdownUp Frontend Reference

[The BareScript Language](https://craigahobbs.github.io/bare-script/language/)

[The BareScript Library](https://craigahobbs.github.io/bare-script/library/)

[MarkdownUp Frontend Examples](https://craigahobbs.github.io/#var.vPage='MarkdownUp')


### MarkdownUp Backend APIs

MarkdownUp backend applications are created by adding a
[MarkdownUp Backend API Configuration File](https://craigahobbs.github.io/markdown-up-py/config.html#var.vName='MarkdownUpAPIConfig'),
`markdown-up-api.json`.

The `markdown-up-api.json` file specifies the following:

- The [Schema Markdown](https://craigahobbs.github.io/schema-markdown-js/language/) files containing
  the API input and output schema definitions

- The [BareScript](https://craigahobbs.github.io/bare-script/language/) files containing the API
  implementations


#### MarkdownUp Backend Reference

[MarkdownUp Backend API Configuration File](https://craigahobbs.github.io/markdown-up-py/config.html#var.vName='MarkdownUpAPIConfig')

[The BareScript Language](https://craigahobbs.github.io/bare-script/language/)

[The Schema Markdown Language](https://craigahobbs.github.io/schema-markdown-js/language/)

[The MarkdownUp Backend API Library](https://craigahobbs.github.io/markdown-up-py/api.html)


### MarkdownUp Full Stack Application Example

In this simple full-stack application example, we'll create a MarkdownUp frontend application to
input two numbers and display their sum. We'll use a MarkdownUp backend API to sum the numbers.


**index.md**

The frontend application's index file, `index.md`, includes the application script and executes the
main entry point:

~~~markdown
```markdown-script
include 'example.bare'

exampleMain()
```
~~~


**example.bare**

The frontend application file, `example.bare`, uses the
[args.bare](https://craigahobbs.github.io/bare-script/library/#var.vGroup='args.bare')
include library to parse the application arguments. It then uses the `sumNumbers` API to sum the
numbers. Finally, it then renders the links to change the input numbers and the result.

```barescript
include <args.bare>


# The example application main entry point
async function exampleMain():
    args = argsParse(exampleArguments)
    n1 = objectGet(args, 'n1')
    n2 = objectGet(args, 'n2')

    # Call the backend service to add the two numbers
    sumResponseText = systemFetch({'url': 'sumNumbers', 'body': jsonStringify({'n1': n1, 'n2': n2})})
    sumResponseJSON = if(sumResponseText, jsonParse(sumResponseText))
    result = if(sumResponseJSON, objectGet(sumResponseJSON, 'result'))

    # Render the page
    title = 'Sum Two Numbers'
    documentSetTitle(title)
    markdownPrint( \
        '# ' + markdownEscape(title), \
        '', \
        'n1 = ' + n1 + ' (' + \
            argsLink(exampleArguments, 'Down', {'n1': n1 - 1}) + ' | ' + \
            argsLink(exampleArguments, 'Up', {'n1': n1 + 1}) + ')', \
        '', \
        'n2 = ' + n2 + ' (' + \
            argsLink(exampleArguments, 'Down', {'n2': n2 - 1}) + ' | ' + \
            argsLink(exampleArguments, 'Up', {'n2': n2 + 1}) + ')', \
        '', \
        n1 + ' + ' + n2 + ' = ' + result \
    )
endfunction


# The example application's arguments (for use with argsParse, etc.)
exampleArguments = [ \
    {'name': 'n1', 'type': 'float', 'default': 0}, \
    {'name': 'n2', 'type': 'float', 'default': 0} \
]
```


**markdown-up-api.json**

The
[MarkdownUp Backend API Configuration File](https://craigahobbs.github.io/markdown-up-py/config.html#var.vName='MarkdownUpAPIConfig'),
`markdown-up-api.json`, specifies the backend API:

```json
{
    "schemas": ["example.smd"],
    "scripts": ["exampleAPI.bare"],
    "apis": [
        {"name": "sumNumbers"}
    ]
}
```


**example.smd**

The API input and output schemas are defined using
[Schema Markdown](https://craigahobbs.github.io/schema-markdown-js/language/).

```schema-markdown
group "Example"


# Sum two numbers
action sumNumbers
    input
        # The first number
        float n1

        # The second number
        float n2

    output
        # The sum of the two numbers
        float result
```


**exampleAPI.bare**

The backend API is implemented in [BareScript](https://craigahobbs.github.io/bare-script/language/).
By default, API implementation functions have the same name as the API schema definition. API
implementation functions take a single argument, `request`, that is the schema-validated input
object.

```barescript
# Implementation of the sumNumbers API
function sumNumbers(request):
    n1 = objectGet(request, 'n1')
    n2 = objectGet(request, 'n2')
    return {'result': n1 + n2}
endfunction
```

To run the application, run `markdown-up` in the directory containing the application files.

```sh
markdown-up index.md
```

With the application running, you can view the backend API documentation at <http://127.0.0.1:8080/doc/>.


## Development

This package is developed using [python-build](https://github.com/craigahobbs/python-build#readme).
It was started using [python-template](https://github.com/craigahobbs/python-template#readme) as follows:

~~~
template-specialize python-template/template/ markdown-up-py/ -k package markdown-up -k name 'Craig A. Hobbs' -k email 'craigahobbs@gmail.com' -k github 'craigahobbs' -k noapi 1
~~~
