"""
CAIP-Karnataka — Pydantic Schemas
Response shapes match supervisor.py's generate_full_report() output —
district_code (not UUID), disabled_features array, data_maturity_notice.
"""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class UserRole(str, Enum):
    analyst = "analyst"
    supervisor = "supervisor"
    admin = "admin"
    readonly = "readonly"


class LoginRequest(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserCreate(BaseModel):
    email: str
    username: str
    full_name: Optional[str] = None
    password: str
    role: UserRole = UserRole.analyst


class UserOut(BaseModel):
    id: str
    email: str
    username: str
    full_name: Optional[str]
    role: str

    class Config:
        from_attributes = True


class DistrictOut(BaseModel):
    district_code: str
    district_name: str
    is_geographic_district: bool
    jurisdiction_type: str
    population_2011_census: Optional[int] = None
    data_available_from: int
    notes: Optional[str] = None
    centroid: Optional[dict] = None  # {"lat": .., "lng": ..}


class DistrictRankingItem(BaseModel):
    rank: int
    district_code: str
    district_name: str
    total_ipc_crimes: int
    crime_rate_per_lakh: Optional[float] = None
    z_score_vs_state_mean: float
    elevated: bool
    ranking_basis: str


class CrimeCategoryGroup(BaseModel):
    crime_group: str
    count: int
    pct_of_total: float


class DisabledFeatureNotice(BaseModel):
    feature: str
    status: str = "disabled"
    reason: str


class ExecutiveSummary(BaseModel):
    headline: str
    period: str
    total_ipc_crimes_statewide: int
    districts_analyzed: int
    data_year: Optional[int]
    key_takeaway: str
    data_maturity_notice: str


class AuditTrailEntry(BaseModel):
    agent: str
    action: str
    data_sources: list[str]
    timestamp: str
    duration_ms: Optional[int] = None


class KarnatakaCrimeReport(BaseModel):
    """Master dashboard-ready response from the Supervisor."""
    executive_summary: ExecutiveSummary
    key_findings: list[str]
    district_ranking: list[DistrictRankingItem]
    crime_category_breakdown: dict[str, Any]
    trend_analysis: dict[str, Any]
    network_analysis: None = None
    repeat_offender_analysis: None = None
    anomaly_alerts: list = Field(default_factory=list)
    disabled_features: list[DisabledFeatureNotice]
    recommendations: list[str]
    confidence_scores: dict[str, float]
    audit_trail: list[AuditTrailEntry]
    generated_at: str
    overall_confidence: float
