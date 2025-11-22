from ._loader import load_original_module

_orig = load_original_module("cursor_plugin_system")

CursorPluginSystem = _orig.CursorPluginSystem
PluginPermission = _orig.PluginPermission
PluginStatus = _orig.PluginStatus

__all__ = [
    "CursorPluginSystem",
    "PluginPermission",
    "PluginStatus",
]


