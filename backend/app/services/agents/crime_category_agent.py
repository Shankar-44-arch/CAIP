"""
CAIP-Karnataka — Crime Category Analysis Agent
=================================================
Analyzes the category-mix of crime within each district using the real
OGD crime_head / crime_sub_head breakdown. This replaces generic
"crime type distribution" logic with Karnataka/OGD-official
categories (Murder, Theft, Dacoity, Crimes Against Women, etc.)
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents.base_agent import AgentResult, BaseAgent


class CrimeCategoryAnalysisAgent(BaseAgent):
    name = "CrimeCategoryAnalysisAgent"
    required_sources = ["postgresql.district_crime_stats"]

    async def run(
        self,
        db: AsyncSession,
        district_code: str | None = None,
        year: int | None = None,
        **_: Any,
    ) -> AgentResult:
        if year is None:
            latest = await db.execute(text("SELECT MAX(year) FROM district_crime_stats"))
            year = latest.scalar_one_or_none()
        if year is None:
            return AgentResult(agent_name=self.name, success=False, confidence=0.0,
                               warnings=["No district_crime_stats data loaded."])

        params = {"yr": year}
        district_filter = ""
        if district_code:
            district_filter = "AND d.district_code = :dcode"
            params["dcode"] = district_code

        rows = (await db.execute(
            text(f"""
                SELECT ch.crime_group_name, csh.crime_head_name, csh.is_aggregate,
                       SUM(dcs.incident_count) AS total_count
                FROM district_crime_stats dcs
                JOIN crime_sub_head csh ON csh.crime_sub_head_id = dcs.crime_sub_head_id
                JOIN crime_head ch ON ch.crime_head_id = csh.crime_head_id
                JOIN district d ON d.district_id = dcs.district_id
                WHERE dcs.year = :yr {district_filter}
                GROUP BY ch.crime_group_name, csh.crime_head_name, csh.is_aggregate
                ORDER BY total_count DESC
            """),
            params,
        )).mappings().all()

        guard = self.guard_empty_data(rows, self.name)
        if guard:
            return guard

        # Exclude aggregate rows (e.g. "Theft (Total)") from the mix breakdown
        # to avoid double counting against their own components
        non_aggregate = [r for r in rows if not r["is_aggregate"]]
        grand_total = sum(r["total_count"] for r in non_aggregate)

        by_group: dict[str, int] = {}
        by_sub_head = []
        for r in non_aggregate:
            by_group[r["crime_group_name"]] = by_group.get(r["crime_group_name"], 0) + r["total_count"]
            by_sub_head.append({
                "crime_head_name": r["crime_head_name"],
                "crime_group": r["crime_group_name"],
                "count": r["total_count"],
                "pct_of_total": round(100 * r["total_count"] / grand_total, 2) if grand_total else 0,
            })

        group_breakdown = [
            {"crime_group": g, "count": c, "pct_of_total": round(100 * c / grand_total, 2) if grand_total else 0}
            for g, c in sorted(by_group.items(), key=lambda kv: -kv[1])
        ]

        return AgentResult(
            agent_name=self.name,
            success=True,
            confidence=0.85,  # this is a direct real-data aggregation, high confidence in the arithmetic itself
            data_sources=[f"postgresql.district_crime_stats(year={year})"],
            data={
                "year": year,
                "district_code": district_code,
                "grand_total": grand_total,
                "group_breakdown": group_breakdown,
                "sub_head_breakdown": sorted(by_sub_head, key=lambda x: -x["count"])[:15],
            },
        )
