from pathlib import Path

from index_tree.index_tree_base import RepoIndexTree, traverse_index_node
from parser.python.build_object_table import file_objects_2_list
from parser.python.extract_nodes import extract_node_objects
from parser.python.update_relative_imports import _import_relative_folder_modules
from _scheme import RepoIndexNode


class PythonRepoIndexTree(RepoIndexTree):
    """
    RepoTree for Python repositories.
    """

    def create_tree(self):
        """
        Parses a Python repo into a RepoIndexNode tree structure.
        """
        self.file_tree = RepoIndexNode(name=self.repo_path.name, path=str(self.repo_path))
        _build_python_index_tree(self.file_tree)

    def extract_node_objects(self):
        """
        For each node in the repo tree, parse the file and extract the objects.
        """
        traverse_index_node(self.file_tree, node_function=extract_node_objects)

    def build_object_table(self):
        """
        Build an object table from the repo tree.
        """
        self._update_node_items(self.file_tree)

    def _update_node_items(self, node: RepoIndexNode):
        """
        Update the objects in a node.

        :param node: The node to update.
        :type node: RepoIndexNode
        """
        if node.is_file:
            obj_list = file_objects_2_list(node.objects)
            self.object_table[node.path] = obj_list
        for child in node.children:
            self._update_node_items(child)

    def update_relative_imports(self):
        """
        Update the relative imports in the repo tree.
        Steps:
        1. For all imports, decide if it is a relative import.
        2, Search for the relative files of the import from object table.
        3. Update links of the relative imports to the node and object table.
        """
        traverse_index_node(self.file_tree,
                            node_function=_import_relative_folder_modules,
                            object_table=self.object_table,
                            root_path=self.repo_path)


    def create_snippets(self):
        """
        Create code snippets from the repo tree.
        """
        raise NotImplementedError("PythonRepoTree.create_snippets is not yet implemented.")

    def parse_repo(self):
        """
        Parses a Python repo into a RepoNode tree structure.
        """
        self.create_tree()
        self._calculate_repo_size()
        self.print_tree()
        self.extract_node_objects()
        self.build_object_table()
        self.update_relative_imports()
        # self.create_snippets()


def _build_python_index_tree(node: RepoIndexNode):
    """
    Recursively builds child nodes.

    :param node: The current RepoIndexNode object.
    :type node: RepoIndexNode
    """
    path = Path(node.path)
    if not path.exists():
        raise FileNotFoundError(f"Path {path} does not exist.")

    for item in path.iterdir():
        if item.is_dir() and not item.stem.startswith('__'):
            child_node = RepoIndexNode(name=item.name, path=str(item))
            node.children.append(child_node)
            _build_python_index_tree(child_node)
        elif item.is_file() and not item.stem.startswith('__'):
            if item.suffix == ".py":
                child_node = RepoIndexNode(name=item.name, path=str(item), is_file=True)
                node.children.append(child_node)
            elif item.suffix == ".ipynb":
                print(f'Not Implemented parsing notebook files yet, skipping file: {item.name}')
                # TODO: Implement ipynb file parsing
