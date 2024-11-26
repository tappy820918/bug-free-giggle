import ast

from _scheme import PythonFileObjects, RepoIndexNode
from parser.python._parser_utils import _load_and_check_file, _not_stdlib_module, _not_common_ds_pkg_module

def extract_node_objects(node: RepoIndexNode):
    """extract_node_objects

    :param node: root node of the tree
    :type node: RepoIndexNode
    """
    if node.is_file:
        node.objects = _extract_file_modules(node.path)

def _extract_file_modules(file_path: str) -> PythonFileObjects:
    """
    For each nodes in repo tree, parse the file and extract the objects.
    """
    tree = _load_and_check_file(file_path)
    i, f, v, c = [], [], [], []
    for module in tree.body:
        if isinstance(module, (ast.Import, ast.ImportFrom)):
            i.append(module)
        elif isinstance(module, ast.FunctionDef):
            f.append(module)
        elif isinstance(module, ast.Assign):
            v.append(module)
        elif isinstance(module, ast.ClassDef):
            c.append(module)

    i = filter(_not_stdlib_module, i)
    i = filter(_not_common_ds_pkg_module, i)
    i_clean = list(i)

    return PythonFileObjects(import_=i_clean, function_=f, variable_=v, class_=c)


