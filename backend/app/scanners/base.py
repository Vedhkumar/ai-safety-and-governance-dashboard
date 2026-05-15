"""Abstract base class for all safety scanners."""

from abc import ABC, abstractmethod
from pydantic import BaseModel
from typing import Any


class ScanResult(BaseModel):
    """Base result class for all scanners."""
    scanner_name: str
    score: float = 0.0  # 0.0 (safe) to 1.0 (unsafe)
    is_flagged: bool = False
    details: dict[str, Any] = {}
    action_taken: str = "passed"  # passed, flagged, blocked, masked


class Scanner(ABC):
    """Abstract base class for safety scanners."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Scanner identifier."""
        ...

    @abstractmethod
    async def scan_input(self, text: str) -> ScanResult:
        """Scan input text (prompt) before sending to LLM."""
        ...

    @abstractmethod
    async def scan_output(self, text: str, context: dict | None = None) -> ScanResult:
        """Scan output text (LLM response). Context may include original prompt, source docs, etc."""
        ...
