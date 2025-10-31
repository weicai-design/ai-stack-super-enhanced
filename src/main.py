try:
    from src.services.api_gateway import (
        router as api_gateway_router,
    )  # 如果 api_gateway 未直接 include

    app.include_router(api_gateway_router)  # type: ignore[name-defined]
except Exception:
    pass
