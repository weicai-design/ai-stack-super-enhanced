"""Compatibility layer for emoji-named AI Programming Assistant modules."""

from .cursor_bridge import CursorBridge
from .cursor_protocol import CursorProtocol, ProtocolCommand
from .cursor_plugin_system import CursorPluginSystem, PluginPermission, PluginStatus
from .cursor_local_bridge import CursorLocalBridge
from .cursor_authorization import CursorAuthorization, AuthorizationLevel, AccessScope

__all__ = [
    "CursorBridge",
    "CursorProtocol",
    "ProtocolCommand",
    "CursorPluginSystem",
    "PluginPermission",
    "PluginStatus",
    "CursorLocalBridge",
    "CursorAuthorization",
    "AuthorizationLevel",
    "AccessScope",
]


