from ._loader import load_original_module

_orig = load_original_module("cursor_local_bridge")

CursorLocalBridge = _orig.CursorLocalBridge

__all__ = ["CursorLocalBridge"]


