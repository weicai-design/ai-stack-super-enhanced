"""
title: test_plugin
author: test
version: 1.0
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Any, Awaitable


class Plugin:
    class Valves(BaseModel):
        test_option: bool = Field(default=True, description="Test option")

    def __init__(self):
        self.valves = self.Valves()

    async def inlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> dict:
        return body

    async def outlet(
        self,
        body: dict,
        __user__: Optional[dict] = None,
        __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None,
    ) -> dict:
        return body


