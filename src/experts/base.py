from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class Expert(ABC):
    name: str
    domain: str

    @abstractmethod
    def predict(self, payload: Dict[str, Any]) -> Dict[str, Any]: ...
