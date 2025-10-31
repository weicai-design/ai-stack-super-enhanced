def test_expert_registry_and_domain():
    # 触发注册（import side-effect）
    from src.experts.finance_expert import FinanceExpert  # noqa: F401
    from src.experts.registry import create, resolve_by_domain
    from src.experts.trend_expert import TrendExpert  # noqa: F401

    e1 = create("finance_expert")
    assert e1.domain == "finance"
    out1 = e1.predict({"metrics": {"debt_ratio": 0.7, "cash_flow": 0.4}})
    assert "risk" in out1

    e2 = resolve_by_domain("trend")
    assert e2 is not None
    out2 = e2.predict({"series": list(range(20))})
    assert out2["direction"] in ("up", "down", "flat")
