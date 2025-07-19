# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

"""
The MarkdownUp launcher back-end API support
"""

from functools import partial
import bare_script
from bare_script.value import value_args_model, value_args_validate
import chisel
import schema_markdown


# Load the MarkdownUp backend config requests
def load_backend_requests(config):
    debug = config.get('debug', False)
    schemas = config.get('schemas') or []
    scripts = config.get('scripts') or []
    apis = config.get('apis') or []

    # Parse the backend schema markdown files
    types = {}
    for schema in schemas:
        with open(schema, 'r', encoding='utf-8') as schema_file:
            schema_markdown.parse_schema_markdown(schema_file, types, filename=schema, validate=False)
    if types:
        schema_markdown.validate_type_model(types)

    # Parse and execute the backend BareScript files
    backend_globals = {
        'backendHeader': _backend_header,
        'backendError': _backend_error
    }
    script_options = {
        'debug': debug,
        'fetchFn': bare_script.fetch_read_write,
        'globals': backend_globals,
        'logFn': bare_script.log_stdout,
        'urlFile': bare_script.url_file_relative
    }
    for script in scripts:
        with open(script, 'r', encoding='utf-8') as script_file:
            bare_script.execute_script(bare_script.parse_script(script_file), script_options)

    # Yield the backend APIs
    for api in apis:
        api_name = api['name']
        api_fn = api.get('function', api_name)

        # Add the API action
        script_fn = backend_globals[api_fn]
        action_fn = partial(_bare_script_action_fn, script_fn, backend_globals, debug)
        yield chisel.Action(action_fn, name=api_name, types=types)


# Special backend global variables
_BACKEND_GLOBAL = '__markdown_up__'


# Action function wrapper for a MarkdownUp backend API function
def _bare_script_action_fn(script_fn, backend_globals, debug, ctx, req):
    # Copy the backend globals
    script_globals = dict(backend_globals)
    script_globals[_BACKEND_GLOBAL] = {'headers': {}}

    # Execute the API function
    script_options = {
        'debug': debug,
        'fetchFn': bare_script.fetch_read_write,
        'globals': script_globals,
        'logFn': bare_script.log_stdout,
        'statementCount': 0,
        'urlFile': bare_script.url_file_relative
    }
    response = script_fn([req], script_options)

    # Add response headers, if any
    backend_state = script_globals[_BACKEND_GLOBAL]
    ctx.headers.update(backend_state['headers'])

    # Error?
    if 'error' in backend_state:
        raise chisel.ActionError(backend_state['error'], status=backend_state.get('errorStatus'))

    return response


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
