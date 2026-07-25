import asyncio
from sqlalchemy import delete
from app.core.db import AsyncSessionLocal
from app.models.orm_models import PdfIntelligenceData

async def main():
    async with AsyncSessionLocal() as session:
        await session.execute(delete(PdfIntelligenceData))
        await session.commit()
        print("Successfully wiped PdfIntelligenceData.")

if __name__ == "__main__":
    asyncio.run(main())
