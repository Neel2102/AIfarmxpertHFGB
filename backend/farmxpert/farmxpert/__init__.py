import os
import pkgutil

__path__ = pkgutil.extend_path(__path__, __name__)

# Allow imports like `farmxpert.config.*` while the actual modules live at repo root (`/app/config`, `/app/interfaces`, etc.)
_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))
if _repo_root not in __path__:
    __path__.append(_repo_root)
