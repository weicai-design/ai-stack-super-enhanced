"""Shim loader for web.api.file_api -> loads file-api.py (filename with hyphen).
This keeps original files untouched and provides a valid module name for imports.
"""

import importlib.util
import os

_here = os.path.dirname(__file__)
_source = os.path.join(_here, "file-api.py")

if os.path.exists(_source):
    spec = importlib.util.spec_from_file_location("web.api._file_api_impl", _source)
    _mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_mod)
    # re-export commonly expected symbols
    router = getattr(_mod, "router", None)
    __all__ = ["router"]
else:
    # fallback: provide empty router placeholder
    router = None
    __all__ = ["router"]
