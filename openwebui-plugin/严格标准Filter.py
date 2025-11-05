"""
title: aistack
author: test
version: 1.0
"""

from pydantic import BaseModel, Field
from typing import Optional, Callable, Awaitable
import httpx


class Filter:
    class Valves(BaseModel):
        priority: int = Field(default=0, description="Priority level")

    def __init__(self):
        self.valves = self.Valves()

    async def inlet(self, body: dict, __user__: Optional[dict] = None, __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None) -> dict:
        print(f"Filter inlet called")
        return body

    async def outlet(self, body: dict, __user__: Optional[dict] = None, __event_emitter__: Optional[Callable[[dict], Awaitable[None]]] = None) -> dict:
        print(f"Filter outlet called")
        return body


