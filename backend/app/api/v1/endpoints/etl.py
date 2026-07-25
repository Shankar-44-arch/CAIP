from fastapi import APIRouter, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import logging
import traceback

from app.core.db import AsyncSessionLocal
from scripts.etl.import_district_data import parse_district_csv_content, load_into_postgres

logger = logging.getLogger("caip_karnataka")
router = APIRouter()

@router.post("/upload", tags=["ETL"])
async def upload_csv(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    try:
        content = await file.read()
        try:
            content_str = content.decode("utf-8-sig")
        except UnicodeDecodeError:
            content_str = content.decode("latin1")
        
        # Parse the CSV content
        structured_rows, stats = parse_district_csv_content(content_str, file.filename, target_state="KARNATAKA")
        
        if stats.unmapped_districts:
            raise HTTPException(
                status_code=400,
                detail=f"Unmapped districts found: {sorted(stats.unmapped_districts)}. Please map them in data/district_mapping.py."
            )
            
        # Load into postgres
        await load_into_postgres(structured_rows)
        
        return JSONResponse(content={
            "success": True,
            "message": f"Successfully imported {stats.rows_imported} rows.",
            "stats": {
                "rows_read": stats.rows_read,
                "rows_imported": stats.rows_imported,
                "rows_skipped": len(stats.rows_skipped),
                "districts_seen": len(stats.districts_seen)
            }
        })
    except HTTPException:
        raise
    except ValueError as e:
        logger.error(f"Validation error during CSV upload: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error during CSV upload: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"An error occurred while processing the file: {str(e)}")
