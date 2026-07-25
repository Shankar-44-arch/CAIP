"""
CAIP-Karnataka — District & Feature Flag Endpoints
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from geoalchemy2.shape import to_shape
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.db import get_db
from app.core.security import require_any
from app.models.orm_models import District

router = APIRouter(tags=["Districts & Configuration"])


@router.get("/districts")
async def list_districts(db: AsyncSession = Depends(get_db), user: dict = Depends(require_any)):
    rows = (await db.execute(select(District).order_by(District.district_name))).scalars().all()
    out = []
    for d in rows:
        centroid = None
        if d.centroid is not None:
            point = to_shape(d.centroid)
            centroid = {"lat": point.y, "lng": point.x}
        out.append({
            "district_code": d.district_code,
            "district_name": d.district_name,
            "historical_data_name": d.historical_data_name,
            "is_geographic_district": d.is_geographic_district,
            "jurisdiction_type": d.jurisdiction_type,
            "population_2011_census": d.population_2011_census,
            "data_available_from": d.data_available_from,
            "notes": d.notes,
            "centroid": centroid,
        })
    return out


@router.get("/feature-flags")
async def list_feature_flags(db: AsyncSession = Depends(get_db), user: dict = Depends(require_any)):
    """Exposes the current on/off state + reason for every gated feature —
    the frontend uses this to decide whether to render a live feature or
    a DisabledFeatureNotice, without hardcoding the logic client-side."""
    rows = (await db.execute(text("SELECT flag_key, is_enabled, reason FROM feature_flag"))).mappings().all()
    return [{"flag_key": r["flag_key"], "is_enabled": r["is_enabled"], "reason": r["reason"]} for r in rows]


@router.get("/data-years")
async def list_available_years(db: AsyncSession = Depends(get_db), user: dict = Depends(require_any)):
    """Which years of real OGD data are actually loaded — the frontend
    uses this to populate year selectors honestly (never showing a year
    that has no underlying data)."""
    rows = (await db.execute(text(
        "SELECT DISTINCT year FROM district_year_totals ORDER BY year"
    ))).all()
    return {"years_available": [r[0] for r in rows]}
