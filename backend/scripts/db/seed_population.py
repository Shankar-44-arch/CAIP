import asyncio
import random
import logging
import sys
from pathlib import Path

_THIS_FILE = Path(__file__).resolve()
_BACKEND_DIR = _THIS_FILE.parents[2]
sys.path.insert(0, str(_BACKEND_DIR))

from app.core.db import AsyncSessionLocal
from sqlalchemy import text

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("seed_population")

async def seed_population():
    async with AsyncSessionLocal() as db:
        # Fetch all geographic districts
        result = await db.execute(text("SELECT district_id, district_name FROM district WHERE is_geographic_district = TRUE"))
        districts = result.fetchall()
        
        if not districts:
            logger.info("No districts found. Run ETL script first.")
            return

        # Assign baseline population (between 500,000 and 10,000,000)
        logger.info(f"Seeding population data for {len(districts)} districts...")
        
        for d in districts:
            baseline_population = random.randint(500_000, 10_000_000)
            
            # Update district table
            await db.execute(
                text("UPDATE district SET population_2011_census = :pop WHERE district_id = :did"),
                {"pop": baseline_population, "did": d.district_id}
            )
            
            # Update district_year_totals
            await db.execute(
                text("""
                    UPDATE district_year_totals
                    SET crime_rate_per_lakh = (CAST(total_ipc_crimes AS numeric) / CAST(:pop AS numeric)) * 100000
                    WHERE district_id = :did
                """),
                {"pop": baseline_population, "did": d.district_id}
            )
            
        await db.commit()
        logger.info("Population data seeded and crime rates updated successfully.")

if __name__ == "__main__":
    asyncio.run(seed_population())
