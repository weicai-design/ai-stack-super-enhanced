from ._loader import load_original_module

_orig = load_original_module("cursor_bridge")

CursorBridge = _orig.CursorBridge

__all__ = ["CursorBridge"]


