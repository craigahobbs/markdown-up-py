# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

"""
MarkdownUp back-end API support
"""

from functools import partial
import os
from pathlib import Path

import bare_script
from bare_script.value import value_args_model, value_args_validate
import chisel
import schema_markdown


# Load the MarkdownUp backend config requests
def load_backend_requests(root, config, api_config):
    debug = config.get('debug', False)

    # Parse the backend schema markdown files
    types = {}
    for schema_posix in api_config.get('schemas'):
        schema_parts = Path(schema_posix).parts
        schema_path = os.path.normpath(os.path.join(root, *(schema_parts[1:] if schema_parts[0] == '/' else schema_parts)))
        with open(schema_path, 'r', encoding='utf-8') as schema_file:
            schema_markdown.parse_schema_markdown(schema_file, types, filename=schema_posix, validate=False)
    schema_markdown.validate_type_model(types)

    # Parse and execute the backend BareScript files
    backend_globals = {
        'backendHeader': _backend_header,
        'backendError': _backend_error
    }
    if 'globals' in config:
        for key, value in config['globals'].items():
            backend_globals[key] = value
    script_options = {
        'debug': debug,
        'fetchFn': bare_script.fetch_read_write,
        'globals': backend_globals,
        'logFn': bare_script.log_stdout,
        'urlFile': bare_script.url_file_relative
    }
    for script_posix in api_config.get('scripts'):
        script_parts = Path(script_posix).parts
        script_path = os.path.normpath(os.path.join(root, *(script_parts[1:] if script_parts[0] == '/' else script_parts)))
        with open(script_path, 'r', encoding='utf-8') as script_file:
            bare_script.execute_script(bare_script.parse_script(script_file), script_options)

    # Yield the backend APIs
    for api in api_config.get('apis'):
        api_name = api['name']
        api_fn = api.get('function', api_name)
        api_wsgi = api.get('wsgi', False)

        # Add the API action
        script_fn = backend_globals[api_fn]
        action_fn = partial(_bare_script_action_fn, script_fn, api_wsgi, backend_globals, debug)
        yield chisel.Action(action_fn, name=api_name, types=types, wsgi_response=api_wsgi)


# Special backend global variables
_BACKEND_GLOBAL = '__markdown_up__'


# Action function wrapper for a MarkdownUp backend API function
def _bare_script_action_fn(script_fn, api_wsgi, backend_globals, debug, ctx, req):
    # Copy the backend globals
    script_globals = dict(backend_globals)
    script_globals[_BACKEND_GLOBAL] = {'headers': {}}

    # Execute the API function
    wsgi_errors = ctx.environ.get('wsgi.errors')
    script_options = {
        'debug': debug,
        'fetchFn': bare_script.fetch_read_write,
        'globals': script_globals,
        'logFn': partial(_log_filehandle, wsgi_errors) if wsgi_errors is not None else None ,
        'statementCount': 0,
        'urlFile': bare_script.url_file_relative
    }
    response = script_fn([req], script_options)

    # Error?
    backend_state = script_globals[_BACKEND_GLOBAL]
    if 'error' in backend_state:
        raise chisel.ActionError(backend_state['error'], status=backend_state.get('errorStatus'))

    # WSGI response?
    if api_wsgi:
        # Add WSGI response headers
        headers = response[1]
        headers.extend(backend_state['headers'].items())

        # WSGI response
        ctx.start_response(response[0], headers)
        return [response[2].encode('utf-8')]

    # Add response headers
    ctx.headers.update(backend_state['headers'])

    return response


# File handle logging function
def _log_filehandle(fh, text):
    print(text, file=fh)


# $function: backendHeader
# $group: Backend
# $doc: Add a backend API response header
# $arg key: The key string
# $arg value: The value string
def _backend_header(args, options):
    key, value = value_args_validate(_BACKEND_HEADER_ARGS, args)
    backend_state = options['globals'][_BACKEND_GLOBAL]
    backend_state['headers'][key] = value

_BACKEND_HEADER_ARGS = value_args_model([
    {'name': 'key', 'type': 'string'},
    {'name': 'value', 'type': 'string'}
])


# $function: backendError
# $group: Backend
# $doc: Set the backend API error response
# $arg error: The error code string (e.g. "UnknownID")
# $arg value: The status string (default is "400 Bad Request")
def _backend_error(args, options):
    error, status = value_args_validate(_BACKEND_ERROR_ARGS, args)
    backend_state = options['globals'][_BACKEND_GLOBAL]
    backend_state['error'] = error
    backend_state['errorStatus'] = status if status else '400 Bad Request'

_BACKEND_ERROR_ARGS = value_args_model([
    {'name': 'error', 'type': 'string'},
    {'name': 'status', 'type': 'string', 'nullable': True}
])
