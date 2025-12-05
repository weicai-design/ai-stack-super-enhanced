import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from core.service_registry import ServiceRegistry, ServiceContract
from core.service_gateway import ServiceGateway


@pytest.mark.asyncio
async def test_service_gateway_internal_call():
    registry = ServiceRegistry()
    contract = ServiceContract(service="rag_hub", operation="search", path="/v1/rag/search")
    registry.register_contract(contract)
    gateway = ServiceGateway(registry=registry)

    async def handler(payload):
        return {"echo": payload.get("query")}

    gateway.register_internal_handler("rag_hub", "search", handler)
    result = await gateway.call_service("rag_hub", "search", {"query": "hello"})
    assert result.status == "success"
    assert result.response == {"echo": "hello"}

