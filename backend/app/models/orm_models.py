"""
CAIP-Karnataka — SQLAlchemy ORM Models
Mirrors backend/database_schema.sql exactly.

Tier 0: reference/lookup tables (state, district, crime_head, crime_sub_head,
        act, section, case_category, gravity_offence, case_status_master,
        unit_type, unit)
Tier 1: district_crime_stats, district_year_totals — REAL DATA, populated now
Tier 2: rank, designation, employee, court, case_master, complainant_details,
        victim, accused, arrest_surrender, act_section_association,
        chargesheet_details — schema-ready, EMPTY until real CCTNS access
App:    app_user, audit_log, feature_flag, agent_task
"""
from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Optional

from geoalchemy2 import Geometry
from sqlalchemy import (ARRAY, BigInteger, Boolean, CheckConstraint, Date,
                         DateTime, ForeignKey, Integer, Numeric, String, Text,
                         UniqueConstraint, func)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base

jurisdiction_type_enum = ENUM(
    "district", "commissionerate", "rural_unit", "cross_district_unit",
    name="jurisdiction_type", create_type=False,
)
case_status_enum = ENUM(
    "under_investigation", "charge_sheeted", "closed", "undetected", "false_case",
    name="case_status_enum", create_type=False,
)
user_role_enum = ENUM("analyst", "supervisor", "admin", "readonly", name="user_role", create_type=False)
data_source_enum = ENUM(
    "ogd_official", "kscrb_official", "derived_calculation", "user_entered",
    name="data_source_enum", create_type=False,
)


def gen_uuid() -> uuid.UUID:
    return uuid.uuid4()


# ============================================================
# TIER 0 — REFERENCE / LOOKUP TABLES
# ============================================================

class State(Base):
    __tablename__ = "state"
    state_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    state_name: Mapped[str] = mapped_column(String(100), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class District(Base):
    __tablename__ = "district"

    district_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    district_code: Mapped[str] = mapped_column(String(10), unique=True, nullable=False)
    district_name: Mapped[str] = mapped_column(String(120), nullable=False)
    historical_data_name: Mapped[Optional[str]] = mapped_column(String(120))
    state_id: Mapped[int] = mapped_column(Integer, ForeignKey("state.state_id"), default=1)
    jurisdiction_type = mapped_column(jurisdiction_type_enum, nullable=False, default="district")
    is_geographic_district: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    parent_district_code: Mapped[Optional[str]] = mapped_column(String(10), ForeignKey("district.district_code"))
    centroid = mapped_column(Geometry("POINT", srid=4326), nullable=True)
    boundary = mapped_column(Geometry("MULTIPOLYGON", srid=4326), nullable=True)
    population_2011_census: Mapped[Optional[int]] = mapped_column(Integer)
    data_available_from: Mapped[int] = mapped_column(Integer, default=2013)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CrimeHead(Base):
    __tablename__ = "crime_head"
    crime_head_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crime_group_name: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class CrimeSubHead(Base):
    __tablename__ = "crime_sub_head"
    crime_sub_head_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    crime_head_id: Mapped[int] = mapped_column(Integer, ForeignKey("crime_head.crime_head_id"), nullable=False)
    crime_head_name: Mapped[str] = mapped_column(String(150), nullable=False)
    historical_csv_column: Mapped[Optional[str]] = mapped_column(String(150))
    is_aggregate: Mapped[bool] = mapped_column(Boolean, default=False)
    seq_id: Mapped[Optional[int]] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Act(Base):
    __tablename__ = "act"
    act_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    act_description: Mapped[str] = mapped_column(String(200), nullable=False)
    short_name: Mapped[Optional[str]] = mapped_column(String(50))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Section(Base):
    __tablename__ = "section"
    section_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    act_code: Mapped[str] = mapped_column(String(20), ForeignKey("act.act_code"), primary_key=True)
    section_description: Mapped[Optional[str]] = mapped_column(String(300))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class CaseCategory(Base):
    __tablename__ = "case_category"
    case_category_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lookup_value: Mapped[str] = mapped_column(String(50), nullable=False)


class GravityOffence(Base):
    __tablename__ = "gravity_offence"
    gravity_offence_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    lookup_value: Mapped[str] = mapped_column(String(50), nullable=False)


class CaseStatusMaster(Base):
    __tablename__ = "case_status_master"
    case_status_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_status_name: Mapped[str] = mapped_column(String(50), nullable=False)


class UnitType(Base):
    __tablename__ = "unit_type"
    unit_type_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    unit_type_name: Mapped[str] = mapped_column(String(80), nullable=False)
    city_dist_state: Mapped[Optional[str]] = mapped_column(String(20))
    hierarchy: Mapped[Optional[int]] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Unit(Base):
    __tablename__ = "unit"
    unit_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    unit_name: Mapped[str] = mapped_column(String(150), nullable=False)
    type_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("unit_type.unit_type_id"))
    parent_unit: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("unit.unit_id"))
    state_id: Mapped[int] = mapped_column(Integer, ForeignKey("state.state_id"), default=1)
    district_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("district.district_id"))
    active: Mapped[bool] = mapped_column(Boolean, default=True)


