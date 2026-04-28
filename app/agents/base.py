from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Generic, Optional, TypeVar

T = TypeVar("T")


class AgentError(RuntimeError):
    pass


@dataclass(frozen=True)
class AgentResult(Generic[T]):
    agent: str
    output: Optional[T] = None
    meta: Dict[str, Any] | None = None

