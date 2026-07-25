-- ============================================================
-- CAIP-Karnataka PostgreSQL Schema
-- ============================================================
-- Designed to be a genuine SUBSET of the official Karnataka Police
-- FIR system schema (see docs/Police_FIR_ER_Diagram source), extended
-- with OGD-sourced district statistical tables.
--
-- Two-tier design:
--   TIER 1 (populated now): district-level annual statistics from
--     real OGD data — districts, crime_head, crime_sub_head,
--     district_crime_stats.
--   TIER 2 (schema-ready, empty until real CCTNS access exists):
--     case_master, victim, accused, arrest_surrender, complainant_details
--     etc. — mirrors the official ER diagram exactly so that if/when
--     KSCRB provides real CCTNS extract access, this schema accepts it
--     with zero structural changes.
--
-- NEVER seed Tier 2 tables with fabricated rows. They exist empty
-- until real data arrives. See docs/DATA_LIMITATIONS.md.
-- ============================================================

CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- ── ENUM TYPES ────────────────────────────────────────────────
CREATE TYPE jurisdiction_type AS ENUM ('district', 'commissionerate', 'rural_unit', 'cross_district_unit');
CREATE TYPE case_status_enum  AS ENUM ('under_investigation', 'charge_sheeted', 'closed', 'undetected', 'false_case');
CREATE TYPE user_role         AS ENUM ('analyst', 'supervisor', 'admin', 'readonly');
CREATE TYPE data_source_enum  AS ENUM ('ogd_official', 'kscrb_official', 'derived_calculation', 'user_entered');

-- ============================================================
-- TIER 0 — REFERENCE / LOOKUP TABLES (real, from ER diagram)
-- ============================================================

CREATE TABLE state (
    state_id     SERIAL PRIMARY KEY,
    state_name   VARCHAR(100) NOT NULL,
    active       BOOLEAN DEFAULT TRUE
);
INSERT INTO state (state_name) VALUES ('Karnataka');

