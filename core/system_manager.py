from __future__ import annotations

from typing import Any, Dict


class LifecycleModule:
    async def initialize(self, config: Dict[str, Any], services: Dict[str, Any]): ...
    async def start(self): ...
    async def stop(self): ...
    async def get_health_status(self) -> Dict[str, Any]: ...
    async def reload_config(self, config: Dict[str, Any]): ...


class SystemManager:
    def __init__(self):
        self.modules: Dict[str, LifecycleModule] = {}
        self.services: Dict[str, Any] = {}
        self.config: Dict[str, Any] = {}

    async def register(self, name: str, module: LifecycleModule, cfg: Dict[str, Any]):
        await module.initialize(cfg, self.services)
        self.modules[name] = module

    async def start_all(self):
        for m in self.modules.values():
            await m.start()

    async def stop_all(self):
        for m in reversed(list(self.modules.values())):
            try:
                await m.stop()
            except Exception:
                pass

    async def health(self) -> Dict[str, Any]:
        res = {}
        for k, m in self.modules.items():
            try:
                res[k] = await m.get_health_status()
            except Exception as e:
                res[k] = {"ok": False, "error": str(e)}
        return {"ok": all(v.get("ok", True) for v in res.values()), "modules": res}
