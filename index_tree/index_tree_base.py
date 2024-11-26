"""
This script transforms a repo into a nested tree structure, where each node represents a python file.
"""
from abc import ABC, abstractmethod
from pathlib import PosixPath, Path
from typing import Callable
from typing import Optional, Union, List, Any, Dict

from _scheme import RepoIndexNode


class RepoIndexTree(ABC):
    """
    Abstract base class for RepoTree objects.
    """

    def __init__(self, repo_path: Union[str, Path]):
        """
        Initializes a RepoTree object.

        :param repo_path: The path to the repo.
        :type repo_path: Union[str, Path]
        """
        self.repo_path = _set_repo_root(repo_path)
        self.file_tree: Optional[RepoIndexNode] = None
        self._file_object_size: int = 0
        self.repo_size: int = -1
        self._folder_count: int = -1
        self._file_count: int = -1
        self.object_table: Dict[str, List[Any]] = {}

    def _calculate_repo_size(self):
        amount = traverse_index_node(self.file_tree,
                                     node_function=_get_tree_size,
                                     collect_results=True)
        self._folder_count, self._file_count = [sum(col) for col in zip(*amount)]
        if self._folder_count >= 0 and self._file_count >= 0:
            self.repo_size = self._folder_count + self._file_count

    @abstractmethod
    def create_tree(self) -> RepoIndexNode:
        """Parses a repo into a RepoNode tree structure."""
        pass

    @abstractmethod
    def extract_node_objects(self):
        """For each nodes in repo tree, parse the file and extract the objects."""
        pass

    @abstractmethod
    def build_object_table(self):
        """Build an object table from the repo tree."""
        pass

    @abstractmethod
    def update_relative_imports(self):
        """Update the relative imports in the repo tree."""
        pass

    @abstractmethod
    def create_snippets(self):
        """Create code snippets from the repo tree."""
        pass

    def print_tree(self, node: RepoIndexNode = None, indent: int = 0):
        """
        Prints a tree-like representation of a RepoNode.

        :param node: The RepoNode to print. Defaults to the root of the tree.
        :type node: RepoNode
        :param indent: The current indentation level.
        :type indent: int
        """
        if node is None:
            node = self.file_tree

        prefix = "  " * indent
        print(f"{prefix}- {node.name}")
        if node.is_file:
            for obj_type, obj_list in node.objects.model_dump().items():
                if obj_list:
                    print(f"{prefix}  - {obj_type}:")
                    for obj in obj_list:
                        print(f"{prefix}    - {obj}")
        else:
            for child in node.children:
                self.print_tree(child, indent + 1)

from typing import Callable, List, Any

def traverse_index_node(node: 'RepoIndexNode',
                        node_function: Callable[..., Any],
                        collect_results: bool = False,
                        *args, **kwargs) -> List[Any]:
    """Traverses a RepoIndexNode tree and applies a function to each file node.

    It also optionally collects the results from the function.

    :param node: The root node of the tree to traverse.
    :type node: RepoIndexNode
    :param node_function: A function that takes a RepoIndexNode as input and
                         returns a value or None. Can accept additional
                         arguments and keyword arguments.
    :type node_function: Callable[..., Any]
    :param collect_results: If True, collects and returns the results from
                          node_function. Defaults to False.
    :type collect_results: bool
    :param args: Positional arguments to pass to node_function.
    :param kwargs: Keyword arguments to pass to node_function.

    :returns: A list of results from node_function if collect_results is True,
            otherwise an empty list.
    :rtype: List[Any]

    :Example:

    .. code-block:: python

     # Example function to extract file names with a prefix
     def get_file_name(node: RepoIndexNode, prefix: str) -> str:
       if node.is_file:
         return prefix + node.name
       return None

     # Call the traversal function to collect file names with prefix "file_"
     file_names = traverse_index_node(
         root_node, get_file_name, collect_results=True, prefix="file_"
     )
    """
    result, results = None, []
    result = node_function(node, *args, **kwargs)
    if collect_results and result is not None:
        results.append(result)
    if node.children:
        for child in node.children:
            results.extend(traverse_index_node(child,
                                               node_function,
                                               collect_results,
                                               *args, **kwargs))
    return results


def _set_repo_root(repo_path) -> Path:
    """
    Sets the repo root path.

    :param repo_path: The path to the repo.
    :type repo_path: str or Path
    :returns: The repo root path.
    :rtype: Path
    """
    if isinstance(repo_path, str):
        repo_path = Path(repo_path)

    if not isinstance(repo_path, (Path, PosixPath)):
        raise TypeError("repo_path must be a string or Path/PosixPath object")
    return repo_path


def _get_tree_size(node: RepoIndexNode) -> List[int]:
    """_get_tree_size

    :param node: root node of the tree
    :type node: RepoIndexNode
    :return: dir_count, file_count
    :rtype: List[int]
    """
    if node.is_file:
        return [0, 1]
    else:
        return [1, 0]
