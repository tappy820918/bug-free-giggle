"""
This script processes a python repo into a list of ast objects, focusing on public classes and functions,
along with their associated imports and helper functions.

The script uses the `tree_sitter` library for parsing the Python code and `ast` module for analyzing the
Abstract Syntax Tree (AST). It identifies public classes and functions, traces their dependencies within
the file, and generates self-contained code snippets.

Process:
1. Load a repository and identifies all python files.
2. Create a tree structure for each python file to identifies linkage between files.
"""
import ast
import click
import os
import re
import sys
import tree_sitter_python

from tree_sitter import Language, Parser
from typing import List, Union, Optional, Dict

from parser.python._commom_ds_packages import _load_common_ds_pkg
from parser.python._trace_import import (
    _parse_import_module,
    _import_relative_folder_modules,
    _filter_class_and_functions,
)

from _scheme import PythonFileObjects

from logger import setup_logger

logger = setup_logger(__name__)

COMMON_DS_PACKAGES = _load_common_ds_pkg()


PY_LANGUAGE = Language(tree_sitter_python.language())
parser = Parser(PY_LANGUAGE)


def _not_stdlib_module(module_name: Union[ast.Import, ast.ImportFrom]) -> bool:
    """
    Checks if a module name belongs to the Python standard library.

    :param module_name: The name of the module to check.
    :type module_name: Union[ast.Import, ast.ImportFrom]
    :returns: True if the module is not in the standard library, False otherwise.
    :rtype: bool
    """
    try:
        module_text = _extract_import(module_name)
        __import__(module_text)
        return module_text not in sys.stdlib_module_names
    except ModuleNotFoundError:
        return True
    except Exception as e:
        logger.error(f"Error in : {e}")
        return True


def _extract_import(module_name: Union[ast.Import, ast.ImportFrom]) -> str:
    """
    Extracts the module name from an import statement.

    :param module_name: The name of the module to extract.
    :type module_name: Union[ast.Import, ast.ImportFrom]
    :returns: The extracted module name.
    :rtype: str
    """
    text = ""
    if isinstance(module_name, ast.Import):
        text = module_name.names[0].name
    elif isinstance(module_name, ast.ImportFrom):
        text = module_name.module

    pattern = r"""
        (?:  # Non-capturing group for optional leading dots
        \.+  # Match one or more dots
        )?
        ([a-zA-Z_]\w*)  # Capture the module name (alphanumeric and underscore)
        (?:  # Non-capturing group for the rest of the import
        \.  # Match a dot
        \w+  # Match one or more word characters
        )*
    """
    matches = re.search(pattern, text, re.VERBOSE)
    return "" if not matches else matches.group(1)


def _not_common_ds_pkg_module(
    module_name: Union[ast.Import, ast.ImportFrom]
) -> bool:
    """
    Checks if a module name belongs to the common data science packages.

    :param module_name: The name of the module to check.
    :type module_name: Union[ast.Import, ast.ImportFrom]
    :returns: True if the module is not in the common data science packages, False otherwise.
    :rtype: bool
    """
    module_name_str = _extract_import(module_name)
    return module_name_str not in COMMON_DS_PACKAGES


def _filter_imports(tree: ast.AST) -> List[Union[ast.Import, ast.ImportFrom]]:
    """
    Filter out the imports.

    :param tree: The AST of the file.
    :type tree: ast.AST
    :returns: A list of imports.
    :rtype: List[ast.AST]
    """
    type_ = (ast.Import, ast.ImportFrom)
    import_obj = filter(lambda node: isinstance(node, type_), tree.body)
    non_std_import_obj = filter(_not_stdlib_module, import_obj)
    non_common_ds_obj = filter(_not_common_ds_pkg_module, non_std_import_obj)
    return list(non_common_ds_obj)


"""
Functions for parsing code objects (classes & functions)
"""


def _load_and_check_file(file_path: str) -> ast.AST:
    """
    Load and check the file.

    :param file_path: The path to the file.
    :type file_path: str
    :returns: The AST of the file.
    :rtype: ast.AST
    """
    if not os.path.exists(file_path):
        raise ValueError("File does not exist.")
    if not file_path.endswith(".py"):
        raise ValueError("File is not a python file.")
    # Check if it's compilable
    try:
        with open(file_path, "r") as f:
            code = f.read()
        tree = ast.parse(code)
    except Exception as e:
        raise ValueError(f"File is not compilable. with error {e}")
    return tree


def _find_used_functions(pool_obj: List[ast.AST],
                         public_obj: List[ast.AST],
                         import_alias: Dict[str, str],
                         ) -> List[List[ast.AST]]:
    """
    Iterate over the public objects and identifies
    functions used within public objects (functions and classes).

    :param pool_obj: A list of all objects in the file.
    :type pool_obj: List[ast.AST]
    :param public_obj: A list of public objects.
    :type public_obj: List[ast.AST]
    :param import_alias: A list of import alias.
    :type import_alias:  List[List[str, Union[ast.Import, ast.ImportFrom]]]
    :returns: A list of lists of functions used within each public object.
    :rtype: List[List[ast.AST]]
    """
    used_functions = []
    for node in public_obj:
        node_str = ast.unparse(node)
        # Replace code string with alias
        for alias, alias_str in import_alias.items():
            node_str = node_str.replace(alias, alias_str)
        used_function = []
        for f in pool_obj:
            try:
                if (
                    hasattr(f, "name")
                    and f.name in node_str
                    and f.name != node.name
                ):
                    used_function.append(f)
            except Exception as e:
                pass
        used_functions.append(used_function)
    return used_functions


def _join_code_snippets(public_objects, used_functions) -> List[str]:
    res = []
    for i, j in zip(public_objects, used_functions):
        res.append(ast.unparse(j) + "\n\n" + ast.unparse(i))
    return res


def _generate_python_snippets(file_path: str, root_path: str) -> List[dict]:
    """
    Create python code snippets from a python file.

    :param file_path: The path to the file.
    :type file_path: str
    
    :returns: A list of code snippets.
    :rtype: List[dict]:
    """
    print(f'file_path: {file_path}')
    tree = _load_and_check_file(file_path)
    imports = _filter_imports(tree)
    import_alias = [[_parse_import_module(i), i] for i in imports]
    import_alias_dict = {str(i[0]): str(i[0]) + ' ' + ast.unparse(i[1]) for i in import_alias if i[0]}
    # Trace code and include import functions in the snippet
    additional_objects = [_import_relative_folder_modules(i, root_path) for i in imports]
    additional_objects = [item for sublist in additional_objects for item in sublist]
    pool_objects, public_objects = _filter_class_and_functions(tree)

    used_functions = _find_used_functions(pool_obj=pool_objects,
                                          public_obj=public_objects + additional_objects,
                                          import_alias=import_alias_dict)
    joined_snippets = _join_code_snippets(public_objects, used_functions)
    snippet_result = [make_snippet_result(i) for i in joined_snippets]
    return [i.model_dump() for i in snippet_result]


def parse_python_file(file_path: str, result_path: str, repo_root: str):
    """
    Chunks a notebook_file into smaller code snippets.

    :param file_path: The path to the python file.
    :type file_path: str
    :param result_path: The path to the result file.
    :type result_path: str
    :param repo_root: The path to the root file.
    :type repo_root: str
    """
    code_snippets = _generate_python_snippets(file_path, repo_root)
    logger.info(f"Total {len(code_snippets)} snippet generated.")
    save_to_jsonl(code_snippets, result_path)
