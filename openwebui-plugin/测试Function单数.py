"""
title: test
author: test
version: 1.0
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Any, Awaitable


class Function:
    class Valves(BaseModel):
        test: bool = Field(default=True)

    def __init__(self):
        self.valves = self.Valves()

    async def inlet(self, body: dict, __user__: Optional[dict] = None, __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None) -> dict:
        return body

    async def outlet(self, body: dict, __user__: Optional[dict] = None, __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None) -> dict:
        return body
