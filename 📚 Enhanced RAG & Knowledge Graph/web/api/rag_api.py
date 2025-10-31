"""Shim loader for web.api.rag_api -> loads rag-api.py (filename with hyphen)."""

import importlib.util
import os

_here = os.path.dirname(__file__)
_source = os.path.join(_here, "rag-api.py")

if os.path.exists(_source):
    spec = importlib.util.spec_from_file_location("web.api._rag_api_impl", _source)
    _mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(_mod)
    router = getattr(_mod, "router", None)
    __all__ = ["router"]
else:
    router = None
    __all__ = ["router"]
