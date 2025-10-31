try:
    from src.experts.registry import create as _create_expert
    from src.experts.registry import resolve_by_domain as _resolve_expert_by_domain
except Exception:
    _resolve_expert_by_domain = None
    _create_expert = None


def get_expert_by_domain(domain: str):
    if _resolve_expert_by_domain is None:
        raise RuntimeError("experts registry not available")
    return _resolve_expert_by_domain(domain)


def get_expert(name: str):
    if _create_expert is None:
        raise RuntimeError("experts registry not available")
    return _create_expert(name)
