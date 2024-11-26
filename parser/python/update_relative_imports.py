import ast
import re
from functools import reduce
from pathlib import PosixPath, Path
from typing import Dict, List, Optional, Union

from _scheme import RepoIndexNode
from parser.python._trace_import import _count_leading_dots, _parse_import_module


def strip_import_alias(import_statement):
    """
    Extracts the module name from an import statement of the form "module as alias".

    Args:
      import_statement: The import statement string.

    Returns:
      The module name as a string, or None if no match is found.
    """
    match = re.match(r"(\w+)\s+as\s+\w+", import_statement)
    if match:
        return match.group(1)
    return import_statement


def _import_relative_folder_modules(
        node: RepoIndexNode,
        object_table: Dict[str, List[str]],
        root_path: Optional[Union[PosixPath, str]] = None
) -> None:
    relative_imports = []
    for import_statement in node.objects.import_:
        # 1. Process paths
        leading_dots_cnt = _count_leading_dots(ast.unparse(import_statement))
        cleaned_path = _parse_import_module(import_statement)
        if not cleaned_path:
            continue
        cur_absolute_path = Path(node.path).parent

        # 2. Create destination file path in the repository,
        #     considering root or current file as working directory
        for _ in range(leading_dots_cnt):
            root_path = root_path.parent
            cur_absolute_path = cur_absolute_path.parent
        for j in cleaned_path.split("."):
            root_path = root_path.joinpath(j)
            cur_absolute_path = cur_absolute_path.joinpath(j)

        # 3. Clean Functions
        functions_str, import_all = [], False
        functions = import_statement.names
        for f in functions:
            if isinstance(f, ast.alias):
                if f.name == '*':
                    import_all = True
                functions_str.append(strip_import_alias(f.name))

        # 4. Traverse file
        ## root_path
        target_file_modules = object_table.get(root_path.with_suffix(".py").__str__(), [['import', '', '']])
        target_file_modules = filter(lambda x: x[0] not in 'import', target_file_modules)
        if not import_all:
            target_file_modules = filter(lambda x: x[1] in functions_str, target_file_modules)
        target_file_modules = list(target_file_modules)
        ## cur_absolute_path
        if not target_file_modules:
            target_file_modules = object_table.get(cur_absolute_path.with_suffix(".py").__str__(), [['import', '', '']])
            target_file_modules = filter(lambda x: x[0] not in 'import', target_file_modules)
            if not import_all:
                target_file_modules = filter(lambda x: x[1] in functions_str, target_file_modules)
            target_file_modules = list(target_file_modules)
        relative_imports.append(target_file_modules)
    if relative_imports:
        node.relative_imports = reduce(lambda x, y: x + y, relative_imports)
    node.has_link_relative_imports = True
