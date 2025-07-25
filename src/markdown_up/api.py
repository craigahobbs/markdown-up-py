# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

"""
MarkdownUp backend API support
"""

from functools import partial
import os
from pathlib import PurePosixPath

import bare_script
from bare_script.value import value_args_model, value_args_validate
import chisel
import schema_markdown


# Load the MarkdownUp API requests
def load_api_requests(root, config, api_config):
    debug = config.get('debug', False)

    # Parse the API schema markdown files
    types = {}
    for schema_posix in api_config['schemas']:
        schema_parts = PurePosixPath(schema_posix).parts
        schema_path = os.path.join(root, *(schema_parts[1:] if schema_parts[0] == '/' else schema_parts))
        with open(schema_path, 'r', encoding='utf-8') as schema_file:
            schema_markdown.parse_schema_markdown(schema_file, types, filename=schema_posix, validate=False)
    schema_markdown.validate_type_model(types)

    # Parse and execute the API BareScript files
    api_globals = {
        'apiHeader': _api_header,
        'apiError': _api_error
    }
    if 'globals' in config:
        for key, value in config['globals'].items():
            api_globals[key] = value
    script_options = {
        'debug': debug,
        'fetchFn': bare_script.fetch_read_write,
        'globals': api_globals,
        'logFn': bare_script.log_stdout,
        'urlFile': bare_script.url_file_relative
    }
    for script_posix in api_config['scripts']:
        script_parts = PurePosixPath(script_posix).parts
        script_path = os.path.join(root, *(script_parts[1:] if script_parts[0] == '/' else script_parts))
        with open(script_path, 'r', encoding='utf-8') as script_file:
            bare_script.execute_script(bare_script.parse_script(script_file), script_options)

    # Yield the API requests
    for api in api_config['apis']:
        api_name = api['name']
        api_fn_name = api.get('function', api_name)
        api_wsgi = api.get('wsgi', False)

        # Add the API action
        api_fn = api_globals.get(api_fn_name)
        if not api_fn or not callable(api_fn):
            raise NameError(f'Unknown API function "{api_fn_name}"')
        action_fn = partial(_bare_script_action_fn, api_fn_name, api_wsgi, api_globals, debug)
        yield chisel.Action(action_fn, name=api_name, types=types, wsgi_response=api_wsgi)


# Special API global variables
_API_GLOBAL = '__markdown_up__'


# Action function wrapper for a MarkdownUp API function
def _bare_script_action_fn(api_fn_name, api_wsgi, api_globals, debug, ctx, req):
    api_fn = api_globals.get(api_fn_name)

    # Copy the API globals
    script_globals = dict(api_globals)
    script_globals[_API_GLOBAL] = {'headers': {}}

    # Execute the API function
    wsgi_errors = ctx.environ.get('wsgi.errors')
    script_options = {
        'debug': debug,
        'fetchFn': bare_script.fetch_read_write,
        'globals': script_globals,
        'logFn': partial(_log_filehandle, wsgi_errors) if wsgi_errors is not None else None,
        'statementCount': 0,
        'urlFile': bare_script.url_file_relative
    }
    response = api_fn([req], script_options)

    # Error?
    api_state = script_globals[_API_GLOBAL]
    if 'error' in api_state:
        raise chisel.ActionError(api_state['error'], status=api_state.get('errorStatus'))

    # WSGI response?
    if api_wsgi:
        # Validate the WSGI response
        status, headers, content = None, None, None
        invalid_response = not isinstance(response, list) or len(response) != 3
        if not invalid_response:
            status, headers, content = response
            invalid_response = not isinstance(status, str) or not isinstance(headers, list) or not isinstance(content, str) or \
                any(not isinstance(header, list) or len(header) != 2 for header in headers) or \
                any(not isinstance(key, str) or not isinstance(value, str) for key, value in headers)
        if invalid_response:
            error_message = f'WSGI API function "{api_fn_name}" invalid return value'
            ctx.log.error(error_message)
            raise chisel.ActionError('InvalidOutput', status='500 Internal Server Error', message=error_message)

        # Add WSGI response headers
        headers.extend(api_state['headers'].items())

        # WSGI response
        ctx.start_response(status, headers)
        return [content.encode('utf-8')]

    # Add response headers
    ctx.headers.update(api_state['headers'])

    return response


# File handle logging function
def _log_filehandle(fh, text):
    print(text, file=fh)


# $function: apiHeader
# $group: API
# $doc: Add an API response header
# $arg key: The key string
# $arg value: The value string
def _api_header(args, options):
    key, value = value_args_validate(_API_HEADER_ARGS, args)
    api_state = options['globals'][_API_GLOBAL]
    api_state['headers'][key] = value

_API_HEADER_ARGS = value_args_model([
    {'name': 'key', 'type': 'string'},
    {'name': 'value', 'type': 'string'}
])


# $function: apiError
# $group: API
# $doc: Set the API error response
# $arg error: The error code string (e.g. "UnknownID")
# $arg value: The status string (default is "400 Bad Request")
def _api_error(args, options):
    error, status = value_args_validate(_API_ERROR_ARGS, args)
    api_state = options['globals'][_API_GLOBAL]
    api_state['error'] = error
    api_state['errorStatus'] = status if status else '400 Bad Request'

_API_ERROR_ARGS = value_args_model([
    {'name': 'error', 'type': 'string'},
    {'name': 'status', 'type': 'string', 'nullable': True}
])
