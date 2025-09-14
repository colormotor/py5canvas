#!/usr/bin/env python3
from py5canvas import canvas, run_sketch
from importlib import reload
import ast
reload(canvas)
reload(run_sketch)
from IPython.display import publish_display_data, clear_output


def parse_class_with_docs_and_args(file_path, class_name):
    with open(file_path, "r") as f:
        tree = ast.parse(f.read())

    class_info = {"methods": []}

    # Find the class in the file
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            # Get class docstring
            class_info["docstring"] = ast.get_docstring(node) or "No class docstring available"

            # Process methods
            for n in node.body:
                if isinstance(n, ast.FunctionDef):
                    # Get method name
                    method_name = n.name

                    # Get method arguments (skip 'self')
                    args = [arg.arg for arg in n.args.args if arg.arg != 'self']
                    is_property = any(
                        isinstance(decorator, ast.Name) and decorator.id == 'property'
                        for decorator in n.decorator_list
                    )
                    if n.args.vararg:
                        args.append('*' + n.args.vararg.arg)
                    # Get docstring (if exists)
                    docstring = ast.get_docstring(n)
                    if docstring:
                        class_info["methods"].append((method_name, args, is_property, docstring))

    return class_info

def doc_methods(methods):
    for name, args, is_property, doc in methods:
        if '__' in name or name[0] == '_':
            continue
        if not doc:
            continue
        if is_property:
            print('### `%s`'%name)
        else:
            if args:
                print('### `%s(...)`'%name)
            else:
                print('### `%s()`'%name)
        print('%s\n'%doc)

from contextlib import redirect_stdout

with open('README.md', 'w') as f:
    with redirect_stdout(f):
        info = parse_class_with_docs_and_args(canvas.__file__, 'Canvas')
        print('\n# Canvas API')
        print('%s\n'%info['docstring'])
        properties = [m for m in info['methods'] if m[2]]
        methods = [m for m in info['methods'] if not m[2]]
        print('## Properties')
        doc_methods(properties)
        print('## Methods')
        doc_methods(methods)

        info = parse_class_with_docs_and_args(run_sketch.__file__, 'Sketch')
        print('\n# Interactive sketches')
        print('%s\n'%info['docstring'])
        properties = [m for m in info['methods'] if m[2]]
        methods = [m for m in info['methods'] if not m[2]]

        print('## Properties\n')
        doc_methods(properties)
        print('### `mouse_pos`')
        print('The current position of the mouse as an array')
        print('\n## Methods\n')
        doc_methods(methods)
