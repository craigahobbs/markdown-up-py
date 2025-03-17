# Licensed under the MIT License
# https://github.com/craigahobbs/markdown-up-py/blob/main/LICENSE

"""
The MarkdownUp launcher back-end API support
"""

from functools import partial
import json
import os

import bare_script
from bare_script.value import value_args_model, value_args_validate
import chisel
import schema_markdown


# The backend configuration schema
CONFIG_TYPES = schema_markdown.parse_schema_markdown('''\
# The MarkdownUp backend API configuration file
struct BackendConfig

    # The schema markdown files
    string[len > 0] schemas

    # The BareScript API files
    BackendScript[len > 0] scripts


# A backend API script
struct BackendScript

    # The BareScript file
    string script

    # The APIs
    BackendAPI[len > 0] apis


# A backend API
struct BackendAPI

    # The schema type name
    string name

    # The script function name. If unspecified, use the schema type name.
    optional string function
''')


# Load the MarkdownUp backend config requests
def load_backend_requests(config_path, debug=False):
    requests = []

    # Read the "markdown-up.json" file - do nothing if it doesn't exist
    if not os.path.isfile(config_path):
        return requests
    with open(config_path, 'r', encoding='utf-8') as config_file:
        config = schema_markdown.validate_type(CONFIG_TYPES, 'BackendConfig', json.load(config_file))

    # Load the schema markdown files
    types = {}
    for smd_path in config['schemas']:
        with open(smd_path, 'r', encoding='utf-8') as smd_file:
            schema_markdown.parse_schema_markdown(smd_file, types, filename=smd_path, validate=False)
    schema_markdown.validate_type_model(types)

    # Load the BareScript API files
    for backend_script in config['scripts']:

        # Parse the script
        with open(backend_script['script'], 'r', encoding='utf-8') as script_file:
            api_script = bare_script.parse_script(script_file)

        # Execute the script
        script_globals = {
            _BACKEND_GLOBAL: {'headers': {}},
            'backendAddHeader': _backend_add_header,
            'backendSetError': _backend_set_error
        }
        script_options = {
            'debug': debug,
            'fetchFn': bare_script.fetch_read_write,
            'globals': script_globals,
            'logFn': bare_script.log_stdout,
            'urlFile': bare_script.url_file_relative
        }
        bare_script.execute_script(api_script, script_options)

        # Create the backend API requests
        for backend_api in backend_script['apis']:
            api_name = backend_api['name']
            api_fn = backend_api.get('function', api_name)

            # Add the API action
            script_fn = script_globals[api_fn]
            action_fn = partial(_bare_script_action_fn, script_fn, script_options)
            requests.append(chisel.Action(action_fn, name=api_name, types=types))

    return requests


# Special backend global variables
_BACKEND_GLOBAL = '__markdown_up__'


# Action function wrapper for a MarkdownUp backend API function
def _bare_script_action_fn(script_fn, script_options, ctx, req):
    response = script_fn([req], script_options)

    # Add response headers, if any
    backend_state = script_options['globals'][_BACKEND_GLOBAL]
    ctx.headers.update(backend_state['headers'])

    # Error?
    if 'error' in backend_state:
        raise chisel.ActionError(backend_state['error'], status=backend_state.get('errorStatus'))

    return response


# $function: backendAddHeader
# $group: Backend
# $doc: Add a backend API response header
# $arg key: The key string
# $arg value: The value string
def _backend_add_header(args, options):
    key, value = value_args_validate(_BACKEND_ADD_HEADER_ARGS, args)
    backend_state = options['globals'][_BACKEND_GLOBAL]
    backend_state['headers'][key] = value

_BACKEND_ADD_HEADER_ARGS = value_args_model([
    {'name': 'key', 'type': 'string'},
    {'name': 'value', 'type': 'string'}
])


# $function: backendSetError
# $group: Backend
# $doc: Set the backend API error response
# $arg error: The error code string (e.g. "UnknownID")
# $arg value: The status string (default is "400 Bad Request")
def _backend_set_error(args, options):
    error, status = value_args_validate(_BACKEND_SET_ERROR_ARGS, args)
    backend_state = options['globals'][_BACKEND_GLOBAL]
    backend_state['error'] = error
    backend_state['errorStatus'] = status if status else '400 Bad Request'

_BACKEND_SET_ERROR_ARGS = value_args_model([
    {'name': 'error', 'type': 'string'},
    {'name': 'status', 'type': 'string', 'nullable': True}
])
