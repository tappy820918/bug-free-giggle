import ast
from typing import Tuple, List

from _scheme import PythonFileObjects, RepoIndexNode
from parser.python._parser_utils import _load_and_check_file, _not_stdlib_module, _not_common_ds_pkg_module


def file_objects_2_list(obj: PythonFileObjects) -> list:
    data = []
    for import_ in obj.import_:
        data.append(["import", import_.names[0].name, import_])
    for function_ in obj.function_:
        data.append(["function", function_.name, function_])
    for variable_ in obj.variable_:
        data.append(["variable", variable_.targets[0].id, variable_])
    for class_ in obj.class_:
        data.append(["class", class_.name, class_])
    return data
