"""
CAIP-Karnataka — Base Agent Contract
(Unchanged from the original CAIP architecture — this pattern is
domain-agnostic and equally valid for Karnataka data. The anti-
fabrication guard is, if anything, MORE important now since we have
genuinely limited data and must never paper over gaps.)
"""
from __future__ import annotations

import time
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Optional


@dataclass
class AgentResult:
    agent_name: str
    success: bool
    data: dict[str, Any] = field(default_factory=dict)
    confidence: float = 0.0
    data_sources: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    error: Optional[str] = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    duration_ms: Optional[int] = None
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))

    def to_audit_entry(self) -> dict[str, Any]:
        return {
            "agent": self.agent_name,
            "action": "analysis_complete" if self.success else "analysis_failed",
            "data_sources": self.data_sources,
            "timestamp": self.started_at.isoformat(),
            "duration_ms": self.duration_ms,
        }


class BaseAgent(ABC):
    name: str = "BaseAgent"
    required_sources: list[str] = []

    async def execute(self, **kwargs: Any) -> AgentResult:
        start = time.perf_counter()
        try:
            result = await self.run(**kwargs)
            result.duration_ms = int((time.perf_counter() - start) * 1000)
            return result
        except Exception as exc:  # noqa: BLE001
            return AgentResult(
                agent_name=self.name,
                success=False,
                error=str(exc),
                duration_ms=int((time.perf_counter() - start) * 1000),
            )

    @abstractmethod
    async def run(self, **kwargs: Any) -> AgentResult:
        raise NotImplementedError

    @staticmethod
    def guard_empty_data(rows, agent_name: str) -> Optional[AgentResult]:
        if not rows:
            return AgentResult(
                agent_name=agent_name,
                success=False,
                confidence=0.0,
                warnings=["No underlying records found for the requested scope/time window."],
            )
        return None

    @staticmethod
    def guard_feature_disabled(is_enabled: bool, agent_name: str, reason: str) -> Optional[AgentResult]:
        """New helper specific to CAIP-Karnataka: short-circuits agents
        gated behind a feature flag (see feature_flag table), returning
        an honest, explained disabled-state result instead of running
        on absent/fabricated data."""
        if not is_enabled:
            return AgentResult(
                agent_name=agent_name,
                success=False,
                confidence=0.0,
                warnings=[f"Feature disabled: {reason}"],
                data={"feature_disabled": True, "reason": reason},
            )
        return None
