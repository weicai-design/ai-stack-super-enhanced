from ._loader import load_original_module

_orig = load_original_module("cursor_authorization")

CursorAuthorization = _orig.CursorAuthorization
AuthorizationLevel = _orig.AuthorizationLevel
AccessScope = _orig.AccessScope

__all__ = ["CursorAuthorization", "AuthorizationLevel", "AccessScope"]


