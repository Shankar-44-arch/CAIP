"""
CAIP-Karnataka — Disabled-Feature Agents
===========================================
These three agents correspond to real CAIP features that CANNOT be
honestly supported with currently available public Karnataka data:

  1. CriminalNetworkAgent   — needs offender relationship data (none public)
  2. RepeatOffenderAgent    — needs offender-level records (none public)
  3. AnomalyDetectionAgent  — needs multi-point time series (only 1 year loaded)

Rather than delete these classes (which would silently hide the
feature from anyone reading the codebase) or fabricate their output, each
agent:
  - Checks its feature flag in the `feature_flag` table
  - Returns AgentResult(success=False) with a clear, specific reason
  - Documents exactly what data would need to exist to enable it
  - Contains the real implementation logic, commented as TODO, ready
    to activate the moment real data access is granted

This mirrors docs/DATA_LIMITATIONS.md §4 exactly.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents.base_agent import AgentResult, BaseAgent


async def _get_flag(db: AsyncSession, key: str) -> tuple[bool, str]:
    row = (await db.execute(
        text("SELECT is_enabled, reason FROM feature_flag WHERE flag_key = :k"), {"k": key}
    )).mappings().first()
    if row is None:
        return False, f"Feature flag '{key}' not found in database — treating as disabled."
    return bool(row["is_enabled"]), row["reason"] or ""


class CriminalNetworkAgent(BaseAgent):
    name = "CriminalNetworkAgent"
    required_sources = ["neo4j.offender_graph (NOT AVAILABLE)"]

    async def run(self, db: AsyncSession, **_: Any) -> AgentResult:
        enabled, reason = await _get_flag(db, "ENABLE_NETWORK_ANALYSIS")
        guard = self.guard_feature_disabled(enabled, self.name, reason)
        if guard:
            return guard

        # ── REAL IMPLEMENTATION (dormant until enabled) ──────────────
        # If a police department connects a genuine KSCRB intelligence
        # feed populating Neo4j :Offender/:KNOWS relationships (see the
        # original CAIP neo4j_schema.cypher for the graph structure),
        # this would run the same Cypher-based degree-centrality and
        # community-detection logic as the original platform. Left
        # unimplemented here deliberately — building it against
        # nonexistent data would require fabricating a graph, which
        # violates the project's core constraint.
        return AgentResult(
            agent_name=self.name, success=False, confidence=0.0,
            warnings=["Reached unreachable code path — feature flag check should have short-circuited."],
        )


class RepeatOffenderAgent(BaseAgent):
    name = "RepeatOffenderAgent"
    required_sources = ["postgresql.accused / arrest_surrender (SCHEMA EXISTS, EMPTY)"]

    async def run(self, db: AsyncSession, **_: Any) -> AgentResult:
        enabled, reason = await _get_flag(db, "ENABLE_OFFENDER_TRACKING")
        guard = self.guard_feature_disabled(enabled, self.name, reason)
        if guard:
            return guard

        # ── REAL IMPLEMENTATION (dormant until enabled) ──────────────
        # The `accused` and `arrest_surrender` tables (see
        # backend/database_schema.sql, Tier 2) already mirror the exact
        # structure of the official Karnataka Police FIR ER diagram.
        # Once a real CCTNS extract populates these tables, this agent
        # would query:
        #   SELECT accused_name, COUNT(DISTINCT case_master_id) AS offence_count
        #   FROM accused GROUP BY accused_name HAVING COUNT(*) >= 2
        # exactly mirroring the original CAIP RepeatOffenderAgent logic.
        # Not implemented against empty tables to avoid a misleading
        # "0 repeat offenders found" result that looks like an analysis
        # rather than an absence of data.
        return AgentResult(
            agent_name=self.name, success=False, confidence=0.0,
            warnings=["Reached unreachable code path — feature flag check should have short-circuited."],
        )


class AnomalyDetectionAgent(BaseAgent):
    name = "AnomalyDetectionAgent"
    required_sources = ["postgresql.district_crime_stats (needs monthly+ granularity)"]

    async def run(self, db: AsyncSession, **_: Any) -> AgentResult:
        enabled, reason = await _get_flag(db, "ENABLE_ANOMALY_DETECTION")
        guard = self.guard_feature_disabled(enabled, self.name, reason)
        if guard:
            return guard

        # ── REAL IMPLEMENTATION (dormant until enabled) ──────────────
        # Isolation Forest / z-score spike detection (as in the original
        # CAIP AnomalyDetectionAgent) requires multiple time points per
        # district — at minimum monthly granularity across 2+ years to
        # establish a meaningful "normal" baseline before flagging
        # deviations. Our current data is one annual total per
        # district. Running Isolation Forest on 35 single-value rows
        # would not detect meaningful anomalies — it would essentially
        # rediscover the district ranking already computed by
        # DistrictRankingAgent, presented misleadingly as "anomaly
        # detection." We refuse to do that.
        return AgentResult(
            agent_name=self.name, success=False, confidence=0.0,
            warnings=["Reached unreachable code path — feature flag check should have short-circuited."],
        )
