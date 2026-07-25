"""
CAIP-Karnataka — OGD District Crime Data ETL Pipeline
=========================================================
Imports data/raw/dstrIPC_2013.csv (and any additional OGD year files
placed in the same directory following the same column structure) into
the PostgreSQL district_crime_stats / district_year_totals tables.

Design principles:
  1. TRACEABILITY — every imported row stores its source_file so any
     number in the dashboard can be traced back to the exact CSV file
     and row it came from.
  2. NO FABRICATION — rows with missing/non-numeric values are logged
     as skipped, never coerced to 0 or guessed.
  3. IDEMPOTENT — re-running the import for the same file is safe
     (uses ON CONFLICT ... DO UPDATE keyed on district+subhead+year).
  4. VALIDATES AGAINST district_mapping.py — any CSV district name not
     in our reconciliation table raises an error rather than silently
     skipping or guessing a mapping.

Usage:
    python scripts/etl/import_district_data.py --file data/raw/dstrIPC_2013.csv
    python scripts/etl/import_district_data.py --all-years   # scans data/raw/ for dstrIPC_*.csv
"""
from __future__ import annotations

import argparse
import asyncio
import csv
import glob
import logging
import re
import sys
from pathlib import Path

_THIS_FILE = Path(__file__).resolve()
_BACKEND_DIR = _THIS_FILE.parents[2]     # .../caip-karnataka/backend
_REPO_ROOT = _THIS_FILE.parents[3]       # .../caip-karnataka
sys.path.insert(0, str(_REPO_ROOT))      # so `import data.*` resolves
sys.path.insert(0, str(_BACKEND_DIR))    # so `import app.*` resolves

from data.district_mapping import DISTRICT_MAPPINGS, DistrictMapping
from data.crime_category_mapping import CRIME_CATEGORY_MAPPINGS, CrimeSubHeadMapping
from data.karnataka_geo_reference import KARNATAKA_DISTRICT_CENTROIDS

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("etl")


class ImportStats:
    def __init__(self):
        self.rows_read = 0
        self.rows_imported = 0
        self.rows_skipped: list[dict] = []
        self.districts_seen: set[str] = set()
        self.unmapped_districts: set[str] = set()

    def summary(self) -> str:
        return (
            f"Rows read: {self.rows_read} | Imported: {self.rows_imported} | "
            f"Skipped: {len(self.rows_skipped)} | "
            f"Districts recognized: {len(self.districts_seen)} | "
            f"Unmapped districts: {sorted(self.unmapped_districts) if self.unmapped_districts else 'none'}"
        )


def build_district_lookup() -> dict[str, DistrictMapping]:
    """CSV district name (normalized) -> DistrictMapping"""
    return {m.historical_data_name.strip().upper(): m for m in DISTRICT_MAPPINGS}


def build_crime_column_lookup() -> dict[str, CrimeSubHeadMapping]:
    """CSV column name (normalized) -> CrimeSubHeadMapping"""
    return {m.csv_column.strip().upper(): m for m in CRIME_CATEGORY_MAPPINGS}


def extract_year_from_filename(filepath: str) -> int | None:
    match = re.search(r"(\d{4})", Path(filepath).stem)
    return int(match.group(1)) if match else None


def parse_district_csv(filepath: str, target_state: str = "KARNATAKA") -> tuple[list[dict], ImportStats]:
    """
    Parses one OGD district-wise CSV file from disk.
    """
    with open(filepath, "r", encoding="utf-8-sig") as f:
        content = f.read()
    return parse_district_csv_content(content, Path(filepath).name, target_state)


