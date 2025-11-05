"""
title: test_pipe
author: test
version: 1.0
"""

from typing import Optional
from pydantic import BaseModel


class Pipe:
    class Valves(BaseModel):
        pass

    def __init__(self):
        self.valves = self.Valves()

    def pipe(self, body: dict) -> dict:
        return body
