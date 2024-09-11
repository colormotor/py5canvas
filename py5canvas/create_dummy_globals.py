#!/usr/bin/env python3
''' Creates a module file `dummy_globals.py` that is used to trick a Python linter
    into knowing the canvas globals that are injected
'''
if __name__ == '__main__':
    import ast

    def parse_class_methods_with_docs(file_path, class_name):
        with open(file_path, "r") as f:
            tree = ast.parse(f.read())

        method_info = []

        # Find the class in the file
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                for n in node.body:
                    if isinstance(n, ast.FunctionDef) and '__' not in n.name and n.name[0] != '_':
                        # Get method name
                        method_name = n.name
                        # Get docstring (if exists)
                        docstring = ast.get_docstring(n) or ""
                        method_info.append((method_name, docstring))

        return method_info

    method_info = parse_class_methods_with_docs('canvas.py', 'Canvas')

    with open('dummy_globals.py', 'w') as f:
        f.write(f"# Autogenerated canvas methods as globals to trick the linter\n\n")
        for method_name, docstring in method_info:
            f.write(f"def {method_name}():\n")
            if docstring:
                f.write(f'    """{docstring} """\n')
            f.write(f"    pass  # Dummy method for linter\n\n")
