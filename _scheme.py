from typing import List, Any, Dict, Union
import ast

from pydantic import BaseModel, Field, field_validator


class FileObjects(BaseModel):
    """
    :param import_: Import statements.
    :type import_: List[Any]
    :param function_: Function definitions.
    :type function_: List[Any]
    :param variable_: Variable definitions.
    :type variable_: List[Any]
    :param class_: Class definitions.
    :type class_: List[Any]
    """
    import_: List[Any] = Field(default_factory=list, description="Import statements")
    function_: List[Any] = Field(default_factory=list, description="Function definitions")
    variable_: List[Any] = Field(default_factory=list, description="Variable definitions")
    class_: List[Any] = Field(default_factory=list, description="Class definitions")


class PythonFileObjects(FileObjects):
    """
    :param import_: Import statements.
    :type import_: List[Any]
    :param function_: Function definitions.
    :type function_: List[Any]
    :param variable_: Variable definitions.
    :type variable_: List[Any]
    :param class_: Class definitions.
    :type class_: List[Any]
    """
    import_: List[Union[ast.Import, ast.ImportFrom]] = Field(default_factory=list, description="Python Import statements")
    function_: List[ast.FunctionDef] = Field(default_factory=list, description="Python Function definitions")
    variable_: List[ast.Assign] = Field(default_factory=list, description="Python Variable definitions")
    class_: List[ast.ClassDef] = Field(default_factory=list, description="Python Class definitions")
    model_config = {"arbitrary_types_allowed": True}


class Snippet(BaseModel):
    target_object: Any = Field(..., description="The target function name")
    imported_objects: Any = Field(..., description="The imported function name")


class RepoIndexNode(BaseModel):
    """Represents a node in a repo index tree.
    :param name: Filename or directory name.
    :type name: str
    :param path: Full path to the file or directory.
    :type path: str
    :param is_file: Whether the node represents a file.
    :type is_file: bool
    :param children: List of child nodes.
    :type children: List[RepoNode]
    :param objects: Python objects in the file.
    :type objects: FileObjects
    """
    name: str = Field(..., description="Filename or directory name")
    path: str = Field(..., description="Full path to the file or directory")
    is_file: bool = Field(default=False, description="Whether the node represents a file")
    has_link_relative_imports: bool = Field(default=False, description="Whether the relative imports have been linked")
    has_join_code_snippets: bool = Field(default=False, description="Whether the code snippets have been joined")

    children: List["RepoIndexNode"] = Field(default_factory=list, description="List of child nodes")
    objects: Union[FileObjects, PythonFileObjects] = Field(default_factory=FileObjects, description="Objects in the file")
    relative_imports: List[Union[ast.FunctionDef, ast.Assign, ast.ClassDef]] = Field(default_factory=list, description="Relative imports")
    snippet: List[Dict[str, Dict[str, Any]]] = Field(default_factory=list, description="Code snippets")

    @field_validator("children")
    def check_file_no_children(cls, v, values):
        """
        Validates that file nodes do not have children.
        """
        if values["is_file"] and v:
            raise ValueError("Files cannot have children.")
        return v

    @field_validator("objects")
    def check_dir_no_objects(cls, v, values):
        """
        Validates that directory nodes do not have Python objects.
        """
        if not values["is_file"] and any(v.model_dump().values()):
            raise ValueError("Directories cannot have FileObjects.")
        return v

    @field_validator("objects")
    def check_objects_type(cls, v):
        """
        Validates that objects is an instance of a class inherited from FileObjects.
        """
        if not isinstance(v, FileObjects):
            raise TypeError("objects must be an instance of a class inherited from FileObjects")
        return v

    @field_validator("snippet")
    def check_snippet_structure(cls, v):
        """
        Validates that the snippet has the correct structure.
        """
        for item in v:
            if not (
                    isinstance(item, dict)
                    and len(item) == 1
                    and isinstance(list(item.keys())[0], str)
                    and isinstance(list(item.values())[0], dict)
                    and "target_function" in list(item.values())[0]
                    and "imported_function" in list(item.values())[0]
            ):
                raise ValueError(
                    "Each item in snippet must be a dictionary with one key (a string) "
                    "and a value that is a dictionary containing 'target_func' and 'imported_funct'"
                )
        return v

    @property
    def object_size(self) -> int:
        return len(self.objects.model_dump().values())

    model_config = {"arbitrary_types_allowed": True}
