"""
CAIP-Karnataka — Supervisor Orchestrator
===========================================
Coordinates the district-level intelligence pipeline. Structurally
identical pattern to the original CAIP supervisor (dispatch agents,
aggregate, validate confidence, build report + audit trail), but the
agent roster reflects Karnataka data reality:

  ACTIVE (real data backs these):
    - DistrictRankingAgent      (replaces HotspotDetectionAgent)
    - CrimeCategoryAnalysisAgent (replaces generic crime-type breakdown)
    - CrimeTrendAgent            (replaces CrimePredictionAgent — honest baseline only)

  DISABLED BY DEFAULT (feature-flagged, explained, never simulated):
    - CriminalNetworkAgent
    - RepeatOffenderAgent
    - AnomalyDetectionAgent

The report structure keeps the same shape as the original
CrimeAnalysisReport (executive_summary, key_findings, ..., audit_trail)
so the frontend contract doesn't need to be reinvented, but every
section is populated only from what our agents can honestly support.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents.crime_category_agent import CrimeCategoryAnalysisAgent
from app.services.agents.crime_trend_agent import CrimeTrendAgent
from app.services.agents.disabled_feature_agents import (AnomalyDetectionAgent,
                                                           CriminalNetworkAgent,
                                                           RepeatOffenderAgent)
from app.services.agents.district_ranking_agent import DistrictRankingAgent


class KarnatakaCrimeIntelligenceSupervisor:
    def __init__(self) -> None:
        self.ranking_agent = DistrictRankingAgent()
        self.category_agent = CrimeCategoryAnalysisAgent()
        self.trend_agent = CrimeTrendAgent()
        self.network_agent = CriminalNetworkAgent()
        self.offender_agent = RepeatOffenderAgent()
        self.anomaly_agent = AnomalyDetectionAgent()

    async def generate_full_report(
        self,
        db: AsyncSession,
        district_code: Optional[str] = None,
        year: Optional[int] = None,
    ) -> dict[str, Any]:
        ranking_result = await self.ranking_agent.execute(db=db, year=year)
        category_result = await self.category_agent.execute(db=db, district_code=district_code, year=year)
        trend_result = await self.trend_agent.execute(db=db, district_code=district_code)
        network_result = await self.network_agent.execute(db=db)
        offender_result = await self.offender_agent.execute(db=db)
        anomaly_result = await self.anomaly_agent.execute(db=db)

        all_results = [ranking_result, category_result, trend_result,
                        network_result, offender_result, anomaly_result]

        active_results = [r for r in all_results if r.success]
        confidence_scores = {r.agent_name: r.confidence for r in all_results}
        overall_confidence = (
            round(sum(r.confidence for r in active_results) / len(active_results), 4)
            if active_results else 0.0
        )

        total_row = (await db.execute(
            text("""SELECT SUM(total_ipc_crimes) AS total, MAX(year) AS yr
                    FROM district_year_totals
                    WHERE year = COALESCE(:yr, (SELECT MAX(year) FROM district_year_totals))"""),
            {"yr": year},
        )).mappings().first()

        total_crimes = total_row["total"] if total_row else 0
        data_year = total_row["yr"] if total_row else None

        key_findings = self._build_key_findings(ranking_result, category_result, trend_result)
        recommendations = self._build_recommendations(ranking_result, category_result)
        disabled_features = self._build_disabled_features_notice(network_result, offender_result, anomaly_result)

        report = {
            "executive_summary": {
                "headline": f"Karnataka Crime Intelligence Report — {data_year or 'N/A'}",
                "period": str(data_year) if data_year else "No data loaded",
                "total_ipc_crimes_statewide": total_crimes or 0,
                "districts_analyzed": len(ranking_result.data.get("district_ranking", [])) if ranking_result.success else 0,
                "data_year": data_year,
                "key_takeaway": key_findings[0] if key_findings else "Insufficient data loaded to generate findings.",
                "data_maturity_notice": (
                    f"This report is based on official OGD district-level statistics "
                    f"for {data_year or 'the selected year'}. It is a foundational baseline."
                ),
            },
            "key_findings": key_findings,
            "district_ranking": ranking_result.data.get("district_ranking", []) if ranking_result.success else [],
            "crime_category_breakdown": category_result.data if category_result.success else {},
            "trend_analysis": trend_result.data if trend_result.success else {},
            "network_analysis": None,   # always None — see disabled_features_notice
            "repeat_offender_analysis": None,
            "anomaly_alerts": [],
            "disabled_features": disabled_features,
            "recommendations": recommendations,
            "confidence_scores": confidence_scores,
            "audit_trail": [r.to_audit_entry() for r in all_results],
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall_confidence": overall_confidence,
        }
        return report

    def _build_key_findings(self, ranking_result, category_result, trend_result) -> list[str]:
        findings = []
        if ranking_result.success:
            ranking = ranking_result.data.get("district_ranking", [])
            if ranking:
                top = ranking[0]
                findings.append(
                    f"{top['district_name']} recorded the highest total IPC crime count "
                    f"({top['total_ipc_crimes']}) among Karnataka districts in "
                    f"{ranking_result.data.get('year')} (OGD official data)."
                )
            elevated = ranking_result.data.get("elevated_districts", [])
            if elevated:
                findings.append(
                    f"{len(elevated)} district(s) recorded crime totals more than 1 standard "
                    f"deviation above the state mean: {', '.join(elevated)}."
                )
        if category_result.success:
            groups = category_result.data.get("group_breakdown", [])
            if groups:
                findings.append(
                    f"'{groups[0]['crime_group']}' accounts for the largest share of reported "
                    f"IPC crime ({groups[0]['pct_of_total']}% of total) in the analyzed scope."
                )
        if not findings:
            findings.append("Insufficient data loaded to surface findings — run the OGD ETL import.")
        return findings

    def _build_recommendations(self, ranking_result, category_result) -> list[str]:
        recs = []
        if ranking_result.success and ranking_result.data.get("elevated_districts"):
            recs.append(
                "Districts flagged as statistically elevated warrant closer district-level "
                "review. This flag is based on a snapshot of aggregate data and should "
                "be corroborated with local police station records before resource reallocation."
            )
        return recs

    def _build_disabled_features_notice(self, network_result, offender_result, anomaly_result) -> list[dict]:
        notices = []
        for result, feature_name in [
            (network_result, "Criminal Network Analysis"),
            (offender_result, "Repeat Offender Tracking"),
            (anomaly_result, "Anomaly Detection"),
        ]:
            notices.append({
                "feature": feature_name,
                "status": "disabled",
                "reason": result.warnings[0] if result.warnings else "No reason recorded.",
            })
        return notices
