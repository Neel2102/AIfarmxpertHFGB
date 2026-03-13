"""
FarmXpert package initializer
This allows the root of the backend files to be treated as a single package.
"""
import os
import sys

# Ensure the parent directory is in sys.path
_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)