# ============================================================
# TIER 1 — DISTRICT-LEVEL STATISTICS (REAL DATA)
# ============================================================

class DistrictCrimeStats(Base):
    __tablename__ = "district_crime_stats"
    __table_args__ = (UniqueConstraint("district_id", "crime_sub_head_id", "year"),)

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("district.district_id"), nullable=False)
    crime_sub_head_id: Mapped[int] = mapped_column(Integer, ForeignKey("crime_sub_head.crime_sub_head_id"), nullable=False)
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    incident_count: Mapped[int] = mapped_column(Integer, nullable=False)
    data_source = mapped_column(data_source_enum, nullable=False, default="ogd_official")
    source_file: Mapped[Optional[str]] = mapped_column(String(200))
    imported_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("district_id", "crime_sub_head_id", "year"),
        CheckConstraint("incident_count >= 0", name="chk_incident_count_nonneg"),
    )


class DistrictYearTotals(Base):
    __tablename__ = "district_year_totals"
    district_id: Mapped[int] = mapped_column(Integer, ForeignKey("district.district_id"), primary_key=True)
    year: Mapped[int] = mapped_column(Integer, primary_key=True)
    total_ipc_crimes: Mapped[int] = mapped_column(Integer, nullable=False)
    crime_rate_per_lakh: Mapped[Optional[float]] = mapped_column(Numeric(10, 2))


# ============================================================
# TIER 2 — INCIDENT-LEVEL SCHEMA (EMPTY, CCTNS-COMPATIBLE)
# ============================================================

class Rank(Base):
    __tablename__ = "rank"
    rank_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    rank_name: Mapped[str] = mapped_column(String(80), nullable=False)
    hierarchy: Mapped[Optional[int]] = mapped_column(Integer)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class Designation(Base):
    __tablename__ = "designation"
    designation_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    designation_name: Mapped[str] = mapped_column(String(100), nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    sort_order: Mapped[Optional[int]] = mapped_column(Integer)


class Employee(Base):
    __tablename__ = "employee"
    employee_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    district_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("district.district_id"))
    unit_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("unit.unit_id"))
    rank_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("rank.rank_id"))
    designation_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("designation.designation_id"))
    kgid: Mapped[Optional[str]] = mapped_column(String(30))
    first_name: Mapped[Optional[str]] = mapped_column(String(100))
    employee_dob: Mapped[Optional[date]] = mapped_column(Date)
    gender_id: Mapped[Optional[int]] = mapped_column(Integer)
    appointment_date: Mapped[Optional[date]] = mapped_column(Date)


class Court(Base):
    __tablename__ = "court"
    court_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    court_name: Mapped[str] = mapped_column(String(200), nullable=False)
    district_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("district.district_id"))
    state_id: Mapped[int] = mapped_column(Integer, ForeignKey("state.state_id"), default=1)
    active: Mapped[bool] = mapped_column(Boolean, default=True)


class CaseMaster(Base):
    __tablename__ = "case_master"
    __table_args__ = (
        CheckConstraint("latitude IS NULL OR latitude BETWEEN 11.5 AND 18.5", name="chk_lat_karnataka"),
        CheckConstraint("longitude IS NULL OR longitude BETWEEN 74.0 AND 78.6", name="chk_lng_karnataka"),
    )

    case_master_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    crime_no: Mapped[Optional[str]] = mapped_column(String(30), unique=True)
    case_no: Mapped[Optional[str]] = mapped_column(String(20))
    crime_registered_date: Mapped[Optional[date]] = mapped_column(Date)
    police_person_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("employee.employee_id"))
    police_station_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("unit.unit_id"))
    case_category_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("case_category.case_category_id"))
    gravity_offence_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("gravity_offence.gravity_offence_id"))
    crime_major_head_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("crime_head.crime_head_id"))
    crime_minor_head_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("crime_sub_head.crime_sub_head_id"))
    case_status_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("case_status_master.case_status_id"))
    court_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("court.court_id"))
    incident_from_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    incident_to_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    info_received_ps_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    latitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    longitude: Mapped[Optional[float]] = mapped_column(Numeric(10, 7))
    brief_facts: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ComplainantDetails(Base):
    __tablename__ = "complainant_details"
    complainant_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_master_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("case_master.case_master_id", ondelete="CASCADE"))
    complainant_name: Mapped[Optional[str]] = mapped_column(String(200))
    age_year: Mapped[Optional[int]] = mapped_column(Integer)
    occupation_id: Mapped[Optional[int]] = mapped_column(Integer)
    religion_id: Mapped[Optional[int]] = mapped_column(Integer)
    caste_id: Mapped[Optional[int]] = mapped_column(Integer)
    gender_id: Mapped[Optional[int]] = mapped_column(Integer)


