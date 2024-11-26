from _scheme import RepoIndexNode
from typing import List, Dict, Any, Union, Optional
from index_tree.build_repo_index_tree import RepoTreeIndexFactory

root = RepoTreeIndexFactory.create_repo_tree('/Users/tappy/Desktop/RepoParser/snippet_generator/python_repo')
root.parse_repo()