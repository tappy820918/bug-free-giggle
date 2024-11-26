from index_tree.index_tree_base import RepoIndexTree
from index_tree.python.index_tree_builder import PythonRepoIndexTree

repo_types = {
    "python": PythonRepoIndexTree
}

class RepoTreeIndexFactory:
    """
    Factory class for creating RepoTree objects.
    """
    @staticmethod
    def create_repo_tree(repo_path: str, repo_type: str = 'python'):
        try:
            return repo_types[repo_type](repo_path)
        except KeyError:
            raise ValueError(f"Invalid repo_type: {repo_type}")
