"""
title: test
author: test
version: 1.0
"""

class Filter:
    def __init__(self):
        pass
    
    async def inlet(self, body: dict) -> dict:
        return body
    
    async def outlet(self, body: dict) -> dict:
        return body