def parse_district_csv_content(content: str, filename: str, target_state: str = "KARNATAKA") -> tuple[list[dict], ImportStats]:
    """
    Parses OGD CSV content directly (useful for API uploads), filters to the target state,
    and returns structured rows ready for DB insertion, alongside detailed stats.
    """
    import io
    stats = ImportStats()
    district_lookup = build_district_lookup()
    crime_column_lookup = build_crime_column_lookup()
    
    fallback_year = extract_year_from_filename(filename)
    if fallback_year is None:
        raise ValueError(
            f"Could not determine year from filename '{filename}'. "
            f"Expected a 4-digit year in the filename, e.g. 'dstrIPC_2013.csv'."
        )

    structured_rows = []
    
    f = io.StringIO(content)
    reader = csv.DictReader(f)

    # Validate expected columns exist before processing anything
    if not reader.fieldnames:
        return structured_rows, stats
    
    # Strip whitespace from all column headers
    reader.fieldnames = [str(f).strip() for f in reader.fieldnames]

    missing_cols = [c.csv_column for c in CRIME_CATEGORY_MAPPINGS if c.csv_column not in reader.fieldnames]
    if missing_cols:
        logger.warning(
            "File '%s' is missing %d expected crime columns: %s — those categories "
            "will simply have no data for this file, which is correct behavior "
            "(not every year's OGD file has identical columns).",
            filename, len(missing_cols), missing_cols,
        )

    for raw_row in reader:
        stats.rows_read += 1
        
        # Safe extraction supporting both 2012/2013 ("STATE/UT") and 2014 ("States/UTs") headers
        state = raw_row.get("STATE/UT", raw_row.get("States/UTs", "")).strip()
        district_raw = raw_row.get("DISTRICT", raw_row.get("District", "")).strip()
        
        row_year_str = raw_row.get("YEAR", raw_row.get("Year", "")).strip()
        year = int(row_year_str) if row_year_str else fallback_year

        if state.upper() != target_state.upper():
            continue  # not an error — just not Karnataka, skip silently

        if district_raw.upper() in ("ZZ TOTAL", "TOTAL"):
            continue  # state aggregate row, not a district — skip, don't import as invalid district

        mapping = district_lookup.get(district_raw.upper())
        if mapping is None:
            stats.unmapped_districts.add(district_raw)
            stats.rows_skipped.append({
                "reason": "unmapped_district",
                "district_raw": district_raw,
                "row_year": year,
            })
            continue

        stats.districts_seen.add(mapping.district_code)

        for col_name, crime_map in crime_column_lookup.items():
            # 2014 changed column names entirely (e.g. "Attempt to commit Murder" instead of "ATTEMPT TO MURDER").
            # Try exact match first, then fallback to case-insensitive match over all keys if necessary.
            raw_value = ""
            if col_name in raw_row:
                raw_value = raw_row[col_name].strip()
            else:
                for k, v in raw_row.items():
                    if k and k.strip().upper() == col_name.upper():
                        raw_value = v.strip()
                        break
                        
            if not raw_value:
                continue  # column doesn't exist in this file — not an error

            if raw_value == "" or raw_value.upper() in ("NA", "N/A", "-"):
                stats.rows_skipped.append({
                    "reason": "missing_value",
                    "district_raw": district_raw,
                    "column": col_name,
                    "row_year": year,
                })
                continue

            try:
                incident_count = int(raw_value)
            except ValueError:
                stats.rows_skipped.append({
                    "reason": "non_numeric_value",
                    "district_raw": district_raw,
                    "column": col_name,
                    "raw_value": raw_value,
                    "row_year": year,
                })
                continue

            if incident_count < 0:
                stats.rows_skipped.append({
                    "reason": "negative_value_rejected",
                    "district_raw": district_raw,
                    "column": col_name,
                    "raw_value": raw_value,
                    "row_year": year,
                })
                continue

            structured_rows.append({
                "district_code": mapping.district_code,
                "district_name": mapping.official_district,
                "csv_column": crime_map.csv_column,
                "crime_sub_head": crime_map.crime_sub_head,
                "crime_head_group": crime_map.crime_head_group,
                "is_aggregate": crime_map.is_aggregate,
                "year": year,
                "incident_count": incident_count,
                "source_file": filename,
            })
            stats.rows_imported += 1

    return structured_rows, stats


