#!/usr/bin/env python3
from py5canvas import canvas, run_sketch
from py5canvas import globals as glob
from contextlib import redirect_stdout
import inspect, importlib, textwrap, re
from importlib import reload
import ast
reload(canvas)
reload(run_sketch)
reload(glob)

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


def doc_globals(items):
    for name, info in items:
        if '__' in name or name[0] == '_':
            continue
        if not 'doc' in info:
            continue
        if info['args'] is not None:
            print('### `%s(%s)`'%(name, info['args']))
        else:
            print('### `%s`'%name)
        print('%s\n'%info['doc'])

# For globals
def _attr_to_dotted(node):
    """Return dotted path for Name/Attribute (e.g., np.random.uniform)."""
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
        return ".".join(reversed(parts))
    return None

def _get_source_segment(source, node):
    try:
        return ast.get_source_segment(source, node)
    except Exception:
        return None

def _safe_signature(obj):
    try:
        return str(inspect.signature(obj))
    except Exception:
        return "(...)"

def _short_doc(obj, width=100):
    doc = inspect.getdoc(obj) or ""
    if '----' not in doc:
       return doc
    lines = doc.split('\n\n')[1:3]
    res = ''
    for line in lines:
        if line.startswith('---'):
            break
        if line.startswith('Parameters'):
            break
        res += line + '\n'
    return res

def _load_module(file_path):
    spec = importlib.util.spec_from_file_location("doc_target", file_path)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod

def parse_module_symbols(file_path, mod=None, resolve_runtime=False):
    """
    Parse top-level assignments and function defs for selected names.
    Returns: { name: { 'kind', 'expr', 'alias_to', 'args', 'doc', 'sig', 'value_repr' } }
    - kind: 'function' | 'alias' | 'constant'
    - expr: source expression string (if available)
    - alias_to: dotted path if right-hand side looks like an alias
    - args: function arg list (from AST) for defs in this file
    - sig/doc/value_repr: filled if resolve_runtime=True
    """
    with open(file_path, "r", encoding="utf-8") as f:
        source = f.read()
    tree = ast.parse(source)

    out = {}

    # Pass 1: functions and assignments
    for node in tree.body:
        # Top-level function defs
        if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
            args = [a.arg for a in node.args.args]
            # strip typical 'self' for parity with your class parser
            if args and args[0] == "self":
                args = args[1:]
            # include *args
            if node.args.vararg:
                args.append('...')
            args = ','.join(args)
            out[node.name] = {
                "kind": "function",
                "expr": None,
                "alias_to": None,
                "args": args,
                "doc": ast.get_docstring(node) or "",
                "sig": None,
                "value_repr": None,
            }

        # Top-level assignments: NAME = <expr>
        elif isinstance(node, ast.Assign):
            targets = [t for t in node.targets if isinstance(t, ast.Name)]
            for t in targets:
                name = t.id
                if name.startswith('_'):
                    continue
                expr_src = _get_source_segment(source, node.value)
                dotted = None
                if isinstance(node.value, (ast.Name, ast.Attribute)):
                    dotted = _attr_to_dotted(node.value)

                out[name] = {
                    "kind": "alias" if dotted else "constant",
                    "expr": expr_src,
                    "alias_to": dotted,
                    "args": None,
                    "doc": "",
                    "sig": None,
                    "value_repr": None,
                }

        # Annotated assignment: NAME: type = <expr>
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            name = node.target.id
            if name.startswith('_'):
                continue
            expr_src = _get_source_segment(source, node.value) if node.value else None
            dotted = None
            if isinstance(node.value, (ast.Name, ast.Attribute)):
                dotted = _attr_to_dotted(node.value)
            out[name] = {
                "kind": "alias" if dotted else "constant",
                "expr": expr_src,
                "alias_to": dotted,
                "args": None,
                "doc": "",
                "sig": None,
                "value_repr": None,
            }

    def args_of(obj):
        import re
        try:
            sig = str(inspect.signature(obj))
        except Exception as e:
            doc = obj.__doc__
            sig = doc.split('\n\n')[0]
        s = sig.strip()
        # find first '(' and last ')'
        m = re.search(r'\((.*)\)', s)
        if m:
            s = m.group(1).strip()
            s = s.split(', /,')[0]

        return s

    # Optional runtime enrichment: signatures, docstrings, reprs
    if resolve_runtime and mod is not None:
        try:
            ns = vars(mod)
            for name in list(out.keys()):

                if name not in ns:
                    continue
                obj = ns[name]
                if callable(obj):
                    out[name]["kind"] = 'function' #_safe_signature(obj)
                    if not out[name]['args']:
                        out[name]["args"] = args_of(obj)
                    out[name]["sig"] = _safe_signature(obj)
                    out[name]["doc"] = out[name]["doc"] or _short_doc(obj)
                else:
                    try:
                        rep = repr(obj)
                        if len(rep) > 200:
                            rep = rep[:197] + "…"
                        out[name]["value_repr"] = rep
                        out[name]["doc"] = f'`{rep}`'
                    except Exception:
                        out[name]["value_repr"] = "<unrepresentable>"
        except Exception as e:
            # Keep AST-only data if import fails
            out["_resolution_error"] = {"error": f"resolve_runtime failed: {e!r}"}

    return out


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

        print('\n# Globals and constants')
        symbols = parse_module_symbols(glob.__file__, glob, resolve_runtime=True)
        constants = []
        funcs = []

        for name, data in symbols.items():
            if 'error' in data:
                #print('Could not resolve', name)
                continue
            #print(name, data)

            if data['kind'] == 'alias' or data['kind'] == 'constant':
                constants.append((name, data))
            else:
                funcs.append((name, data))
        print('\n## Functions')
        doc_globals(funcs)
        print('\n## Constants')
        doc_globals(constants)
