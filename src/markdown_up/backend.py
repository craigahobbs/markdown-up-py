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
BACKEND_TYPES = schema_markdown.parse_schema_markdown('''\
# The MarkdownUp backend API configuration file schemax
struct BackendConfig

    # The list of schema markdown files
    string[] schemaFiles

    # The list of APIs
    BackendAPI[] apis


# The backend API model
struct BackendAPI

    # The API name
    string name

    # The BareScript file containing the API function
    string script
''')


def load_backend_requests(config_path):
    requests = []

    # Read the "markdown-up.json" file - do nothing if it doesn't exist
    if not os.path.isfile(config_path):
        return requests
    with open(config_path, 'r', encoding='utf-8') as backend_file:
        backend = schema_markdown.validate_type(BACKEND_TYPES, 'BackendConfig', json.load(backend_file))

    # Load the schema markdown files
    types = {}
    for smd_path in backend['schemaFiles']:
        with open(smd_path, 'r', encoding='utf-8') as smd_file:
            schema_markdown.parse_schema_markdown(smd_file, types, filename=smd_path, validate=False)
    schema_markdown.validate_type_model(types)

    # Add an action for each backend API
    for api in backend['apis']:

        # Parse the script
        with open(api['script'], 'r', encoding='utf-8') as script_file:
            script = bare_script.parse_script(script_file)

        # Execute the script
        script_globals = {
            _BACKEND_GLOBAL: {'headers': {}},
            'backendAddHeader': _backend_add_header
        }
        script_options = {
            'fetchFn': bare_script.fetch_read_write,
            'globals': script_globals,
            'logFn': bare_script.log_stdout,
            'urlFile': bare_script.url_file_relative,
            'systemPrefix': 'https://craigahobbs.github.io/markdown-up/include/'
        }
        bare_script.execute_script(script, script_options)

        # Add the API action
        script_fn = script_globals[api['name']]
        action_fn = partial(_bare_script_action_fn, script_fn, script_options)
        requests.append(chisel.Action(action_fn, name=api['name'], types=types))

    return requests


# Special backend global variables
_BACKEND_GLOBAL = '__markdown_up__'


# Action function wrapper for a MarkdownUp backend API function
def _bare_script_action_fn(script_fn, script_options, ctx, req):
    response = script_fn([req], script_options)

    # Add response headers, if any
    backend_state = script_options['globals'][_BACKEND_GLOBAL]
    ctx.headers.update(backend_state['headers'])

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
