"""
CAIP-Karnataka — District Priority Ranking Agent
===================================================
REPLACES the old HotspotDetectionAgent (which ran HDBSCAN point
clustering — impossible here since we have no incident-level
coordinates, only annual district totals).

This agent ranks Karnataka districts by crime burden using ONLY the
real OGD district-year totals we actually have. It does NOT invent
geographic clusters. It is explicitly labeled as
"district-level statistical ranking," never as "hotspot geospatial
clustering," to avoid overstating what the underlying data supports.

Method (fully transparent, no black box):
  1. Pull latest-year total_ipc_crimes per district
  2. If population data is loaded (feature flag ENABLE_PER_CAPITA_RATES),
     rank by crime rate per lakh population — the fairer comparison.
     Otherwise, rank by raw count and clearly label it as such (a
     large district will naturally have a higher raw count).
  3. Compute a z-score of each district relative to the state mean to
     flag "elevated" districts (>1 std dev above mean) — a simple,
     auditable statistical rule, not an ML model.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents.base_agent import AgentResult, BaseAgent


class DistrictRankingAgent(BaseAgent):
    name = "DistrictRankingAgent"
    required_sources = ["postgresql.district_year_totals"]

    async def run(self, db: AsyncSession, year: int | None = None, ranking_basis: str = "raw_count", **_: Any) -> AgentResult:
        # Determine the latest year available if not specified
        if year is None:
            latest_year_row = await db.execute(
                text("SELECT MAX(year) FROM district_year_totals")
            )
            year = latest_year_row.scalar_one_or_none()

        if year is None:
            return AgentResult(
                agent_name=self.name,
                success=False,
                confidence=0.0,
                warnings=["No district_year_totals data loaded. Run the OGD ETL import first."],
            )

        per_capita_enabled = (ranking_basis == "per_capita_rate")

        order_by_sql = "dyt.crime_rate_per_lakh DESC NULLS LAST" if per_capita_enabled else "dyt.total_ipc_crimes DESC"

        rows = (await db.execute(
            text(f"""
                SELECT d.district_code, d.district_name, d.is_geographic_district,
                       dyt.total_ipc_crimes, dyt.crime_rate_per_lakh, d.population_2011_census
                FROM district_year_totals dyt
                JOIN district d ON d.district_id = dyt.district_id
                WHERE dyt.year = :yr AND d.is_geographic_district = TRUE
                ORDER BY {order_by_sql}
            """),
            {"yr": year},
        )).mappings().all()

        guard = self.guard_empty_data(rows, self.name)
        if guard:
            return guard

        counts = [r["crime_rate_per_lakh"] if per_capita_enabled and r["crime_rate_per_lakh"] else r["total_ipc_crimes"] for r in rows]
        # convert counts to float just in case
        counts = [float(c) for c in counts]
        
        mean = sum(counts) / len(counts)
        variance = sum((c - mean) ** 2 for c in counts) / len(counts)
        std = variance ** 0.5

        ranking = []
        for idx, r in enumerate(rows, start=1):
            val = float(r["crime_rate_per_lakh"]) if per_capita_enabled and r["crime_rate_per_lakh"] else float(r["total_ipc_crimes"])
            z = (val - mean) / std if std > 0 else 0.0
            ranking.append({
                "rank": idx,
                "district_code": r["district_code"],
                "district_name": r["district_name"],
                "total_ipc_crimes": r["total_ipc_crimes"],
                "crime_rate_per_lakh": float(r["crime_rate_per_lakh"]) if r["crime_rate_per_lakh"] else None,
                "z_score_vs_state_mean": round(z, 3),
                "elevated": z > 1.0,
                "ranking_basis": "crime_rate_per_lakh" if per_capita_enabled else "raw_total_count",
            })

        elevated_districts = [r["district_code"] for r in ranking if r["elevated"]]

        # Confidence reflects: (a) single-year snapshot is inherently limited,
        # (b) whether we're using the fairer per-capita method
        confidence = 0.55 if per_capita_enabled else 0.40

        return AgentResult(
            agent_name=self.name,
            success=True,
            confidence=confidence,
            data_sources=[f"postgresql.district_year_totals(year={year})"],
            data={
                "year": year,
                "ranking_method": "per_capita_rate" if per_capita_enabled else "raw_count",
                "district_ranking": ranking,
                "elevated_districts": elevated_districts,
                "state_mean_total_crimes": round(mean, 1),
                "state_std_dev": round(std, 1),
            },
            warnings=(
                [] if per_capita_enabled else
                ["Ranking is by RAW crime count, not per-capita rate."]
            ),
        )