-- Districts — seeded from real OGD + current official Karnataka list.
-- is_geographic_district = FALSE for non-geographic units like GRP.
CREATE TABLE district (
    district_id           SERIAL PRIMARY KEY,
    district_code         VARCHAR(10) UNIQUE NOT NULL,   -- e.g. 'BLR', 'MYS'
    district_name         VARCHAR(120) NOT NULL,          -- official current name
    historical_data_name         VARCHAR(120),                   -- original OGD CSV label, kept for traceability
    state_id              INT REFERENCES state(state_id) DEFAULT 1,
    jurisdiction_type      jurisdiction_type NOT NULL DEFAULT 'district',
    is_geographic_district BOOLEAN NOT NULL DEFAULT TRUE,  -- FALSE for GRP (railways)
    parent_district_code   VARCHAR(10) REFERENCES district(district_code),
                                          -- e.g. HDU (commissionerate) -> DWD (parent revenue district)
    centroid              GEOMETRY(POINT, 4326),          -- HQ-town centroid (see karnataka_geo_reference.py)
    boundary               GEOMETRY(MULTIPOLYGON, 4326),   -- populated from OSM boundary import (optional)
    population_2011_census INTEGER,                        -- for per-capita rate calc, added via Census import
    data_available_from   INTEGER DEFAULT 2013,            -- year this district's series starts (e.g. 2021 for Vijayanagara)
    active                BOOLEAN DEFAULT TRUE,
    notes                 TEXT,                            -- transparency notes from district_mapping.py
    created_at            TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_district_centroid ON district USING GIST (centroid);
CREATE INDEX idx_district_code ON district (district_code);

-- Two-level crime classification, mirroring CrimeHead / CrimeSubHead
-- from the official ER diagram.
CREATE TABLE crime_head (
    crime_head_id    SERIAL PRIMARY KEY,
    crime_group_name VARCHAR(120) UNIQUE NOT NULL,  -- e.g. 'Crimes Against Body'
    active           BOOLEAN DEFAULT TRUE
);

CREATE TABLE crime_sub_head (
    crime_sub_head_id SERIAL PRIMARY KEY,
    crime_head_id     INT REFERENCES crime_head(crime_head_id) NOT NULL,
    crime_head_name   VARCHAR(150) NOT NULL,   -- e.g. 'Murder', 'Theft (Total)'
    historical_csv_column   VARCHAR(150),             -- traceability back to source CSV column
    is_aggregate      BOOLEAN DEFAULT FALSE,    -- TRUE if this rolls up other sub-heads (e.g. 'Theft (Total)')
    seq_id            INT,
    active            BOOLEAN DEFAULT TRUE
);
CREATE INDEX idx_crimesubhead_head ON crime_sub_head (crime_head_id);

-- Act / Section reference (matches ER diagram exactly; IPC seeded,
-- BNS-2023 sections can be added later without schema change)
CREATE TABLE act (
    act_code        VARCHAR(20) PRIMARY KEY,
    act_description VARCHAR(200) NOT NULL,
    short_name      VARCHAR(50),
    active          BOOLEAN DEFAULT TRUE
);
INSERT INTO act (act_code, act_description, short_name) VALUES
    ('IPC', 'Indian Penal Code, 1860', 'IPC'),
    ('BNS', 'Bharatiya Nyaya Sanhita, 2023', 'BNS'),
    ('NDPS', 'Narcotic Drugs and Psychotropic Substances Act, 1985', 'NDPS'),
    ('POCSO', 'Protection of Children from Sexual Offences Act, 2012', 'POCSO'),
    ('IT_ACT', 'Information Technology Act, 2000', 'IT Act');

CREATE TABLE section (
    section_code        VARCHAR(20),
    act_code            VARCHAR(20) REFERENCES act(act_code),
    section_description VARCHAR(300),
    active              BOOLEAN DEFAULT TRUE,
    PRIMARY KEY (act_code, section_code)
);

CREATE TABLE crime_head_act_section (
    crime_head_id INT REFERENCES crime_head(crime_head_id),
    act_code      VARCHAR(20) REFERENCES act(act_code),
    section_code  VARCHAR(20),
    PRIMARY KEY (crime_head_id, act_code, section_code)
);

CREATE TABLE case_category (
    case_category_id SERIAL PRIMARY KEY,
    lookup_value     VARCHAR(50) NOT NULL   -- FIR, UDR, PAR, Zero FIR
);
INSERT INTO case_category (lookup_value) VALUES ('FIR'), ('UDR'), ('PAR'), ('Zero FIR');

CREATE TABLE gravity_offence (
    gravity_offence_id SERIAL PRIMARY KEY,
    lookup_value       VARCHAR(50) NOT NULL   -- Heinous / Non-Heinous
);
INSERT INTO gravity_offence (lookup_value) VALUES ('Heinous'), ('Non-Heinous');

CREATE TABLE case_status_master (
    case_status_id   SERIAL PRIMARY KEY,
    case_status_name VARCHAR(50) NOT NULL
);
INSERT INTO case_status_master (case_status_name) VALUES
    ('Under Investigation'), ('Charge Sheeted'), ('Closed'), ('Undetected');

CREATE TABLE unit_type (
    unit_type_id     SERIAL PRIMARY KEY,
    unit_type_name   VARCHAR(80) NOT NULL,   -- Police Station, Circle Office, Commissionerate
    city_dist_state  VARCHAR(20),             -- City / District / State
    hierarchy        INT,
    active           BOOLEAN DEFAULT TRUE
);

CREATE TABLE unit (
    unit_id      SERIAL PRIMARY KEY,
    unit_name    VARCHAR(150) NOT NULL,     -- police station / commissionerate name
    type_id      INT REFERENCES unit_type(unit_type_id),
    parent_unit  INT REFERENCES unit(unit_id),
    state_id     INT REFERENCES state(state_id) DEFAULT 1,
    district_id  INT REFERENCES district(district_id),
    active       BOOLEAN DEFAULT TRUE
);

-- ============================================================
-- TIER 1 — DISTRICT-LEVEL STATISTICS (REAL DATA, POPULATED NOW)
-- ============================================================

-- One row per (district, crime_sub_head, year) — this is the direct
-- structured import target for dstrIPC_2013.csv and any future OGD
-- year files placed alongside it.
CREATE TABLE district_crime_stats (
    id                 BIGSERIAL PRIMARY KEY,
    district_id        INT REFERENCES district(district_id) NOT NULL,
    crime_sub_head_id  INT REFERENCES crime_sub_head(crime_sub_head_id) NOT NULL,
    year               INT NOT NULL,
    incident_count     INTEGER NOT NULL CHECK (incident_count >= 0),
    data_source        data_source_enum NOT NULL DEFAULT 'ogd_official',
    source_file        VARCHAR(200),   -- e.g. 'dstrIPC_2013.csv' — full traceability
    imported_at        TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE (district_id, crime_sub_head_id, year)
);
CREATE INDEX idx_dcs_district_year ON district_crime_stats (district_id, year);
CREATE INDEX idx_dcs_subhead_year  ON district_crime_stats (crime_sub_head_id, year);
CREATE INDEX idx_dcs_year          ON district_crime_stats (year);

-- Pre-aggregated per-district-per-year total (materialized on import
-- for fast dashboard queries; equals sum of non-aggregate sub-head rows)
CREATE TABLE district_year_totals (
    district_id     INT REFERENCES district(district_id) NOT NULL,
    year            INT NOT NULL,
    total_ipc_crimes INTEGER NOT NULL,
    crime_rate_per_lakh NUMERIC(10,2),   -- NULL until population data is loaded
    PRIMARY KEY (district_id, year)
);
CREATE INDEX idx_dyt_year ON district_year_totals (year);

-- ============================================================
-- TIER 2 — INCIDENT-LEVEL SCHEMA (EMPTY, CCTNS-COMPATIBLE)
-- These tables mirror the official Karnataka Police FIR ER diagram
-- field-for-field. They remain EMPTY until real CCTNS/KSCRB incident
-- data access is granted. Application code must check row counts and
-- clearly label any UI section built on these tables as
-- "Awaiting live police data integration" rather than hide the
-- feature or fabricate rows. See docs/DATA_LIMITATIONS.md.
-- ============================================================

CREATE TABLE rank (
    rank_id   SERIAL PRIMARY KEY,
    rank_name VARCHAR(80) NOT NULL,
    hierarchy INT,
    active    BOOLEAN DEFAULT TRUE
);

CREATE TABLE designation (
    designation_id SERIAL PRIMARY KEY,
    designation_name VARCHAR(100) NOT NULL,
    active         BOOLEAN DEFAULT TRUE,
    sort_order     INT
);

CREATE TABLE employee (
    employee_id       SERIAL PRIMARY KEY,
    district_id       INT REFERENCES district(district_id),
    unit_id           INT REFERENCES unit(unit_id),
    rank_id           INT REFERENCES rank(rank_id),
    designation_id    INT REFERENCES designation(designation_id),
    kgid              VARCHAR(30),        -- Karnataka Govt ID — real PII, never fabricate
    first_name        VARCHAR(100),
    employee_dob      DATE,
    gender_id         INT,
    appointment_date  DATE
);

CREATE TABLE court (
    court_id     SERIAL PRIMARY KEY,
    court_name   VARCHAR(200) NOT NULL,
    district_id  INT REFERENCES district(district_id),
    state_id     INT REFERENCES state(state_id) DEFAULT 1,
    active       BOOLEAN DEFAULT TRUE
);

CREATE TABLE case_master (
    case_master_id       BIGSERIAL PRIMARY KEY,
    crime_no             VARCHAR(30) UNIQUE,     -- structured 18-digit format per ER diagram
    case_no              VARCHAR(20),
    crime_registered_date DATE,
    police_person_id     INT REFERENCES employee(employee_id),
    police_station_id    INT REFERENCES unit(unit_id),
    case_category_id     INT REFERENCES case_category(case_category_id),
    gravity_offence_id   INT REFERENCES gravity_offence(gravity_offence_id),
    crime_major_head_id  INT REFERENCES crime_head(crime_head_id),
    crime_minor_head_id  INT REFERENCES crime_sub_head(crime_sub_head_id),
    case_status_id       INT REFERENCES case_status_master(case_status_id),
    court_id             INT REFERENCES court(court_id),
    incident_from_date   TIMESTAMPTZ,
    incident_to_date     TIMESTAMPTZ,
    info_received_ps_date TIMESTAMPTZ,
    latitude             DECIMAL(10,7),   -- REAL incident coordinates, when CCTNS access exists
    longitude            DECIMAL(10,7),
    brief_facts          TEXT,
    created_at           TIMESTAMPTZ DEFAULT NOW(),
    CONSTRAINT chk_lat_karnataka CHECK (latitude IS NULL OR latitude BETWEEN 11.5 AND 18.5),
    CONSTRAINT chk_lng_karnataka CHECK (longitude IS NULL OR longitude BETWEEN 74.0 AND 78.6)
);
CREATE INDEX idx_case_master_date ON case_master (crime_registered_date);
CREATE INDEX idx_case_master_station ON case_master (police_station_id);
-- Spatial index only useful once real lat/lng rows exist:
CREATE INDEX idx_case_master_geo ON case_master (latitude, longitude)
    WHERE latitude IS NOT NULL AND longitude IS NOT NULL;

CREATE TABLE complainant_details (
    complainant_id   SERIAL PRIMARY KEY,
    case_master_id   BIGINT REFERENCES case_master(case_master_id) ON DELETE CASCADE,
    complainant_name VARCHAR(200),
    age_year         INT,
    occupation_id    INT,
    religion_id      INT,
    caste_id         INT,
    gender_id        INT
);

CREATE TABLE victim (
    victim_master_id BIGSERIAL PRIMARY KEY,
    case_master_id   BIGINT REFERENCES case_master(case_master_id) ON DELETE CASCADE,
    victim_name      VARCHAR(200),
    age_year         INT,
    gender_id        INT,
    victim_police    BOOLEAN DEFAULT FALSE
);

CREATE TABLE accused (
    accused_master_id BIGSERIAL PRIMARY KEY,
    case_master_id    BIGINT REFERENCES case_master(case_master_id) ON DELETE CASCADE,
    accused_name      VARCHAR(200),
    age_year          INT,
    gender_id         INT,
    person_id         VARCHAR(10)   -- A1, A2, A3...
);

CREATE TABLE arrest_surrender (
    arrest_surrender_id      BIGSERIAL PRIMARY KEY,
    case_master_id           BIGINT REFERENCES case_master(case_master_id) ON DELETE CASCADE,
    arrest_surrender_type_id INT,
    arrest_surrender_date    DATE,
    arrest_surrender_state_id INT REFERENCES state(state_id),
    arrest_surrender_district_id INT REFERENCES district(district_id),
    police_station_id        INT REFERENCES unit(unit_id),
    io_id                    INT REFERENCES employee(employee_id),
    court_id                 INT REFERENCES court(court_id),
    accused_master_id        BIGINT REFERENCES accused(accused_master_id),
    is_accused               BOOLEAN DEFAULT TRUE,
    is_complainant_accused   BOOLEAN DEFAULT FALSE
);

CREATE TABLE act_section_association (
    case_master_id BIGINT REFERENCES case_master(case_master_id) ON DELETE CASCADE,
    act_code       VARCHAR(20),
    section_code   VARCHAR(20),
    act_order_id   INT,
    section_order_id INT,
    PRIMARY KEY (case_master_id, act_code, section_code)
);

CREATE TABLE chargesheet_details (
    cs_id            SERIAL PRIMARY KEY,
    case_master_id   BIGINT REFERENCES case_master(case_master_id) ON DELETE CASCADE,
    cs_date          TIMESTAMPTZ,
    cs_type          CHAR(1),   -- A=Chargesheet, B=False Case, C=Undetected
    police_person_id INT REFERENCES employee(employee_id)
);

-- ============================================================
-- APPLICATION TABLES (users, audit, agent tasks, feature flags)
-- ============================================================

CREATE TABLE app_user (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email        VARCHAR(200) UNIQUE NOT NULL,
    username     VARCHAR(80) UNIQUE NOT NULL,
    full_name    VARCHAR(200),
    role         user_role NOT NULL DEFAULT 'analyst',
    district_ids INT[] DEFAULT '{}',
    is_active    BOOLEAN DEFAULT TRUE,
    hashed_pw    TEXT NOT NULL,
    last_login   TIMESTAMPTZ,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE audit_log (
    id          BIGSERIAL PRIMARY KEY,
    user_id     UUID REFERENCES app_user(id),
    action      VARCHAR(100) NOT NULL,
    resource    VARCHAR(100),
    resource_id VARCHAR(100),
    ip_address  INET,
    payload     JSONB DEFAULT '{}'::JSONB,
    outcome     VARCHAR(20) DEFAULT 'success',
    created_at  TIMESTAMPTZ DEFAULT NOW()
);
CREATE INDEX idx_audit_user ON audit_log (user_id, created_at DESC);

-- Feature flags gate features that require data we don't have yet.
-- Application code MUST check these before rendering/enabling a
-- feature — never bypass. See docs/DATA_LIMITATIONS.md for rationale.
CREATE TABLE feature_flag (
    flag_key    VARCHAR(80) PRIMARY KEY,
    is_enabled  BOOLEAN NOT NULL DEFAULT FALSE,
    reason      TEXT,
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);
INSERT INTO feature_flag (flag_key, is_enabled, reason) VALUES
    ('ENABLE_NETWORK_ANALYSIS', FALSE,
     'No offender relationship data available in any public source. Requires KSCRB intelligence data access.'),
    ('ENABLE_OFFENDER_TRACKING', FALSE,
     'No offender-level public data exists. Requires CCTNS Accused/ArrestSurrender data access.'),
    ('ENABLE_ANOMALY_DETECTION', FALSE,
     'Requires multi-point time series per district (monthly+); only annual totals currently loaded.'),
    ('ENABLE_ML_PREDICTION', FALSE,
     'Requires 3+ years of district data for any statistically defensible model; only 2013 currently loaded.'),
    ('ENABLE_PER_CAPITA_RATES', FALSE,
     'Requires Census population data import — not yet loaded.');

CREATE TABLE agent_task (
    id           UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    task_id      VARCHAR(120) UNIQUE NOT NULL,
    agent_name   VARCHAR(80) NOT NULL,
    status       VARCHAR(20) DEFAULT 'pending',
    result       JSONB,
    error        TEXT,
    duration_ms  INTEGER,
    created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ── updated_at trigger (reused across tables) ────────────────
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$;

CREATE TABLE pdf_intelligence_data (
    id BIGSERIAL PRIMARY KEY,
    filename VARCHAR(255) NOT NULL,
    extracted_text TEXT,
    parsed_json JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
