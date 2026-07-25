"""
CAIP-Karnataka — District Crime Trend / Prediction Agent
===========================================================
CRITICAL DESIGN CONSTRAINT: with only ONE year (2013) of district
totals currently loaded, there is no time-series signal to predict
from, and 35 rows is far too small a sample for a robust ML
classifier. This agent NEVER trains or runs XGBoost/LightGBM/SHAP
unless at least MIN_YEARS_FOR_ML years of real district data exist in
the database — checked at runtime, not assumed.

Until then, it returns a transparent, clearly-labeled statistical
baseline: each district's latest-year total compared to the state
mean, expressed as a "relative crime burden" (not a "prediction" —
we do not claim to forecast the future from a single data point).

This is intentionally less impressive than a baseline ML model. That is
the point: an honest baseline beats a dishonest prediction.
"""
from __future__ import annotations

from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.agents.base_agent import AgentResult, BaseAgent

MIN_YEARS_FOR_ML = 3


class CrimeTrendAgent(BaseAgent):
    name = "CrimeTrendAgent"
    required_sources = ["postgresql.district_year_totals"]

    async def run(self, db: AsyncSession, district_code: str | None = None, **_: Any) -> AgentResult:
        years_available_row = await db.execute(
            text("SELECT DISTINCT year FROM district_year_totals ORDER BY year")
        )
        years_available = [r[0] for r in years_available_row.all()]

        if not years_available:
            return AgentResult(
                agent_name=self.name, success=False, confidence=0.0,
                warnings=["No district_year_totals data loaded — run the OGD ETL import."],
            )

        n_years = len(years_available)

        if n_years < MIN_YEARS_FOR_ML:
            # Honest baseline path — the only path currently reachable
            # given we have exactly 1 year of data loaded.
            return await self._single_or_few_year_baseline(db, district_code, years_available)

        # ML path
        return await self._ml_prediction_path(db, district_code, years_available)

    async def _ml_prediction_path(
        self, db: AsyncSession, district_code: str | None, years_available: list[int]
    ) -> AgentResult:
        from sklearn.linear_model import LinearRegression
        import numpy as np

        latest_year = max(years_available)
        params = {}
        filter_sql = ""
        if district_code:
            filter_sql = "AND d.district_code = :dcode"
            params["dcode"] = district_code

        # Fetch all historical data
        rows = (await db.execute(
            text(f"""
                SELECT d.district_code, d.district_name, dyt.year, dyt.total_ipc_crimes
                FROM district_year_totals dyt
                JOIN district d ON d.district_id = dyt.district_id
                WHERE d.is_geographic_district = TRUE {filter_sql}
                ORDER BY d.district_code, dyt.year
            """),
            params,
        )).mappings().all()

        guard = self.guard_empty_data(rows, self.name)
        if guard:
            return guard
            
        # Group data by district
        district_data = {}
        for r in rows:
            code = r["district_code"]
            if code not in district_data:
                district_data[code] = {"name": r["district_name"], "years": [], "crimes": []}
            district_data[code]["years"].append(r["year"])
            district_data[code]["crimes"].append(r["total_ipc_crimes"])

        forecast_horizon = 5
        predictions = []

        for code, data in district_data.items():
            if len(data["years"]) < MIN_YEARS_FOR_ML:
                continue

            X = np.array(data["years"]).reshape(-1, 1)
            y = np.array(data["crimes"])
            
            model = LinearRegression()
            model.fit(X, y)
            
            future_years = np.array(range(latest_year + 1, latest_year + 1 + forecast_horizon)).reshape(-1, 1)
            future_preds = model.predict(future_years)
            
            # Combine history and predictions
            trend_data = [{"year": y, "count": int(c), "is_prediction": False} for y, c in zip(data["years"], data["crimes"])]
            trend_data.extend([{"year": int(y[0]), "count": max(0, int(c)), "is_prediction": True} for y, c in zip(future_years, future_preds)])
            
            predictions.append({
                "district_code": code,
                "district_name": data["name"],
                "trend": trend_data,
                "model_coefficient": round(model.coef_[0], 2)
            })

        return AgentResult(
            agent_name=self.name,
            success=True,
            confidence=0.75,
            data_sources=["postgresql.district_year_totals"],
            data={
                "method": "linear_regression_forecast",
                "is_prediction": True,
                "years_available_total": years_available,
                "forecast_horizon": forecast_horizon,
                "predictions": predictions,
                "explainability": {
                    "method": "Linear Regression (scikit-learn)",
                    "note": "Forecasts generated using simple linear regression on historical yearly totals."
                },
            },
        )

    async def _single_or_few_year_baseline(
        self, db: AsyncSession, district_code: str | None, years_available: list[int]
    ) -> AgentResult:
        latest_year = max(years_available)
        params = {"yr": latest_year}
        filter_sql = ""
        if district_code:
            filter_sql = "AND d.district_code = :dcode"
            params["dcode"] = district_code

        rows = (await db.execute(
            text(f"""
                SELECT d.district_code, d.district_name, dyt.total_ipc_crimes
                FROM district_year_totals dyt
                JOIN district d ON d.district_id = dyt.district_id
                WHERE dyt.year = :yr AND d.is_geographic_district = TRUE {filter_sql}
                ORDER BY dyt.total_ipc_crimes DESC
            """),
            params,
        )).mappings().all()

        guard = self.guard_empty_data(rows, self.name)
        if guard:
            return guard

        counts = [r["total_ipc_crimes"] for r in rows]
        mean = sum(counts) / len(counts)

        baseline = []
        for r in rows:
            relative_burden = round(r["total_ipc_crimes"] / mean, 3) if mean else None
            baseline.append({
                "district_code": r["district_code"],
                "district_name": r["district_name"],
                "total_ipc_crimes": r["total_ipc_crimes"],
                "relative_to_state_mean": relative_burden,  # 1.0 = exactly average, 2.0 = double the average district
            })

        return AgentResult(
            agent_name=self.name,
            success=True,
            confidence=0.30,  # deliberately low — this is descriptive, not predictive
            data_sources=[f"postgresql.district_year_totals(year={latest_year})"],
            data={
                "method": "single_year_relative_burden_baseline",
                "is_prediction": False,   # explicit flag: this is NOT a forecast
                "year_analyzed": latest_year,
                "years_available_total": years_available,
                "district_relative_burden": baseline,
                "contributing_factors": ["total_ipc_crimes (single year, no trend signal available)"],
                "explainability": {
                    "method": "descriptive_ratio_to_state_mean",
                    "note": (
                        "This is a descriptive comparison of one year's crime totals "
                        "against the state average, NOT a machine-learned forecast. "
                        "No prediction of future crime is made because only one year "
                        "of district data currently exists in this database."
                    ),
                },
            },
            warnings=[
                f"Only {len(years_available)} year(s) of data loaded ({years_available}). "
                f"This is a descriptive baseline, explicitly NOT a prediction. "
                f"See docs/DATA_LIMITATIONS.md for what's required to enable real "
                f"trend forecasting."
            ],
        )
