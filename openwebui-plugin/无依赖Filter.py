"""
title: aistack
author: test
version: 1.0
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Awaitable


class Filter:
    class Valves(BaseModel):
        priority: int = Field(default=0, description="Priority")
        test_mode: bool = Field(default=True, description="Test mode")

    def __init__(self):
        self.valves = self.Valves()

    async def inlet(self, body: dict, __user__: Optional[dict] = None, __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None) -> dict:
        if __event_emitter__:
            await __event_emitter__({"type": "status", "data": {"description": "AI Stack Test", "done": False}})
        return body

    async def outlet(self, body: dict, __user__: Optional[dict] = None, __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None) -> dict:
        return body