async def load_into_postgres(structured_rows: list[dict]) -> None:
    """Upserts structured rows into district / crime_head / crime_sub_head /
    district_crime_stats / district_year_totals tables. Idempotent."""
    from app.core.db import AsyncSessionLocal
    from sqlalchemy import text

    if not structured_rows:
        logger.warning("No structured rows to load — nothing will be written to the database.")
        return

    async with AsyncSessionLocal() as db:
        # 1. Ensure crime_head / crime_sub_head reference rows exist
        head_groups = {r["crime_head_group"] for r in structured_rows}
        for group in head_groups:
            await db.execute(
                text("""INSERT INTO crime_head (crime_group_name)
                        VALUES (:g) ON CONFLICT (crime_group_name) DO NOTHING"""),
                {"g": group},
            )
        await db.flush()

        sub_heads = {(r["crime_sub_head"], r["crime_head_group"], r["csv_column"], r["is_aggregate"]) for r in structured_rows}
        for sub_head_name, head_group, csv_col, is_agg in sub_heads:
            head_id_row = await db.execute(
                text("SELECT crime_head_id FROM crime_head WHERE crime_group_name = :g"),
                {"g": head_group},
            )
            head_id = head_id_row.scalar()
            await db.execute(
                text("""INSERT INTO crime_sub_head (crime_head_id, crime_head_name, historical_csv_column, is_aggregate)
                        VALUES (:hid, :name, :col, :agg)
                        ON CONFLICT DO NOTHING"""),
                {"hid": head_id, "name": sub_head_name, "col": csv_col, "agg": is_agg},
            )
        await db.flush()

        # 2. Ensure district rows exist (with centroid from geo reference if PostGIS available)
        districts = {(r["district_code"], r["district_name"]) for r in structured_rows}

        # Detect whether the centroid column exists (it's absent on non-PostGIS local DBs)
        centroid_col_exists_row = await db.execute(
            text("""SELECT COUNT(*) FROM information_schema.columns
                    WHERE table_name='district' AND column_name='centroid'""")
        )
        centroid_col_exists = centroid_col_exists_row.scalar() > 0

        for code, name in districts:
            centroid = KARNATAKA_DISTRICT_CENTROIDS.get(code)
            if centroid_col_exists and centroid and centroid[0] is not None:
                await db.execute(
                    text("""INSERT INTO district (district_code, district_name, centroid)
                             VALUES (:code, :name, ST_SetSRID(ST_MakePoint(:lng, :lat), 4326))
                             ON CONFLICT (district_code) DO UPDATE SET district_name = :name"""),
                    {"code": code, "name": name, "lat": centroid[0], "lng": centroid[1]},
                )
            else:
                await db.execute(
                    text("""INSERT INTO district (district_code, district_name)
                             VALUES (:code, :name)
                             ON CONFLICT (district_code) DO UPDATE SET district_name = :name"""),
                    {"code": code, "name": name},
                )
        await db.flush()

        # 3. Insert district_crime_stats rows (idempotent upsert)
        for row in structured_rows:
            sub_head_id_row = await db.execute(
                text("SELECT crime_sub_head_id FROM crime_sub_head WHERE historical_csv_column = :col"),
                {"col": row["csv_column"]},
            )
            sub_head_id = sub_head_id_row.scalar()

            district_id_row = await db.execute(
                text("SELECT district_id FROM district WHERE district_code = :code"),
                {"code": row["district_code"]},
            )
            district_id = district_id_row.scalar()

            await db.execute(
                text("""INSERT INTO district_crime_stats
                            (district_id, crime_sub_head_id, year, incident_count, data_source, source_file)
                        VALUES (:did, :shid, :yr, :cnt, 'ogd_official', :src)
                        ON CONFLICT (district_id, crime_sub_head_id, year)
                        DO UPDATE SET incident_count = :cnt, source_file = :src, imported_at = NOW()"""),
                {"did": district_id, "shid": sub_head_id, "yr": row["year"],
                 "cnt": row["incident_count"], "src": row["source_file"]},
            )

        # 4. Recompute district_year_totals from non-aggregate sub-heads only
        #    (avoids double-counting e.g. THEFT total + AUTO THEFT + OTHER THEFT)
        await db.execute(text("""
            INSERT INTO district_year_totals (district_id, year, total_ipc_crimes)
            SELECT dcs.district_id, dcs.year, SUM(dcs.incident_count)
            FROM district_crime_stats dcs
            JOIN crime_sub_head csh ON csh.crime_sub_head_id = dcs.crime_sub_head_id
            WHERE csh.is_aggregate = FALSE
            GROUP BY dcs.district_id, dcs.year
            ON CONFLICT (district_id, year)
            DO UPDATE SET total_ipc_crimes = EXCLUDED.total_ipc_crimes
        """))

        await db.commit()
        logger.info("Committed %d district_crime_stats rows to PostgreSQL.", len(structured_rows))


def main():
    parser = argparse.ArgumentParser(description="Import OGD Karnataka district crime CSVs")
    parser.add_argument("--file", type=str, help="Path to a single OGD CSV file")
    parser.add_argument("--all-years", action="store_true",
                        help="Scan data/raw/ for all dstrIPC_*.csv files and import each")
    parser.add_argument("--dry-run", action="store_true",
                        help="Parse and validate only; do not write to the database")
    args = parser.parse_args()

    if not args.file and not args.all_years:
        parser.error("Specify either --file <path> or --all-years")

    files = [args.file] if args.file else sorted(glob.glob("data/raw/dstrIPC_*.csv"))
    if not files:
        logger.error("No input files found.")
        sys.exit(1)

    all_rows = []
    for filepath in files:
        logger.info("Processing %s ...", filepath)
        rows, stats = parse_district_csv(filepath)
        logger.info("  %s", stats.summary())
        if stats.unmapped_districts:
            logger.error(
                "  UNMAPPED DISTRICTS FOUND in %s: %s — add these to data/district_mapping.py "
                "before importing. Refusing to guess a mapping.",
                filepath, sorted(stats.unmapped_districts),
            )
            sys.exit(1)
        if stats.rows_skipped:
            logger.warning("  %d rows skipped (missing/invalid values) — see details below:", len(stats.rows_skipped))
            for skip in stats.rows_skipped[:10]:
                logger.warning("    %s", skip)
            if len(stats.rows_skipped) > 10:
                logger.warning("    ... and %d more", len(stats.rows_skipped) - 10)
        all_rows.extend(rows)

    logger.info("Total structured rows ready for import: %d", len(all_rows))

    if args.dry_run:
        logger.info("Dry run complete — no data written to database.")
        return

    asyncio.run(load_into_postgres(all_rows))
    logger.info("Import complete.")


if __name__ == "__main__":
    main()