class Victim(Base):
    __tablename__ = "victim"
    victim_master_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_master_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("case_master.case_master_id", ondelete="CASCADE"))
    victim_name: Mapped[Optional[str]] = mapped_column(String(200))
    age_year: Mapped[Optional[int]] = mapped_column(Integer)
    gender_id: Mapped[Optional[int]] = mapped_column(Integer)
    victim_police: Mapped[bool] = mapped_column(Boolean, default=False)


class Accused(Base):
    __tablename__ = "accused"
    accused_master_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_master_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("case_master.case_master_id", ondelete="CASCADE"))
    accused_name: Mapped[Optional[str]] = mapped_column(String(200))
    age_year: Mapped[Optional[int]] = mapped_column(Integer)
    gender_id: Mapped[Optional[int]] = mapped_column(Integer)
    person_id: Mapped[Optional[str]] = mapped_column(String(10))


class ArrestSurrender(Base):
    __tablename__ = "arrest_surrender"
    arrest_surrender_id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    case_master_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("case_master.case_master_id", ondelete="CASCADE"))
    arrest_surrender_type_id: Mapped[Optional[int]] = mapped_column(Integer)
    arrest_surrender_date: Mapped[Optional[date]] = mapped_column(Date)
    arrest_surrender_state_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("state.state_id"))
    arrest_surrender_district_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("district.district_id"))
    police_station_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("unit.unit_id"))
    io_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("employee.employee_id"))
    court_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("court.court_id"))
    accused_master_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("accused.accused_master_id"))
    is_accused: Mapped[bool] = mapped_column(Boolean, default=True)
    is_complainant_accused: Mapped[bool] = mapped_column(Boolean, default=False)


class ActSectionAssociation(Base):
    __tablename__ = "act_section_association"
    case_master_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("case_master.case_master_id", ondelete="CASCADE"), primary_key=True)
    act_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    section_code: Mapped[str] = mapped_column(String(20), primary_key=True)
    act_order_id: Mapped[Optional[int]] = mapped_column(Integer)
    section_order_id: Mapped[Optional[int]] = mapped_column(Integer)


class ChargesheetDetails(Base):
    __tablename__ = "chargesheet_details"
    cs_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_master_id: Mapped[Optional[int]] = mapped_column(BigInteger, ForeignKey("case_master.case_master_id", ondelete="CASCADE"))
    cs_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    cs_type: Mapped[Optional[str]] = mapped_column(String(1))
    police_person_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("employee.employee_id"))


# ============================================================
# APPLICATION TABLES
# ============================================================

class AppUser(Base):
    __tablename__ = "app_user"
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=gen_uuid)
    email: Mapped[str] = mapped_column(String(200), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(200))
    role = mapped_column(user_role_enum, nullable=False, default="analyst")
    district_ids: Mapped[Optional[list]] = mapped_column(ARRAY(Integer), default=list)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    hashed_pw: Mapped[str] = mapped_column(Text, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    __tablename__ = "audit_log"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(UUID, ForeignKey("app_user.id"))
    action: Mapped[str] = mapped_column(String(100), nullable=False)
    resource: Mapped[Optional[str]] = mapped_column(String(100))
    resource_id: Mapped[Optional[str]] = mapped_column(String(100))
    ip_address: Mapped[Optional[str]] = mapped_column(String(64))
    payload: Mapped[dict] = mapped_column(JSONB, default=dict)
    outcome: Mapped[str] = mapped_column(String(20), default="success")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class FeatureFlag(Base):
    __tablename__ = "feature_flag"
    flag_key: Mapped[str] = mapped_column(String(80), primary_key=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AgentTask(Base):
    __tablename__ = "agent_task"
    id: Mapped[uuid.UUID] = mapped_column(UUID, primary_key=True, default=gen_uuid)
    task_id: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    agent_name: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    result: Mapped[Optional[dict]] = mapped_column(JSONB)
    error: Mapped[Optional[str]] = mapped_column(Text)
    duration_ms: Mapped[Optional[int]] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

class PdfIntelligenceData(Base):
    __tablename__ = "pdf_intelligence_data"
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    filename: Mapped[str] = mapped_column(String(255), nullable=False)
    extracted_text: Mapped[Optional[str]] = mapped_column(Text)
    parsed_json: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
