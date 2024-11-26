"""
Functions for parsing imports
"""

import ast
import re

from pathlib import Path, PosixPath
from typing import List, Union, Optional, Tuple
from logger import setup_logger

logger = setup_logger(__name__)

"""
Functions for include relative imported files from the file
"""


def _count_leading_dots(import_statement: Union[str, PosixPath]) -> int:
    """Count the number of leading dots in an import statement.

    :param import_statement: The import statement, e.g., "import ..b.c as d" or "from ...a.b import c".
    :type import_statement: Union[str, PosixPath]
    :returns: The number of leading dots.
    :rtype: int
    """
    match = re.match(r"(import|from)\s+(\.+)", str(import_statement))
    if match:
        return len(match.group(2))
    return 0


def _filter_class_and_functions(tree: ast.AST) -> Tuple[List[ast.AST], List[ast.AST]]:
    """
    Filters out all the classes and functions from the AST.

    :param tree: The AST of the code.
    :type tree: ast.AST
    :returns: A dictionary containing all the objects and public objects.
    :rtype: Tuple[List[ast.AST], List[ast.AST]]
    """
    # List out all the public functions and classes
    pool_objects = list(
        filter(
            lambda node: isinstance(node, (ast.FunctionDef, ast.ClassDef)), tree.body
        )
    )
    public_objects = list(
        filter(lambda node: not node.name.startswith("_"), pool_objects)
    )
    return pool_objects, public_objects


def _parse_import_module(
        import_statement: Union[ast.Import, ast.ImportFrom]
) -> Optional[str]:
    """Parse the module name from an import statement using ast.

    :param import_statement: The import statement
    :type import_statement: Union[ast.Import, ast.ImportFrom]
    :returns: The module name, e.g., "a.b.python_file_parser" or "e.f.g".
    :rtype: Optional[str]
    """
    assert isinstance(import_statement, (ast.ImportFrom, ast.Import))
    res = None
    try:
        if isinstance(import_statement, ast.ImportFrom):
            res = import_statement.module
        elif isinstance(import_statement, ast.Import):
            res = ".".join(name.name for name in import_statement.names)
    except SyntaxError as e:
        logger.error(e)
    finally:
        return res


def _import_relative_folder_modules(
        module_ast: Union[ast.ImportFrom, ast.Import],
        root_path: Optional[Union[PosixPath, str]] = None,
) -> List[Optional[ast.AST]]:
    """Import relative folder and return the functions.

    :param module_ast: AST of imported modules
    :type module_ast: Union[ast.ImportFrom, ast.Import]
    :param root_path: Root path, defaults to None
    :type root_path: Optional[Union[PosixPath, str]], optional
    :return: Lists of import functions
    :rtype: List[Optional[ast.AST]]
    """
    # Set root path
    if isinstance(root_path, str):
        root_path = Path(root_path)
    if not root_path:
        root_path = Path.cwd()
    leading_dots_cnt = _count_leading_dots(ast.unparse(module_ast))
    cleaned_path = _parse_import_module(module_ast)

    # Clean Functions
    functions_str, import_all = [], False
    functions = module_ast.names

    for f in functions:
        if isinstance(f, ast.alias):
            if f.name == '*':
                import_all = True
            functions_str.append(f.name)

    # Traverse file
    if not cleaned_path:
        return []
    for _ in range(leading_dots_cnt):
        root_path = root_path.parent
    for j in cleaned_path.split("."):
        root_path = root_path.joinpath(j)

    # Find module
    def _read_file(file_name: Union[PosixPath, str]) -> Optional[List[ast.AST]]:
        try:
            with open(file_name, "r") as file:
                code = file.read()
            tree = ast.parse(code)
            _, func = _filter_class_and_functions(tree)
            return func
        except FileNotFoundError:
            logger.warning(f'Unsourced file: {file_name}')
            return []
        except Exception as e:
            logger.error(e)
            return []

    loaded_func = _read_file(root_path.with_suffix(".py"))
    res = []
    if loaded_func:
        res = (loaded_func
               if import_all
               else [i for i in loaded_func if i.name in functions_str]
               )
    if res:
        return res
    # Retry by importing all modules
    loaded_func_all = _read_file(root_path.parent.with_suffix(".py"))
    res = (
        []
        if not loaded_func_all
        else [i for i in loaded_func_all if i.name == root_path.stem]
    )
    return res


def _parse_import_alias(
    import_statement: Union[ast.Import, ast.ImportFrom]
) -> Optional[str]:
    """Parse the alias from an import statement using ast.

    :param import_statement: The import statement.
    :type import_statement: Union[ast.Import, ast.ImportFrom]
    :returns: The alias name, if any.
    :rtype: Optional[str]
    """
    try:
        isinstance(import_statement, (ast.ImportFrom, ast.Import))
        if isinstance(import_statement, ast.ImportFrom):
            # Assuming only one alias in the statement for simplicity
            if import_statement.names:
                return import_statement.names[0].asname or import_statement.names[0].name
        elif isinstance(import_statement, ast.Import):
            # Assuming only one alias in the statement for simplicity
            if import_statement.names:
                return import_statement.names[0].asname or import_statement.names[0].name
    except SyntaxError as e:
        logger.error(e)
    return None