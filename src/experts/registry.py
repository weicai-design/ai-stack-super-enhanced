from typing import Any, Dict, Optional, Type

from .base import Expert

_REGISTRY: Dict[str, Type[Expert]] = {}
_SINGLETONS: Dict[str, Expert] = {}


def register(name: str, cls: Type[Expert]) -> None:
    _REGISTRY[name] = cls


def create(name: str, **kwargs: Any) -> Expert:
    if name in _SINGLETONS:
        return _SINGLETONS[name]
    cls = _REGISTRY.get(name)
    if not cls:
        raise KeyError(f"expert '{name}' not registered")
    inst = cls(**kwargs)
    _SINGLETONS[name] = inst
    return inst


def resolve_by_domain(domain: str) -> Optional[Expert]:
    for n, cls in _REGISTRY.items():
        if getattr(cls, "domain", None) == domain:
            return create(n)
    return None
