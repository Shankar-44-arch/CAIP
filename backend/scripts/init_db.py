import asyncio
import logging
import ssl
import subprocess
import sys
from pathlib import Path

# Add backend directory to python path
_THIS_FILE = Path(__file__).resolve()
_BACKEND_DIR = _THIS_FILE.parent.parent
sys.path.insert(0, str(_BACKEND_DIR))

import asyncpg
from app.core.config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("db_init")


async def init_database():
    if not settings.DATABASE_URL:
        logger.error("DATABASE_URL is not set. Cannot initialize database.")
        sys.exit(1)

    url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    if settings.database_ssl_enabled:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
    else:
        ssl_context = None

    logger.info("Connecting to database...")
    try:
        conn = await asyncpg.connect(url, ssl=ssl_context)
    except Exception as e:
        logger.error(f"Failed to connect to database: {e}")
        sys.exit(1)

    try:
        # Check if district table already exists (idempotency guard)
        table_exists = await conn.fetchval(
            "SELECT EXISTS (SELECT FROM pg_tables WHERE schemaname = 'public' AND tablename = 'district');"
        )

        if table_exists:
            logger.info("Database tables already exist. Skipping schema initialization.")
            return

        logger.info("Database tables not found. Initializing database schema...")

        schema_path = _BACKEND_DIR / "database_schema.sql"
        if not schema_path.exists():
            logger.error(f"Schema file not found at {schema_path}")
            sys.exit(1)

        with open(schema_path, "r", encoding="utf-8") as f:
            schema_sql = f.read()

        # Check if PostGIS is available. On local dev installs it often isn't;
        # on managed hosts (Render, Supabase, Neon) it is. Strip PostGIS-dependent
        # DDL gracefully so the init works in both environments.
        postgis_available = await conn.fetchval(
            "SELECT COUNT(*) FROM pg_available_extensions WHERE name = 'postgis';"
        )
        if not postgis_available:
            logger.warning(
                "PostGIS extension not available on this server — stripping "
                "PostGIS-dependent DDL (geometry columns, GIST indexes) for local dev. "
                "Geometry columns (centroid, boundary) will be omitted."
            )
            stripped_lines = []
            for line in schema_sql.splitlines():
                upper = line.strip().upper()
                if "POSTGIS" in upper:
                    continue
                if "GEOMETRY(" in upper:
                    # Replace the column definition with a comment so commas aren't orphaned
                    continue
                if "USING GIST" in upper:
                    continue
                stripped_lines.append(line)
            schema_sql = "\n".join(stripped_lines)

        logger.info("Executing database_schema.sql...")
        await conn.execute(schema_sql)
        logger.info("Database schema applied successfully.")

    finally:
        await conn.close()

    # Run the ETL pipeline to import all OGD district CSVs
    logger.info("Running OGD district data ETL pipeline...")
    etl_script = _BACKEND_DIR / "scripts" / "etl" / "import_district_data.py"
    # The repo root is one level above the backend dir
    repo_root = _BACKEND_DIR.parent
    import glob as _glob
    csv_files = sorted(_glob.glob(str(repo_root / "data" / "raw" / "dstrIPC_*.csv")))
    if not csv_files:
        logger.warning("No OGD CSV files found in data/raw/ — skipping ETL import.")
    else:
        for csv_path in csv_files:
            logger.info(f"Importing {csv_path} ...")
            try:
                subprocess.run(
                    [sys.executable, str(etl_script), "--file", csv_path],
                    check=True
                )
            except subprocess.CalledProcessError as e:
                logger.error(f"ETL pipeline failed for {csv_path}: {e}")
                sys.exit(1)
        logger.info("ETL pipeline completed successfully.")

    # Seed synthetic population figures so crime-rate-per-lakh can be computed
    logger.info("Running population seeding script...")
    seed_script = _BACKEND_DIR / "scripts" / "db" / "seed_population.py"
    try:
        subprocess.run([sys.executable, str(seed_script)], check=True)
        logger.info("Population seeding completed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Population seeding failed: {e}")
        sys.exit(1)

    logger.info("Database initialization completed successfully!")


if __name__ == "__main__":
    asyncio.run(init_database())
