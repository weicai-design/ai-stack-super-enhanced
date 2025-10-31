"""Compatibility shim to load hyphenated API files with correct package context.
This module is used at runtime to ensure `web.api` package can import routers when
uvicorn runs with --app-dir set to the web/ directory.
"""

import importlib.util
import os
import sys

_here = os.path.dirname(__file__)


def _load(name, filename):
    path = os.path.join(_here, filename)
    if not os.path.exists(path):
        return None
    fullname = f"web.api.{name}"
    # Ensure package placeholders
    if "web" not in sys.modules:
        pkg = importlib.util.module_from_spec(
            importlib.util.spec_from_loader("web", loader=None)
        )
        pkg.__path__ = [os.path.dirname(__file__)]
        sys.modules["web"] = pkg
    if "web.api" not in sys.modules:
        pkg = importlib.util.module_from_spec(
            importlib.util.spec_from_loader("web.api", loader=None)
        )
        pkg.__path__ = [_here]
        sys.modules["web.api"] = pkg

    spec = importlib.util.spec_from_file_location(fullname, path)
    module = importlib.util.module_from_spec(spec)
    module.__package__ = "web.api"
    sys.modules[fullname] = module
    spec.loader.exec_module(module)
    return getattr(module, "router", None)


file_router = _load("file_api", "file-api.py")
kg_router = _load("kg_api", "kg-api.py")
rag_router = _load("rag_api", "rag-api.py")


def get_api_routers():
    routers = []
    if rag_router is not None:
        routers.append(rag_router)
    if kg_router is not None:
        routers.append(kg_router)
    if file_router is not None:
        routers.append(file_router)
    return routers
